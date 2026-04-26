"""
CodeArena RL Environment — Production FastAPI entrypoint.
This is the primary server that Hugging Face Spaces / OpenEnv evaluator hits.
All endpoints are wrapped with fallback safety so they NEVER return non-200.
"""

import random
import traceback
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from server.models import CodeArenaObservation, CodeArenaAction, TaskInfo
from server.executor import run_code_with_tests
from server.grader import calculate_reward, safe_reward, force_valid_reward
from server.ai_fixer import generate_fix
from server.raw_runner import run_raw_code
from server.memory import store_success, log_complexity_reward, get_complexity_reward_stats, get_all_memories
from server.algorithm_detector import detect_complexity, detect_problem_type, get_optimization_hint
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
        self.episode_rewards_history: list[float] = []

    def reset(self, task_id: str = "easy") -> CodeArenaObservation:
        if task_id == "auto":
            if not self.episode_rewards_history:
                task_id = "easy"
            else:
                avg_reward = sum(self.episode_rewards_history) / len(self.episode_rewards_history)
                if avg_reward < 0.4:
                    task_id = "easy"
                elif avg_reward <= 0.75:
                    task_id = "medium"
                else:
                    task_id = "hard"
        
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

        print(f"[DEBUG] Step {self.step_count}: Processing action")
        print(f"[DEBUG] Proposed fix length: {len(action.proposed_fix)} chars")
        print(f"[DEBUG] Proposed fix preview: {action.proposed_fix[:200]}...")

        exec_result = run_code_with_tests(
            code=action.proposed_fix,
            test_code=self.current_task.test_code,
            timeout=max(self.current_task.optimal_time_seconds * 10, 2.0),
        )

        print(f"[DEBUG] Execution result: compile_success={exec_result.compile_success}, test_passed={exec_result.test_passed}/{exec_result.test_total}, exec_time={exec_result.execution_time_seconds:.2f}s")
        if exec_result.runtime_errors:
            print(f"[DEBUG] Runtime errors: {exec_result.runtime_errors[:500]}")

        base_reward, reward_components = calculate_reward(exec_result, self.current_task, action.proposed_fix)

        print(f"[DEBUG] Base reward: {base_reward:.3f}")
        print(f"[DEBUG] Reward components: {reward_components}")

        step_penalty = 0.01 * self.step_count  # Reduced from 0.02 for gentler learning
        novelty_penalty = 0.1 if action.proposed_fix in self.previous_attempts else 0.0

        print(f"[DEBUG] Penalties: step={step_penalty:.3f}, novelty={novelty_penalty:.3f}")

        final_reward = base_reward - step_penalty - novelty_penalty
        final_reward = max(0.001, min(0.999, float(final_reward)))

        print(f"[DEBUG] Final reward: {final_reward:.3f}")

        self.previous_attempts.append(action.proposed_fix)
        self.last_error_log = exec_result.runtime_errors
        self.last_test_results = (
            f"{exec_result.test_passed}/{exec_result.test_total} tests passed."
        )

        if final_reward > 0.99 or self.step_count >= self.max_steps:
            self.is_done = True
            self.episode_rewards_history.append(final_reward)
            if len(self.episode_rewards_history) > 5:
                self.episode_rewards_history.pop(0)

        info = {
            "execution_metadata": exec_result.model_dump(),
            "task_id": self.current_task.task_id,
            "reward_components": reward_components,
            "test_results": self.last_test_results,
            "llm_feedback": reward_components.get("feedback", "No feedback provided.")
        }
        return self._state(), final_reward, self.is_done, info

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

# Allow the Vite dev server (port 3000) and any other origin to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
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
            "info": {
                "task_id": _env.current_task.task_id if _env.current_task else "",
                "difficulty": _env.current_task.difficulty if _env.current_task else ""
            }
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
        # Compatibility: support both 'proposed_fix' and 'action'
        fix = action.proposed_fix or action.action
        if not fix:
            return {"status": "error", "message": "No code provided in 'proposed_fix' or 'action'"}
        
        # Patch the action object to ensure _env.step gets what it expects
        action.proposed_fix = fix
        
        obs, reward, done, info = _env.step(action)
        # Safety fallback before force_valid_reward
        if reward is None:
            reward = 0.5
        return {
            "observation": obs.model_dump(),
            "reward": force_valid_reward(reward),
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
            "reward": force_valid_reward(0.1),
            "done": True,
            "info": {},
        }


