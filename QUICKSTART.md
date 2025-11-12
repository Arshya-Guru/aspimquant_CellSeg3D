# 🚀 Quick Start: Co-localization Ground Truth Generation

## TL;DR - 3 Commands to Ground Truth

```bash
# 1. Setup (one-time)
bash setup_nnunet_interactive.sh

# 2. Extract patches where Iba1 and Abeta co-localize
python extract_colocalized_patches.py

# 3. Annotate cells interactively
python annotate_patches_napari.py
```

That's it! You'll have 3 annotated patches ready for SwinUNetR training.

---

## 📸 What This Does

### Step 1: Extract Patches
- Loads your two-channel microscopy data (Iba1 + Abeta)
- Finds where the stains **co-localize** (microglia near plaques)
- Extracts **3 patches (64×64×64)** from hottest regions
- Takes ~2-5 minutes depending on data size

**Output**: `colocalization_patches/` folder with:
- `patch_01_combined.tif` ← Multi-channel patch for annotation
- `patch_01_iba1.tif` ← Iba1 only (green)
- `patch_01_abeta.tif` ← Abeta only (magenta)
- `patch_01_coloc_mask.tif` ← Where they overlap
- ... (same for patches 2 and 3)

### Step 2: Annotate in napari
- Opens napari viewer with each patch
- Shows both channels (Iba1=green, Abeta=magenta)
- You paint labels on cells where they co-localize
- Press `s` to save, close window for next patch
- Takes ~10-30 minutes per patch

**Output**:
- `patch_01_labels.tif` ← Your cell annotations
- `patch_02_labels.tif`
- `patch_03_labels.tif`

---

## 🎯 What to Annotate

Focus on **activated microglia near amyloid plaques**:

```
Iba1 (green) ━━━╮
                  ╰━━→ [Co-localized cell] ← Label this!
Abeta (magenta) ━━╯
```

**Label criteria:**
- ✅ Cells with **both** Iba1 and Abeta signal
- ✅ Complete cell bodies (3D across Z-slices)
- ✅ Each cell = unique label number (1, 2, 3, ...)
- ❌ Skip cells at patch edges
- ❌ Skip unclear/ambiguous regions

---

## 🎨 napari Annotation Tips

### Tools
- Press `3` → **Paint tool** (label cells)
- Press `[` or `]` → Change brush size
- Press `5` → **Eraser** (fix mistakes)
- Press `s` → **Save** your work

### 3D Navigation
- Scroll mouse wheel → Move through Z-slices
- Shift + drag → Rotate 3D view (if enabled)
- Paint on multiple Z-slices to label full 3D cell

### Strategy
1. Find a clear cell in middle Z-slice
2. Paint rough outline
3. Navigate up/down in Z
4. Refine on each slice
5. Repeat for next cell (use next label number)

**Aim for 10-30 cells per patch** (quality matters more than quantity!)

---

## ⚙️ Customization

Edit `extract_colocalized_patches.py` if needed:

```python
# Line ~197-200
PATCH_SIZE = (64, 64, 64)      # Make smaller/larger
NUM_PATCHES = 3                 # Extract more patches
RESOLUTION_LEVEL = 2            # 0=full res, 2=downsampled
```

**When to change:**
- **PATCH_SIZE**: If 64³ is too small/large for your cells
- **NUM_PATCHES**: If you want more training data (5-10 recommended)
- **RESOLUTION_LEVEL**: If patches are too detailed or too blurry

---

## 📊 Expected Results

After extraction, check `patch_metadata.json`:

```json
{
  "manders_coefficient": 0.45,           ← Good: >0.3
  "total_colocalization_percentage": 8.2, ← Good: >5%
  "patches": [
    {
      "patch_id": 1,
      "coloc_density": 15.3,              ← Excellent: >10%
      "center": [120, 450, 380]
    },
    ...
  ]
}
```

**Good indicators:**
- Manders coefficient > 0.3
- Co-loc density > 10% per patch
- Visual inspection: clear cell structures visible

---

## 🔄 After Annotation

### Verify Your Labels

```python
import tifffile
import numpy as np

# Load a labeled patch
labels = tifffile.imread('colocalization_patches/patch_01_labels.tif')

print(f"Number of cells: {labels.max()}")  # Should be ~10-30
print(f"Labeled voxels: {(labels > 0).sum()}")  # Should be >1000
print(f"Label range: {labels.min()} to {labels.max()}")  # Should be 0 to N
```

### Train SwinUNetR

See `COLOCALIZATION_ANNOTATION_GUIDE.md` for full training workflow.

**Quick version:**
1. Organize images + labels into `training_data/` folder
2. Open napari → Plugins → Trainer
3. Select SwinUNetR model
4. Point to training_data folders
5. Train for ~100 epochs

---

## 🆘 Common Issues

### "Can't find ZARR file"
→ Edit paths at top of `extract_colocalized_patches.py` (lines ~197-201)

### "No co-localization found"
→ Channels might be swapped or empty. Check with:
```python
from zarrnii import ZarrNii
img = ZarrNii.from_ome_zarr('your_path.zarr', channel_labels=['Iba1'], level=2)
print(img.ngff_image.data.compute()[0].max())  # Should be >0
```

### "napari won't open"
→ Make sure you're not in a headless environment. If on server, use X11 forwarding:
```bash
ssh -X your_server
```

### "Patches are all black"
→ Try lower resolution level (0 or 1) in `extract_colocalized_patches.py`

---

## 📈 Workflow Checklist

- [ ] Install dependencies (`setup_nnunet_interactive.sh`)
- [ ] Verify ZARR paths in extraction script
- [ ] Run extraction (`extract_colocalized_patches.py`)
- [ ] Check patch quality in `colocalization_patches/`
- [ ] Annotate patch 1 in napari
- [ ] Annotate patch 2
- [ ] Annotate patch 3
- [ ] Verify labels with quick Python check
- [ ] Organize into training folder structure
- [ ] Train SwinUNetR model

**Total time**: ~2-4 hours for full workflow

---

## 🎓 Pro Tips

1. **Save often**: Press `s` every few cells in napari
2. **Take breaks**: Annotation fatigue leads to inconsistency
3. **Use co-loc mask**: Reference `patch_XX_coloc_mask.tif` to focus effort
4. **Start with best patch**: Check metadata for highest co-loc density
5. **Validate as you go**: Train on 2 patches, test on 3rd to check quality

---

## 📚 Full Guide

For detailed explanations, troubleshooting, and advanced options:
→ See `COLOCALIZATION_ANNOTATION_GUIDE.md`

---

Ready to create some ground truth? Let's go! 🔬✨

```bash
python extract_colocalized_patches.py
```
