#!/usr/bin/env python3
"""
Launch patches in napari with nnU-Net interactive ready for annotation.
This script streamlines the nnU-Net interactive workflow.
"""

import napari
import numpy as np
from pathlib import Path
import tifffile
import json
import sys


def launch_nnunet_for_patch(patch_path):
    """
    Launch napari with nnU-Net interactive for a single patch.

    Args:
        patch_path: Path to combined patch TIFF file
    """
    patch_path = Path(patch_path)

    if not patch_path.exists():
        print(f"❌ Error: Patch not found: {patch_path}")
        return None

    print(f"\n{'='*60}")
    print(f"Loading: {patch_path.name}")
    print(f"{'='*60}")

    # Create napari viewer
    viewer = napari.Viewer(title=f"nnU-Net Interactive - {patch_path.name}")

    # Load the multi-channel patch
    patch = tifffile.imread(patch_path)

    if patch.ndim == 4:  # (C, Z, Y, X)
        # Add each channel separately with good visualization
        viewer.add_image(
            patch[0],
            name='Iba1 (microglia)',
            colormap='green',
            blending='additive',
            opacity=0.7,
            contrast_limits=[patch[0].min(), np.percentile(patch[0], 99.5)]
        )
        viewer.add_image(
            patch[1],
            name='Abeta (amyloid)',
            colormap='magenta',
            blending='additive',
            opacity=0.7,
            contrast_limits=[patch[1].min(), np.percentile(patch[1], 99.5)]
        )

        # Load co-localization mask if available (for reference)
        coloc_mask_path = patch_path.parent / f"{patch_path.stem.replace('combined', 'coloc_mask')}.tif"
        if coloc_mask_path.exists():
            coloc_mask = tifffile.imread(coloc_mask_path)
            viewer.add_image(
                coloc_mask,
                name='Co-localization (reference)',
                colormap='yellow',
                blending='additive',
                opacity=0.3,
                visible=False  # Hidden by default, toggle on to see hotspots
            )
            print("   ℹ️  Co-localization mask loaded (toggle visibility to see hotspots)")

        labels_shape = patch.shape[1:]  # (Z, Y, X)
    else:  # Single channel
        viewer.add_image(
            patch,
            name='Image',
            colormap='gray',
            contrast_limits=[patch.min(), np.percentile(patch, 99)]
        )
        labels_shape = patch.shape

    # Check if there's an existing annotation to continue from
    labels_path = patch_path.parent / f"{patch_path.stem}_labels.tif"
    if labels_path.exists():
        print(f"   📂 Loading existing annotations from: {labels_path.name}")
        existing_labels = tifffile.imread(labels_path)
        labels_layer = viewer.add_labels(
            existing_labels,
            name='Cell Labels'
        )
        num_cells = existing_labels.max()
        print(f"   ✓ Found {num_cells} already labeled cells")
    else:
        print(f"   📝 Starting fresh annotation")
        labels_layer = viewer.add_labels(
            np.zeros(labels_shape, dtype=np.uint16),
            name='Cell Labels'
        )

    # Print instructions
    print(f"\n{'='*60}")
    print("nnU-Net Interactive Workflow:")
    print(f"{'='*60}")
    print("\n1. Open nnU-Net Interactive:")
    print("   → Plugins → napari-nnunet → nnUNet (interactive)")
    print("\n2. For EACH cell:")
    print("   a) Select 'Cell Labels' layer")
    print("   b) Choose a NEW label number (1, 2, 3, ...)")
    print("   c) Click 3-5 points INSIDE the cell (positive seeds)")
    print("   d) Click 2-3 points OUTSIDE the cell (negative seeds)")
    print("   e) Click 'Segment' button → AI predicts boundary")
    print("   f) Review the result:")
    print("      - Good? Click 'Accept' → Done!")
    print("      - Bad? Add more seeds → Click 'Segment' again")
    print("   g) Repeat for next cell (use next label number)")
    print("\n3. Save your work:")
    print(f"   → Press 'Ctrl+S' or use File → Save Selected Layer")
    print(f"   → Save to: {labels_path.name}")
    print("\n4. Focus on cells in co-localized regions")
    print("   → Toggle 'Co-localization (reference)' layer to see hotspots")
    print(f"\n{'='*60}")
    print("💡 Tips:")
    print(f"{'='*60}")
    print("   • More seeds = better results")
    print("   • Place seeds in CENTER of cell (not edges)")
    print("   • Negative seeds should be clearly OUTSIDE")
    print("   • Navigate Z-slices to verify 3D segmentation")
    print("   • Aim for 10-30 cells per patch")
    print("   • Save frequently (Ctrl+S)")
    print(f"{'='*60}\n")

    # Setup auto-save keybinding
    @viewer.bind_key('Ctrl-S')
    def save_labels(viewer):
        """Save labels when Ctrl+S is pressed."""
        if 'Cell Labels' in viewer.layers:
            labels_data = viewer.layers['Cell Labels'].data
            tifffile.imwrite(labels_path, labels_data.astype(np.uint16))
            num_cells = labels_data.max()
            print(f"   💾 Saved {num_cells} cells to: {labels_path.name}")
        else:
            print("   ⚠️  No 'Cell Labels' layer found")

    return viewer, labels_path


