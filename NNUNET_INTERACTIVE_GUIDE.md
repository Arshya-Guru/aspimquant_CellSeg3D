# 🎯 nnU-Net Interactive Annotation - Quick Start

**AI-assisted interactive annotation for co-localized cell patches**

This guide shows you how to use **nnU-Net interactive** to quickly annotate cells where Iba1 (microglia) and Abeta (amyloid) co-localize.

---

## 🚀 3-Step Workflow

### **Step 1: Setup (2 minutes)**

```bash
bash setup_nnunet_only.sh
```

This installs:
- `napari` - Visualization tool
- `napari-nnunet` - Interactive annotation plugin
- Required dependencies

---

### **Step 2: Extract Patches (5 minutes)**

```bash
python extract_colocalized_patches.py
```

**What happens:**
- Loads both Iba1 and Abeta channels
- Finds top 3 co-localized regions
- Extracts 64×64×64 patches
- Creates `colocalization_patches/` folder

**You'll be asked:** Crop to brain region? (e.g., "Hipp" or press 'n' for whole brain)

---

### **Step 3: Annotate with nnU-Net (30-60 minutes)**

```bash
python launch_nnunet_interactive.py
```

**What happens:**
- Opens napari with first patch
- Shows Iba1 (green) + Abeta (magenta)
- You annotate cells using nnU-Net interactive
- Auto-moves to next patch when you close window
- Saves annotations as `patch_XX_labels.tif`

---

## 🎨 Using nnU-Net Interactive

### **Opening the Plugin**

When napari opens:

1. Look at the top menu bar
2. Click: **Plugins → napari-nnunet → nnUNet (interactive)**
3. A panel appears on the right side

![napari with plugin panel]

---

### **Annotating a Single Cell**

**For each cell, follow these steps:**

#### **A. Select Layer & Label Number**
```
1. Click "Cell Labels" layer in layer list (left panel)
2. At bottom, set "label" to a NEW number (1, 2, 3, ...)
   - Each cell gets a unique number
   - Start at 1, increment for each new cell
```

#### **B. Place POSITIVE Seeds (Inside Cell)**
```
3. In nnU-Net panel, select "Positive" mode
4. Click 3-5 points INSIDE the cell
   - Click in cell center
   - Click in different Z-slices (navigate with mouse wheel)
   - Seeds should be clearly inside the cell boundary
```

**Example:**
```
      Cell Boundary
      ┌─────────┐
      │  • • •  │  ← Positive seeds (inside)
      │    •    │
      └─────────┘
```

#### **C. Place NEGATIVE Seeds (Outside Cell)**
```
5. In nnU-Net panel, select "Negative" mode
6. Click 2-3 points OUTSIDE the cell
   - Click in background/space around cell
   - Seeds should be clearly outside the cell boundary
```

**Example:**
```
  •         •        ← Negative seeds (outside)
      ┌─────────┐
      │  • • •  │
      │    •    │
      └─────────┘
          •          ← Negative seed (outside)
```

#### **D. Segment**
```
7. Click "Segment" button in nnU-Net panel
   → AI predicts the cell boundary
   → Result appears in "Cell Labels" layer
```

#### **E. Review & Refine**
```
8. Navigate through Z-slices to check 3D segmentation
   - Does it look correct?

   ✅ YES → Click "Accept" in nnU-Net panel → DONE!

   ❌ NO → Add more seeds where it's wrong
          → Click "Segment" again
          → Repeat until satisfied
          → Click "Accept"
```

#### **F. Move to Next Cell**
```
9. Increment label number (2, 3, 4, ...)
10. Repeat steps A-E for next cell
```

---

### **Visual Workflow**

```
Start
  │
  ├─→ Select "Cell Labels" layer
  ├─→ Set label = 1
  │
  ├─→ [Positive mode] Click inside cell (3-5 points)
  ├─→ [Negative mode] Click outside cell (2-3 points)
  │
  ├─→ Click "Segment" → AI predicts
  │
  ├─→ Review result
  │    │
  │    ├─→ Good? → "Accept" → label += 1 → Next cell
  │    │
  │    └─→ Bad? → Add more seeds → "Segment" again
  │
  └─→ Repeat until 10-30 cells labeled
```

