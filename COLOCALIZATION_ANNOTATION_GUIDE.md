# Co-localization Based Ground Truth Generation Guide

This guide will walk you through creating ground truth training data for SwinUNetR by extracting and annotating patches where two fluorescent stains co-localize.

## 🎯 Overview

You have two-channel microscopy data:
- **Iba1** (microglia marker) - Channel 1
- **Abeta** (amyloid plaques) - Channel 2

The goal is to:
1. **Find regions** where both stains co-localize (indicating microglia near plaques)
2. **Extract 3 patches** from these high co-localization regions
3. **Annotate cells** interactively using napari
4. **Use annotations** to train SwinUNetR for automated segmentation

---

## 📋 Prerequisites

### Required Data
- OME-ZARR file with both Iba1 and Abeta channels
- Brain atlas files (optional, for region-specific extraction)

### Software Requirements
```bash
# Install dependencies
bash setup_nnunet_interactive.sh

# Or manually:
pip install nnunetv2 napari-nnunet zarrnii scipy tifffile
```

---

## 🚀 Step-by-Step Workflow

### Step 1: Extract Co-localized Patches

Run the extraction script:

```bash
python extract_colocalized_patches.py
```

**What it does:**
1. Loads both Iba1 and Abeta channels from your OME-ZARR
2. Calculates Manders' co-localization coefficient
3. Finds the top 3 regions with highest co-localization density
4. Extracts 64×64×64 patches from these regions
5. Saves patches as multi-channel TIFF files

**Interactive prompts:**
- You'll be asked if you want to crop to a specific brain region (e.g., "Hipp" for hippocampus)
- Press Enter or type 'n' to use the whole brain

**Output:**
```
colocalization_patches/
├── patch_01_combined.tif        # Multi-channel patch (2, Z, Y, X)
├── patch_01_iba1.tif            # Iba1 channel only
├── patch_01_abeta.tif           # Abeta channel only
├── patch_01_coloc_mask.tif      # Co-localization mask
├── patch_02_combined.tif        # Second patch
├── patch_02_iba1.tif
├── ...
├── colocalization_map.tif       # Full volume co-localization
└── patch_metadata.json          # Metadata about all patches
```

**Configuration options** (edit `extract_colocalized_patches.py`):
```python
PATCH_SIZE = (64, 64, 64)      # Size of each patch (Z, Y, X)
NUM_PATCHES = 3                 # Number of patches to extract
RESOLUTION_LEVEL = 2            # 0=full res, higher=downsampled
```

---

### Step 2: Annotate Patches Interactively

#### Option A: Sequential Annotation (Recommended)

Annotate all patches one by one:

```bash
python annotate_patches_napari.py
```

The script will:
1. Load each patch sequentially
2. Display both Iba1 (green) and Abeta (magenta) channels
3. Provide an empty labels layer for annotation
4. Wait for you to finish, then move to next patch

**Annotation workflow:**
1. **Napari opens** showing your patch with both channels
2. **Select the "Cell Labels" layer** in the layer list
3. **Use the paint brush** 🖌️ to label cells:
   - Click the "paint" tool (or press `3`)
   - Adjust brush size with `[` and `]` keys
   - Each cell should get a unique label number (1, 2, 3, ...)
   - Label cells where Iba1 and Abeta overlap
4. **Press `s` to save** your annotations
5. **Close the window** to move to the next patch

#### Option B: Single Patch Annotation

Annotate one specific patch:

```bash
python annotate_patches_napari.py --single-patch colocalization_patches/patch_01_combined.tif
```

---

### Step 3: Using nnU-Net Interactive (Advanced)

For **AI-assisted annotation** (faster than manual):

1. **Install napari-nnunet plugin:**
   ```bash
   pip install napari-nnunet
   ```

2. **Open napari:**
   ```bash
   napari
   ```

3. **Load your patch:**
   - File → Open Files → Select `patch_01_combined.tif`

4. **Launch nnU-Net interactive:**
   - Plugins → napari-nnunet → nnUNet (interactive)

5. **Annotation workflow:**
   - Click a few points **inside** a cell (positive seeds)
   - Click a few points **outside** cells (negative seeds)
   - Click "Segment" - AI predicts the cell boundary
   - Refine with more seeds if needed
   - Accept and move to next cell

**Benefits:**
- Much faster than manual painting
- AI learns cell boundaries from your seeds
- Can segment complex 3D structures easily

---

## 📊 Understanding Co-localization

### Manders' Coefficient
- Range: 0.0 to 1.0
- **> 0.5**: Strong co-localization (good for training)
- **0.2-0.5**: Moderate co-localization
- **< 0.2**: Weak co-localization

