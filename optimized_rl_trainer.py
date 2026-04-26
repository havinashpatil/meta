#!/usr/bin/env python3
"""
Optimized RL Trainer for CodeArena with speed and efficiency improvements.
"""

import asyncio
import aiohttp
import time
import json
import random
from typing import List, Dict, Tuple
from collections import deque
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading

class OptimizedCodeArenaRLTrainer:
    def __init__(self, model_name: str = "llama3.2:latest", memory_size: int = 2000):
        self.model_name = model_name
        self.api_base = "http://localhost:11434"

        # Optimized memory management
        self.memory = deque(maxlen=memory_size)
        self.trajectories = []
        self.successful_trajectories = []

        # Performance optimizations
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.session = None  # For async HTTP
        self.response_cache = {}
        self.prompt_cache = {}

        # RL parameters (optimized)
        self.learning_rate = 0.001
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.05  # Lower minimum for more exploitation
        self.epsilon_decay = 0.997  # Slower decay
        self.batch_size = 64  # Larger batches

        # Performance tracking
        self.start_time = time.time()
        self.episode_times = []
        self.api_call_times = []

        # Adaptive difficulty
        self.current_difficulty = "easy"
        self.task_performance = {"easy": [], "medium": [], "hard": []}

    async def init_session(self):
        """Initialize async HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Close async session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def generate_fix_optimized(self, prompt: str) -> str:
        """Optimized fix generation with caching and async"""
        # Check cache first
        cache_key = hash(prompt)
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]

        start_time = time.time()

        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": max(0.1, self.epsilon),
                    "num_predict": 600,  # Shorter for speed
                    "top_p": 0.9,
                    "num_thread": 4  # Use multiple threads
                }
            }

            async with self.session.post(f"{self.api_base}/api/generate",
                                       json=payload, timeout=15) as response:
                result = await response.json()
                fix = result.get("response", "").strip()

                # Clean response
                if fix.startswith("```python"):
                    fix = fix[9:]
                if fix.startswith("```"):
                    fix = fix[3:]
                if fix.endswith("```"):
                    fix = fix[:-3]
                fix = fix.strip()

                # Cache successful responses
                if fix and len(fix) > 10:
                    self.response_cache[cache_key] = fix

                api_time = time.time() - start_time
                self.api_call_times.append(api_time)

                return fix

        except Exception as e:
            print(f"API Error: {e}")
            return "def placeholder():\n    pass"

    def get_optimized_prompt(self, buggy_code: str, error_log: str,
                           test_results: str, step_count: int,
                           previous_attempts: List[str]) -> str:
        """Generate optimized prompt with caching"""

        # Create cache key
        state_key = f"{hash(buggy_code)}|{hash(error_log)}|{hash(test_results)}|{step_count}"
        if state_key in self.prompt_cache:
            return self.prompt_cache[state_key]

        # Optimized prompt template
        prompt = f"""Fix Python code - Step {step_count}:

CODE:
{buggy_code}

ERRORS:
{error_log}

TESTS:
{test_results}