---

## 🎓 Pro Tips

### **Seed Placement Strategy**

**GOOD seed placement:**
✅ Positive seeds in CENTER of cell (not edges)
✅ Negative seeds clearly in background
✅ Seeds distributed across different Z-slices
✅ More seeds = better accuracy

**BAD seed placement:**
❌ Positive seeds on cell boundary
❌ Negative seeds touching the cell
❌ All seeds on same Z-slice
❌ Too few seeds (< 3 positive)

### **How Many Seeds?**

| Cell Complexity | Positive Seeds | Negative Seeds |
|----------------|---------------|----------------|
| Simple, round | 3-4 | 2 |
| Moderate | 5-7 | 3 |
| Complex shape | 8-10 | 4-5 |

**Rule of thumb:** If segmentation is wrong, add more seeds in problem areas

### **3D Annotation**

```
Z-slice view:

Z=10: •  •  •     ← Seeds on top slice
        ─────
Z=20:  │ • • │    ← Seeds in middle
        ─────
Z=30:   • • •     ← Seeds on bottom slice

Result: Full 3D cell segmented
```

**Navigate Z-slices:**
- Scroll mouse wheel
- Or use slider at bottom of viewer

### **Focus on Co-localized Cells**

```
Priority cells to label:

High:  Iba1 (green) ━┓
                      ┣━━→ Strong overlap
       Abeta (magenta)━┛

Medium: Iba1 ━━┓
                ┣━→ Partial overlap
        Abeta ━━┛

Low:   Iba1 only     ← Skip these
       Abeta only    ← Skip these
```

**Toggle the "Co-localization (reference)" layer to see hotspots!**

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+S** | Save annotations |
| **Mouse wheel** | Navigate Z-slices |
| **1-9** | Select label number |
| **Ctrl+Z** | Undo last action |
| **Shift+E** | Toggle 3D rendering |

---

## 💾 Saving Your Work

### **Auto-save**
- Press **Ctrl+S** anytime
- Auto-saves when you close napari window

### **Files created:**
```
colocalization_patches/
├── patch_01_labels.tif    ← Your annotations for patch 1
├── patch_02_labels.tif    ← Patch 2
└── patch_03_labels.tif    ← Patch 3
```

### **Verify saved labels:**
```python
import tifffile
labels = tifffile.imread('colocalization_patches/patch_01_labels.tif')
print(f"Labeled {labels.max()} cells")  # Should be 10-30
print(f"Label range: {labels.min()}-{labels.max()}")
```

---

## 🎯 Annotation Goals

**Per patch:**
- ✅ 10-30 high-quality cell labels
- ✅ Focus on co-localized regions
- ✅ Complete 3D cells (across all Z-slices)
- ✅ Each cell = unique label number

**Overall (3 patches):**
- ✅ 30-90 total labeled cells
- ✅ Diverse cell shapes and sizes
- ✅ Consistent labeling criteria across patches

---

## 🔧 Troubleshooting

### **Problem: nnU-Net plugin not showing**

**Solution:**
```bash
pip install napari-nnunet
# Restart napari
```

Check installation:
```python
import napari_nnunet
print("✓ Installed")
```

---

### **Problem: Segmentation is way off**

**Solutions:**
1. Add more positive seeds in cell center
2. Add more negative seeds clearly outside
3. Try placing seeds on different Z-slices
4. Make sure you're in correct "Positive/Negative" mode

---

### **Problem: Can't see cells clearly**

**Solutions:**
1. Adjust contrast: Right-click layer → adjust sliders
2. Toggle individual channels on/off
3. Change opacity in layer controls
4. Use 3D view: Shift+E

---

### **Problem: Labeled wrong cell by mistake**

**Solutions:**
1. Use eraser tool to remove
2. Or: Use paint tool with label=0 to erase
3. Or: Ctrl+Z to undo

---

## 📊 Quality Check

After annotating each patch, verify:

