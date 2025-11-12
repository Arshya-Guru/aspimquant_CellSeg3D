# 🎯 nnU-Net Interactive - 3-Command Quick Start

**Complete workflow for AI-assisted annotation of co-localized cells**

---

## TL;DR

```bash
# 1. Setup (one-time, 2 min)
bash setup_nnunet_only.sh

# 2. Extract patches (5 min)
python extract_colocalized_patches.py

# 3. Annotate interactively (1-2 hours)
python launch_nnunet_interactive.py
```

**That's it!** You'll have annotated training data ready for SwinUNetR.

---

## 📺 What Actually Happens

### **Command 1: Setup**
```bash
bash setup_nnunet_only.sh
```
✅ Installs napari
✅ Installs napari-nnunet plugin
✅ Installs dependencies
⏱️ Takes ~2 minutes

---

### **Command 2: Extract**
```bash
python extract_colocalized_patches.py
```
✅ Loads Iba1 (microglia) + Abeta (amyloid) channels
✅ Finds top 3 co-localized regions
✅ Extracts 64×64×64 patches
✅ Creates `colocalization_patches/` folder
⏱️ Takes ~5 minutes

**You'll be asked:** Crop to brain region? (Type "Hipp" or press Enter for whole brain)

---

### **Command 3: Annotate**
```bash
python launch_nnunet_interactive.py
```
✅ Opens napari with patch 1
✅ Shows Iba1 (green) + Abeta (magenta)
✅ Opens nnU-Net interactive plugin
✅ You annotate cells (see workflow below)
✅ Close window → automatically loads patch 2
✅ Repeat for patch 3
✅ Saves `patch_01_labels.tif`, `patch_02_labels.tif`, `patch_03_labels.tif`
⏱️ Takes ~1-2 hours total

---

## 🎨 nnU-Net Interactive Workflow (Per Cell)

When napari opens, follow these steps for EACH cell:

### **Step 1: Open Plugin**
```
Top menu: Plugins → napari-nnunet → nnUNet (interactive)
```
A panel appears on the right →

### **Step 2: Select Layer & Label**
```
• Click "Cell Labels" layer (left panel)
• At bottom, set label = 1 (then 2, 3, 4... for each new cell)
```

### **Step 3: Place Seeds**
```
In nnU-Net panel on right:

a) Select "Positive" mode
   → Click 3-5 points INSIDE the cell
   → Click in CENTER of cell, not edges
   → Navigate Z-slices (mouse wheel) and place seeds on different slices

b) Select "Negative" mode
   → Click 2-3 points OUTSIDE the cell
   → Click clearly in background, away from cell
```

**Visual:**
```
    •           •        ← Negative (outside)
        ┌─────────┐
        │ • • • • │      ← Positive (inside)
        │    •    │
        └─────────┘
            •            ← Negative (outside)
```

### **Step 4: Segment**
```
Click "Segment" button in nnU-Net panel
→ AI predicts cell boundary
→ Result appears in viewer
```

### **Step 5: Review**
```
Navigate through Z-slices to check 3D result

✅ Looks good? → Click "Accept" in nnU-Net panel

❌ Looks bad?  → Add more seeds where it's wrong
              → Click "Segment" again
              → Repeat until satisfied
              → Click "Accept"
```

### **Step 6: Next Cell**
```
• Increment label number (2, 3, 4...)
• Repeat steps 3-5 for next cell
• Aim for 10-30 cells per patch
```

### **Step 7: Save & Continue**
```
• Press Ctrl+S to save (or close window for auto-save)
• Close napari window → next patch loads automatically
```

---

## ⏱️ Time Breakdown

| Task | Time |
|------|------|
| Setup (once) | 2 min |
| Extract patches (once) | 5 min |
| Annotate patch 1 | 30-40 min |
| Annotate patch 2 | 25-35 min (getting faster!) |
| Annotate patch 3 | 20-30 min |
| **Total** | **~1.5-2 hours** |

Compare to manual painting: **2-3 hours**
**nnU-Net interactive saves ~1 hour!** ⚡

---

## 💡 Pro Tips

### **Seed Placement**
✅ **DO:** Place positive seeds in CENTER of cell
✅ **DO:** Use 5+ positive seeds for complex cells
✅ **DO:** Place seeds on multiple Z-slices
✅ **DO:** Place negative seeds clearly in background

❌ **DON'T:** Place positive seeds on cell edges
❌ **DON'T:** Use too few seeds (< 3)
❌ **DON'T:** Place all seeds on same Z-slice

