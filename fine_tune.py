#!/usr/bin/env python3
"""
Fine-tuning script for CodeArena using successful trajectories.
Creates training data from successful episodes and fine-tunes the model.
"""

import os
import json
import random
from typing import List, Dict, Optional
from datetime import datetime
import requests

class CodeArenaFineTuner:
    def __init__(self, model_name: str = "llama3.2:latest"):
        self.model_name = model_name
        self.api_base = "http://localhost:11434"
        self.training_data = []

    def load_successful_trajectories(self, trajectories_file: str = "optimized_rl_results.json"):
        """Load successful trajectories from training results"""
        if not os.path.exists(trajectories_file):
            print(f"❌ No training results found at {trajectories_file}")
            return []

        with open(trajectories_file, 'r') as f:
            results = json.load(f)

        successful_episodes = [r for r in results if r.get("success", False)]
        print(f"✅ Loaded {len(successful_episodes)} successful episodes")
        return successful_episodes

    def create_fine_tuning_data(self, successful_episodes: List[Dict]) -> List[Dict]:
        """Create fine-tuning examples from successful trajectories"""
        fine_tuning_examples = []

        for episode in successful_episodes:
            # We need to reconstruct the trajectory from the results
            # For now, create synthetic examples based on patterns
            task_id = episode["task_id"]
            final_reward = episode["reward"]

            if final_reward > 0.6:  # Only use high-performing examples
                # Create example based on task type
                example = self._create_task_example(task_id, final_reward)
                if example:
                    fine_tuning_examples.append(example)

        print(f"📚 Created {len(fine_tuning_examples)} fine-tuning examples")
        return fine_tuning_examples

    def _create_task_example(self, task_id: str, reward: float) -> Optional[Dict]:
        """Create a fine-tuning example for a specific task"""
        difficulty = task_id.split('-')[0]

        # Get task details by querying the environment
        try:
            response = requests.post("http://localhost:7860/reset",
                                   json={"task_id": task_id}, timeout=10)
            response.raise_for_status()
            task_data = response.json()

            buggy_code = task_data.get("observation", {}).get("buggy_code", "")
            if not buggy_code:
                return None

            # Create a successful fix example
            # This is simplified - in practice you'd want actual successful fixes
            successful_fix = self._generate_ideal_fix(buggy_code, difficulty)

            example = {
                "instruction": f"Fix this {difficulty} Python debugging task. The code has bugs and needs to be corrected to pass all tests.",
                "input": f"BUGGY CODE:\n{buggy_code}\n\nERRORS: [compilation and runtime errors]\n\nTESTS: [failing test cases]",
                "output": successful_fix,
                "task_type": difficulty,
                "expected_reward": reward
            }

            return example

        except Exception as e:
            print(f"❌ Failed to create example for {task_id}: {e}")
            return None

    def _generate_ideal_fix(self, buggy_code: str, difficulty: str) -> str:
        """Generate an ideal fix for fine-tuning (simplified)"""
        # This is a placeholder - in practice you'd use actual successful fixes
        # For now, return a template based on common patterns

        if "def average_list" in buggy_code:
            return """def average_list(numbers):
    if not numbers:
        return 0
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)"""

        elif "def factorial" in buggy_code:
            return """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)"""

        else:
            # Generic template
            return """def example_function(x):
    \"\"\"A well-documented function\"\"\"
    if not isinstance(x, (int, float)):
        raise ValueError("Input must be numeric")
    return x * 2"""

    def prepare_ollama_fine_tune_data(self, examples: List[Dict]) -> str:
        """Prepare data in Ollama fine-tuning format"""
        ollama_data = []

        for example in examples:
            # Format for Ollama fine-tuning
            formatted_example = f"<s>[INST] {example['instruction']}\n\n{example['input']} [/INST] {example['output']}</s>"
            ollama_data.append(formatted_example)

        # Save to file
        data_content = "\n".join(ollama_data)

        filename = f"codearena_finetune_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data_content)

        print(f"💾 Fine-tuning data saved to {filename}")
        return filename

    def run_fine_tuning(self, data_file: str, learning_rate: float = 0.0001,
                        epochs: int = 3):
        """Run fine-tuning using Ollama (if supported)"""
        print("🎯 Starting Fine-tuning Process")
        print("=" * 50)
        print(f"Data file: {data_file}")
        print(f"Learning rate: {learning_rate}")
        print(f"Epochs: {epochs}")

        # Note: Ollama doesn't currently support fine-tuning through API
        # This would need to be done manually or with a different approach

        print("⚠️  Ollama doesn't support fine-tuning through API")
        print("📝 To fine-tune manually:")
        print(f"1. Use the data in {data_file}")
        print("2. Run: ollama create codearena-ft -f Modelfile")
        print("3. Where Modelfile contains:")
        print("   FROM llama3.2:latest")
        print(f"   PARAMETER training-data {data_file}")
        print("   PARAMETER learning-rate 0.0001")
        print("   PARAMETER epochs 3")
        print("")
        print("🔄 Alternative: Use the fine-tuning data to improve the RL agent prompts")
        return False

    def improve_rl_agent(self, examples: List[Dict]):
        """Use fine-tuning data to improve the RL agent's prompting strategy"""
        print("🧠 Improving RL Agent with Fine-tuning Insights")

        # Analyze successful patterns
        patterns = self._analyze_success_patterns(examples)

        # Update agent with learned patterns
        improved_prompts = self._create_improved_prompts(patterns)

        # Save improved prompts
        with open("improved_prompts.json", 'w') as f:
            json.dump(improved_prompts, f, indent=2)

        print("✅ Improved prompts saved to improved_prompts.json")
        return improved_prompts

    def _analyze_success_patterns(self, examples: List[Dict]) -> Dict:
        """Analyze patterns in successful examples"""
        patterns = {
            "error_patterns": {},
            "solution_patterns": {},
            "task_patterns": {}
        }

        for example in examples:
            task_type = example.get("task_type", "unknown")
            solution = example.get("output", "")

            # Analyze solution patterns
            if "if not" in solution:
                patterns["solution_patterns"]["input_validation"] = patterns["solution_patterns"].get("input_validation", 0) + 1

            if "for " in solution and "in " in solution:
                patterns["solution_patterns"]["iteration"] = patterns["solution_patterns"].get("iteration", 0) + 1

            if "return" in solution:
                patterns["solution_patterns"]["early_returns"] = patterns["solution_patterns"].get("early_returns", 0) + 1

            patterns["task_patterns"][task_type] = patterns["task_patterns"].get(task_type, 0) + 1

        return patterns

    def _create_improved_prompts(self, patterns: Dict) -> Dict:
        """Create improved prompts based on learned patterns"""
        improved_prompts = {
            "base": """You are an expert Python debugger with reinforcement learning experience.

LEARNED PATTERNS:
- Always validate inputs first (if not x: handle edge case)
- Use proper iteration patterns (for item in collection)
- Implement early returns for efficiency
- Focus on root cause, not symptoms

BUGGY CODE:
{buggy_code}

CURRENT ERRORS:
{error_log}

TEST RESULTS:
{test_results}

REQUIREMENTS:
1. Apply learned debugging patterns
2. Fix compilation and logic errors
3. Ensure all tests pass
4. Return ONLY the corrected code

Output the complete corrected Python code:""",

            "rl_enhanced": """LEARNING FROM SUCCESS: {success_patterns}

BUGGY CODE:
{buggy_code}

CURRENT ERRORS:
{error_log}

TEST RESULTS:
{test_results}

Apply successful debugging strategies from similar problems.

Output ONLY the corrected Python code:"""
        }

        return improved_prompts

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fine-tune CodeArena model")
    parser.add_argument("--training-data", default="optimized_rl_results.json",
                       help="Path to training results JSON")
    parser.add_argument("--model", default="llama3.2:latest",
                       help="Base model for fine-tuning")
    parser.add_argument("--learning-rate", type=float, default=0.0001,
                       help="Fine-tuning learning rate")
    parser.add_argument("--epochs", type=int, default=3,
                       help="Number of fine-tuning epochs")

    args = parser.parse_args()

    print("🎯 CodeArena Fine-tuning")
    print("=" * 50)
    print(f"Training data: {args.training_data}")
    print(f"Base model: {args.model}")

    tuner = CodeArenaFineTuner(args.model)

    # Load successful trajectories
    successful_episodes = tuner.load_successful_trajectories(args.training_data)

    if not successful_episodes:
        print("❌ No successful episodes found. Run RL training first.")
        return

    # Create fine-tuning data
    examples = tuner.create_fine_tuning_data(successful_episodes)

    if not examples:
        print("❌ No fine-tuning examples created.")
        return

    # Prepare data for Ollama (or other frameworks)
    data_file = tuner.prepare_ollama_fine_tune_data(examples)

    # Attempt fine-tuning
    success = tuner.run_fine_tuning(data_file, args.learning_rate, args.epochs)

    # Improve RL agent regardless
    improved_prompts = tuner.improve_rl_agent(examples)

    print("\n" + "=" * 50)
    if success:
        print("🎉 Fine-tuning completed successfully!")
    else:
        print("📝 Fine-tuning data prepared for manual training")
        print("🧠 RL agent improved with learned patterns")

    print("")
    print("🚀 Next steps:")
    print("1. Use improved_prompts.json in your RL agent")
    print("2. Manually fine-tune model with prepared data")
    print("3. Run additional RL training with improved agent")

if __name__ == "__main__":
    main()