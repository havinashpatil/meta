from .models import ExecutionResult, TaskInfo

def safe_reward(reward) -> float:
    try:
        r = float(reward)
    except Exception:
        return 0.5
    return max(0.001, min(0.999, r))

def normalize_reward(passed: int, total: int) -> float:
    if total == 0:
        return 0.5
    return max(0.001, min(0.999, passed / total))

def calculate_reward(exec_result: ExecutionResult, task_info: TaskInfo) -> float:
    reward = normalize_reward(exec_result.test_passed, exec_result.test_total)
    return safe_reward(reward)

def grade(*args, **kwargs) -> float:
    try:
        if len(args) == 2:
            return calculate_reward(args[0], args[1])
        return 0.5
    except Exception:
        return 0.5
