import random
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .models import CodeArenaObservation, CodeArenaAction, TaskInfo
from .executor import run_code_with_tests
from .grader import calculate_reward, safe_reward, force_valid_reward
from tasks import ALL_TASKS

class CodeArenaEnv:
    def __init__(self):
        self.tasks = ALL_TASKS
        self.current_task: TaskInfo = None
        self.previous_attempts = []
        self.last_error_log = ""
        self.last_test_results = ""
        self.is_done = False
        self.step_count = 0
        self.max_steps = 5

    def reset(self, task_id: str = None) -> CodeArenaObservation:
        if task_id:
            matched = [t for t in self.tasks if t.task_id == task_id]
            self.current_task = matched[0] if matched else random.choice(self.tasks)
        else:
            self.current_task = random.choice(self.tasks)
        self.previous_attempts = []
        self.last_error_log = ""
        self.last_test_results = ""
        self.is_done = False
        self.step_count = 0
        return self.state()

    def step(self, action: CodeArenaAction) -> tuple[CodeArenaObservation, float, bool, dict]:
        if self.is_done:
            raise ValueError("Environment is already done. Call reset().")
            
        self.step_count += 1
        
        # Execute the proposed fix with 10x optimal time as a hard timeout limit
        exec_result = run_code_with_tests(
            code=action.proposed_fix,
            test_code=self.current_task.test_code,
            timeout=max(self.current_task.optimal_time_seconds * 10, 2.0) 
        )
        
        # Calculate Reward
        reward = safe_reward(calculate_reward(exec_result, self.current_task))
        reward = max(0.001, min(0.999, float(reward)))
        
        # Update State
        self.previous_attempts.append(action.proposed_fix)
        self.last_error_log = exec_result.runtime_errors
        self.last_test_results = f"{exec_result.test_passed}/{exec_result.test_total} tests passed."
        
        # Check termination condition
        if reward > 0.99 or self.step_count >= self.max_steps:
            self.is_done = True
            
        info = {
            "execution_metadata": exec_result.model_dump(),
            "task_id": self.current_task.task_id
        }
        
        return self.state(), reward, self.is_done, info

    def state(self) -> CodeArenaObservation:
        if not self.current_task:
            raise ValueError("Environment not initialized. Call reset() first.")
            
        return CodeArenaObservation(
            buggy_code=self.current_task.buggy_code,
            error_log=self.last_error_log,
            test_results=self.last_test_results,
            previous_attempts=self.previous_attempts,
        )

# Initialize a global environment instance for the FastAPI wrapper
_env = CodeArenaEnv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    _env.reset()
    yield

app = FastAPI(lifespan=lifespan, title="CodeArena RL Environment")

@app.post("/reset")
def api_reset(body: dict = None):
    task_id = (body or {}).get("task_id")
    obs = _env.reset(task_id=task_id)
    return {"message": "Environment reset successfully", "observation": obs.model_dump()}

@app.post("/step")
def api_step(action: CodeArenaAction):
    try:
        obs, reward, done, info = _env.step(action)
        # Safety fallback before force_valid_reward
        if reward is None:
            reward = 0.5
        return {
            "observation": obs.model_dump(),
            "reward": force_valid_reward(reward),
            "done": done,
            "info": info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/state")
def api_state():
    try:
        obs = _env.state()
        return {"observation": obs.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
