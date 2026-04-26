#!/usr/bin/env python3
"""
Fine-tune models on the XCoder-80K dataset using TRL.

Models:
- meta-llama/Llama-2-7b-hf (maps to llama3.2:latest in Ollama)
- google/gemma-7b (maps to gemma3:4b - adjusted)
- google/gemma-2b (maps to gemma3:1b - adjusted)
- LLaVA (multimodal - skipped for text-only fine-tuning)

Dataset: banksy235/XCoder-80K

Fine-tuning approaches:
1. SFT (Supervised Fine-Tuning) - simple and effective
2. DPO (Direct Preference Optimization) - if preference data available
3. GRPO (Group Relative Policy Optimization) - for RL environments
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Optional

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import get_peft_model, LoraConfig, TaskType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model registry - maps available models to HF model IDs
MODEL_REGISTRY = {
    "llama3.2": "meta-llama/Llama-2-7b-hf",
    "gemma3:4b": "google/gemma-7b",
    "gemma3:1b": "google/gemma-2b",
}

XCODER_DATASET = "banksy235/XCoder-80K"

def load_xcoder_dataset(split: str = "train", max_samples: Optional[int] = None):
    """Load XCoder-80K dataset from Hugging Face."""
    logger.info(f"Loading {XCODER_DATASET} ({split} split)...")
    try:
        ds = load_dataset(XCODER_DATASET, split=split)
        if max_samples:
            ds = ds.select(range(min(max_samples, len(ds))))
        logger.info(f"Loaded {len(ds)} examples")
        return ds
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def prepare_dataset_for_sft(dataset, tokenizer, max_length: int = 2048):
    """Prepare dataset for SFT (Supervised Fine-Tuning)."""
    logger.info("Preparing dataset for SFT...")
    
    def tokenize_function(examples):
        """Tokenize function for the dataset."""
        # Assuming dataset has 'code' and/or 'text' fields
        texts = []
        for i in range(len(examples.get("code", []))):
            # Try different field combinations
            if "code" in examples:
                code = examples["code"][i]
                if "comment" in examples:
                    text = f"{examples['comment'][i]}\n{code}"
                elif "problem" in examples:
                    text = f"{examples['problem'][i]}\n{code}"
                else:
                    text = code
            elif "text" in examples:
                text = examples["text"][i]
            else:
                # Fallback: concatenate all string fields
                text = " ".join([str(v) for k, v in examples.items() if isinstance(v, list) and i < len(v)])
            texts.append(text)
        
        # Tokenize
        encodings = tokenizer(
            texts,
            max_length=max_length,
            truncation=True,
            padding="max_length",
            return_tensors=None,
        )
        return encodings
    
    # Apply tokenization
    tokenized_ds = dataset.map(
        tokenize_function,
        batched=True,
        batch_size=32,
        remove_columns=dataset.column_names,
    )
    
    logger.info(f"Prepared {len(tokenized_ds)} samples")
    return tokenized_ds

def setup_lora(model, lora_rank: int = 8, lora_alpha: int = 16):
    """Setup LoRA (Low-Rank Adaptation) for efficient fine-tuning."""
    logger.info(f"Setting up LoRA (rank={lora_rank}, alpha={lora_alpha})...")
    
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=0.1,
        bias="none",
        target_modules=["q_proj", "v_proj"],  # Common for causal LM
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    return model

def finetune_model(
    model_name: str,
    output_dir: str = "./finetuned_models",
    num_epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
    max_samples: Optional[int] = None,
    use_lora: bool = True,
    use_gradient_checkpointing: bool = True,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
):
    """Fine-tune a model on the XCoder-80K dataset."""
    
    # Validate model
    if model_name not in MODEL_REGISTRY:
        logger.error(f"Model {model_name} not found. Available: {list(MODEL_REGISTRY.keys())}")
        return False
    
    hf_model_id = MODEL_REGISTRY[model_name]
    output_model_dir = Path(output_dir) / model_name.replace(":", "_")
    output_model_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Fine-tuning: {model_name}")
    logger.info(f"HF Model: {hf_model_id}")
    logger.info(f"Output: {output_model_dir}")
    logger.info(f"Device: {device}")
    logger.info(f"{'='*60}\n")
    
    # Load dataset
    dataset = load_xcoder_dataset(split="train", max_samples=max_samples)
    
    # Load tokenizer and model
    logger.info(f"Loading {hf_model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        hf_model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else "cpu",
    )
    
    if use_gradient_checkpointing:
        model.gradient_checkpointing_enable()
    
    # Setup LoRA if requested
    if use_lora:
        model = setup_lora(model)
    
    # Prepare dataset
    train_dataset = prepare_dataset_for_sft(dataset, tokenizer)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_model_dir),
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_steps=500,
        logging_steps=100,
        save_steps=500,
        save_total_limit=2,
        gradient_accumulation_steps=2,
        gradient_checkpointing=use_gradient_checkpointing,
        fp16=device == "cuda",
        optim="paged_adamw_8bit" if device == "cuda" else "adamw_torch",
        report_to=["tensorboard"],
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    
    # Train
    logger.info("Starting training...")
    try:
        trainer.train()
        logger.info(f"✓ Training completed successfully")
        logger.info(f"Model saved to: {output_model_dir}")
        
        # Save final model and tokenizer
        model.save_pretrained(str(output_model_dir / "final"))
        tokenizer.save_pretrained(str(output_model_dir / "final"))
        
        # Save metadata
        metadata = {
            "model_name": model_name,
            "hf_model_id": hf_model_id,
            "dataset": XCODER_DATASET,
            "training_args": training_args.to_dict(),
            "num_epochs": num_epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
        }
        with open(output_model_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Fine-tune models on XCoder-80K dataset")
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.2",
        choices=list(MODEL_REGISTRY.keys()),
        help="Model to fine-tune",
    )
    parser.add_argument(
        "--all-models",
        action="store_true",
        help="Fine-tune all available models sequentially",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./finetuned_models",
        help="Output directory for fine-tuned models",
    )
    parser.add_argument(
        "--num-epochs",
        type=int,
        default=3,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Training batch size",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Learning rate",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to use (None = all)",
    )
    parser.add_argument(
        "--no-lora",
        action="store_true",
        help="Disable LoRA (full fine-tuning instead)",
    )
    parser.add_argument(
        "--no-gradient-checkpointing",
        action="store_true",
        help="Disable gradient checkpointing",
    )
    
    args = parser.parse_args()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    if args.all_models:
        results = {}
        for model_name in MODEL_REGISTRY.keys():
            success = finetune_model(
                model_name=model_name,
                output_dir=args.output_dir,
                num_epochs=args.num_epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                max_samples=args.max_samples,
                use_lora=not args.no_lora,
                use_gradient_checkpointing=not args.no_gradient_checkpointing,
                device=device,
            )
            results[model_name] = "✓ Success" if success else "✗ Failed"
        
        logger.info("\n" + "="*60)
        logger.info("FINE-TUNING RESULTS")
        logger.info("="*60)
        for model, status in results.items():
            logger.info(f"{model}: {status}")
    else:
        success = finetune_model(
            model_name=args.model,
            output_dir=args.output_dir,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_samples=args.max_samples,
            use_lora=not args.no_lora,
            use_gradient_checkpointing=not args.no_gradient_checkpointing,
            device=device,
        )
        
        if success:
            logger.info("\n✓ Fine-tuning completed successfully!")
            logger.info(f"Output directory: {args.output_dir}")
        else:
            logger.error("\n✗ Fine-tuning failed!")

if __name__ == "__main__":
    main()
