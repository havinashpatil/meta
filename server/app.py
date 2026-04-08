"""
CodeArena RL Environment — Production FastAPI entrypoint.
This is the primary server that Hugging Face Spaces / OpenEnv evaluator hits.
All endpoints are wrapped with fallback safety so they NEVER return non-200.
"""

import random
import traceback
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from server.models import CodeArenaObservation, CodeArenaAction, TaskInfo
from server.executor import run_code_with_tests
from server.grader import calculate_reward
from tasks import ALL_TASKS


# ── Lookup map: difficulty string → list of tasks ──────────────────────────
TASK_MAP: dict[str, list[TaskInfo]] = {}
for _t in ALL_TASKS:
    TASK_MAP.setdefault(_t.difficulty, []).append(_t)
# Also allow lookup by exact task_id  (e.g. "easy-1")
TASK_ID_MAP: dict[str, TaskInfo] = {_t.task_id: _t for _t in ALL_TASKS}


# ── Request schema ─────────────────────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id: Optional[str] = "easy"


# ── Environment state ─────────────────────────────────────────────────────
class CodeArenaEnv:
    def __init__(self):
        self.tasks = ALL_TASKS
        self.current_task: TaskInfo | None = None
        self.previous_attempts: list[str] = []
        self.last_error_log = ""
        self.last_test_results = ""
        self.is_done = False
        self.step_count = 0
        self.max_steps = 5

    def reset(self, task_id: str = "easy") -> CodeArenaObservation:
        # Priority: exact task_id match → difficulty match → random
        if task_id in TASK_ID_MAP:
            self.current_task = TASK_ID_MAP[task_id]
        elif task_id in TASK_MAP:
            self.current_task = random.choice(TASK_MAP[task_id])
        else:
            self.current_task = random.choice(self.tasks)

        self.previous_attempts = []
        self.last_error_log = ""
        self.last_test_results = ""
        self.is_done = False
        self.step_count = 0
        return self._state()

    def step(self, action: CodeArenaAction):
        if self.is_done:
            raise ValueError("Environment is done. Call /reset first.")

        self.step_count += 1

        exec_result = run_code_with_tests(
            code=action.proposed_fix,
            test_code=self.current_task.test_code,
            timeout=max(self.current_task.optimal_time_seconds * 10, 2.0),
        )

        reward = calculate_reward(exec_result, self.current_task)

        self.previous_attempts.append(action.proposed_fix)
        self.last_error_log = exec_result.runtime_errors
        self.last_test_results = (
            f"{exec_result.test_passed}/{exec_result.test_total} tests passed."
        )

        if reward > 0.99 or self.step_count >= self.max_steps:
            self.is_done = True

        info = {
            "execution_metadata": exec_result.model_dump(),
            "task_id": self.current_task.task_id,
        }
        return self._state(), reward, self.is_done, info

    def _state(self) -> CodeArenaObservation:
        if not self.current_task:
            raise ValueError("Environment not initialised. Call /reset first.")
        return CodeArenaObservation(
            buggy_code=self.current_task.buggy_code,
            error_log=self.last_error_log,
            test_results=self.last_test_results,
            previous_attempts=self.previous_attempts,
        )


# ── FastAPI app ────────────────────────────────────────────────────────────
_env = CodeArenaEnv()

app = FastAPI(title="CodeArena RL Environment")


@app.get("/")
def health():
    return {"status": "ok", "environment": "CodeArena"}


@app.post("/reset")
def api_reset(body: ResetRequest = ResetRequest()):
    """Reset the environment. NEVER crashes — returns fallback JSON on error."""
    try:
        task_id = body.task_id or "easy"
        obs = _env.reset(task_id=task_id)
        return {
            "status": "success",
            "message": "Environment reset successfully",
            "observation": obs.model_dump(),
        }
    except Exception:
        traceback.print_exc()
        return {
            "status": "error",
            "message": "fallback response",
            "observation": {
                "buggy_code": "",
                "error_log": str(traceback.format_exc()),
                "test_results": "",
                "previous_attempts": [],
            },
        }


@app.post("/step")
def api_step(action: CodeArenaAction):
    try:
        obs, reward, done, info = _env.step(action)
        return {
            "observation": obs.model_dump(),
            "reward": reward,
            "done": done,
            "info": info,
        }
    except Exception:
        traceback.print_exc()
        return {
            "status": "error",
            "message": "fallback response",
            "observation": {
                "buggy_code": "",
                "error_log": str(traceback.format_exc()),
                "test_results": "",
                "previous_attempts": [],
            },
            "reward": 0.1,
            "done": True,
            "info": {},
        }


@app.get("/state")
def api_state():
    try:
        obs = _env._state()
        return {"observation": obs.model_dump()}
    except Exception:
        traceback.print_exc()
        return {
            "status": "error",
            "message": "fallback response",
        }


# ── CLI entrypoint (OpenEnv / script console_scripts) ─────────────────────
def main():
    """Run the CodeArena server via uvicorn."""
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
