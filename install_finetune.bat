@echo off
REM Installation script for PyTorch and fine-tuning dependencies (Windows)
REM Run this to set up your environment correctly

echo.
echo ======================================
echo CODEARENA FINE-TUNING SETUP
echo ======================================
echo.

REM Check Python version
echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+ first.
    pause
    exit /b 1
)
echo.

REM Check GPU
echo Checking GPU availability...
python -c "
import torch
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
else:
    print('WARNING: No GPU detected - training will be slow')
" 2>nul || echo GPU check skipped
echo.

REM Install PyTorch (with CUDA 12.1 support)
echo Installing PyTorch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
if errorlevel 1 (
    echo ERROR: Failed to install PyTorch
    echo Try installing manually:
    echo pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    pause
    exit /b 1
)
echo PyTorch installed successfully
echo.

REM Install fine-tuning dependencies
echo Installing fine-tuning dependencies...
pip install -r requirements-finetune.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try installing manually:
    echo pip install -r requirements-finetune.txt
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Verify installation
echo Verifying installation...
python -c "
import torch
import transformers
import peft
import trl
import datasets
print(f'PyTorch: {torch.__version__}')
print(f'Transformers: {transformers.__version__}')
print(f'PEFT: {peft.__version__}')
print(f'TRL: {trl.__version__}')
print(f'Datasets: {datasets.__version__}')
"
echo.

echo ======================================
echo SETUP COMPLETE
echo ======================================
echo.
echo Next steps:
echo 1. Run fine-tuning (interactive):
echo    python quickstart_finetune.py
echo.
echo 2. Or directly specify model:
echo    python finetune_models.py --model llama3.2 --num-epochs 3
echo.
pause
