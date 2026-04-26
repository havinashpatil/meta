"""
CodeArena — Fine-Tuning Script
Fine-tunes LLaMA / Gemma models on the XCoder-80K dataset using Unsloth.

Supported base models (pick one):
  - unsloth/Llama-3.2-3B-Instruct      (recommended for code tasks)
  - unsloth/gemma-3-4b-it
  - unsloth/gemma-3-1b-it
  - unsloth/llava-1.5-7b-hf            (multimodal — skip for code-only)

Usage:
  python finetune.py --model llama3 --output ./finetuned_model

After training:
  The model is saved to ./finetuned_model (GGUF + LoRA adapter)
  Pull into Ollama:
    ollama create codearena -f ./finetuned_model/Modelfile
"""

import argparse
import os
import sys

# ─── Check GPU ────────────────────────────────────────────────────────────────

def check_gpu():
    try:
        import torch
        if not torch.cuda.is_available():
            print("⚠ WARNING: No CUDA GPU found. Fine-tuning will be very slow on CPU.")
            print("  Recommended: Use Google Colab (free T4 GPU) or Kaggle Notebooks.")
        else:
            print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("✗ PyTorch not installed. Run: pip install torch torchvision")
        sys.exit(1)

# ─── Model Registry ───────────────────────────────────────────────────────────

MODELS = {
    "llama3":  "unsloth/Llama-3.2-3B-Instruct",
    "llama3_8b": "unsloth/Meta-Llama-3.1-8B-Instruct",
    "gemma4b": "unsloth/gemma-3-4b-it",
    "gemma1b": "unsloth/gemma-3-1b-it",
}

# ─── Dataset Formatter ────────────────────────────────────────────────────────

def format_xcoder_example(example: dict) -> dict:
    """
    Convert XCoder-80K format to chat-style instruction tuning.
    XCoder format: { instruction, input, output, system? }
    """
    instruction = example.get("instruction", "")
    inp = example.get("input", "")
    output = example.get("output", "")
    system = example.get("system", "You are an expert Python debugging assistant.")

    user_msg = instruction
    if inp:
        user_msg += f"\n\n```python\n{inp}\n```"

    return {
        "messages": [
            {"role": "system",    "content": system},
            {"role": "user",      "content": user_msg},
            {"role": "assistant", "content": output},
        ]
    }


def load_xcoder_dataset(max_samples: int = 5000):
    """Load and format the XCoder-80K dataset."""
    from datasets import load_dataset
    print("📦 Loading banksy235/XCoder-80K dataset...")
    ds = load_dataset("banksy235/XCoder-80K", split="train")

    # Filter for code-related examples
    def is_code_task(ex):
        text = (ex.get("instruction", "") + ex.get("input", "") + ex.get("output", "")).lower()
        return any(kw in text for kw in ["python", "def ", "function", "bug", "error", "fix", "optimize", "algorithm"])

    print(f"  Total examples: {len(ds)}")
    ds = ds.filter(is_code_task)
    print(f"  Code-related: {len(ds)}")

    if max_samples and len(ds) > max_samples:
        ds = ds.select(range(max_samples))
        print(f"  Using {max_samples} samples for training")

    ds = ds.map(format_xcoder_example, remove_columns=ds.column_names)
    return ds


# ─── Main Fine-Tuning ─────────────────────────────────────────────────────────

def run_finetune(model_key: str, output_dir: str, max_samples: int, epochs: int, batch_size: int):
    check_gpu()

    try:
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import get_chat_template, train_on_responses_only
        from trl import SFTTrainer
        from transformers import TrainingArguments, DataCollatorForSeq2Seq
    except ImportError:
        print("\n✗ Unsloth not installed. Install it first:")
        print("  pip install unsloth trl transformers accelerate bitsandbytes datasets")
        sys.exit(1)

    model_id = MODELS.get(model_key, MODELS["llama3"])
    print(f"\n🚀 Loading model: {model_id}")

    # Load model with 4-bit quantization (fits in ~6GB VRAM)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_id,
        max_seq_length=2048,
        dtype=None,          # Auto-detect (bfloat16 on modern GPUs)
        load_in_4bit=True,   # QLoRA — use less VRAM
    )

    # Apply LoRA adapters (PEFT — only train ~1% of params)
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,                   # LoRA rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # Apply chat template
    tokenizer = get_chat_template(tokenizer, chat_template="llama-3")

    def apply_template(examples):
        texts = tokenizer.apply_chat_template(
            examples["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": texts}

    # Load dataset
    dataset = load_xcoder_dataset(max_samples)
    dataset = dataset.map(apply_template, batched=True, remove_columns=["messages"])

    print(f"\n📊 Training on {len(dataset)} examples for {epochs} epoch(s)")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=10,
            num_train_epochs=epochs,
            learning_rate=2e-4,
            fp16=False,
            bf16=True,
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            output_dir=output_dir,
            save_strategy="epoch",
            report_to="none",
        ),
    )

    # Only train on assistant responses, not user prompts
    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
        response_part="<|start_header_id|>assistant<|end_header_id|>\n\n",
    )

    print("\n🔥 Starting training...")
    trainer_stats = trainer.train()
    print(f"\n✓ Training complete! Stats: {trainer_stats.metrics}")

    # Save model
    print(f"\n💾 Saving LoRA adapter to {output_dir}/lora_model")
    model.save_pretrained(f"{output_dir}/lora_model")
    tokenizer.save_pretrained(f"{output_dir}/lora_model")

    # Export to GGUF for Ollama
    print("\n📦 Exporting to GGUF (Q4_K_M quantization)...")
    try:
        model.save_pretrained_gguf(
            f"{output_dir}/gguf_model",
            tokenizer,
            quantization_method="q4_k_m",
        )
        # Write Modelfile for Ollama
        modelfile = f"""FROM {output_dir}/gguf_model/model-q4_k_m.gguf

SYSTEM You are CodeArena, an expert Python debugging and code optimization agent.
You fix bugs, optimize algorithms, and improve code quality.
Always return ONLY the fixed code without explanation unless asked.

PARAMETER temperature 0.1
PARAMETER num_ctx 2048
"""
        with open(f"{output_dir}/Modelfile", "w") as f:
            f.write(modelfile)

        print(f"""
╔═══════════════════════════════════════════════════════╗
║  ✓ Fine-tuning complete!                              ║
║                                                       ║
║  To use in CodeArena:                                 ║
║    1. Install the model into Ollama:                  ║
║       ollama create codearena -f {output_dir}/Modelfile  ║
║    2. Set model name to "codearena" in the dashboard  ║
╚═══════════════════════════════════════════════════════╝
""")
    except Exception as e:
        print(f"⚠ GGUF export failed: {e}")
        print("  LoRA adapter saved. You can merge it manually later.")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune a model on XCoder-80K for CodeArena")
    parser.add_argument("--model", choices=list(MODELS.keys()), default="llama3",
                        help="Base model to fine-tune")
    parser.add_argument("--output", default="./finetuned_model",
                        help="Output directory for the fine-tuned model")
    parser.add_argument("--samples", type=int, default=5000,
                        help="Max training samples from XCoder-80K (default: 5000)")
    parser.add_argument("--epochs", type=int, default=1,
                        help="Number of training epochs (default: 1)")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Batch size per device (default: 2)")
    args = parser.parse_args()

    run_finetune(
        model_key=args.model,
        output_dir=args.output,
        max_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
