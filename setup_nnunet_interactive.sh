#!/bin/bash
# Setup script for nnU-Net interactive annotation

set -e

echo "====================================="
echo "Setting up nnU-Net Interactive"
echo "====================================="

# Check if conda/mamba is available
if command -v mamba &> /dev/null; then
    CONDA_CMD="mamba"
elif command -v conda &> /dev/null; then
    CONDA_CMD="conda"
else
    echo "Error: Neither conda nor mamba found. Please install conda first."
    exit 1
fi

echo ""
echo "Using: $CONDA_CMD"
echo ""

# Install nnU-Net v2
echo "Installing nnU-Net v2..."
pip install nnunetv2

# Install napari-nnunet plugin (for interactive annotation)
echo ""
echo "Installing napari-nnunet plugin..."
pip install napari-nnunet

# Install additional dependencies
echo ""
echo "Installing additional dependencies..."
pip install zarrnii scipy

# Verify installations
echo ""
echo "====================================="
echo "Verifying installations..."
echo "====================================="

python -c "import nnunetv2; print('✓ nnunetv2 installed')" || echo "✗ nnunetv2 failed"
python -c "import napari; print('✓ napari installed')" || echo "✗ napari failed"
python -c "import zarrnii; print('✓ zarrnii installed')" || echo "✗ zarrnii failed"

echo ""
echo "====================================="
echo "Setup complete!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Run: python extract_colocalized_patches.py"
echo "2. Run: python annotate_patches_napari.py"
echo "3. Train your model with annotated data"
echo ""