### Co-localization Density (per patch)
- Percentage of voxels where both channels are active
- **> 10%**: High co-localization (excellent training regions)
- **5-10%**: Moderate (good training regions)
- **< 5%**: Low (consider excluding)

The script prioritizes patches with **highest co-localization density**.

---

## 🎨 Annotation Best Practices

### What to Label
✅ **DO label:**
- Individual cells where Iba1 and Abeta overlap
- Complete cell bodies (not just nuclei)
- Cells with clear boundaries
- Activated microglia near plaques

❌ **DON'T label:**
- Background or unclear regions
- Partial cells at patch edges
- Debris or artifacts
- Overlapping cells as single label

### Labeling Strategy
1. **Instance segmentation**: Each cell = unique label (1, 2, 3, ...)
2. **3D annotation**: Navigate through Z-slices to label full 3D cell
3. **Consistency**: Use same criteria across all patches
4. **Quality > Quantity**: 3 well-labeled patches > 10 rushed ones

### Keyboard Shortcuts (napari)
- `3` - Paint tool
- `4` - Fill tool
- `5` - Eraser
- `[` / `]` - Decrease/increase brush size
- `Shift+E` - Toggle 3D rendering
- `s` - Save (custom binding from our script)

---

## 🔄 Using Annotated Data for Training

After annotation, you'll have:
```
colocalization_patches/
├── patch_01_combined.tif
├── patch_01_labels.tif        ← Your annotations
├── patch_02_combined.tif
├── patch_02_labels.tif
└── ...
```

### Prepare Training Dataset

```python
from pathlib import Path
import shutil

# Organize for CellSeg3D training
train_dir = Path('./training_data')
(train_dir / 'images').mkdir(parents=True, exist_ok=True)
(train_dir / 'labels').mkdir(parents=True, exist_ok=True)

# Copy patches and labels
patch_dir = Path('./colocalization_patches')
for patch in patch_dir.glob('patch_*_combined.tif'):
    # Copy image
    shutil.copy(patch, train_dir / 'images' / patch.name)

    # Copy corresponding label
    label = patch.parent / f"{patch.stem}_labels.tif"
    if label.exists():
        shutil.copy(label, train_dir / 'labels' / patch.name)
```

### Train SwinUNetR

Use the CellSeg3D training plugin:

1. Open napari: `napari`
2. Plugins → napari-cellseg3d → Trainer
3. Configure:
   - **Images folder**: `./training_data/images`
   - **Labels folder**: `./training_data/labels`
   - **Model**: SwinUNetR
   - **Patch size**: 64×64×64
   - **Epochs**: 100-200
   - **Batch size**: 2-4
4. Start training

---

## 🔧 Troubleshooting

### "No co-localization found"
- Try lowering `threshold_percentile` in `extract_colocalized_patches.py` (line ~15)
- Verify both channels exist in your ZARR file
- Check that channels have signal (not empty)

### Patches are too dark/bright
- Adjust `RESOLUTION_LEVEL` (higher = more downsampled but clearer)
- Modify contrast limits in napari viewer

### Can't find brain region
- Check atlas path is correct
- Use 'n' to skip region filtering and process whole brain
- Verify region name (e.g., 'Hipp', 'CA1', 'cortex')

### nnU-Net interactive not working
- Ensure `napari-nnunet` is installed: `pip install napari-nnunet`
- May need to install nnU-Net models first
- Fall back to manual annotation if needed

---

## 📚 Additional Resources

### Documentation
- [napari documentation](https://napari.org/stable/)
- [nnU-Net v2 docs](https://github.com/MIC-DKFZ/nnUNet)
- [CellSeg3D guide](https://adaptivemotorcontrollab.github.io/cellseg3d-docs/)

### Example Workflow
See `zarrnii_example.ipynb` for data loading examples.

---

## 💡 Tips for Better Training Data

1. **Diversity**: Include patches from different brain regions
2. **Balance**: Similar number of cells per patch
3. **Edge cases**: Include both easy and challenging cells
4. **Validation set**: Keep 1 patch for validation (don't train on it)
5. **Iterate**: Train on 3 patches, evaluate, annotate more if needed

---

## 🎓 Next Steps

After creating ground truth:
1. ✅ Extract 3 co-localized patches
2. ✅ Annotate cells in napari
3. ⬜ Organize training/validation split
4. ⬜ Train SwinUNetR model
5. ⬜ Evaluate on held-out data
6. ⬜ Iterate: add more annotations if needed
7. ⬜ Apply trained model to full dataset

---

## 📞 Questions?

If you run into issues:
1. Check the output in `colocalization_patches/patch_metadata.json`
2. Verify patch quality by viewing in napari
3. Ensure labels match images (same filenames)
4. Check that labels are non-zero (cells were actually annotated)

Good luck with your annotations! 🔬✨
