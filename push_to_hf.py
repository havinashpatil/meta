"""Push changed files to Hugging Face Space."""
from huggingface_hub import HfApi
import os

TOKEN = os.environ.get("HF_TOKEN", "your_hf_token_here")
REPO_ID = "adityanaikhpt/codeareana"
REPO_TYPE = "space"
BASE = "e:/meta"

# Only the files that were modified
FILES_TO_PUSH = [
    "server/grader.py",
]

api = HfApi(token=TOKEN)

print(f"Pushing to: {REPO_ID}")
for rel_path in FILES_TO_PUSH:
    local_path = os.path.join(BASE, rel_path.replace("/", os.sep))
    if os.path.exists(local_path):
        print(f"  Uploading: {rel_path} ...", end=" ", flush=True)
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=rel_path,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message=f"fix: clamp strictly to 0.01 and 0.99 to prevent .2f rounding to 1.00",
        )
        print("OK")
    else:
        print(f"  SKIP (not found): {rel_path}")

print("\nDone. All files pushed successfully.")
