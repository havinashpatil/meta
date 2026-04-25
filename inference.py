import requests, csv, os, sys, time
from datetime import datetime

# Load config
sys.path.insert(0, os.path.dirname(__file__))
import config

LOG_FILE = os.path.join(os.path.dirname(__file__), "rewards_log.csv")
os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)

def get_fix(buggy_code: str) -> str:
    prompt_system = (
        "You are a Python debugging agent. "
        "You will be given broken Python code. "
        "Find the bug and fix it. "
        "Return ONLY the corrected Python code. "
        "No explanation. No markdown. No code blocks. Just raw Python."
    )

    if config.MODEL_PROVIDER == "openai":
        import openai
        client = openai.OpenAI(api_key=config.API_KEY, base_url=config.API_BASE_URL)
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": f"Fix this code:\n\n{buggy_code}"}
            ],
            temperature=0.2,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()

    elif config.MODEL_PROVIDER == "huggingface":
        from transformers import pipeline
        pipe = pipeline("text-generation", model=config.MODEL_NAME, max_new_tokens=256)
        result = pipe(f"Fix this Python bug:\n{buggy_code}\nFixed code:")
        return result[0]["generated_text"].split("Fixed code:")[-1].strip()

    elif config.MODEL_PROVIDER == "ollama":
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": config.MODEL_NAME,
                  "prompt": f"{prompt_system}\n\nFix this code:\n{buggy_code}",
                  "stream": False}
        )
        return response.json()["response"].strip()

    else:
        raise ValueError(f"Unknown provider: {config.MODEL_PROVIDER}")

def run_training():
    print(f"\n{'='*50}")
    print(f"CodeArena Training Run")
    print(f"Model: {config.MODEL_NAME} via {config.MODEL_PROVIDER}")
    print(f"Episodes: {config.EPISODES} x {config.STEPS_PER_EPISODE} steps")
    print(f"{'='*50}\n")

    # Write CSV header
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "episode", "step", "task_id",
            "reward", "compile_score", "test_pass_ratio"
        ])
        writer.writeheader()

    all_rewards = []

    for episode in range(config.EPISODES):
        # Alternate between easy and medium for variety
        difficulty = "easy" if episode % 3 != 2 else "medium"
        
        reset_resp = requests.post(
            f"{config.ENVIRONMENT_URL}/reset",
            json={"task_id": difficulty}
        ).json()

        obs = reset_resp["observation"]
        task_id = reset_resp["task_id"]
        episode_rewards = []

        for step_num in range(config.STEPS_PER_EPISODE):
            try:
                fix = get_fix(obs["buggy_code"])
            except Exception as e:
                print(f"  Model error: {e}")
                fix = obs["buggy_code"]  # fallback: send buggy code back

            try:
                result = requests.post(
                    f"{config.ENVIRONMENT_URL}/step",
                    json={"proposed_fix": fix},
                    timeout=30
                ).json()
            except Exception as e:
                print(f"  Environment error: {e}")
                break

            reward = result["reward"]
            components = result.get("reward_components", {})
            episode_rewards.append(reward)
            all_rewards.append(reward)

            # Log to CSV
            with open(LOG_FILE, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "episode", "step", "task_id",
                    "reward", "compile_score", "test_pass_ratio"
                ])
                writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "episode": episode,
                    "step": step_num,
                    "task_id": task_id,
                    "reward": reward,
                    "compile_score": components.get("compile_score", 0),
                    "test_pass_ratio": components.get("test_pass_ratio", 0)
                })

            print(f"  Ep {episode:02d} Step {step_num} | "
                  f"reward={reward:.3f} | "
                  f"compile={components.get('compile_score',0):.1f} | "
                  f"tests={components.get('test_pass_ratio',0):.2f} | "
                  f"done={result['done']}")

            if result["done"]:
                break

            obs = result["observation"]
            time.sleep(0.5)  # be polite to API

        ep_avg = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0
        print(f"Episode {episode:02d} done. Avg reward: {ep_avg:.3f}\n")

    # Final summary
    if all_rewards:
        first10 = sum(all_rewards[:10]) / min(10, len(all_rewards))
        last10 = sum(all_rewards[-10:]) / min(10, len(all_rewards))
        improvement = last10 - first10
        print(f"\n{'='*50}")
        print(f"Training Complete")
        print(f"First 10 steps avg reward : {first10:.3f}")
        print(f"Last  10 steps avg reward : {last10:.3f}")
        print(f"Improvement               : {improvement:+.3f}")
        print(f"Rewards logged to         : {LOG_FILE}")
        print(f"{'='*50}\n")

if __name__ == "__main__":
    run_training()
