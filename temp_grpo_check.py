import re
import argparse
from typing import Any

import httpx
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import GRPOConfig, GRPOTrainer


ENV_URL = "http://127.0.0.1:7860"
MODEL_NAME = "distilgpt2"


def _extract_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list):
        chunks = []
        for item in completion:
            if isinstance(item, dict) and "content" in item:
                chunks.append(str(item["content"]))
            else:
                chunks.append(str(item))
        return "\n".join(chunks)
    if isinstance(completion, dict):
        return str(completion.get("content", ""))
    return str(completion)


def _clean_fix(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:python)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip() or "pass"


def codearena_reward_func(completions, prompts, **kwargs):
    rewards = []
    with httpx.Client(timeout=60.0) as client:
        for completion in completions:
            proposed_fix = _clean_fix(_extract_text(completion))
            reward = 0.001
            for _ in range(2):
                try:
                    client.post(f"{ENV_URL}/reset", json={"task_id": "easy-1"})
                    res = client.post(
                        f"{ENV_URL}/step",
                        json={"proposed_fix": proposed_fix},
                    )
                    reward = float(res.json().get("reward", 0.001))
                    break
                except Exception:
                    reward = 0.001
            rewards.append(max(0.001, min(0.999, reward)))
    return rewards


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-steps", type=int, default=3)
    parser.add_argument("--output-dir", type=str, default="./grpo-check-output")
    args = parser.parse_args()

    prompts = [
        "Fix this Python function: def average_list(numbers)\\n    if length(numbers) == 0:\\n        return 0\\n    return sum(numbers) / length(numbers)",
        "Repair all root-cause issues in the function and keep readability high.",
        "Return a corrected Python function only. Ensure tests pass.",
        "Fix missing syntax and replace invalid APIs with valid Python APIs.",
        "Correct both compile and semantic issues in the provided function.",
        "Provide a secure, clean fix for average_list in Python.",
    ]
    train_dataset = Dataset.from_dict({"prompt": prompts})

    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    training_args = GRPOConfig(
        output_dir=args.output_dir,
        learning_rate=1e-5,
        max_steps=args.max_steps,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=1,
        logging_steps=1,
        num_generations=2,
        max_prompt_length=256,
        max_completion_length=96,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1,
        shuffle_dataset=False,
        seed=42,
        bf16=False,
        fp16=False,
        report_to=[],
    )

    trainer = GRPOTrainer(
        model=model,
        reward_funcs=codearena_reward_func,
        args=training_args,
        train_dataset=train_dataset,
    )
    trainer.train()
    print("GRPO check finished.")


if __name__ == "__main__":
    main()