def launch_all_patches_sequential(patches_dir='./colocalization_patches'):
    """
    Launch all patches for annotation one by one.

    Args:
        patches_dir: Directory containing extracted patches
    """
    patches_dir = Path(patches_dir)

    if not patches_dir.exists():
        print(f"❌ Error: Patches directory not found: {patches_dir}")
        print(f"\n👉 Run this first: python extract_colocalized_patches.py")
        return

    # Load metadata to get patch info
    metadata_path = patches_dir / 'patch_metadata.json'
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        print(f"\n{'='*60}")
        print("Co-localization Summary:")
        print(f"{'='*60}")
        print(f"Manders' coefficient: {metadata.get('manders_coefficient', 'N/A'):.3f}")
        print(f"Overall co-localization: {metadata.get('total_colocalization_percentage', 'N/A'):.1f}%")
        print(f"Number of patches: {len(metadata.get('patches', []))}")
        print(f"{'='*60}\n")

        patches = metadata['patches']

        # Sort by co-localization density (annotate best patches first)
        patches.sort(key=lambda x: x.get('coloc_density', 0), reverse=True)
    else:
        # Find all combined patches
        patch_files = sorted(patches_dir.glob('patch_*_combined.tif'))
        patches = [{'combined_path': str(p)} for p in patch_files]

    if not patches:
        print(f"❌ No patches found in {patches_dir}")
        print(f"\n👉 Run this first: python extract_colocalized_patches.py")
        return

    print(f"Found {len(patches)} patches to annotate\n")

    # Annotate each patch
    for i, patch_info in enumerate(patches):
        print(f"\n{'#'*60}")
        print(f"  PATCH {i+1}/{len(patches)}")
        print(f"{'#'*60}")

        if 'coloc_density' in patch_info:
            print(f"Co-localization density: {patch_info['coloc_density']:.1f}%")
        if 'center' in patch_info:
            z, y, x = patch_info['center']
            print(f"Location: Z={z}, Y={y}, X={x}")

        patch_path = Path(patch_info['combined_path'])

        viewer, labels_path = launch_nnunet_for_patch(patch_path)

        if viewer is None:
            continue

        # Wait for user to finish and close viewer
        print(f"\n⏳ Waiting for you to finish annotating...")
        print(f"   Close the napari window when done to continue to next patch\n")

        napari.run()  # Blocking - waits for viewer to close

        # Auto-save on close if not saved already
        try:
            if 'Cell Labels' in viewer.layers:
                labels_data = viewer.layers['Cell Labels'].data
                if labels_data.max() > 0:  # Only save if something was labeled
                    tifffile.imwrite(labels_path, labels_data.astype(np.uint16))
                    print(f"\n   ✓ Auto-saved {labels_data.max()} cells")
                else:
                    print(f"\n   ⚠️  No cells labeled in this patch")
        except Exception as e:
            print(f"\n   ⚠️  Could not auto-save: {e}")

        print(f"\n   Patch {i+1} complete!\n")

    print(f"\n{'='*60}")
    print("🎉 ALL PATCHES ANNOTATED!")
    print(f"{'='*60}")
    print(f"\nAnnotations saved in: {patches_dir.absolute()}")
    print("\nNext steps:")
    print("  1. Verify labels: ls colocalization_patches/*_labels.tif")
    print("  2. Organize for training")
    print("  3. Train SwinUNetR model")
    print(f"\n{'='*60}\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Launch nnU-Net interactive annotation for co-localized patches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Annotate all patches sequentially (recommended)
  python launch_nnunet_interactive.py

  # Annotate specific patch
  python launch_nnunet_interactive.py --patch colocalization_patches/patch_01_combined.tif

  # Specify custom patches directory
  python launch_nnunet_interactive.py --patches-dir ./my_patches
        """
    )

    parser.add_argument(
        '--patch',
        type=str,
        help='Annotate a specific patch (path to combined.tif file)'
    )
    parser.add_argument(
        '--patches-dir',
        type=str,
        default='./colocalization_patches',
        help='Directory containing extracted patches (default: ./colocalization_patches)'
    )

    args = parser.parse_args()

    # Check if napari-nnunet is installed
    try:
        import napari_nnunet
    except ImportError:
        print("\n❌ napari-nnunet plugin not found!")
        print("\n👉 Install it first:")
        print("   bash setup_nnunet_only.sh")
        print("\n   OR manually:")
        print("   pip install napari-nnunet")
        sys.exit(1)

    if args.patch:
        # Annotate single patch
        viewer, labels_path = launch_nnunet_for_patch(args.patch)
        if viewer:
            napari.run()

            # Auto-save on close
            try:
                labels_data = viewer.layers['Cell Labels'].data
                if labels_data.max() > 0:
                    tifffile.imwrite(labels_path, labels_data.astype(np.uint16))
                    print(f"\n✓ Saved {labels_data.max()} cells to: {labels_path}")
            except Exception as e:
                print(f"\n⚠️  Could not auto-save: {e}")
    else:
        # Annotate all patches sequentially
        launch_all_patches_sequential(args.patches_dir)


if __name__ == '__main__':
    main()