```python
import tifffile
import numpy as np

labels = tifffile.imread('colocalization_patches/patch_01_labels.tif')

# Check number of cells
num_cells = labels.max()
print(f"Number of cells: {num_cells}")  # Should be 10-30

# Check coverage
labeled_fraction = (labels > 0).sum() / labels.size
print(f"Labeled {labeled_fraction*100:.1f}% of patch")  # Should be 5-20%

# Check 3D connectivity
from scipy.ndimage import label
for cell_id in range(1, num_cells + 1):
    cell_mask = (labels == cell_id)
    connected, n = label(cell_mask)
    if n > 1:
        print(f"⚠️  Cell {cell_id} has {n} disconnected parts")
```

---

## 🎬 Complete Session Example

**Time breakdown for one patch:**

1. **Launch napari** (10 seconds)
   - `python launch_nnunet_interactive.py`

2. **Open nnU-Net plugin** (5 seconds)
   - Plugins → napari-nnunet → nnUNet (interactive)

3. **Annotate cells** (20-30 minutes)
   - Cell 1: 2 min (seeds + segment + refine)
   - Cell 2: 1.5 min
   - Cell 3: 1.5 min
   - ...
   - Cell 15: 1 min (getting faster!)

4. **Save & close** (10 seconds)
   - Ctrl+S → Close window

**Total per patch: ~25-35 minutes**
**Total for 3 patches: ~1.5-2 hours**

Compare to **manual painting: 30-40 min per patch = 2-3 hours total**

**nnU-Net interactive saves ~1 hour!** ⚡

---

## 🚀 After Annotation

Once all 3 patches are annotated:

### **1. Verify all labels exist:**
```bash
ls colocalization_patches/patch_*_labels.tif
```

Should show:
```
patch_01_labels.tif
patch_02_labels.tif
patch_03_labels.tif
```

### **2. Quick stats:**
```python
import tifffile
from pathlib import Path

patches_dir = Path('colocalization_patches')
total_cells = 0

for labels_file in sorted(patches_dir.glob('patch_*_labels.tif')):
    labels = tifffile.imread(labels_file)
    n_cells = labels.max()
    total_cells += n_cells
    print(f"{labels_file.name}: {n_cells} cells")

print(f"\nTotal: {total_cells} cells across all patches")
```

### **3. Organize for training:**
```bash
# See COLOCALIZATION_ANNOTATION_GUIDE.md for full training setup
# Or use CellSeg3D Trainer plugin in napari
```

---

## 📚 Additional Resources

- [napari-nnunet documentation](https://github.com/MIC-DKFZ/napari-nnunet)
- [Full workflow guide](COLOCALIZATION_ANNOTATION_GUIDE.md)
- [napari tutorials](https://napari.org/stable/tutorials/index.html)

---

## ✅ Checklist

Before starting:
- [ ] Installed dependencies (`bash setup_nnunet_only.sh`)
- [ ] Extracted patches (`python extract_colocalized_patches.py`)
- [ ] Verified patches exist in `colocalization_patches/`

During annotation:
- [ ] Opened nnU-Net plugin
- [ ] Using correct label numbers (1, 2, 3, ...)
- [ ] Placing seeds on multiple Z-slices
- [ ] Reviewing 3D segmentations
- [ ] Saving frequently (Ctrl+S)
- [ ] Focusing on co-localized cells

After annotation:
- [ ] All 3 patches have `*_labels.tif` files
- [ ] Verified label counts (10-30 per patch)
- [ ] Ready to organize for training

---

## 🎯 Quick Command Reference

```bash
# Setup (once)
bash setup_nnunet_only.sh

# Extract patches (once)
python extract_colocalized_patches.py

# Annotate all patches (interactive)
python launch_nnunet_interactive.py

# Annotate specific patch
python launch_nnunet_interactive.py --patch colocalization_patches/patch_01_combined.tif
```

---

**Ready to annotate? Let's go!** 🚀

```bash
python launch_nnunet_interactive.py
```

**Remember:** You're in control! The AI only suggests boundaries based on YOUR seed placement. Add more seeds for better results.

Good luck! 🔬✨
