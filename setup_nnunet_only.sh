#!/bin/bash
# Focused setup for nnU-Net interactive annotation

set -e

echo "=================================================="
echo "  nnU-Net Interactive Setup"
echo "=================================================="
echo ""

# Install napari if not already installed
echo "1. Checking napari..."
if python -c "import napari" 2>/dev/null; then
    echo "   ✓ napari already installed"
else
    echo "   → Installing napari..."
    pip install "napari[all]"
fi

# Install napari-nnunet plugin (the interactive annotation tool)
echo ""
echo "2. Installing napari-nnunet plugin..."
pip install napari-nnunet

# Install dependencies for our extraction scripts
echo ""
echo "3. Installing dependencies..."
pip install zarrnii scipy tifffile dask

echo ""
echo "=================================================="
echo "  Verification"
echo "=================================================="

python -c "import napari; print('✓ napari installed')" || echo "✗ napari failed"
python -c "import napari_nnunet; print('✓ napari-nnunet installed')" || echo "✗ napari-nnunet failed"
python -c "from zarrnii import ZarrNii; print('✓ zarrnii installed')" || echo "✗ zarrnii failed"
python -c "import scipy; print('✓ scipy installed')" || echo "✗ scipy failed"

echo ""
echo "=================================================="
echo "  Setup Complete! ✨"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Extract patches: python extract_colocalized_patches.py"
echo "  2. Annotate with nnU-Net: python launch_nnunet_interactive.py"
echo ""
