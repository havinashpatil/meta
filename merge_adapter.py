import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def merge_and_save(base_model_name: str, adapter_path: str, output_path: str):
    print(f"Loading base model: {base_model_name}...")
    # Load base model on CPU
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float32, # Safe for CPU
        device_map="cpu",
        low_cpu_mem_usage=True
    )
    
    print("Loading tokenizer from base model...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    
    print(f"Applying LoRA adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    
    print("Merging weights (this may take a few minutes and use system RAM)...")
    merged_model = model.merge_and_unload()
    
    print(f"Saving merged model to {output_path} (Using PyTorch chunks to save memory)...")
    merged_model.save_pretrained(
        output_path, 
        safe_serialization=False, 
        max_shard_size="1GB"
    )
    tokenizer.save_pretrained(output_path)
    print("Done! The model is now a standalone Hugging Face model.")

if __name__ == "__main__":
    ADAPTER_DIR = r"E:\meta\gemma-code-optimizer"
    BASE_MODEL = "google/gemma-2b-it"
    MERGED_DIR = r"E:\meta\gemma-merged"
    
    if not os.path.exists(MERGED_DIR):
        os.makedirs(MERGED_DIR)
        
    merge_and_save(BASE_MODEL, ADAPTER_DIR, MERGED_DIR)
