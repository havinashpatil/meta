import argparse
import json
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


def load_sft(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            text = (
                "### Instruction\n"
                f"{obj['prompt']}\n\n"
                "### Response\n"
                f"{obj['response']}\n"
            )
            rows.append({"text": text})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft-data", default="ollama_rl_out/sft_dataset.jsonl")
    parser.add_argument("--model-name", default="distilgpt2")
    parser.add_argument("--output-dir", default="hf_sft_checkpoint")
    parser.add_argument("--max-steps", type=int, default=60)
    args = parser.parse_args()

    rows = load_sft(Path(args.sft_data))
    if not rows:
        raise ValueError(
            f"Empty SFT dataset at {args.sft_data}. Run rollout + dataset builder first and verify the dataset path."
        )
    print(f"Loaded {len(rows)} SFT examples from {args.sft_data}")
    dataset = Dataset.from_list(rows)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def tok(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=384,
            padding="max_length",
        )

    tokenized = dataset.map(tok, batched=True, remove_columns=["text"])
    model = AutoModelForCausalLM.from_pretrained(args.model_name)

    train_args = TrainingArguments(
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=1,
        learning_rate=2e-5,
        logging_strategy="steps",
        logging_steps=10,
        save_strategy="steps",
        save_steps=10,
        save_total_limit=2,
        report_to=[],
        fp16=False,
        bf16=False,
    )

    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"saved_checkpoint={args.output_dir}")


if __name__ == "__main__":
    main()
