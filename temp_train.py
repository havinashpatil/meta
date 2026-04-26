!pip install trl transformers datasets httpx fastapi uvicorn pydantic openai
!git clone https://github.com/havinashpatil/meta.git
!cd meta && pip install -r requirements.txt
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import GRPOConfig, GRPOTrainer
import httpx

# Start the backend server in the background (Colab trick)
import subprocess
import time
subprocess.Popen(["uvicorn", "server.app:app", "--port", "7860", "--app-dir", "meta"])
time.sleep(5)  # Wait for server to start
def codearena_reward_func(completions, prompts):
    """
    Reward function that queries the CodeArena OpenEnv server.
    For each proposed fix in `completions`, we step the environment.
    """
    rewards = []
    for completion in completions:
        # Clean the generated code
        proposed_fix = completion[0].get('content', '').strip()
        if proposed_fix.startswith('```python'):
            proposed_fix = proposed_fix[9:].replace('```', '').strip()
            
        try:
            # Step the environment
            res = httpx.post(
                "http://localhost:7860/step",
                json={"proposed_fix": proposed_fix},
                timeout=10.0
            )
            res.raise_for_status()
            reward = res.json().get('reward', 0.0)
            rewards.append(reward)
        except Exception as e:
            print(f"Env Error: {e}")
            rewards.append(0.0)
            
    return rewards
# Load Model
model_name = "Qwen/Qwen2.5-Coder-1.5B"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# Load dataset for Coding Debugging and Time Complexity Optimization
dataset = load_dataset("m-a-p/Code-Feedback", split="train")

def format_prompt(example):
    # m-a-p/Code-Feedback contains 'messages' with user and assistant roles
    messages = example.get('messages', [])
    user_query = ""
    if messages and len(messages) > 0 and messages[0].get('role') == 'user':
        user_query = messages[0].get('content', '')
    
    prompt = f"Optimize and debug this code to improve time complexity:\n{user_query}"
    return {"prompt": prompt}

dataset = dataset.map(format_prompt)
# Keep only the prompt column for the trainer
dataset = dataset.select_columns(["prompt"])
# Limit for demo purposes
dataset = dataset.select(range(100))

# Initialize GRPO Trainer
training_args = GRPOConfig(
    output_dir="./codearena-grpo",
    learning_rate=1e-5,
    max_steps=50,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=2,
)

trainer = GRPOTrainer(
    model=model,
    reward_funcs=codearena_reward_func,
    args=training_args,
    train_dataset=dataset,
)

trainer.train()