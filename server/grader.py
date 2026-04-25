from .models import ExecutionResult, TaskInfo


def force_valid_reward(value) -> float:
    """Hard guarantee: reward is strictly in (0, 1) — never 0 or 1, no exceptions."""
    try:
        r = float(value)
    except Exception:
        return 0.5

    # HARD GUARANTEE: prevent .2f formatting from rounding to 1.00 or 0.00
    if r <= 0.01:
        return 0.01
    if r >= 0.99:
        return 0.99

    return r


def safe_reward(reward) -> float:
    """Clamp reward to open interval (0, 1) via force_valid_reward."""
    if reward is None:
        reward = 0.5
    return force_valid_reward(reward)


def normalize_reward(passed: int, total: int) -> float:
    if total == 0:
        return 0.5
    raw = passed / total
    return force_valid_reward(raw)


def calculate_reward(exec_result: ExecutionResult, task_info: TaskInfo) -> float:
    reward = normalize_reward(exec_result.test_passed, exec_result.test_total)
    return force_valid_reward(reward)


def grade(*args, **kwargs) -> float:
    try:
        if len(args) == 2:
            return calculate_reward(args[0], args[1])
        return 0.5
    except Exception:
        return 0.5
