#!/usr/bin/env python3
"""
Improved CodeArena RL Agent with better prompting and debugging strategy.
"""

import os
import requests
import time
from typing import Dict, List, Tuple

class CodeArenaAgent:
    def __init__(self, backend: str = "ollama", model: str = "llama3.2:latest"):
        self.backend = backend
        self.model = model
        self.api_base = "http://localhost:11434"
        self.api_key = None  # Ollama doesn't need API key

    def generate_fix(self, buggy_code: str, error_log: str, test_results: str,
                    previous_attempts: List[str], step_count: int) -> str:
        """Generate a fix using improved prompting strategy"""

        # Build context from previous failures
        context = ""
        if previous_attempts:
            context += f"\nPrevious attempts that failed:\n"
            for i, attempt in enumerate(previous_attempts[-2:], 1):  # Last 2 attempts
                context += f"Attempt {len(previous_attempts)-len(previous_attempts[-2:])+i}: {attempt[:100]}...\n"

        # Step-aware prompt
        step_instructions = {
            1: "Focus on fixing syntax errors and basic compilation issues first.",
            2: "Now address logic errors and test failures from the previous attempt.",
            3: "Optimize the solution and ensure all edge cases are handled.",
            4: "Final attempt: ensure the solution is robust and handles all test cases.",
            5: "Last chance: fix any remaining issues with a completely different approach."
        }

        prompt = f"""You are an expert Python debugger. Fix the buggy code below.

BUGGY CODE:
{buggy_code}

CURRENT ERRORS:
{error_log}

TEST RESULTS:
{test_results}

STEP {step_count} INSTRUCTIONS:
{step_instructions.get(step_count, "Fix all remaining issues.")}

{context}

REQUIREMENTS:
1. The code must compile without syntax errors
2. All tests must pass
3. Fix the ROOT CAUSE, not just symptoms
4. Do NOT repeat previous failed approaches
5. Ensure proper Python syntax and indentation
6. Return ONLY the corrected code, no explanations

Output the complete corrected Python code:"""

        if not self.api_key and self.backend == "openai":
            # Fallback for OpenAI without key
            return self._fallback_fix(buggy_code, step_count)

        try:
            if self.backend == "ollama":
                # Use Ollama API
                import requests
                response = requests.post(
                    f"{self.api_base}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1000
                        }
                    },
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                fix = result.get("response", "").strip()
            else:
                # Use OpenAI API
                import openai
                client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.3
                )
                fix = response.choices[0].message.content.strip()

            # Clean up common markdown artifacts
            if fix.startswith("```python"):
                fix = fix[9:]
            if fix.startswith("```"):
                fix = fix[3:]
            if fix.endswith("```"):
                fix = fix[:-3]
            return fix.strip()

        except Exception as e:
            print(f"API Error: {e}")
            return self._fallback_fix(buggy_code, step_count)

    def _fallback_fix(self, buggy_code: str, step_count: int) -> str:
        """Simple fallback fix for when API is unavailable"""
        print(f"[DEBUG] Fallback input code ({len(buggy_code)} chars): {repr(buggy_code[:100])}")
        
        # Try to fix common syntax errors in the buggy code
        fixed_code = buggy_code
        
        # Fix 1: Add missing colons after function definitions
        lines = fixed_code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def ') and not stripped.endswith(':'):
                lines[i] = line + ':'
                print(f"[DEBUG] Added colon to line {i+1}")
        
        fixed_code = '\n'.join(lines)
        
        # Fix 2: Replace length() with len()
        if 'length(' in fixed_code:
            fixed_code = fixed_code.replace('length(', 'len(')
            print("[DEBUG] Replaced length() with len()")
        
        print(f"[DEBUG] Fallback output code ({len(fixed_code)} chars): {repr(fixed_code[:100])}")
        return fixed_code

def run_episode(task_id: str = "easy-1", max_steps: int = 5) -> Dict:
    """Run a single episode with improved agent"""
    agent = CodeArenaAgent()

    print(f"\n🎯 Starting episode: {task_id}")

    # Reset
    try:
        response = requests.post("http://localhost:7860/reset", json={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        obs = response.json()
        print(f"✅ Reset successful - task: {obs.get('task_id')}")
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return {"success": False, "error": str(e)}

    rewards = []
    previous_attempts = []
    done = False
    step_count = 0

    while not done and step_count < max_steps:
        step_count += 1

        # Generate fix
        fix = agent.generate_fix(
            buggy_code=obs.get('buggy_code', ''),
            error_log=obs.get('error_log', ''),
            test_results=obs.get('test_results', ''),
            previous_attempts=previous_attempts,
            step_count=step_count
        )

        print(f"\n🔧 Step {step_count}: Generated fix ({len(fix)} chars)")

        # Step
        try:
            response = requests.post("http://localhost:7860/step",
                                   json={"proposed_fix": fix},
                                   timeout=20)
            response.raise_for_status()
            result = response.json()

            reward = result.get('reward', 0)
            done = result.get('done', False)
            info = result.get('info', {})

            rewards.append(reward)
            previous_attempts.append(fix)

            print(".3f")
            print(f"   Tests: {info.get('test_results', 'unknown')}")
            print(f"   Done: {done}")

            if reward > 0.5:
                print("🎉 Good reward! Continuing...")
            elif reward < 0.1:
                print("⚠️  Low reward - check debug logs")

            obs = result.get('observation', {})

        except Exception as e:
            print(f"❌ Step failed: {e}")
            break

    # Summary
    final_reward = rewards[-1] if rewards else 0
    success = final_reward > 0.5

    print(f"\n🏁 Episode complete!")
    print(f"   Steps: {step_count}")
    print(".3f")
    print(f"   Success: {success}")

    return {
        "success": success,
        "steps": step_count,
        "final_reward": final_reward,
        "rewards": rewards
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Improved CodeArena RL Agent")
    parser.add_argument("--task", default="easy-1", help="Task ID to run")
    parser.add_argument("--episodes", type=int, default=1, help="Number of episodes")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai", "hf"], help="Backend to use")
    parser.add_argument("--model", default="llama3.2:latest", help="Model name")

    args = parser.parse_args()

    print("🤖 Improved CodeArena Agent")
    print("=" * 50)
    print(f"Task: {args.task}")
    print(f"Episodes: {args.episodes}")
    print(f"Backend: {args.backend}")
    print(f"Model: {args.model}")

    results = []
    for i in range(args.episodes):
        print(f"\n📊 Episode {i+1}/{args.episodes}")
        result = run_episode(args.task)
        results.append(result)

        # Log to CSV
        import csv
        with open("rewards_log.csv", "a", newline="") as f:
            writer = csv.writer(f)
            if os.path.getsize("rewards_log.csv") == 0:  # Empty file
                writer.writerow(["timestamp", "task_id", "step", "reward", "compile_score", "test_ratio", "efficiency_score"])
            # Note: We don't have detailed component breakdown here, so we'll use placeholders
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                args.task,
                result["steps"],
                result["final_reward"],
                0.0, 0.0, 0.0  # Placeholder values
            ])

    # Summary
    successes = sum(1 for r in results if r["success"])
    avg_reward = sum(r["final_reward"] for r in results) / len(results)

    print(f"\n📈 Summary:")
    print(f"   Success rate: {successes}/{len(results)} ({successes/len(results)*100:.1f}%)")
    print(".3f")
    if successes > 0:
        print("🎉 Some episodes succeeded! Check rewards_log.csv and run plot_rewards.py")
    else:
        print("⚠️  All episodes failed. Check debug output and fix issues.")

if __name__ == "__main__":
    main()