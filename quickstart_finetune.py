#!/usr/bin/env python3
"""
Quick-start script for fine-tuning models on XCoder-80K dataset.
Run this script to automatically set up and fine-tune your model.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def check_cuda():
    """Check if CUDA is available."""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            logger.info(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            logger.info(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            logger.warning("⚠ CUDA not available - training will use CPU (very slow)")
        return cuda_available
    except Exception as e:
        logger.error(f"Error checking CUDA: {e}")
        return False

def install_dependencies():
    """Install required dependencies."""
    logger.info("\n" + "="*60)
    logger.info("INSTALLING DEPENDENCIES")
    logger.info("="*60)
    
    try:
        logger.info("Installing fine-tuning requirements...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-finetune.txt", "-q"],
            check=True
        )
        logger.info("✓ Dependencies installed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def verify_xcoder_dataset():
    """Verify that XCoder-80K dataset can be accessed."""
    logger.info("\n" + "="*60)
    logger.info("VERIFYING XCODER-80K DATASET")
    logger.info("="*60)
    
    try:
        from datasets import load_dataset
        logger.info("Checking XCoder-80K dataset availability...")
        ds_info = load_dataset("banksy235/XCoder-80K", split="train", streaming=True)
        logger.info(f"✓ XCoder-80K dataset is accessible")
        logger.info(f"  Dataset features: {ds_info.column_names}")
        return True
    except Exception as e:
        logger.warning(f"⚠ Could not verify dataset: {e}")
        logger.info("  This may be normal if you're offline - dataset will be downloaded on first run")
        return False

def run_finetuning():
    """Run the fine-tuning script."""
    logger.info("\n" + "="*60)
    logger.info("STARTING FINE-TUNING")
    logger.info("="*60)
    logger.info("\nAvailable models:")
    logger.info("  1. llama3.2 (Llama-2-7B) - Recommended")
    logger.info("  2. gemma3:4b (Gemma-7B) - Alternative")
    logger.info("  3. gemma3:1b (Gemma-2B) - Lightweight")
    logger.info("  4. all-models - Fine-tune all")
    
    choice = input("\nSelect model (1-4, or enter custom model name): ").strip()
    
    model_map = {
        "1": "llama3.2",
        "2": "gemma3:4b",
        "3": "gemma3:1b",
        "4": "--all-models",
    }
    
    model_arg = model_map.get(choice, choice)
    
    if not model_arg or model_arg == "":
        logger.error("Invalid selection")
        return False
    
    # Ask for training parameters
    logger.info("\nTraining configuration (press Enter for defaults):")
    
    epochs = input("Number of epochs (default: 3): ").strip() or "3"
    batch_size = input("Batch size (default: 4): ").strip() or "4"
    learning_rate = input("Learning rate (default: 2e-4): ").strip() or "2e-4"
    max_samples = input("Max samples (default: all): ").strip() or ""
    
    # Build command
    cmd = [
        sys.executable,
        "finetune_models.py",
    ]
    
    if model_arg == "--all-models":
        cmd.append("--all-models")
    else:
        cmd.extend(["--model", model_arg])
    
    cmd.extend([
        "--num-epochs", epochs,
        "--batch-size", batch_size,
        "--learning-rate", learning_rate,
    ])
    
    if max_samples:
        cmd.extend(["--max-samples", max_samples])
    
    logger.info("\n" + "="*60)
    logger.info("TRAINING CONFIGURATION")
    logger.info("="*60)
    logger.info(f"Model: {model_arg if model_arg != '--all-models' else 'All models'}")
    logger.info(f"Epochs: {epochs}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Learning rate: {learning_rate}")
    if max_samples:
        logger.info(f"Max samples: {max_samples}")
    logger.info("\n" + "="*60)
    
    confirm = input("Start training? (y/n): ").strip().lower()
    if confirm != "y":
        logger.info("Cancelled")
        return False
    
    # Run training
    logger.info("\nStarting training process...")
    logger.info("Monitor training with: tensorboard --logdir ./finetuned_models/[model_name]")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return False

def main():
    """Main entry point."""
    logger.info("="*60)
    logger.info("CODEARENA FINE-TUNING QUICK START")
    logger.info("="*60)
    
    # Check CUDA
    cuda_available = check_cuda()
    
    if not cuda_available:
        logger.warning("\n⚠ Warning: CUDA not available. Training will be extremely slow.")
        logger.warning("  Consider using a GPU (RTX 3090, A100, etc.) or cloud services (Colab, Lambda Labs)")
        confirm = input("\nContinue with CPU training? (y/n): ").strip().lower()
        if confirm != "y":
            logger.info("Cancelled")
            return
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Failed to install dependencies")
        return
    
    # Verify dataset
    verify_xcoder_dataset()
    
    # Run fine-tuning
    if run_finetuning():
        logger.info("\n" + "="*60)
        logger.info("✓ FINE-TUNING COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Check output in ./finetuned_models/")
        logger.info("2. Export to Ollama (see FINETUNE_GUIDE.md)")
        logger.info("3. Use in CodeArena: update Dashboard.jsx or ollama_rl_rollout.py")
        logger.info("4. Monitor performance: python plot_rewards.py")
    else:
        logger.error("\n✗ Fine-tuning failed or was cancelled")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
