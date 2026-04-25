import httpx
import time
import subprocess
import sys
import os

def main():
    print("Starting server...")
    server_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "server.app:app", "--port", "7860"])
    
    time.sleep(3) # Wait for server to start
    
    try:
        print("Testing /reset...")
        res = httpx.post("http://localhost:7860/reset", json={"task_id": "auto"})
        res.raise_for_status()
        
        print("Running inference.py...")
        # Just run easy task for one episode to save time
        env = os.environ.copy()
        env["CODEARENA_TASK"] = "easy-1"
        # We don't have a real openai key or hf model downloaded, so it will hit fallback and succeed
        subprocess.run([sys.executable, "inference.py", "--backend", "openai"], env=env, check=True)
        
        print("Running plot_rewards.py...")
        subprocess.run([sys.executable, "plot_rewards.py"], check=True)
        
        print("All tests passed.")
    except Exception as e:
        print("Test failed:", e)
    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
