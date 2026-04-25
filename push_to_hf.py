"""Push the full CodeArena project to a Hugging Face Space."""
from huggingface_hub import HfApi
import os

TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    raise SystemExit("Set HF_TOKEN environment variable first.\n  $env:HF_TOKEN='hf_your_token_here'")
REPO_ID = "adityanaikhpt/codearena"
REPO_TYPE = "space"
BASE = os.path.dirname(os.path.abspath(__file__))

# All files needed for the HF Space deployment
FILES_TO_PUSH = [
    # Root
    "Dockerfile",
    "requirements.txt",
    "openenv.yaml",
    "config.py",
    "inference.py",
    "plot_rewards.py",
    "create_tasks.py",
    "train_grpo.ipynb",
    "README.md",
    "pyproject.toml",
    # Server
    "server/__init__.py",
    "server/app.py",
    "server/grader.py",
    "server/executor.py",
    "server/models.py",
    "server/llm_judge.py",
    # Results
    "results/reward_curve.png",
    "results/reward_by_task.png",
    # Rewards log
    "rewards_log.csv",
    # Root-level task files
    "tasks/__init__.py",
    "tasks/easy.json",
    "tasks/easy.py",
    "tasks/medium.json",
    "tasks/medium.py",
    "tasks/hard.json",
    "tasks/hard.py",
    # Test file
    "test_server.py",
]

# Also push all task files
TASK_DIRS = ["tasks/easy", "tasks/medium", "tasks/hard", "tasks/type_errors", "tasks/security_bugs"]
for task_dir in TASK_DIRS:
    full_dir = os.path.join(BASE, task_dir)
    if os.path.isdir(full_dir):
        for f in os.listdir(full_dir):
            if f.endswith(".json"):
                FILES_TO_PUSH.append(f"{task_dir}/{f}")

api = HfApi(token=TOKEN)

# Create the repo if it doesn't exist
try:
    api.create_repo(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        space_sdk="docker",
        exist_ok=True,
    )
    print(f"Space ready: https://huggingface.co/spaces/{REPO_ID}")
except Exception as e:
    print(f"Repo create/check: {e}")

print(f"\nPushing {len(FILES_TO_PUSH)} files to: {REPO_ID}\n")

success = 0
skipped = 0
for rel_path in FILES_TO_PUSH:
    local_path = os.path.join(BASE, rel_path.replace("/", os.sep))
    if os.path.exists(local_path):
        print(f"  Uploading: {rel_path} ...", end=" ", flush=True)
        try:
            api.upload_file(
                path_or_fileobj=local_path,
                path_in_repo=rel_path,
                repo_id=REPO_ID,
                repo_type=REPO_TYPE,
                commit_message=f"Deploy: {rel_path}",
            )
            print("OK")
            success += 1
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        print(f"  SKIP (not found): {rel_path}")
        skipped += 1

print(f"\nDone. {success} uploaded, {skipped} skipped.")
print(f"Space URL: https://huggingface.co/spaces/{REPO_ID}")
