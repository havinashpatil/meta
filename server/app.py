from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, random, subprocess, tempfile, sys
from typing import Optional, List

app = FastAPI(title="CodeArena RL Environment")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# -- State ------------------------------------------------
current_task = {}
step_count = 0
previous_attempts = []
TASKS_DIR = os.path.join(os.path.dirname(__file__), "..", "tasks")

# -- Models -----------------------------------------------
class ResetRequest(BaseModel):
    task_id: str = "easy"
    buggy_code: Optional[str] = None

class StepRequest(BaseModel):
    proposed_fix: str

# -- Helpers ----------------------------------------------
def load_random_task(difficulty: str):
    folder = os.path.join(TASKS_DIR, difficulty)
    files = [f for f in os.listdir(folder) if f.endswith(".json")]
    if not files:
        raise ValueError(f"No tasks found in {folder}")
    path = os.path.join(folder, random.choice(files))
    with open(path) as f:
        return json.load(f)

def run_tests(code: str, tests: list):
    passed = 0
    total = len(tests)
    compile_ok = True
    error_log = ""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                     delete=False, dir=tempfile.gettempdir()) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        for test in tests:
            inp = test["input"]
            expected = test["expected"]

            # Build a test runner script
            test_script = f"""
import sys
sys.path.insert(0, '')
exec(open(r'{tmp_path}').read())

inp = {repr(inp)}
if isinstance(inp, list):
    result = list(locals().values())[-1](*inp) if callable(list(locals().values())[-1]) else None
    # find the function
    import types
    funcs = {{k:v for k,v in locals().items() if isinstance(v, types.FunctionType)}}
    if funcs:
        fn = list(funcs.values())[0]
        result = fn(*inp)
    else:
        result = None
else:
    result = None

expected = {repr(expected)}
print('PASS' if result == expected else f'FAIL got {{result}} expected {{expected}}')
"""
            runner = tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                                  delete=False, dir=tempfile.gettempdir())
            runner.write(test_script)
            runner.close()

            try:
                proc = subprocess.run(
                    [sys.executable, runner.name],
                    capture_output=True, text=True, timeout=5
                )
                if "PASS" in proc.stdout:
                    passed += 1
                elif proc.returncode != 0:
                    compile_ok = False
                    error_log = proc.stderr[:300]
            except subprocess.TimeoutExpired:
                error_log = "Timeout"
            finally:
                os.unlink(runner.name)

    finally:
        os.unlink(tmp_path)

    return compile_ok, passed, total, error_log

# -- Endpoints --------------------------------------------
@app.get("/")
def health():
    return {"status": "ok", "environment": "CodeArena"}

@app.post("/reset")
def reset(req: ResetRequest):
    global current_task, step_count, previous_attempts

    step_count = 0
    previous_attempts = []

    if req.buggy_code:
        # Custom mode -- user pasted their own broken code
        current_task = {
            "task_id": "custom",
            "buggy_code": req.buggy_code,
            "description": "User-provided code -- fix the bug",
            "tests": [
                {"input": [1, 2], "expected": None},
                {"input": [0, 0], "expected": None},
                {"input": [5, 5], "expected": None}
            ]
        }
    elif req.task_id in ("easy", "medium", "hard"):
        current_task = load_random_task(req.task_id)
    elif req.task_id == "auto":
        # Pick random difficulty
        current_task = load_random_task(random.choice(["easy", "medium", "hard"]))
    else:
        current_task = load_random_task("easy")

    return {
        "task_id": current_task["task_id"],
        "observation": {
            "buggy_code": current_task["buggy_code"],
            "error_log": "",
            "test_results": f"0/{len(current_task['tests'])} tests passing",
            "previous_attempts": []
        }
    }

@app.post("/step")
def step(req: StepRequest):
    global step_count, previous_attempts

    step_count += 1
    previous_attempts.append(req.proposed_fix)

    tests = current_task.get("tests", [])
    
    # For custom tasks with no expected values, just check compile + run
    if current_task["task_id"] == "custom":
        compile_ok, passed, total, error_log = True, 0, 1, ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(req.proposed_fix)
                tmp_path = f.name
            proc = subprocess.run([sys.executable, tmp_path],
                                   capture_output=True, text=True, timeout=5)
            compile_ok = proc.returncode == 0
            passed = 1 if compile_ok else 0
            error_log = proc.stderr[:300] if not compile_ok else ""
            os.unlink(tmp_path)
        except Exception as e:
            compile_ok = False
            error_log = str(e)
    else:
        compile_ok, passed, total, error_log = run_tests(req.proposed_fix, tests)
        total = max(total, 1)

    # Reward calculation
    compile_score = 1.0 if compile_ok else 0.0
    test_pass_ratio = passed / len(tests) if tests else compile_score
    reward = round(0.4 * compile_score + 0.6 * test_pass_ratio, 4)
    reward = max(0.001, min(0.999, reward))

    done = (reward > 0.95) or (step_count >= 5)

    return {
        "reward": reward,
        "done": done,
        "reward_components": {
            "compile_score": compile_score,
            "test_pass_ratio": test_pass_ratio
        },
        "observation": {
            "buggy_code": current_task["buggy_code"],
            "error_log": error_log,
            "test_results": f"{passed}/{len(tests)} tests passing",
            "previous_attempts": previous_attempts[-3:]
        }
    }

@app.get("/state")
def state():
    return {
        "task_id": current_task.get("task_id", "none"),
        "step_count": step_count,
        "observation": {
            "buggy_code": current_task.get("buggy_code", ""),
            "error_log": "",
            "test_results": "",
            "previous_attempts": previous_attempts
        }
    }
