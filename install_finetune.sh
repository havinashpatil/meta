#!/usr/bin/env bash
# Installation script for PyTorch and fine-tuning dependencies
# Run this to set up your environment correctly

set -e  # Exit on error

echo "======================================"
echo "CODEARENA FINE-TUNING SETUP"
echo "======================================"
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"
echo ""

# Detect CUDA/GPU
echo "Checking GPU availability..."
python -c "
import torch
if torch.cuda.is_available():
    print(f'✓ GPU: {torch.cuda.get_device_name(0)}')
    print(f'  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
else:
    print('⚠ No GPU detected - training will use CPU (very slow)')
" || echo "GPU check failed (this is OK if running on CPU-only system)"
echo ""

# Install PyTorch with CUDA 12.1 support (compatible with modern GPUs)
echo "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
echo "✓ PyTorch installed"
echo ""

# Install fine-tuning dependencies
echo "Installing fine-tuning dependencies..."
pip install -r requirements-finetune.txt -q
echo "✓ Dependencies installed"
echo ""

# Verify installation
echo "Verifying installation..."
python -c "
import torch
import transformers
import peft
import trl
import datasets

print(f'✓ PyTorch: {torch.__version__}')
print(f'✓ Transformers: {transformers.__version__}')
print(f'✓ PEFT: {peft.__version__}')
print(f'✓ TRL: {trl.__version__}')
print(f'✓ Datasets: {datasets.__version__}')
"
echo ""

echo "======================================"
echo "SETUP COMPLETE"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Run fine-tuning:"
echo "   python quickstart_finetune.py"
echo ""
echo "2. Or directly specify model:"
echo "   python finetune_models.py --model llama3.2 --num-epochs 3"
echo ""
