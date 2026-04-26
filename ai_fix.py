#!/usr/bin/env python3
"""
AI Code Fixer using Hugging Face Transformers
Reads code from stdin, fixes it using TinyLlama, outputs fixed code.
"""

import sys
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Model configuration
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

def load_model():
    """Load the model and tokenizer."""
    print("Loading model...", file=sys.stderr)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Try to use GPU if available, fallback to CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}", file=sys.stderr)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        low_cpu_mem_usage=True
    )

    if device == "cpu":
        model = model.to(device)

    return model, tokenizer

def generate_fix(model, tokenizer, code):
    """Generate fixed code using the model."""
    prompt = f"""You are an expert competitive programmer.

Fix the following Python code:
- Remove syntax errors
- Ensure correct logic
- Optimize to O(n) if possible

Code:
{code}

Return ONLY corrected code.
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=500,
            temperature=0.3,  # Lower temperature for more deterministic fixes
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode and extract only the code part
    full_output = tokenizer.decode(output[0], skip_special_tokens=True)

    # Try to extract just the code after the prompt
    if "Return ONLY corrected code." in full_output:
        code_part = full_output.split("Return ONLY corrected code.")[-1].strip()
    else:
        code_part = full_output.replace(prompt, "").strip()

    return code_part

def main():
    # Read code from stdin
    code = sys.stdin.read().strip()

    if not code:
        print("No code provided", file=sys.stderr)
        sys.exit(1)

    try:
        model, tokenizer = load_model()
        fixed_code = generate_fix(model, tokenizer, code)
        print(fixed_code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()