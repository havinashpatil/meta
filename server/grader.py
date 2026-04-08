from .models import ExecutionResult, TaskInfo


def normalize_reward(passed: int, total: int) -> float:
    """
    Compute a reward strictly within the open interval (0, 1).
    Never returns exactly 0.0 or 1.0.
    """
    if total == 0:
        return 0.5
    reward = passed / total
    if reward <= 0:
        return 0.1
    elif reward >= 1:
        return 0.9
    return float(reward)


def calculate_reward(exec_result: ExecutionResult, task_info: TaskInfo) -> float:
    """
    Single entry-point used by env.py and app.py.
    Delegates entirely to normalize_reward so every task
    always produces a score in (0, 1).
    """
    return normalize_reward(exec_result.test_passed, exec_result.test_total)
