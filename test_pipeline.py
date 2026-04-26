#!/usr/bin/env python3
"""
Quick debug test for CodeArena execution pipeline.
Tests reset and step endpoints to ensure they work before RL training.
"""

import requests
import time

def test_reset():
    """Test the reset endpoint"""
    print("🔄 Testing /reset endpoint...")
    try:
        response = requests.post("http://localhost:7860/reset", json={"task_id": "easy-1"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("✅ Reset successful!")
        print(f"   Task: {data.get('task_id', 'unknown')}")
        print(f"   Buggy code length: {len(data.get('buggy_code', ''))}")
        return True
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False

def test_step():
    """Test the step endpoint with a simple fix"""
    print("\n🚀 Testing /step endpoint...")

    # Simple fix attempt - just try to make it compile
    simple_fix = """
def add_numbers(a, b):
    return a + b
"""

    try:
        response = requests.post("http://localhost:7860/step", json={"proposed_fix": simple_fix}, timeout=15)
        response.raise_for_status()
        data = response.json()

        reward = data.get('reward', 0)
        done = data.get('done', False)
        info = data.get('info', {})

        print("✅ Step successful!")
        print(".3f")
        print(f"   Done: {done}")
        print(f"   Test results: {info.get('test_results', 'unknown')}")

        reward_comps = info.get('reward_components', {})
        print("   Reward breakdown:")
        for k, v in reward_comps.items():
            print(".3f")
        return reward > 0.01  # Better than minimum

    except Exception as e:
        print(f"❌ Step failed: {e}")
        return False

def main():
    print("🧪 CodeArena Execution Pipeline Test")
    print("=" * 50)

    # Check if server is running
    try:
        health = requests.get("http://localhost:7860/health", timeout=5)
        print("✅ Server is running!")
    except:
        print("❌ Server not running on localhost:7860")
        print("   Start with: python -m uvicorn server.app:app --port 7860")
        return

    success = True
    success &= test_reset()
    time.sleep(1)  # Brief pause
    success &= test_step()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Execution pipeline is working.")
        print("   Ready for RL training.")
    else:
        print("⚠️  Some tests failed. Check debug output above.")
        print("   Fix issues before running RL training.")

if __name__ == "__main__":
    main()