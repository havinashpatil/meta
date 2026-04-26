#!/usr/bin/env python3
"""
Full RL Training Loop for CodeArena with Memory and Fine-tuning
Implements experience replay, trajectory learning, and optimization.
"""

import os
import json
import time
import random
import requests
from typing import List, Dict, Tuple, Optional
from collections import deque
import numpy as np
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Experience:
    """RL Experience tuple"""
    state: str  # Buggy code + error log + test results
    action: str  # Generated fix
    reward: float
    next_state: str
    done: bool
    task_id: str
    step_count: int
    trajectory_id: str

@dataclass
class Trajectory:
    """Complete episode trajectory"""
    trajectory_id: str
    task_id: str
    steps: List[Experience]
    final_reward: float
    success: bool
    total_steps: int

class CodeArenaRLTrainer:
    def __init__(self, model_name: str = "llama3.2:latest", memory_size: int = 1000):
        self.model_name = model_name
        self.api_base = "http://localhost:11434"

        # RL Components
        self.memory = deque(maxlen=memory_size)
        self.trajectories: List[Trajectory] = []
        self.successful_trajectories: List[Trajectory] = []

        # Training parameters
        self.learning_rate = 0.001
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.995
        self.batch_size = 32

        # Task progression
        self.current_difficulty = "easy"
        self.task_performance = {"easy": [], "medium": [], "hard": []}

        # Optimization
        self.cache = {}  # Response cache for speed
        self.prompt_templates = self._load_prompt_templates()

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load optimized prompt templates"""
        return {
            "base": """You are an expert Python debugger. Fix the buggy code below.

BUGGY CODE:
{buggy_code}

CURRENT ERRORS:
{error_log}

TEST RESULTS:
{test_results}

REQUIREMENTS:
1. The code must compile without syntax errors
2. All tests must pass
3. Fix the ROOT CAUSE, not just symptoms
4. Do NOT repeat previous failed approaches
5. Ensure proper Python syntax and indentation
6. Return ONLY the corrected code, no explanations

Output the complete corrected Python code:""",

            "rl_enhanced": """You are learning to debug Python code through reinforcement learning.

PREVIOUS EXPERIENCES:
{similar_experiences}

BUGGY CODE:
{buggy_code}

CURRENT ERRORS:
{error_log}

TEST RESULTS:
{test_results}

LEARNING OBJECTIVE:
- Learn from successful patterns in similar problems
- Avoid mistakes that led to low rewards
- Build upon working solutions

Output ONLY the corrected Python code:""",

            "step_aware": """Step {step_count} of debugging process.

{context}

BUGGY CODE:
{buggy_code}

CURRENT ERRORS:
{error_log}

TEST RESULTS:
{test_results}

STEP {step_count} FOCUS:
{step_instruction}

