#!/usr/bin/env python3
"""
Extract patches from regions where two fluorescent stains co-localize.
This script will:
1. Load both Iba1 and Abeta channels
2. Detect regions with high co-localization
3. Extract 3 patches from co-localized regions
4. Save patches for annotation with nnU-Net interactive
"""

import numpy as np
from pathlib import Path
import tifffile
from scipy import ndimage
from zarrnii import ZarrNii, ZarrNiiAtlas
from dask.diagnostics import ProgressBar


def calculate_colocalization_score(ch1, ch2, threshold_percentile=50):
    """
    Calculate co-localization score for two channels.

    Args:
        ch1: First channel (e.g., Iba1)
        ch2: Second channel (e.g., Abeta)
        threshold_percentile: Percentile for thresholding each channel

    Returns:
        Manders' colocalization coefficient and binary overlap mask
    """
    # Normalize channels
    ch1_norm = (ch1 - ch1.min()) / (ch1.max() - ch1.min() + 1e-10)
    ch2_norm = (ch2 - ch2.min()) / (ch2.max() - ch2.min() + 1e-10)

    # Threshold at specified percentile
    thresh1 = np.percentile(ch1_norm, threshold_percentile)
    thresh2 = np.percentile(ch2_norm, threshold_percentile)

    # Binary masks
    mask1 = ch1_norm > thresh1
    mask2 = ch2_norm > thresh2

    # Co-localization: both channels above threshold
    coloc_mask = mask1 & mask2

    # Manders' coefficient (fraction of ch1 signal that overlaps with ch2)
    if mask1.sum() > 0:
        manders_coeff = (ch1_norm[coloc_mask].sum() / ch1_norm[mask1].sum())
    else:
        manders_coeff = 0.0

    return manders_coeff, coloc_mask