### **Focus on Co-localized Cells**
- Toggle "Co-localization (reference)" layer ON to see hotspots (yellow)
- Label cells where green (Iba1) + magenta (Abeta) overlap
- Skip cells with only one channel

### **Save Frequently**
- Press **Ctrl+S** every 5-10 cells
- Script auto-saves when you close window

### **Quality > Quantity**
- 15 well-labeled cells > 50 rushed cells
- Take breaks to maintain consistency

---

## 🎯 Expected Results

After running all 3 commands, you'll have:

```
colocalization_patches/
├── patch_01_combined.tif      # Image data (2 channels)
├── patch_01_labels.tif        # YOUR ANNOTATIONS ✨
├── patch_01_iba1.tif          # Reference
├── patch_01_abeta.tif         # Reference
├── patch_01_coloc_mask.tif    # Reference
├── patch_02_combined.tif
├── patch_02_labels.tif        # YOUR ANNOTATIONS ✨
├── ...
├── patch_03_labels.tif        # YOUR ANNOTATIONS ✨
└── patch_metadata.json
```

**Verify:**
```python
import tifffile
labels = tifffile.imread('colocalization_patches/patch_01_labels.tif')
print(f"Labeled {labels.max()} cells")  # Should be 10-30
```

---

## 🔧 Troubleshooting

### **"napari-nnunet plugin not found"**
```bash
pip install napari-nnunet
# Restart napari
```

### **"No patches found"**
```bash
# Make sure you ran extraction first:
python extract_colocalized_patches.py
```

### **Segmentation is completely wrong**
- Add MORE seeds (especially positive seeds)
- Place seeds in cell CENTER, not edges
- Add seeds on different Z-slices
- Make sure you're in correct Positive/Negative mode

### **Can't see cells clearly**
- Right-click layer → adjust contrast sliders
- Toggle individual channels on/off (eye icon)
- Increase opacity of image layers

---

## 📚 Full Documentation

For detailed explanations:
- **Complete guide:** `NNUNET_INTERACTIVE_GUIDE.md`
- **General workflow:** `COLOCALIZATION_ANNOTATION_GUIDE.md`

---

## ✅ Checklist

- [ ] Run `bash setup_nnunet_only.sh`
- [ ] Run `python extract_colocalized_patches.py`
- [ ] Verify patches exist: `ls colocalization_patches/`
- [ ] Run `python launch_nnunet_interactive.py`
- [ ] Open nnU-Net plugin in napari
- [ ] Annotate 10-30 cells per patch
- [ ] Save (Ctrl+S) and close for next patch
- [ ] Verify labels: `ls colocalization_patches/*_labels.tif`
- [ ] Ready to train SwinUNetR!

---

## 🚀 Next Steps After Annotation

Once you have all 3 `*_labels.tif` files:

1. **Organize for training:**
   ```bash
   mkdir -p training_data/{images,labels}
   cp colocalization_patches/patch_*_combined.tif training_data/images/
   cp colocalization_patches/patch_*_labels.tif training_data/labels/
   ```

2. **Train SwinUNetR:**
   - Open napari: `napari`
   - Plugins → napari-cellseg3d → Trainer
   - Select SwinUNetR model
   - Point to training_data folders
   - Train for 100-200 epochs

---

## 🎓 Key Concepts

**What is co-localization?**
Regions where both Iba1 (microglia) and Abeta (amyloid plaques) are present together. These regions show activated microglia near plaques - biologically interesting!

**What is nnU-Net interactive?**
AI-assisted annotation where YOU place seed points, and AI predicts cell boundaries. Much faster than manual painting, but YOU control everything.

**Why 3 patches?**
Minimum for diverse training data. More patches = better model, but diminishing returns after ~10 patches for initial training.

**Why 64×64×64?**
Good balance for SwinUNetR architecture. Large enough for cell context, small enough for GPU memory.

---

## 🎉 Ready to Start?

```bash
bash setup_nnunet_only.sh && \
python extract_colocalized_patches.py && \
python launch_nnunet_interactive.py
```

**Or step-by-step:**
```bash
bash setup_nnunet_only.sh              # Setup
python extract_colocalized_patches.py  # Extract
python launch_nnunet_interactive.py    # Annotate
```

**Good luck! You've got this!** 🔬✨

---

**Questions?** See `NNUNET_INTERACTIVE_GUIDE.md` for detailed help.
