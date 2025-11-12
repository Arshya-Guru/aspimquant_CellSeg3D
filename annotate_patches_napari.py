#!/usr/bin/env python3
"""
Load extracted co-localized patches into napari for interactive annotation.
Can be used with:
1. nnU-Net interactive (AI-assisted annotation)
2. Native napari annotation tools (manual painting)
"""

import napari
import numpy as np
from pathlib import Path
import tifffile
import json


def load_patch_for_annotation(patch_path, viewer=None):
    """
    Load a patch into napari for annotation.

    Args:
        patch_path: Path to the combined patch TIFF file
        viewer: Existing napari viewer (optional)

    Returns:
        napari viewer instance
    """
    if viewer is None:
        viewer = napari.Viewer()

    # Load the multi-channel patch
    patch = tifffile.imread(patch_path)

    if patch.ndim == 4:  # (C, Z, Y, X)
        # Add each channel separately
        viewer.add_image(
            patch[0],
            name='Iba1 (microglia)',
            colormap='green',
            blending='additive',
            contrast_limits=[patch[0].min(), np.percentile(patch[0], 99)]
        )
        viewer.add_image(
            patch[1],
            name='Abeta (amyloid)',
            colormap='magenta',
            blending='additive',
            contrast_limits=[patch[1].min(), np.percentile(patch[1], 99)]
        )
    else:  # Single channel
        viewer.add_image(
            patch,
            name='Image',
            colormap='gray',
            contrast_limits=[patch.min(), np.percentile(patch, 99)]
        )

    # Add empty labels layer for annotation
    if patch.ndim == 4:
        labels_shape = patch.shape[1:]  # (Z, Y, X)
    else:
        labels_shape = patch.shape

    labels = viewer.add_labels(
        np.zeros(labels_shape, dtype=np.uint16),
        name='Cell Labels'
    )

    # Check if there's an existing annotation
    patch_path = Path(patch_path)
    labels_path = patch_path.parent / f"{patch_path.stem}_labels.tif"
    if labels_path.exists():
        print(f"Loading existing annotations from: {labels_path}")
        existing_labels = tifffile.imread(labels_path)
        labels.data = existing_labels

    return viewer


def save_annotations(viewer, output_path):
    """
    Save the annotated labels from napari viewer.

    Args:
        viewer: napari viewer instance
        output_path: Path to save labels
    """
    labels_layer = viewer.layers['Cell Labels']
    tifffile.imwrite(output_path, labels_layer.data.astype(np.uint16))
    print(f"Saved annotations to: {output_path}")


def annotate_all_patches(patches_dir='./colocalization_patches'):
    """
    Sequentially load all patches for annotation.

    Args:
        patches_dir: Directory containing extracted patches
    """
    patches_dir = Path(patches_dir)

    # Load metadata
    metadata_path = patches_dir / 'patch_metadata.json'
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        patches = metadata['patches']
    else:
        # Find all combined patches
        patches = [{'combined_path': str(p)} for p in
                   sorted(patches_dir.glob('patch_*_combined.tif'))]

    print("="*60)
    print("INTERACTIVE PATCH ANNOTATION")
    print("="*60)
    print(f"\nFound {len(patches)} patches to annotate")
    print("\nAnnotation tips:")
    print("  • Use the 'paint' tool to label cells")
    print("  • Use 'fill' to fill regions")
    print("  • Press '[' and ']' to change brush size")
    print("  • Use 'eraser' to remove labels")
    print("  • Each cell should have a unique label (1, 2, 3, ...)")
    print("  • Focus on cells in co-localized regions")
    print("\n" + "="*60)

    for i, patch_info in enumerate(patches):
        print(f"\n\nPatch {i+1}/{len(patches)}")
        print("-"*40)

        patch_path = Path(patch_info['combined_path'])
        if not patch_path.exists():
            print(f"  ! Patch not found: {patch_path}")
            continue

        if 'coloc_density' in patch_info:
            print(f"  Co-localization density: {patch_info['coloc_density']:.1f}%")

        print(f"  Loading: {patch_path.name}")

        # Load patch in napari
        viewer = load_patch_for_annotation(patch_path)

        print("\n  Napari viewer opened. When finished annotating:")
        print("    1. Press 's' to save")
        print("    2. Close the viewer window to continue to next patch")

        # Add keybinding to save
        labels_path = patch_path.parent / f"{patch_path.stem}_labels.tif"

        @viewer.bind_key('s')
        def save(viewer):
            save_annotations(viewer, labels_path)
            print(f"  ✓ Saved! Annotations: {labels_path}")

        # Show viewer (blocking)
        napari.run()

        # Auto-save on close
        if 'Cell Labels' in viewer.layers:
            save_annotations(viewer, labels_path)

    print("\n" + "="*60)
    print("ANNOTATION COMPLETE!")
    print("="*60)
    print(f"\nAll annotations saved in: {patches_dir.absolute()}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Annotate co-localized patches in napari'
    )
    parser.add_argument(
        '--patches-dir',
        type=str,
        default='./colocalization_patches',
        help='Directory containing extracted patches'
    )
    parser.add_argument(
        '--single-patch',
        type=str,
        help='Annotate a single patch (provide path to combined.tif file)'
    )

    args = parser.parse_args()

    if args.single_patch:
        # Annotate single patch
        viewer = load_patch_for_annotation(args.single_patch)

        patch_path = Path(args.single_patch)
        labels_path = patch_path.parent / f"{patch_path.stem}_labels.tif"

        @viewer.bind_key('s')
        def save(viewer):
            save_annotations(viewer, labels_path)
            print(f"Saved! Annotations: {labels_path}")

        print("\nNapari opened. Press 's' to save annotations.")
        napari.run()

        # Auto-save on close
        save_annotations(viewer, labels_path)
    else:
        # Annotate all patches sequentially
        annotate_all_patches(args.patches_dir)


if __name__ == '__main__':
    main()