def find_colocalization_hotspots(coloc_mask, num_patches=3, patch_size=(64, 64, 64)):
    """
    Find regions with highest co-localization density.

    Args:
        coloc_mask: Binary mask of co-localized voxels
        num_patches: Number of patches to extract
        patch_size: Size of each patch (Z, Y, X)

    Returns:
        List of patch center coordinates
    """
    # Create density map by convolving with a box kernel
    kernel_size = np.array(patch_size) // 2
    kernel = np.ones(kernel_size)

    density_map = ndimage.convolve(
        coloc_mask.astype(float),
        kernel,
        mode='constant'
    )

    # Find top N regions
    patch_centers = []
    volume_shape = np.array(coloc_mask.shape)

    for i in range(num_patches):
        # Find maximum
        max_idx = np.unravel_index(density_map.argmax(), density_map.shape)

        # Check if valid (not too close to edges)
        valid = True
        for dim in range(3):
            if (max_idx[dim] < patch_size[dim]//2 or
                max_idx[dim] > volume_shape[dim] - patch_size[dim]//2):
                valid = False
                break

        if valid:
            patch_centers.append(max_idx)

        # Zero out this region to find next hotspot
        z, y, x = max_idx
        pad = np.array(patch_size) // 2
        density_map[
            max(0, z-pad[0]):min(volume_shape[0], z+pad[0]),
            max(0, y-pad[1]):min(volume_shape[1], y+pad[1]),
            max(0, x-pad[2]):min(volume_shape[2], x+pad[2])
        ] = 0

    return patch_centers


def extract_patch(volume, center, patch_size=(64, 64, 64)):
    """
    Extract a patch from a volume centered at given coordinates.

    Args:
        volume: 3D or 4D numpy array (C, Z, Y, X) or (Z, Y, X)
        center: Tuple of (z, y, x) coordinates
        patch_size: Size of patch to extract

    Returns:
        Extracted patch
    """
    is_multichannel = volume.ndim == 4

    if is_multichannel:
        shape = volume.shape[1:]  # Skip channel dimension
    else:
        shape = volume.shape

    # Calculate bounds
    z, y, x = center
    pz, py, px = patch_size

    z_start = max(0, z - pz//2)
    z_end = min(shape[0], z + pz//2)
    y_start = max(0, y - py//2)
    y_end = min(shape[1], y + py//2)
    x_start = max(0, x - px//2)
    x_end = min(shape[2], x + px//2)

    if is_multichannel:
        patch = volume[:, z_start:z_end, y_start:y_end, x_start:x_end]
    else:
        patch = volume[z_start:z_end, y_start:y_end, x_start:x_end]

    # Pad if necessary to reach desired patch size
    if is_multichannel:
        actual_size = patch.shape[1:]
        if actual_size != patch_size:
            padded = np.zeros((volume.shape[0],) + patch_size, dtype=patch.dtype)
            padded[:, :actual_size[0], :actual_size[1], :actual_size[2]] = patch
            return padded
    else:
        actual_size = patch.shape
        if actual_size != patch_size:
            padded = np.zeros(patch_size, dtype=patch.dtype)
            padded[:actual_size[0], :actual_size[1], :actual_size[2]] = patch
            return padded

    return patch


def main():
    # Configuration
    ZARR_PATH = '/nfs/trident3/lightsheet/prado/mouse_app_lecanemab_ki3/bids/sub-AS134F3/micr/sub-AS134F3_sample-brain_acq-imaris4x_SPIM.ome.zarr'
    ATLAS_PATH = '/nfs/trident3/lightsheet/prado/mouse_app_lecanemab_ki3/derivatives/spimquant_aae813e/sub-AS134F3/micr/sub-AS134F3_sample-brain_acq-imaris4x_seg-all_from-ABAv3_level-5_desc-deform_dseg.nii.gz'
    ATLAS_TSV = '/nfs/trident3/lightsheet/prado/mouse_app_lecanemab_ki3/derivatives/spimquant_aae813e/tpl-ABAv3/seg-all_tpl-ABAv3_dseg.tsv'

    OUTPUT_DIR = Path('./colocalization_patches')
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    PATCH_SIZE = (64, 64, 64)  # Z, Y, X
    NUM_PATCHES = 3
    RESOLUTION_LEVEL = 2  # Downsample level (0=full resolution, higher=more downsampled)

    print("="*60)
    print("CO-LOCALIZATION PATCH EXTRACTION")
    print("="*60)

    # Load atlas for region-based cropping (optional)
    print("\n1. Loading atlas...")
    try:
        atlas = ZarrNiiAtlas.from_files(ATLAS_PATH, ATLAS_TSV)
        print(f"   ✓ Atlas loaded with {len(atlas.labels_df)} regions")

        # You can optionally crop to a specific brain region
        # For example, hippocampus where both Iba1 and Abeta are interesting
        use_region = input("\n   Crop to specific brain region? (e.g., 'Hipp' for hippocampus, or 'n' for whole brain): ").strip()

        if use_region.lower() != 'n' and use_region:
            bbox = atlas.get_region_bounding_box(regex=use_region)
            print(f"   ✓ Will crop to region matching '{use_region}'")
            crop_to_region = True
        else:
            crop_to_region = False
            bbox = None
    except Exception as e:
        print(f"   ! Could not load atlas: {e}")
        print("   → Will process whole brain")
        crop_to_region = False
        bbox = None

    # Load channel 1 (Iba1 - microglia)
    print("\n2. Loading Iba1 channel (microglia)...")
    with ProgressBar():
        img_iba1 = ZarrNii.from_ome_zarr(
            ZARR_PATH,
            channel_labels=['Iba1'],
            level=RESOLUTION_LEVEL,
            downsample_near_isotropic=True
        )

        if crop_to_region and bbox is not None:
            img_iba1 = img_iba1.crop_with_bounding_box(*bbox, ras_coords=True)

        iba1_data = img_iba1.ngff_image.data.compute()
        print(f"   ✓ Iba1 loaded: shape={iba1_data.shape}, dtype={iba1_data.dtype}")

    # Load channel 2 (Abeta - amyloid plaques)
    print("\n3. Loading Abeta channel (amyloid)...")
    with ProgressBar():
        img_abeta = ZarrNii.from_ome_zarr(
            ZARR_PATH,
            channel_labels=['Abeta'],
            level=RESOLUTION_LEVEL,
            downsample_near_isotropic=True
        )

        if crop_to_region and bbox is not None:
            img_abeta = img_abeta.crop_with_bounding_box(*bbox, ras_coords=True)

        abeta_data = img_abeta.ngff_image.data.compute()
        print(f"   ✓ Abeta loaded: shape={abeta_data.shape}, dtype={abeta_data.dtype}")

    # Remove channel dimension if present (C, Z, Y, X) -> (Z, Y, X)
    if iba1_data.ndim == 4:
        iba1_data = iba1_data[0]
    if abeta_data.ndim == 4:
        abeta_data = abeta_data[0]

    # Calculate co-localization
    print("\n4. Calculating co-localization...")
    manders, coloc_mask = calculate_colocalization_score(iba1_data, abeta_data)
    coloc_percentage = 100 * coloc_mask.sum() / coloc_mask.size
    print(f"   ✓ Manders' coefficient: {manders:.3f}")
    print(f"   ✓ Co-localized voxels: {coloc_percentage:.2f}%")

    # Save co-localization map
    coloc_map_path = OUTPUT_DIR / 'colocalization_map.tif'
    tifffile.imwrite(coloc_map_path, coloc_mask.astype(np.uint8) * 255)
    print(f"   ✓ Saved co-localization map to: {coloc_map_path}")

    # Find hotspots
    print(f"\n5. Finding top {NUM_PATCHES} co-localization hotspots...")
    patch_centers = find_colocalization_hotspots(
        coloc_mask,
        num_patches=NUM_PATCHES,
        patch_size=PATCH_SIZE
    )

    if len(patch_centers) < NUM_PATCHES:
        print(f"   ! Warning: Only found {len(patch_centers)} valid regions")

    # Extract and save patches
    print(f"\n6. Extracting {PATCH_SIZE} patches...")

    # Create multi-channel volume (2, Z, Y, X) for both stains
    multichannel_volume = np.stack([iba1_data, abeta_data], axis=0)

    patch_info = []

    for i, center in enumerate(patch_centers):
        print(f"\n   Patch {i+1}/{len(patch_centers)}:")
        print(f"   → Center: Z={center[0]}, Y={center[1]}, X={center[2]}")

        # Extract patch from both channels
        patch = extract_patch(multichannel_volume, center, PATCH_SIZE)

        # Calculate stats
        iba1_patch = patch[0]
        abeta_patch = patch[1]
        coloc_patch = extract_patch(coloc_mask, center, PATCH_SIZE)

        coloc_density = 100 * coloc_patch.sum() / coloc_patch.size
        print(f"   → Co-localization density: {coloc_density:.1f}%")
        print(f"   → Iba1 range: [{iba1_patch.min()}, {iba1_patch.max()}]")
        print(f"   → Abeta range: [{abeta_patch.min()}, {abeta_patch.max()}]")

        # Save individual channels (for visualization)
        iba1_path = OUTPUT_DIR / f'patch_{i+1:02d}_iba1.tif'
        abeta_path = OUTPUT_DIR / f'patch_{i+1:02d}_abeta.tif'
        coloc_path = OUTPUT_DIR / f'patch_{i+1:02d}_coloc_mask.tif'

        tifffile.imwrite(iba1_path, iba1_patch)
        tifffile.imwrite(abeta_path, abeta_patch)
        tifffile.imwrite(coloc_path, (coloc_patch * 255).astype(np.uint8))

        # Save combined multi-channel (for nnU-Net)
        combined_path = OUTPUT_DIR / f'patch_{i+1:02d}_combined.tif'
        tifffile.imwrite(combined_path, patch)  # Shape: (2, Z, Y, X)

        print(f"   ✓ Saved to: {combined_path}")

        patch_info.append({
            'patch_id': i+1,
            'center': center,
            'coloc_density': coloc_density,
            'combined_path': str(combined_path),
            'iba1_path': str(iba1_path),
            'abeta_path': str(abeta_path)
        })

    # Save metadata
    import json
    metadata_path = OUTPUT_DIR / 'patch_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump({
            'zarr_path': ZARR_PATH,
            'resolution_level': RESOLUTION_LEVEL,
            'patch_size': PATCH_SIZE,
            'manders_coefficient': float(manders),
            'total_colocalization_percentage': float(coloc_percentage),
            'patches': patch_info
        }, f, indent=2)

    print(f"\n   ✓ Saved metadata to: {metadata_path}")

    print("\n" + "="*60)
    print("EXTRACTION COMPLETE!")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print(f"\nExtracted {len(patch_centers)} patches ready for annotation.")
    print("\nNext steps:")
    print("1. Install nnU-Net: pip install nnunetv2")
    print("2. Open patches in napari with nnU-Net interactive plugin")
    print("3. Annotate cells in regions with high co-localization")
    print("4. Use annotated patches to train SwinUNetR")


if __name__ == '__main__':
    main()
