"""
CodeArena RL Inference
Rewritten for strict OpenEnv parsing.
"""

import os
import httpx
from openai import OpenAI

def run_task(task_id: str):
    # Retrieve environment variables as instructed
    base_url = os.environ.get("API_BASE_URL")
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("API_KEY")
    model_name = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
    
    # We pass base_url explicitly. If os.environ["API_BASE_URL"] was strictly intended, 
    # it is fine since OpenAI client accepts None for default.
    client = OpenAI(
        base_url=base_url,
        api_key=api_key or "NO_KEY_PROVIDED"
    )
    
    # 1. Print the [START] line
    print(f"[START] task={task_id} env=codearena-rl-benchmark model={model_name}")
    
    # 2. Call POST http://localhost:7860/reset
    try:
        response = httpx.post("http://localhost:7860/reset", json={"task_id": task_id}, timeout=30.0)
        response.raise_for_status()
        obs_json = response.json()
    except Exception as e:
        error_msg = str(e).replace("\n", " ").replace("\r", "")
        print(f"[STEP] step=1 action=reset_failed reward=0.01 done=true error={error_msg}")
        print(f"[END] success=false steps=1 score=0.01 rewards=0.01")
        return
        
    rewards = []
    success = False
    done = False
    step = 0
    
    # 3. For up to 5 steps
    for i in range(5):
        if done:
            break
            
        step += 1
        obs = obs_json.get("observation", {})
        buggy_code = obs.get("buggy_code", "")
        error_log = obs.get("error_log", "")
        test_results = obs.get("test_results", "")
        
        system_prompt = "You are an expert Python code repair agent. Fix the buggy Python code.\nReturn ONLY the fixed raw Python code. No markdown, no explanation."
        user_prompt = f"Fix this buggy Python code:\n\n{buggy_code}\n\nError log:\n{error_log}\n\nTest results so far:\n{test_results}"
        
        error_msg = "null"
        proposed_fix = ""
        
        # 3b/c. Call the LLM
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            proposed_fix = completion.choices[0].message.content
        except Exception as e:
            error_msg = str(e).replace("\n", " ").replace("\r", "")
            # If the LLM call fails, use this fallback fix
            proposed_fix = obs_json.get("observation", {}).get("buggy_code", "pass")
            
        # Cleanup markdown from proposed_fix if LLM ignores instructions
        if proposed_fix:
            proposed_fix = proposed_fix.strip()
            if proposed_fix.startswith("```python"):
                proposed_fix = proposed_fix[9:]
            elif proposed_fix.startswith("```"):
                proposed_fix = proposed_fix[3:]
            if proposed_fix.endswith("```"):
                proposed_fix = proposed_fix[:-3]
            proposed_fix = proposed_fix.strip()

        # 3d. Send proposed_fix to /step
        try:
            step_resp = httpx.post("http://localhost:7860/step", json={"proposed_fix": proposed_fix}, timeout=60.0)
            step_resp.raise_for_status()
            step_data = step_resp.json()
            raw_reward = step_data.get("reward", 0.0)
            done = step_data.get("done", True)
            obs_json = step_data
        except Exception as e:
            raw_reward = 0.01
            done = True
            if error_msg == "null":
                error_msg = str(e).replace("\n", " ").replace("\r", "")

        # 3e. Clamp it
        reward = max(0.001, min(0.999, float(raw_reward)))
        rewards.append(reward)
        
        # 3f. Print [STEP] line immediately
        done_str = "true" if done else "false"
        action_summary = "llm_fix" if error_msg == "null" else "fallback_fix"
        print(f"[STEP] step={step} action={action_summary} reward={reward:.2f} done={done_str} error={error_msg}")
        
    # 4. Print [END]
    success = any(r > 0.5 for r in rewards)
    success_str = "true" if success else "false"
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    score = max(0.001, min(0.999, (sum(rewards) / len(rewards)) if rewards else 0.5))
    print(f"[END] success={success_str} steps={step} score={score:.2f} rewards={rewards_str}")

def main():
    target_task = os.environ.get("CODEARENA_TASK")
    if target_task:
        run_task(target_task)
    else:
        for t in ["easy", "medium", "hard"]:
            run_task(t)

if __name__ == "__main__":
    main()
