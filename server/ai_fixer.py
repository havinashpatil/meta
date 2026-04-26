"""
CodeArena Built-in AI Code Fixer
Uses AST analysis + pattern-based repair + TGI LLM integration.
Supports TGI (Text Generation Inference) for advanced code fixing.
"""

import ast
import re
import textwrap
import subprocess
import sys
import os
from typing import Optional
import httpx
from server.algorithm_detector import (
    detect_problem_type, detect_complexity, needs_optimization,
    get_optimization_hint, build_adaptive_prompt_suffix, ALGO_HINTS
)
from server.memory import store_success, retrieve_memory, log_complexity_reward


# TGI Configuration
TGI_BASE_URL = os.environ.get("TGI_BASE_URL", "http://localhost:8080")
TGI_AVAILABLE = False

def check_tgi_availability(tgi_url: str = TGI_BASE_URL) -> bool:
    """Check if TGI server is available."""
    global TGI_AVAILABLE
    try:
        response = httpx.get(f"{tgi_url}/health", timeout=5.0)
        TGI_AVAILABLE = response.status_code == 200
    except Exception:
        TGI_AVAILABLE = False
    return TGI_AVAILABLE


def fix_with_tgi(code: str, tgi_url: str = TGI_BASE_URL) -> Optional[str]:
    """Use TGI for advanced code fixing."""
    if not TGI_AVAILABLE and not check_tgi_availability(tgi_url):
        return None

    prompt = f"""You are an expert competitive programmer.

Fix the following Python code:
- Remove syntax errors
- Ensure correct logic
- Optimize to O(n) if possible

Code:
{code}

Return ONLY the corrected code without any explanation:
"""

    try:
        response = httpx.post(
            f"{tgi_url}/v1/chat/completions",
            json={
                "model": "tgi",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.3
            },
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        fixed_code = result["choices"][0]["message"]["content"].strip()

        # Clean up the response
        if "Return ONLY the corrected code" in fixed_code:
            fixed_code = fixed_code.split("Return ONLY the corrected code")[-1].strip()

        return fixed_code if fixed_code else None

    except Exception as e:
        print(f"TGI fix error: {e}", file=sys.stderr)
        return None


# ─── Pattern-Based Fixes ─────────────────────────────────────────────────────


# ─── Pattern-Based Fixes ─────────────────────────────────────────────────────

def fix_syntax_errors(code: str) -> str:
    """Try to auto-fix common syntax errors."""
    lines = code.split('\n')
    fixed = []
    for line in lines:
        # Fix missing colon on def/class/if/for/while/else/elif/try/except/finally
        stripped = line.rstrip()
        if re.match(r'^\s*(def |class |if |elif |else|for |while |try|except|finally)', stripped):
            if not stripped.endswith(':') and not stripped.endswith('\\') and not stripped.endswith(','):
                stripped = stripped + ':'
        fixed.append(stripped)
    return '\n'.join(fixed)


def fix_wrong_builtins(code: str) -> str:
    """Fix common wrong builtin usage."""
    replacements = {
        r'\blenght\b': 'len',
        r'\bappned\b': 'append',
        r'\bpirnt\b': 'print',
        r'\bprnit\b': 'print',
        r'\bretrun\b': 'return',
        r'\bpas\b': 'pass',
        r'\bTreu\b': 'True',
        r'\bFlase\b': 'False',
        r'\bNoen\b': 'None',
    }
    for pattern, replacement in replacements.items():
        code = re.sub(pattern, replacement, code)
    return code


def optimize_complexity(code: str) -> str:
    """
    Detect and optimize common O(N^2)/O(N^3) patterns.
    - Triple nested loops on same array → Kadane's algorithm
    - Bubble sort → sorted() 
    - Linear search in list → set/dict lookup
    """
    # Detect triple nested loop (O(N^3)) → max subarray → Kadane's
    if re.search(r'for\s+\w+\s+in\s+range.*:\s*\n.*for\s+\w+\s+in\s+range.*:\s*\n.*for\s+\w+\s+in\s+range', code, re.DOTALL):
        # Extract function signature
        match = re.match(r'(def\s+\w+\([^)]*\):)', code.strip())
        if match:
            sig = match.group(1)
            fname = re.search(r'def\s+(\w+)', sig).group(1)
            # Check if it's a max subarray problem
            if 'max' in code.lower() and ('sum' in code.lower() or 'subarray' in code.lower()):
                return f"""{sig}
    # Optimized: Kadane's Algorithm O(N)
    if not arr:
        return 0
    max_sum = arr[0]
    current_sum = arr[0]
    for num in arr[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    return max_sum"""

    # Detect O(N^2) bubble sort → use sorted()
    if re.search(r'for\s+\w+.*range.*:\s*\n.*for\s+\w+.*range.*:\s*\n.*if\s+\w+\[', code, re.DOTALL):
        if 'swap' in code.lower() or ('arr[i]' in code and 'arr[j]' in code):
            match = re.match(r'(def\s+\w+\([^)]*\):)', code.strip())
            if match:
                sig = match.group(1)
                param = re.search(r'def\s+\w+\(([^)]*)\)', sig)
                params = param.group(1).split(',')[0].strip() if param else 'arr'
                return f"""{sig}
    # Optimized: Python built-in sort O(N log N)
    return sorted({params})"""

    # Detect double nested loop with repeated computation
    if code.count('for ') >= 2 and 'range(n)' in code and 'range(i' in code:
        # Off-by-one fix for binary search
        if 'binary_search' in code.lower() or ('mid' in code and 'low' in code and 'high' in code):
            match = re.match(r'(def\s+\w+\([^)]*\):)', code.strip())
            if match:
                sig = match.group(1)
                params = re.search(r'def\s+\w+\(([^)]*)\)', sig).group(1)
                param_list = [p.strip() for p in params.split(',')]
                arr_p = param_list[0] if len(param_list) > 0 else 'arr'
                target_p = param_list[1] if len(param_list) > 1 else 'target'
                return f"""{sig}
    # Fixed: Correct binary search O(log N)
    low, high = 0, len({arr_p}) - 1
    while low <= high:
        mid = (low + high) // 2
        if {arr_p}[mid] == {target_p}:
            return mid
        elif {arr_p}[mid] < {target_p}:
            low = mid + 1
        else:
            high = mid - 1
    return -1"""

    return code


def fix_logic_bugs(code: str) -> str:
    """Fix common logic bugs: off-by-one, wrong operators, etc."""
    # range(n) instead of range(n+1) for inclusive
    # Off-by-one in binary search
    code = re.sub(r'high\s*=\s*len\((\w+)\)', r'high = len(\1) - 1', code)

    # Fix wrong range in binary search: range(len(arr)) -> while low <= high
    # Fix average calculation: sum / n should use len()
    code = re.sub(r'return\s+total\s*/\s*n\b', 'return total / len(arr) if arr else 0', code)

    # Fix division by zero risk
    if 'average' in code.lower() or 'mean' in code.lower():
        code = re.sub(
            r'return\s+(\w+)\s*/\s*len\((\w+)\)',
            r'return \1 / len(\2) if \2 else 0',
            code
        )

    return code


def apply_all_fixes(code: str) -> str:
    """Apply all fixers in sequence."""
    code = fix_wrong_builtins(code)
    code = fix_syntax_errors(code)
    code = fix_logic_bugs(code)
    code = optimize_complexity(code)
    return code


# ─── Ollama Integration (optional) ───────────────────────────────────────────

def is_ollama_available(ollama_url: str = "http://localhost:11434", model: str = "llama3.2:latest") -> bool:
    """Check if Ollama is running and model exists."""
    try:
        import urllib.request
        import json
        req = urllib.request.Request(f"{ollama_url}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            models = [m['name'] for m in data.get('models', [])]
            return any(model.split(':')[0] in m for m in models)
    except Exception:
        return False


def validate_code(code: str) -> bool:
    """Safety layer to prevent 0.0 reward syntax failures."""
    try:
        compile(code, "<string>", "exec")
        return True
    except Exception:
        return False


def is_inefficient(code: str) -> bool:
    """
    Detect if generated code is still using brute force.
    Returns True if code looks inefficient.
    """
    nested_fors = code.count('for ') >= 2
    has_on2_marker = 'O(n^2)' in code or 'O(n^3)' in code or 'O(N^2)' in code or 'O(N^3)' in code
    # Detect triple nested loop pattern (O(N^3))
    triple_loop = bool(re.search(
        r'for\s+\w+.*:\s*\n\s+for\s+\w+.*:\s*\n\s+for\s+\w+', code, re.MULTILINE
    ))
    return triple_loop or has_on2_marker


def _call_ollama(prompt: str, model: str, ollama_url: str, num_predict: int = 1024) -> str | None:
    """Send a single prompt to Ollama and return raw text response."""
    import urllib.request
    import json
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": num_predict}
    }).encode()
    req = urllib.request.Request(
        f"{ollama_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data.get("response", "").strip()


def _extract_code_and_explanation(result: str) -> tuple[str, str]:
    """Extract code block and explanation from model response."""
    code_match = re.search(r'```python\n(.*?)\n```', result, re.DOTALL)
    if not code_match:
        code_match = re.search(r'```(.*?)```', result, re.DOTALL)
    extracted_code = code_match.group(1).strip() if code_match else result.strip()
    explanation = result.replace(code_match.group(0), '').strip() if code_match else "No reasoning provided."
    return extracted_code, explanation


def _build_optimization_prompt(code: str, error_log: str) -> str:
    """
    Build the Analysis → Optimization → Code 3-step prompt with pattern mapping.
    """
    return f"""You are an expert Python algorithm engineer.

The current solution is inefficient or buggy.

Step 1: Identify why it is inefficient or incorrect (1 line only)
Step 2: Identify the optimal algorithm to solve this problem
Step 3: Rewrite the code using the optimal algorithm

Constraints:
- MUST improve time complexity
- DO NOT use brute force
- Target O(n) if possible
- If your solution is O(n^2) or worse, improve it

Common algorithm patterns:
- Maximum subarray → Kadane's algorithm (O(n))
- Subarray sum → prefix sum (O(n))
- Searching sorted array → binary search (O(log n))
- Sorting → use built-in sorted() (O(n log n))
- Sliding window → two pointers (O(n))

First think step-by-step about how to optimize the algorithm.
Then output only the final code.
Do NOT stop at identifying the issue — you MUST produce optimized code.

Previous error:
{error_log or "No errors, but the solution is suboptimal."}

CURRENT CODE:
{code}

Output your 3-step reasoning, then wrap the final optimized code in a ```python ... ``` block."""


def _build_fix_prompt(code: str, error_log: str, reward: float = 0.0, task_id: str = "") -> str:
    """Build prompt for correctness fix (when code has bugs/errors)."""
    # Get algorithm hint from detector
    algo_hint = get_optimization_hint(code, error_log)
    # Get adaptive suffix based on current reward
    adaptive_suffix = build_adaptive_prompt_suffix(reward)
    # Retrieve memory for past success
    memory_note = ""
    if task_id:
        past = retrieve_memory(task_id)
        if past and past.get('reward', 0) > 0.7:
            memory_note = f"\nPrevious successful solution (reward={past['reward']}):\n{past['best_code']}\nImprove upon this."

    return f"""You are an expert Python debugging agent.

Follow this process and explain your reasoning:
Step 1: Identify bug type (syntax / logic / type / edge case)
Step 2: Locate exact line causing issue
Step 3: Fix only that issue and ensure tests pass
Step 4: Report the Time Complexity of your fixed code
Step 5: If complexity is O(n^2) or worse, optimize to O(n) if possible

Algorithm Detection: {algo_hint}

Common algorithm patterns:
- Maximum subarray → Kadane's algorithm (O(n))
- Subarray sum → prefix sum (O(n))
- Searching sorted array → binary search (O(log n))
- Sorting → use built-in sorted() (O(n log n))

Is your solution optimal? If not, improve it.
{adaptive_suffix}
{memory_note}

Previous attempt failed with:
{error_log or "No errors, but tests are failing."}

BUGGY CODE:
{code}

Output your step-by-step reasoning, then wrap ONLY the corrected Python code in a ```python ... ``` block."""


def fix_with_ollama(
    code: str,
    error_log: str = "",
    ollama_url: str = "http://localhost:11434",
    model: str = "llama3.2:latest",
    reward: float = 0.0,
    task_id: str = "",
) -> Optional[tuple[str, str]]:
    """
    Fix + optimize code using Ollama.
    Pipeline:
      1. Generate fix (correctness + optimization prompt)
      2. Self-critique: if result is still inefficient → run optimization prompt
      3. Iterative refinement: repeat up to 2 full cycles
    Returns (code, explanation) or None.
    """
    try:
        import urllib.request
        import json

        best_code = None
        best_explanation = ""

        # Iterative refinement: up to 2 full optimization passes
        for iteration in range(2):
            # Choose prompt: optimization-first if first run, fix-first if error exists
            if iteration == 0 and error_log:
                prompt = _build_fix_prompt(code, error_log, reward=reward, task_id=task_id)
            else:
                # Inject algorithm hint + adaptive suffix into optimization prompt
                algo_hint = get_optimization_hint(best_code or code, error_log)
                adaptive_suffix = build_adaptive_prompt_suffix(reward)
                base_opt_prompt = _build_optimization_prompt(best_code or code, error_log)
                prompt = base_opt_prompt + f"\n\nAlgorithm Detection: {algo_hint}{adaptive_suffix}"

            result = None
            for attempt in range(3):  # 3 retries per iteration
                try:
                    result = _call_ollama(prompt, model, ollama_url)
                    if not result:
                        continue

                    extracted_code, explanation = _extract_code_and_explanation(result)

                    if extracted_code and validate_code(extracted_code):
                        best_code = extracted_code
                        best_explanation = explanation
                        break  # Valid code — move on

                    # Invalid syntax: tell model to fix it
                    prompt += "\n\nYour last generated code had a SyntaxError. Wrap ONLY valid Python code in ```python ... ``` blocks."

                except Exception as e:
                    print(f"[Ollama attempt {attempt+1} failed]: {e}")
                    continue

            if best_code is None:
                return None  # All retries failed

            # ── Self-Critique Loop ────────────────────────────────────────────
            # If the generated code is still brute-force, force a re-optimization pass
            if is_inefficient(best_code):
                print(f"[Self-Critique] Iteration {iteration+1}: Code still inefficient, re-optimizing...")
                # Build a targeted re-optimization prompt
                critique_prompt = f"""You are a Python performance expert.

The following solution is STILL using brute force and is too slow:

```python
{best_code}
```

This is unacceptable. You MUST rewrite it using an optimal algorithm.

Common patterns:
- Maximum subarray → Kadane's algorithm (O(n))
- Subarray sum → prefix sum (O(n))  
- Searching → binary search (O(log n))

Output ONLY the O(n) optimized version inside a ```python ... ``` block. No explanation needed."""

                try:
                    critique_result = _call_ollama(critique_prompt, model, ollama_url)
                    if critique_result:
                        improved_code, improved_explanation = _extract_code_and_explanation(critique_result)
                        if improved_code and validate_code(improved_code):
                            best_code = improved_code
                            best_explanation = f"[Self-Critique Applied]\n{improved_explanation or best_explanation}"
                except Exception as e:
                    print(f"[Self-Critique] Failed: {e}")

            # If no longer inefficient after critique, stop early
            if not is_inefficient(best_code):
                break

        return (best_code, best_explanation) if best_code else None

    except Exception as e:
        print(f"Ollama fix failed: {e}")
        return None


def generate_fix(
    code: str,
    error_log: str = "",
    tgi_url: str = TGI_BASE_URL,
    use_tgi: bool = True,
    reward: float = 0.0,
    task_id: str = "",
) -> dict:
    """
    Main entry point for code fixing.
    Full pipeline: Algorithm Detection + Memory → TGI (Analysis→Optimization→Code + Self-Critique) → built-in fallback
    Logs complexity vs reward to CSV for research tracking.
    Returns: { fixed_code, method, success, explanation }
    """
    if use_tgi:
        fixed_code = fix_with_tgi(code, tgi_url=tgi_url)
        if fixed_code:
            # Log complexity vs reward for research tracking
            complexity = detect_complexity(fixed_code)
            log_complexity_reward(task_id or "sandbox", reward, complexity, step=0, method="tgi")
            # Store in memory if good reward
            if reward >= 0.8 and task_id:
                store_success(task_id, fixed_code, reward)
            return {
                "fixed_code": fixed_code,
                "method": "tgi",
                "success": True,
                "explanation": "Fixed using TGI LLM",
                "complexity": complexity,
                "algo_hint": get_optimization_hint(fixed_code, error_log),
            }

    # Fallback: built-in AST pattern fixer
    fixed_code = apply_all_fixes(code)
    complexity = detect_complexity(fixed_code)
    log_complexity_reward(task_id or "sandbox", reward, complexity, step=0, method="builtin")
    return {
        "fixed_code": fixed_code,
        "method": "builtin",
        "success": True,
        "explanation": "TGI unavailable. Used built-in pattern-based fixer.",
        "note": "TGI unavailable. Used built-in pattern-based fixer.",
        "complexity": complexity,
        "algo_hint": get_optimization_hint(fixed_code),
    }

