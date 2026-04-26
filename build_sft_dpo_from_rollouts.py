import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollouts", required=True, help="Path to rollout trajectories jsonl")
    parser.add_argument("--out-dir", default="ollama_rl_out")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    episodes = load_jsonl(Path(args.rollouts))

    sft_records = []
    grouped = defaultdict(list)
    for ep in episodes:
        for st in ep.get("steps", []):
            row = {
                "prompt": st["prompt"],
                "response": st["proposed_fix"],
                "reward": float(st["reward"]),
                "task_id": st.get("task_id", "unknown"),
            }
            sft_records.append(row)
            grouped[(st["prompt"], st.get("task_id", "unknown"))].append(row)

    dpo_records = []
    for (_, task_id), rows in grouped.items():
        rows = sorted(rows, key=lambda x: x["reward"])
        if len(rows) < 2:
            continue
        chosen = rows[-1]
        rejected = rows[0]
        if chosen["response"].strip() == rejected["response"].strip():
            continue
        dpo_records.append(
            {
                "prompt": chosen["prompt"],
                "chosen": chosen["response"],
                "rejected": rejected["response"],
                "task_id": task_id,
                "chosen_reward": chosen["reward"],
                "rejected_reward": rejected["reward"],
            }
        )

    sft_path = out_dir / "sft_dataset.jsonl"
    dpo_path = out_dir / "dpo_dataset.jsonl"
    with sft_path.open("w", encoding="utf-8") as f:
        for r in sft_records:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")
    with dpo_path.open("w", encoding="utf-8") as f:
        for r in dpo_records:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")

    print(f"sft_records={len(sft_records)} path={sft_path}")
    print(f"dpo_records={len(dpo_records)} path={dpo_path}")


if __name__ == "__main__":
    main()
