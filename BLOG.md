# CodeArena: Teaching LLMs to Debug Code Through Reinforcement Learning

**An OpenEnv-compatible RL environment for iterative code repair with adaptive difficulty, hybrid grading, and self-improving agent memory.**

[![HuggingFace Space](https://img.shields.io/badge/🤗%20Space-Live%20Demo-brightgreen)](https://huggingface.co/spaces/ceoavinash/codearena-rl)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/havinashpatil/meta/blob/main/train_grpo.ipynb)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/havinashpatil/meta)

---

## The Problem: Why We Built CodeArena

Every major AI coding assistant — GitHub Copilot, Cursor, Devin — is benchmarked on **code generation**. Can it write a function? Can it complete a snippet?

But here's the gap nobody is talking about: **what happens when the code breaks?**

In production, code breaks constantly. A real developer doesn't just generate code — they spend the majority of their time **reading error logs, reasoning about failure, iterating on fixes, and recovering from mistakes.** This iterative debugging loop is the core skill that separates a junior developer from a senior one.

Yet there is no standardized RL environment to train or evaluate an LLM on this capability. HumanEval measures one-shot generation. MBPP measures function completion. Neither measures what happens across multiple repair attempts when the first fix doesn't work.

**CodeArena** is the first open-source, OpenEnv-compatible reinforcement learning environment built specifically for **iterative code repair**.

---

## How CodeArena Works

### The Loop

CodeArena simulates the real-world debugging workflow:

```
1. Agent receives buggy Python code + error log
2. Agent proposes a fix
3. Environment executes the fix in a sandboxed subprocess
4. Environment runs unit tests and scores the fix
5. Agent receives reward + updated error log
6. Repeat up to 5 steps
```

This is fundamentally different from one-shot code generation benchmarks. The agent must:
- **Read and interpret error messages** from previous attempts
- **Track what it has already tried** (repeated fixes are penalized)
- **Decide whether to patch locally or rewrite entirely**
- **Optimize for efficiency**, not just correctness

### Architecture

```
Agent ─── POST /reset ──→ CodeArena Server ──→ Returns buggy_code + error_log
  │                            │
  │                            ├── Task Loader (9 tasks across 5 categories)
  │                            ├── Sandboxed Executor (subprocess + timeout)
  │                            ├── Hybrid Grader (tests + LLM judge)
  │                            ├── Algorithm Detector (complexity analysis)
  │                            └── Agent Memory (self-improving store)
  │
  └── POST /step ────────→ Returns observation, reward, done, info
```

The server is a standard FastAPI application that implements the OpenEnv specification (`/reset`, `/step`, `/state`). The `openenv.yaml` manifest defines the observation space (buggy code, error log, test results, previous attempts) and the action space (proposed fix).

---

## What Makes CodeArena Special (Environment Innovation)

### 1. Hybrid Grader: Tests + LLM-as-Judge

Most coding benchmarks use a single signal: did the tests pass? This creates a fundamental problem — agents learn to produce code that passes weak tests through reward-hacking (e.g., hardcoding expected outputs, or producing syntactically correct but semantically broken code).

CodeArena uses a **Hybrid Grader** with six weighted components:

| Component | Weight | What It Measures |
|---|---|---|
| `compile_score` | 15% | Code compiles without syntax errors |
| `test_pass_ratio` | 35% | Fraction of unit tests passed |
| `efficiency_score` | 30% | Execution time vs. optimal runtime |
| `llm_correctness` | 10% | LLM judge: is the fix logically correct? |
| `llm_security` | 5% | LLM judge: does the fix introduce vulnerabilities? |
| `llm_quality` | 5% | LLM judge: is the code readable and maintainable? |

Additionally, two penalties are applied:
- **Step penalty** (`-0.01 × step_count`): Rewards faster fixes
- **Novelty penalty** (`-0.10`): Penalizes submitting the same fix twice

The LLM judge is called via the OpenAI-compatible API (configurable to GPT-4o-mini, local Ollama, or HuggingFace Inference). When no API key is available, it falls back to neutral scores (0.5), ensuring the environment always runs.

**Why this matters for training:** The heavy 30% weight on efficiency means that an agent that passes all tests with an O(n²) brute-force solution gets a significantly lower reward than one that uses an O(n) algorithm. This forces the model to learn *algorithmic reasoning*, not just syntax repair.

### 2. Adaptive Curriculum (Theme #4: Self-Improvement)

CodeArena doesn't use a fixed task set. It features an **Adaptive Curriculum** that tracks the agent's rolling average reward over recent episodes and automatically adjusts difficulty:

| Condition | Transition |
|---|---|
| avg reward > 0.80 on Easy | → Medium |
| avg reward > 0.75 on Medium | → Hard |
| avg reward < 0.35 on Hard | → Medium (de-escalate) |
| avg reward < 0.35 on Medium | → Easy (de-escalate) |

This is activated by passing `task_id: "auto"` to the `/reset` endpoint.

**Why this matters:** The agent cannot plateau by memorizing solutions to easy tasks. As soon as it masters syntax errors, the environment pushes it to algorithmic logic bugs. If it struggles, it recovers on easier tasks before trying again. This creates a natural *recursive skill amplification* loop — the environment drives the agent's own capability growth.

### 3. Algorithm Detection + Adaptive Prompting

CodeArena includes a built-in **Algorithm Detector** (`server/algorithm_detector.py`) that:

1. **Classifies the problem type** (max subarray, two-sum, binary search, sliding window, etc.) from code patterns
2. **Estimates time complexity** by analyzing loop nesting depth (O(1) → O(n) → O(n²) → O(n³))
3. **Generates targeted optimization hints** (e.g., "Use Kadane's Algorithm O(n): `curr = max(num, curr+num)`")

When the AI fixer generates a repair, the algorithm detector provides **adaptive prompt suffixes** based on the current reward level:
- Low reward (< 0.4): "Focus on correctness. Fix syntax errors first."
- Medium reward (0.4–0.7): "Fix edge cases and logic bugs."
- High reward (> 0.7): "Optimize for performance. Use O(n) algorithms."

### 4. Self-Improving Agent Memory

CodeArena includes a persistent **Agent Memory** system (`server/memory.py`) that stores the best solution found for each task. When the agent encounters the same task type again, it can retrieve its previous best solution as a starting point.

This creates a genuine self-improvement loop:
- Episode 1: Agent fixes syntax → reward 0.45
- Episode 5: Agent recalls its best previous fix, optimizes further → reward 0.72
- Episode 10: Agent has accumulated enough memory to skip basic fixes entirely → reward 0.88

The memory is persisted to `agent_memory.json` and survives server restarts.

### 5. Rich Task Diversity

CodeArena ships with **9 tasks across 5 categories**:

| Category | Tasks | What It Tests |
|---|---|---|
| Easy (syntax) | Missing colons, wrong indentation | Basic Python syntax repair |
| Medium (logic) | Off-by-one errors, wrong conditions | Algorithmic reasoning |
| Hard (optimization) | O(n²) → O(n) refactoring | Algorithm design |
| Type Errors | Wrong types, missing conversions | Type system understanding |
| Security Bugs | SQL injection, path traversal | Security awareness |

Each task includes:
- Buggy source code
- Multiple unit tests
- An optimal execution time baseline (for efficiency scoring)

---

## Training Pipeline: TRL GRPO on CodeArena

We trained a coding model using **Hugging Face TRL's GRPO (Group Relative Policy Optimization)** trainer, connecting it directly to the CodeArena environment as a live reward signal.

### How It Works

```python
# The reward function queries CodeArena's /step endpoint
def codearena_reward_func(completions, prompts):
    rewards = []
    for completion in completions:
        proposed_fix = completion[0].get('content', '').strip()
        res = httpx.post("http://localhost:7860/step",
                         json={"proposed_fix": proposed_fix})
        reward = res.json().get('reward', 0.0)
        rewards.append(reward)
    return rewards

# GRPO training with CodeArena as the reward environment
trainer = GRPOTrainer(
    model=model,
    reward_funcs=codearena_reward_func,
    args=GRPOConfig(
        output_dir="./codearena-grpo",
        learning_rate=1e-5,
        max_steps=50,
        per_device_train_batch_size=2,
    ),
    train_dataset=dataset,
)
trainer.train()
```

The key insight is that **the reward is not static** — it comes from actually executing the agent's proposed code against real unit tests in a sandboxed environment, then grading it with the hybrid scorer. This is true environment-in-the-loop RL, not reward modeling on a frozen dataset.

### Training Results

We trained `Qwen/Qwen2.5-Coder-1.5B` on the `m-a-p/Code-Feedback` dataset with CodeArena as the reward environment.

![Fig 1: Reward Curve](results/reward_curve.png)
*Fig 1: Episode reward over training steps. The rolling 10-step average shows clear learning and improvement from initial near-zero rewards to consistent 0.65+ rewards.*

![Fig 2: Reward by Task](results/reward_by_task.png)
*Fig 2: Average reward broken down by task category. The agent learned to handle syntax and type errors reliably, while algorithmic optimization tasks remain challenging — exactly the behavior we'd expect from a curriculum that pushes harder problems as the agent improves.*

![Fig 3: Task Performance Matrix](results/task_performance_matrix.png)
*Fig 3: Task Difficulty Performance Matrix showing the mean, max, and standard deviation of rewards across difficulty levels.*

![Fig 4: Complexity Distribution](results/complexity_distribution.png)
*Fig 4: Complexity Distribution highlighting the frequency of O(1) vs O(n) solutions generated by the agent.*

![Fig 5: Fixer Method Boxplot](results/method_boxplot.png)
*Fig 5: Reward Distribution by Fixer Method, comparing the performance of the Ollama LLM to the built-in pattern-based fixer.*

![Fig 6: Cumulative Reward](results/cumulative_reward.png)
*Fig 6: Cumulative Reward over time, highlighting the total accumulated reward across multiple episodes.*

![Fig 7: Method Performance Comparison](results/method_performance.png)
*Fig 7: LLM Fixer Method Performance Comparison scatter plot showing the individual performance data points of Ollama vs Builtin methods.*

### Reproducing the Training

The complete training pipeline is available as a Colab notebook:
👉 **[Open in Google Colab](https://colab.research.google.com/github/havinashpatil/meta/blob/main/train_grpo.ipynb)**

The notebook:
1. Installs all dependencies (`trl`, `transformers`, `httpx`)
2. Clones the CodeArena repository
3. Starts the FastAPI backend server
4. Loads `Qwen2.5-Coder-1.5B` with GRPO configuration
5. Trains against the live environment
6. Logs rewards per step

---

## Live Demo: Try It Now

The fully-functional CodeArena environment is deployed on Hugging Face Spaces with a React frontend dashboard:

👉 **[https://huggingface.co/spaces/ceoavinash/codearena-rl](https://huggingface.co/spaces/ceoavinash/codearena-rl)**

### What You Can Do on the Live Demo:

1. **Start an Episode**: Select Easy/Medium/Hard difficulty and load a buggy code task
2. **Manual Fix**: Edit the code yourself and click "Run Step" to see your reward
3. **AI Fix**: Click the ✨ AI FIX button to have the built-in AI repair agent (powered by `Qwen2.5-Coder-3B-Instruct` via HuggingFace Serverless Inference) generate a fix
4. **Agent Mode**: Toggle auto-pilot to watch the agent autonomously fix → test → fix → test in a loop
5. **Sandbox Mode**: Paste your own arbitrary Python code and watch the environment evaluate it

The dashboard shows real-time reward components (compile score, test ratio, efficiency), a terminal log of every step, and a reward chart that updates live.

---

## Technical Deep Dive

### Sandboxed Execution

All agent-submitted code runs in an isolated subprocess with:
- **AST syntax validation** before execution (catches syntax errors without running code)
- **Timeout enforcement** (configurable per task, default 5s)
- **Temporary file execution** (code is written to a temp file, executed, then deleted)
- **Structured output parsing** (test results are communicated via a `|CODEARENA_STATS|` sentinel)

This ensures that malicious or infinite-loop code cannot crash the server.

### AI Code Fixer Pipeline

The built-in AI fixer (`server/ai_fixer.py`, 600+ lines) implements a sophisticated multi-fallback pipeline:

1. **TGI / HuggingFace Serverless API** (Priority 1): Calls `Qwen2.5-Coder-3B-Instruct` for high-quality fixes
2. **Local Ollama** (Priority 2): Falls back to a local LLM if available
3. **AST Pattern-Based Fixer** (Priority 3): 20+ pattern rules for common Python bugs:
   - Missing colons after `def`, `if`, `for`, `while`
   - Missing `return` statements
   - Wrong comparison operators (`=` → `==`)
   - Missing `self` parameter in class methods
   - Incorrect indentation repair
   - And many more

The fixer also includes a **code validator** that catches fixes worse than the original (e.g., introduces new syntax errors), and a **self-critique loop** that re-checks the generated code before returning it.

### Complexity-Reward Tracking

Every fix is logged to `complexity_rewards.csv` with:
- Task ID
- Reward achieved
- Detected time complexity
- Fix method (TGI/Ollama/built-in)

This creates a research dataset that proves our core hypothesis: **agents that produce O(n) solutions consistently receive higher rewards than those producing O(n²) solutions.**

---

## Why CodeArena Matters

**Writing code is a solved problem.** GPT-4, Claude, Gemini — they can all generate working functions from natural language descriptions.

**Debugging code autonomously — reasoning about failure, iterating on fixes, recovering from wrong turns — is not solved.**

Every production coding system will eventually face broken code. There is no other standardized RL environment that trains and benchmarks iterative repair at this level. CodeArena fills that gap with:

- A **hybrid grader** that prevents reward-hacking
- An **adaptive curriculum** for continuous self-improvement
- A **persistent memory** for cross-episode learning
- A **rich task library** spanning syntax, logic, algorithms, types, and security
- Full **OpenEnv compatibility** for plug-and-play evaluation

CodeArena is infrastructure. Plug any model in. Run it. Get a number. Compare it against the baseline. Train on it. Watch it improve.

---

## Links & Resources

| Resource | Link |
|---|---|
| 🤗 Live Demo (HF Space) | [huggingface.co/spaces/ceoavinash/codearena-rl](https://huggingface.co/spaces/ceoavinash/codearena-rl) |
| 📓 Training Notebook (Colab) | [Open in Colab](https://colab.research.google.com/github/havinashpatil/meta/blob/main/train_grpo.ipynb) |
| 💻 Source Code (GitHub) | [github.com/havinashpatil/meta](https://github.com/havinashpatil/meta) |
| 📋 OpenEnv Manifest | [openenv.yaml](https://github.com/havinashpatil/meta/blob/main/openenv.yaml) |

---

*Built for the OpenEnv Hackathon India 2026 — Theme #4: Self-Improvement*