@app.get("/state")
def api_state():
    try:
        obs = _env._state()
        return {
            "step": _env.step_count,
            "history": _env.previous_attempts,
            "observation": obs.model_dump()
        }
    except Exception:
        traceback.print_exc()
        return {
            "status": "error",
            "message": "fallback response",
        }


# ── AI Fix endpoint ───────────────────────────────────────────────────────
class FixRequest(BaseModel):
    code: str
    error_log: Optional[str] = ""
    tgi_url: Optional[str] = "http://localhost:8080"
    use_tgi: Optional[bool] = True
    reward: Optional[float] = 0.0
    task_id: Optional[str] = ""


@app.post("/fix")
def api_fix(body: FixRequest):
    """Generate a code fix using TGI (if available) or built-in pattern fixer."""
    try:
        result = generate_fix(
            code=body.code,
            error_log=body.error_log or "",
            tgi_url=body.tgi_url,
            use_tgi=body.use_tgi,
            reward=body.reward or 0.0,
            task_id=body.task_id or "",
        )
        return result
    except Exception:
        traceback.print_exc()
        return {
            "fixed_code": body.code,
            "method": "passthrough",
            "success": False,
            "error": traceback.format_exc()
        }


# ── Raw Runner endpoint (Sandbox) ──────────────────────────────────────────
class RawRequest(BaseModel):
    code: str

@app.post("/run_raw")
def api_run_raw(body: RawRequest):
    """Run arbitrary code without tests and return output/complexity and reward."""
    try:
        result = run_raw_code(body.code)
        
        # Calculate simulated reward for sandbox
        # Penalty for errors, slight penalty for extremely high exec time
        reward = 0.95
        reward_components = {"Execution Success": 0.5, "Error Free": 0.45}
        
        if result.stderr:
            reward = 0.1
            reward_components["Error Free"] = 0.0
            
        if result.execution_time > 1.0:
            reward -= 0.15
            reward_components["Time Complexity"] = -0.15
            
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": result.execution_time,
            "time_complexity_hint": result.time_complexity_hint,
            "reward": force_valid_reward(reward),
            "reward_components": reward_components,
            "done": False  # Sandbox mode is never "done" strictly by execution, AI must verify optimality
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "status": "error",
            "stderr": str(e),
            "stdout": "",
            "execution_time": 0,
            "time_complexity_hint": "Error evaluating complexity.",
            "reward": force_valid_reward(0.0),
            "reward_components": {},
            "done": False
        }


# ── Stats & Memory endpoints (Research Dashboard) ─────────────────────────
@app.get("/stats")
def api_stats():
    """Return complexity vs reward stats from CSV log."""
    try:
        return {
            "complexity_reward_stats": get_complexity_reward_stats(),
            "episode_history": _env.episode_rewards_history,
            "mean_reward": round(sum(_env.episode_rewards_history) / max(1, len(_env.episode_rewards_history)), 3),
        }
    except Exception:
        traceback.print_exc()
        return {"complexity_reward_stats": {}, "episode_history": [], "mean_reward": 0.0}


@app.get("/memory")
def api_memory():
    """Return all stored best solutions from agent memory."""
    try:
        return {"memories": get_all_memories()}
    except Exception:
        return {"memories": {}}


# ── Static Frontend Serving ───────────────────────────────────────────────
dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        path_in_dist = os.path.join(dist_path, full_path)
        if os.path.isfile(path_in_dist):
            return FileResponse(path_in_dist)
        return FileResponse(os.path.join(dist_path, "index.html"))

# ── CLI entrypoint (OpenEnv / script console_scripts) ─────────────────────
def main():
    """Run the CodeArena server via uvicorn."""
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
