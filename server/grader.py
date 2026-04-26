import os
import json
from openai import OpenAI
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

_LLM_CACHE = {}
_JUDGE_DISABLED_WARNED = False

def get_llm_quality_score(proposed_fix: str) -> dict:
    global _JUDGE_DISABLED_WARNED
    if proposed_fix in _LLM_CACHE:
        return _LLM_CACHE[proposed_fix]

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        if not _JUDGE_DISABLED_WARNED:
            print("LLM judge disabled: OPENAI_API_KEY not set. Using neutral fallback scores.")
            _JUDGE_DISABLED_WARNED = True
        fallback = {"code_quality": 0.5, "security": 0.5, "correctness": 0.5}
        _LLM_CACHE[proposed_fix] = fallback
        return fallback

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.environ.get("JUDGE_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a code judge. Evaluate the provided Python code on a scale of 0.0 to 1.0 for three metrics: code_quality, security, and correctness. Respond with JSON format strictly matching: {\"code_quality\": 0.0, \"security\": 0.0, \"correctness\": 0.0}"},
                {"role": "user", "content": proposed_fix}
            ],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        _LLM_CACHE[proposed_fix] = result
        return result
    except Exception as e:
        print(f"LLM judge error: {e}")
        fallback = {"code_quality": 0.5, "security": 0.5, "correctness": 0.5}
        _LLM_CACHE[proposed_fix] = fallback
        return fallback

def calculate_reward_components(exec_result: ExecutionResult, task_info: TaskInfo, proposed_fix: str) -> dict:
    compile_score = 1.0 if not exec_result.runtime_errors else 0.0
    
    test_ratio = 0.0
    if exec_result.test_total > 0:
        test_ratio = exec_result.test_passed / exec_result.test_total
        
    efficiency = 0.0
    if test_ratio == 1.0:
        if exec_result.execution_time_seconds <= task_info.optimal_time_seconds:
            efficiency = 1.0
        else:
            ratio = exec_result.execution_time_seconds / max(0.001, task_info.optimal_time_seconds)
            efficiency = max(0.0, 1.0 - (ratio - 1.0) / 2.0)
            
    llm_scores = get_llm_quality_score(proposed_fix)
    
    return {
        "compile_score": compile_score,
        "test_ratio": test_ratio,
        "efficiency": efficiency,
        "llm_correctness": float(llm_scores.get("correctness", 0.5)),
        "llm_security": float(llm_scores.get("security", 0.5)),
        "llm_quality": float(llm_scores.get("code_quality", 0.5))
    }

def calculate_reward(exec_result: ExecutionResult, task_info: TaskInfo, proposed_fix: str) -> tuple[float, dict]:
    comps = calculate_reward_components(exec_result, task_info, proposed_fix)
    base_reward = (
        0.15 * comps["compile_score"] +  
        0.35 * comps["test_ratio"] +      
        0.30 * comps["efficiency"] +     # Increased from 0.15 to push optimization
        0.10 * comps["llm_correctness"] +
        0.05 * comps["llm_security"] +   
        0.05 * comps["llm_quality"]      
    )
    
    # Compile bonus: encourage first milestone
    if comps["compile_score"] > 0.0:
        base_reward += 0.05
        
    # Harsh complexity penalty: if runtime is > 5x optimal, penalize heavily
    if exec_result.test_passed == exec_result.test_total and exec_result.test_total > 0:
        if exec_result.execution_time_seconds > task_info.optimal_time_seconds * 5:
            base_reward -= 0.30
    
    return base_reward, comps

def grade(*args, **kwargs) -> float:
    try:
        if len(args) == 3:
            return calculate_reward(args[0], args[1], args[2])[0]
        return 0.5
    except Exception:
        return 0.5