Requirements: Compile, pass tests, fix root cause. Return only code."""

        self.prompt_cache[state_key] = prompt
        return prompt

    async def run_episode_async(self, task_id: str, episode_num: int) -> Dict:
        """Run episode with async optimizations"""
        episode_start = time.time()

        try:
            # Async reset
            async with self.session.post("http://localhost:7860/reset",
                                       json={"task_id": task_id}, timeout=10) as response:
                obs = await response.json()

        except Exception as e:
            print(f"Episode {episode_num} reset failed: {e}")
            return {"success": False, "reward": 0, "steps": 0, "time": time.time() - episode_start}

        rewards = []
        previous_attempts = []
        done = False
        step_count = 0

        while not done and step_count < 5:
            step_count += 1

            # Generate optimized prompt
            prompt = self.get_optimized_prompt(
                obs.get('buggy_code', ''),
                obs.get('error_log', ''),
                obs.get('test_results', ''),
                step_count,
                previous_attempts
            )

            # Async fix generation
            fix = await self.generate_fix_optimized(prompt)

            try:
                # Async step execution
                async with self.session.post("http://localhost:7860/step",
                                           json={"proposed_fix": fix}, timeout=20) as response:
                    result = await response.json()

                    reward = result.get('reward', 0)
                    done = result.get('done', False)
                    obs = result.get('observation', {})

                    rewards.append(reward)
                    previous_attempts.append(fix)

            except Exception as e:
                print(f"Episode {episode_num} step {step_count} failed: {e}")
                break

        episode_time = time.time() - episode_start
        self.episode_times.append(episode_time)

        final_reward = rewards[-1] if rewards else 0
        success = final_reward > 0.5

        return {
            "episode": episode_num,
            "task_id": task_id,
            "success": success,
            "reward": final_reward,
            "steps": step_count,
            "time": episode_time
        }

    async def train_async(self, episodes: int = 50):
        """Async training loop for maximum speed"""
        await self.init_session()

        print("🚀 Starting Optimized Async RL Training")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Episodes: {episodes}")
        print(f"Async: Enabled")
        print(f"Workers: 4 threads")

        results = []
        batch_size = 5  # Run 5 episodes concurrently

        for batch_start in range(0, episodes, batch_size):
            batch_end = min(batch_start + batch_size, episodes)
            batch_tasks = []

            # Create batch of concurrent episodes
            for i in range(batch_start, batch_end):
                task_id = f"{self.current_difficulty}-{random.randint(1, 3)}"
                task = self.run_episode_async(task_id, i + 1)
                batch_tasks.append(task)

            # Execute batch concurrently
            batch_start_time = time.time()
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            batch_time = time.time() - batch_start_time

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"Batch error: {result}")
                    continue

                results.append(result)

                # Update difficulty if needed
                if result["success"] and result["reward"] > 0.7:
                    self.task_performance[self.current_difficulty].append(result["reward"])

                # Progress tracking
                if len(results) % 10 == 0:
                    recent = results[-10:]
                    success_rate = sum(1 for r in recent if r["success"]) / len(recent)
                    avg_reward = sum(r["reward"] for r in recent) / len(recent)
                    avg_time = sum(r["time"] for r in recent) / len(recent)

                    print(f"Ep {len(results):3d} | Success: {success_rate:.1%} | Reward: {avg_reward:.3f} | Time: {avg_time:.2f}s")
            print(f"📦 Batch {batch_start//batch_size + 1} completed in {batch_time:.1f}s")

        await self.close_session()
        return results

    def print_performance_stats(self, results: List[Dict]):
        """Print detailed performance statistics"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE STATISTICS")
        print("=" * 60)

        total_time = time.time() - self.start_time
        total_episodes = len(results)
        successful = sum(1 for r in results if r["success"])

        print(f"⏱️  Total time: {total_time:.1f}s")
        print(f"🎯 Success rate: {successful}/{total_episodes} ({successful/total_episodes:.1%})")
        print(f"💰 Average reward: {sum(r['reward'] for r in results)/len(results):.3f}")
        if self.episode_times:
            print(f"⚡ Average episode time: {sum(self.episode_times)/len(self.episode_times):.3f}s")
            print(f"🐌 Slowest episode: {max(self.episode_times):.3f}s")
            print(f"🚀 Fastest episode: {min(self.episode_times):.3f}s")
        if self.api_call_times:
            print(f"🌐 Average API call: {sum(self.api_call_times)/len(self.api_call_times):.3f}s")
            print(f"📡 Slowest API call: {max(self.api_call_times):.3f}s")
            print(f"💨 Fastest API call: {min(self.api_call_times):.3f}s")
        print(f"💾 Memory usage: {len(self.memory)} experiences")
        print(f"🧠 Cache hits: {len(self.response_cache)} responses cached")
        print(f"📝 Prompts cached: {len(self.prompt_cache)} states")

        # Success rate over time
        print(f"\n📈 Learning Progress:")
        for i in range(0, len(results), 10):
            batch = results[i:i+10]
            if batch:
                success_rate = sum(1 for r in batch if r["success"]) / len(batch)
                avg_reward = sum(r["reward"] for r in batch) / len(batch)
                print(f"Ep {i+1:2d}-{min(i+10, len(results)):2d}: Success {success_rate:.1%} | Reward {avg_reward:.3f}")
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Optimized Async RL Training")
    parser.add_argument("--episodes", type=int, default=50, help="Training episodes")
    parser.add_argument("--model", default="llama3.2:latest", help="Ollama model")
    parser.add_argument("--use_async", action="store_true", default=True, help="Use async training")

    args = parser.parse_args()

    print("⚡ Optimized CodeArena RL Trainer")
    print("=" * 50)
    print(f"Model: {args.model}")
    print(f"Episodes: {args.episodes}")
    print(f"Async: {args.use_async}")

    trainer = OptimizedCodeArenaRLTrainer(args.model)

    if args.use_async:
        # Run async training
        results = asyncio.run(trainer.train_async(args.episodes))
    else:
        # Fallback to sync (not implemented in this optimized version)
        print("⚠️  Async training required for optimal performance")
        return

    # Save results
    with open("optimized_rl_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    trainer.print_performance_stats(results)

    print("\n💾 Results saved to optimized_rl_results.json")
    print("🎯 Optimization achieved: Async processing + caching + batching")

if __name__ == "__main__":
    main()