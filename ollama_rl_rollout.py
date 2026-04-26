import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import httpx


SYSTEM_PROMPT = (
    "You are an expert Python code repair agent. "
    "Fix the buggy Python code and return ONLY raw Python code."
)


def clean_code(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```python"):
        text = text[9:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def ollama_generate(client: httpx.Client, model: str, prompt: str, base_url: str) -> str:
    def try_chat() -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "max_tokens": 512,
                "top_p": 0.9,
            },
        }
        resp = client.post(f"{base_url}/api/chat", json=payload, timeout=90.0)
        resp.raise_for_status()
        data = resp.json()
        return clean_code(data.get("message", {}).get("content", ""))

    def try_generate() -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 512,
            },
        }
        resp = client.post(f"{base_url}/api/generate", json=payload, timeout=90.0)
        if resp.status_code == 404 or resp.status_code == 405:
            return ""
        resp.raise_for_status()
        data = resp.json()
        return clean_code(data.get("response", "") or data.get("text", ""))

    code = try_generate()
    if not code:
        code = try_chat()
    if not code:
        raise RuntimeError("Ollama returned no valid code from /api/generate or /api/chat.")
    return code


def run_episode(env_client: httpx.Client, ollama_client: httpx.Client, model: str, task_id: str, max_steps: int, env_url: str, ollama_url: str):
    reset = env_client.post(f"{env_url}/reset", json={"task_id": task_id}, timeout=60.0)
    reset.raise_for_status()
    obs_json = reset.json()

    steps = []
    rewards = []
    done = False
    for step in range(1, max_steps + 1):
        if done:
            break
        obs = obs_json.get("observation", {})
        buggy_code = obs.get("buggy_code", "")
        error_log = obs.get("error_log", "")
        test_results = obs.get("test_results", "")

        user_prompt = (
            f"Fix this buggy Python code:\n\n{buggy_code}\n\n"
            f"Error log:\n{error_log}\n\n"
            f"Test results:\n{test_results}\n"
        )
        try:
            proposed_fix = ollama_generate(ollama_client, model, user_prompt, ollama_url)
        except Exception:
            proposed_fix = buggy_code or "pass"

        step_resp = env_client.post(
            f"{env_url}/step",
            json={"proposed_fix": proposed_fix},
            timeout=90.0,
        )
        step_resp.raise_for_status()
        step_data = step_resp.json()
        reward = float(step_data.get("reward", 0.001))
        reward = max(0.001, min(0.999, reward))
        done = bool(step_data.get("done", False))

        steps.append(
            {
                "step": step,
                "prompt": user_prompt,
                "proposed_fix": proposed_fix,
                "reward": reward,
                "done": done,
                "task_id": step_data.get("info", {}).get("task_id", task_id),
                "reward_components": step_data.get("info", {}).get("reward_components", {}),
            }
        )
        rewards.append(reward)
        obs_json = step_data

    return {
        "episode_reward_mean": sum(rewards) / len(rewards) if rewards else 0.001,
        "episode_reward_best": max(rewards) if rewards else 0.001,
        "episode_reward_last": rewards[-1] if rewards else 0.001,
        "steps": steps,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.2:latest")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--env-url", default="http://127.0.0.1:7860")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--output-dir", default="ollama_rl_out")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    traj_path = out_dir / f"trajectories_{ts}.jsonl"
    summary_path = out_dir / f"summary_{ts}.csv"

    tasks = ["easy", "medium", "hard", "type_errors-1", "security_bugs-1"]
    episodes = []
    with httpx.Client() as env_client, httpx.Client() as ollama_client:
        for idx in range(args.episodes):
            task = tasks[idx % len(tasks)]
            ep = run_episode(
                env_client,
                ollama_client,
                args.model,
                task,
                args.max_steps,
                args.env_url,
                args.ollama_url,
            )
            ep["episode_idx"] = idx + 1
            ep["task_seed"] = task
            episodes.append(ep)

    with traj_path.open("w", encoding="utf-8") as f:
        for ep in episodes:
            f.write(json.dumps(ep, ensure_ascii=True) + "\n")

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["episode", "task_seed", "mean_reward", "best_reward", "last_reward"])
        for ep in episodes:
            writer.writerow(
                [
                    ep["episode_idx"],
                    ep["task_seed"],
                    ep["episode_reward_mean"],
                    ep["episode_reward_best"],
                    ep["episode_reward_last"],
                ]
            )

    all_mean = [e["episode_reward_mean"] for e in episodes]
    print(f"episodes={len(episodes)}")
    print(f"start_mean_reward={all_mean[0]:.4f}")
    print(f"end_mean_reward={all_mean[-1]:.4f}")
    print(f"best_mean_reward={max(all_mean):.4f}")
    print(f"avg_mean_reward={(sum(all_mean)/len(all_mean)):.4f}")
    print(f"trajectories={traj_path}")
    print(f"summary={summary_path}")


if __name__ == "__main__":
    main()