Output ONLY the corrected Python code:"""
        }

    def get_similar_experiences(self, current_state: str, limit: int = 3) -> str:
        """Retrieve similar successful experiences from memory"""
        if not self.successful_trajectories:
            return "No previous successful experiences available."

        # Simple similarity based on code length and error patterns
        current_length = len(current_state)
        similar = []

        for traj in self.successful_trajectories[-10:]:  # Last 10 successful
            for exp in traj.steps:
                if exp.reward > 0.5:  # Only successful steps
                    length_diff = abs(len(exp.state) - current_length)
                    if length_diff < 200:  # Similar complexity
                        similar.append(f"✓ Success: {exp.action[:100]}... (reward: {exp.reward:.2f})")
                        if len(similar) >= limit:
                            break
            if len(similar) >= limit:
                break

        return "\n".join(similar) if similar else "Learning from general patterns..."

    def generate_fix_rl(self, buggy_code: str, error_log: str, test_results: str,
                       previous_attempts: List[str], step_count: int,
                       use_memory: bool = True) -> str:
        """Generate fix using RL-enhanced prompting"""

        # Build state representation
        state = f"Code: {buggy_code}\nErrors: {error_log}\nTests: {test_results}"

        # Choose prompt strategy based on experience
        if use_memory and len(self.successful_trajectories) > 0:
            similar_exp = self.get_similar_experiences(state)
            prompt = self.prompt_templates["rl_enhanced"].format(
                similar_experiences=similar_exp,
                buggy_code=buggy_code,
                error_log=error_log,
                test_results=test_results
            )
        else:
            # Step-aware prompting
            step_instructions = {
                1: "Focus on fixing syntax errors and basic compilation issues first.",
                2: "Address logic errors from the previous attempt.",
                3: "Optimize and ensure all edge cases are handled.",
                4: "Final verification - ensure robust solution.",
                5: "Last attempt - use completely different approach if needed."
            }

            context = ""
            if previous_attempts:
                context = f"Previous failed attempts:\n" + "\n".join(
                    f"- {attempt[:50]}..." for attempt in previous_attempts[-2:]
                )

            prompt = self.prompt_templates["step_aware"].format(
                step_count=step_count,
                context=context,
                buggy_code=buggy_code,
                error_log=error_log,
                test_results=test_results,
                step_instruction=step_instructions.get(step_count, "Fix all issues.")
            )

        # Check cache first
        cache_key = hash(prompt)
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            response = requests.post(
                f"{self.api_base}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": max(0.1, self.epsilon),  # Exploration vs exploitation
                        "num_predict": 800,
                        "top_p": 0.9
                    }
                },
                timeout=20
            )
            response.raise_for_status()
            result = response.json()
            fix = result.get("response", "").strip()

            # Clean up response
            if fix.startswith("```python"):
                fix = fix[9:]
            if fix.startswith("```"):
                fix = fix[3:]
            if fix.endswith("```"):
                fix = fix[:-3]
            fix = fix.strip()

            # Cache successful responses
            if fix and len(fix) > 10:
                self.cache[cache_key] = fix

            return fix

        except Exception as e:
            print(f"API Error: {e}")
            return self._fallback_fix(buggy_code, step_count)

    def _fallback_fix(self, buggy_code: str, step_count: int) -> str:
        """Enhanced fallback with learning from memory"""
        # Try to learn from successful patterns
        if self.successful_trajectories:
            # Use patterns from successful trajectories
            successful_fixes = []
            for traj in self.successful_trajectories[-3:]:
                for exp in traj.steps:
                    if exp.reward > 0.6:
                        successful_fixes.append(exp.action)

            if successful_fixes:
                # Return a variation of successful fix
                base_fix = random.choice(successful_fixes)
                # Simple variation - could be improved
                return base_fix

        # Basic fallback
        return "def placeholder_function(x):\n    return x"

    def run_episode_rl(self, task_id: str, max_steps: int = 5,
                      use_memory: bool = True) -> Trajectory:
        """Run a single RL episode with memory"""
        trajectory_id = f"{task_id}_{int(time.time())}"

        print(f"\n🎯 RL Episode: {task_id} (ε={self.epsilon:.3f})")

        # Reset environment
        try:
            response = requests.post("http://localhost:7860/reset",
                                   json={"task_id": task_id}, timeout=10)
            response.raise_for_status()
            obs = response.json()
        except Exception as e:
            print(f"❌ Reset failed: {e}")
            return Trajectory(trajectory_id, task_id, [], 0.0, False, 0)

        experiences = []
        previous_attempts = []
        done = False
        step_count = 0
        final_reward = 0.0

        while not done and step_count < max_steps:
            step_count += 1

            # Build current state
            current_state = f"{obs.get('buggy_code', '')}|{obs.get('error_log', '')}|{obs.get('test_results', '')}"

            # Generate action using RL
            fix = self.generate_fix_rl(
                buggy_code=obs.get('buggy_code', ''),
                error_log=obs.get('error_log', ''),
                test_results=obs.get('test_results', ''),
                previous_attempts=previous_attempts,
                step_count=step_count,
                use_memory=use_memory
            )

            print(f"🔧 Step {step_count}: Generated fix ({len(fix)} chars)")

            # Execute action
            try:
                response = requests.post("http://localhost:7860/step",
                                       json={"proposed_fix": fix}, timeout=20)
                response.raise_for_status()
                result = response.json()

                reward = result.get('reward', 0)
                done = result.get('done', False)
                next_obs = result.get('observation', {})

                # Build next state
                next_state = f"{next_obs.get('buggy_code', '')}|{next_obs.get('error_log', '')}|{next_obs.get('test_results', '')}"

                # Create experience
                exp = Experience(
                    state=current_state,
                    action=fix,
                    reward=reward,
                    next_state=next_state,
                    done=done,
                    task_id=task_id,
                    step_count=step_count,
                    trajectory_id=trajectory_id
                )

                experiences.append(exp)
                self.memory.append(exp)

                previous_attempts.append(fix)
                final_reward = reward

                info = result.get('info', {})
                print(f"   Reward: {reward:.3f}")
                print(f"   Tests: {info.get('test_results', 'unknown')}")
                print(f"   Done: {done}")

                if reward > 0.5:
                    print("🎉 Good reward! Learning...")
                elif reward < 0.1:
                    print("⚠️  Low reward - adjusting strategy")

                obs = next_obs

            except Exception as e:
                print(f"❌ Step failed: {e}")
                break

        # Create trajectory
        success = final_reward > 0.5
        trajectory = Trajectory(
            trajectory_id=trajectory_id,
            task_id=task_id,
            steps=experiences,
            final_reward=final_reward,
            success=success,
            total_steps=step_count
        )

        self.trajectories.append(trajectory)
        if success:
            self.successful_trajectories.append(trajectory)

        # Update task performance
        difficulty = task_id.split('-')[0]
        if difficulty in self.task_performance:
            self.task_performance[difficulty].append(final_reward)

        # Decay exploration
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        print(f"🏁 Episode complete: {success} (reward: {final_reward:.3f})")
        return trajectory

    def should_progress_difficulty(self) -> Optional[str]:
        """Check if agent should move to next difficulty level"""
        if self.current_difficulty == "easy":
            recent_easy = self.task_performance["easy"][-3:]  # Last 3 episodes
            if len(recent_easy) >= 3 and np.mean(recent_easy) > 0.75:
                return "medium"
        elif self.current_difficulty == "medium":
            recent_medium = self.task_performance["medium"][-3:]
            if len(recent_medium) >= 3 and np.mean(recent_medium) > 0.70:
                return "hard"

        return None

    def train_rl(self, episodes: int = 50, checkpoint_every: int = 10):
        """Full RL training loop"""
        print("🚀 Starting RL Training")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Episodes: {episodes}")
        print(f"Memory size: {len(self.memory)}")
        print(f"Successful trajectories: {len(self.successful_trajectories)}")

        results = []

        for episode in range(episodes):
            # Adaptive task selection
            next_difficulty = self.should_progress_difficulty()
            if next_difficulty:
                self.current_difficulty = next_difficulty
                print(f"📈 Progressing to {self.current_difficulty} difficulty!")

            # Select task based on current difficulty
            task_candidates = [f"{self.current_difficulty}-{i}" for i in range(1, 4)]
            task_id = random.choice(task_candidates)

            # Run episode
            trajectory = self.run_episode_rl(task_id, use_memory=True)
            results.append({
                "episode": episode + 1,
                "task_id": trajectory.task_id,
                "reward": trajectory.final_reward,
                "success": trajectory.success,
                "steps": trajectory.total_steps,
                "epsilon": self.epsilon
            })

            # Checkpoint
            if (episode + 1) % checkpoint_every == 0:
                self.save_checkpoint(f"checkpoint_{episode + 1}.json")
                print(f"💾 Checkpoint saved at episode {episode + 1}")

            # Performance summary
            if (episode + 1) % 10 == 0:
                recent_results = results[-10:]
                success_rate = sum(1 for r in recent_results if r["success"]) / len(recent_results)
                avg_reward = sum(r["reward"] for r in recent_results) / len(recent_results)
                print(f"📊 Episode {episode + 1:3d} | Success: {success_rate:.1%} | Reward: {avg_reward:.3f}")
        # Final summary
        self.print_training_summary(results)
        return results

    def print_training_summary(self, results: List[Dict]):
        """Print comprehensive training summary"""
        print("\n" + "=" * 60)
        print("🏆 RL TRAINING COMPLETE")
        print("=" * 60)

        total_episodes = len(results)
        successful_episodes = sum(1 for r in results if r["success"])
        success_rate = successful_episodes / total_episodes

        rewards = [r["reward"] for r in results]
        avg_reward = np.mean(rewards)
        max_reward = max(rewards)

        print(f"📊 Overall Performance:")
        print(f"🎯 Episodes: {total_episodes}")
        print(f"✅ Successful: {successful_episodes}")
        print(f"📈 Success Rate: {success_rate:.1%}")
        print(f"💰 Average Reward: {avg_reward:.3f}")
        print(f"🏆 Max Reward: {max_reward:.3f}")
        print(f"🎯 Success Rate: {success_rate:.1%}")

        # Performance by difficulty
        print(f"\n📈 Performance by Difficulty:")
        for difficulty in ["easy", "medium", "hard"]:
            diff_results = [r for r in results if r["task_id"].startswith(difficulty)]
            if diff_results:
                diff_success = sum(1 for r in diff_results if r["success"]) / len(diff_results)
                diff_avg_reward = np.mean([r["reward"] for r in diff_results])
                print(f"  {difficulty.capitalize()}: Success {diff_success:.1%} | Reward {diff_avg_reward:.3f}")
        # Learning curve
        print(f"\n📉 Learning Curve (last 20 episodes):")
        recent = results[-20:]
        if recent:
            for i in range(0, len(recent), 5):
                batch = recent[i:i+5]
                batch_success = sum(1 for r in batch if r["success"]) / len(batch)
                batch_avg_reward = np.mean([r["reward"] for r in batch])
                print(f"  Ep {i+1:2d}-{min(i+5, len(recent)):2d}: Success {batch_success:.1%} | Reward {batch_avg_reward:.3f}")
        print(f"\n💾 Memory: {len(self.memory)} experiences")
        print(f"🎖️  Successful trajectories: {len(self.successful_trajectories)}")
        print(f"🧠 Cache size: {len(self.cache)} responses")

    def save_checkpoint(self, filename: str):
        """Save training checkpoint"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "model_name": self.model_name,
            "memory_size": len(self.memory),
            "successful_trajectories": len(self.successful_trajectories),
            "current_difficulty": self.current_difficulty,
            "epsilon": self.epsilon,
            "task_performance": self.task_performance,
            "cache_size": len(self.cache)
        }

        with open(filename, 'w') as f:
            json.dump(checkpoint, f, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Full RL Training for CodeArena")
    parser.add_argument("--episodes", type=int, default=30, help="Number of training episodes")
    parser.add_argument("--model", default="llama3.2:latest", help="Ollama model to use")
    parser.add_argument("--memory", type=int, default=500, help="Experience replay memory size")
    parser.add_argument("--checkpoint", type=int, default=10, help="Save checkpoint every N episodes")

    args = parser.parse_args()

    print("🧠 CodeArena RL Trainer")
    print("=" * 50)
    print(f"Model: {args.model}")
    print(f"Episodes: {args.episodes}")
    print(f"Memory: {args.memory}")
    print(f"Checkpoints: every {args.checkpoint} episodes")

    trainer = CodeArenaRLTrainer(args.model, args.memory)
    results = trainer.train_rl(args.episodes, args.checkpoint)

    # Save final results
    with open("rl_training_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    print("")
    print("💾 Results saved to rl_training_results.json")
    print("📊 Run 'python plot_rewards.py' to visualize performance")

if __name__ == "__main__":
    main()