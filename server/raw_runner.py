import subprocess
import time
import os
import tempfile
import sys
from pydantic import BaseModel
from typing import Optional

class RawRunResult(BaseModel):
    stdout: str
    stderr: str
    execution_time: float
    time_complexity_hint: str

def analyze_complexity_hint_fallback(code: str, exec_time: float) -> str:
    """Fallback rough hint about time complexity based on loops and execution time."""
    loops = code.count("for ") + code.count("while ")
    nested_loops = code.count("for") + code.count("while") if "    for" in code or "    while" in code else 0
    
    if "def " not in code:
        return "N/A (No function defined)"
    
    hint = "O(1) or O(N)"
    if nested_loops >= 2:
        hint = "O(N^2) or O(N^3) detected"
    elif loops >= 1:
        hint = "O(N) or O(N log N) detected"
        
    if exec_time > 1.0:
        hint += " — High execution time, consider optimizing!"
    elif exec_time < 0.01:
        hint += " — Runs very fast!"
        
    return hint

def analyze_complexity_ai(code: str, exec_time: float) -> str:
    """Use Ollama AI to perform a 5-step complexity analysis on the custom code."""
    try:
        import urllib.request
        import json
        
        prompt = f"""You are an expert Python performance analyst.
        
Analyze the following code using these 5 steps:
1. Identify the core algorithm.
2. Calculate current Time Complexity (Big-O).
3. Calculate current Space Complexity (Big-O).
4. Identify bottlenecks.
5. Propose a more efficient time complexity if possible.

CODE:
{code}

Return a concise 5-line summary (one line per step). No markdown blocks."""

        payload = json.dumps({
            "model": "codearena",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 256}
        }).encode()

        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            result = data.get("response", "").strip()
            if result:
                return f"\n🤖 AI Complexity Analysis:\n{result}"
    except Exception as e:
        print(f"Ollama complexity failed: {e}")
        pass
    
    return analyze_complexity_hint_fallback(code, exec_time)

def run_raw_code(code: str, timeout: float = 5.0) -> RawRunResult:
    """Runs arbitrary Python code and returns output, errors, and time."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
        
    start_time = time.time()
    try:
        process = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        exec_time = time.time() - start_time
        
        stdout = process.stdout
        stderr = process.stderr
        
        hint = analyze_complexity_ai(code, exec_time)
        
        return RawRunResult(
            stdout=stdout,
            stderr=stderr,
            execution_time=exec_time,
            time_complexity_hint=hint
        )
        
    except subprocess.TimeoutExpired as e:
        exec_time = time.time() - start_time
        return RawRunResult(
            stdout=e.stdout.decode('utf-8') if e.stdout else "",
            stderr="Execution timed out! The code took too long to run or entered an infinite loop.",
            execution_time=timeout,
            time_complexity_hint="O(∞) - Infinite loop or very high complexity."
        )
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
