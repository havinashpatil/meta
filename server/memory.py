"""
CodeArena Agent Memory
Self-improving memory across episodes.
Stores best solutions per task + retrieves them to seed future fixes.
"""

import json
import os
import csv
import time
from typing import Optional

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "agent_memory.json")
CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "complexity_rewards.csv")

# ── Memory Store ──────────────────────────────────────────────────────────────

def load_memory() -> dict:
    """Load agent memory from disk."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"[Memory] Load error: {e}")
    return {}


def save_memory(memory: dict) -> None:
    """Persist agent memory to disk."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"[Memory] Save error: {e}")


def store_success(task_id: str, code: str, reward: float) -> None:
    """
    Store a successful solution if reward improves on previous best.
    Only keeps the BEST solution per task.
    """
    memory = load_memory()
    existing = memory.get(task_id)

    if existing is None or reward > existing.get("reward", 0):
        memory[task_id] = {
            "best_code": code,
            "reward": round(reward, 4),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        save_memory(memory)
        print(f"[Memory] Stored new best for '{task_id}' with reward={reward:.3f}")


def retrieve_memory(task_id: str) -> Optional[dict]:
    """
    Retrieve the best known solution for a task.
    Returns dict with 'best_code' and 'reward', or None.
    """
    memory = load_memory()
    return memory.get(task_id)


def get_all_memories() -> dict:
    """Return all stored task memories (for dashboard display)."""
    return load_memory()


# ── Complexity vs Reward CSV Logger ──────────────────────────────────────────

def log_complexity_reward(
    task_id: str,
    reward: float,
    complexity: str,
    step: int,
    method: str = "ollama",
) -> None:
    """
    Append a log entry to complexity_rewards.csv.
    Used to track: better algorithms → better rewards.
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task_id": task_id,
        "reward": round(reward, 4),
        "complexity": complexity,
        "step": step,
        "method": method,
    }
    try:
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=log_entry.keys())
            if not file_exists or f.tell() == 0:
                writer.writeheader()
            writer.writerow(log_entry)
    except Exception as e:
        print(f"[Memory] CSV log error: {e}")


def get_complexity_reward_stats() -> dict:
    """
    Read CSV and compute average reward per complexity class.
    Returns dict like: {"O(n)": 0.88, "O(n^2)": 0.55, "O(n^3)": 0.12}
    """
    stats: dict[str, list] = {}
    try:
        if not os.path.exists(CSV_FILE):
            return {}
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                c = row.get("complexity", "unknown")
                r = float(row.get("reward", 0))
                stats.setdefault(c, []).append(r)
        return {k: round(sum(v) / len(v), 3) for k, v in stats.items()}
    except Exception as e:
        print(f"[Memory] Stats error: {e}")
        return {}
