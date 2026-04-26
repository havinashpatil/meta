---
title: CodeArena RL Benchmark
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
pinned: true
---
[![HuggingFace Space](https://img.shields.io/badge/🤗%20Space-Live-brightgreen)](https://huggingface.co/spaces/ceoavinash/codearena-rl)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/havinashpatil/meta/blob/main/train_grpo.ipynb)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](./openenv.yaml)
[![Theme](https://img.shields.io/badge/Theme%20%234-Self--Improvement-purple)]()

# 🚀 CodeArena: The Iterative Code Repair RL Benchmark

GitHub Copilot, Cursor, Devin — every major coding AI is benchmarked on *generation*. Can it write a function? Can it complete a snippet? 

But nobody benchmarks what happens when the code **breaks**. When the agent has to reason about failure, read error logs, iterate on fixes, and recover from its own mistakes.

**CodeArena** measures exactly that. It is the first standardized, open-source Reinforcement Learning environment built specifically for **iterative code repair**. It grades an agent not just on whether the tests pass, but on whether the fix is correct, secure, and algorithmically efficient.

---

## 🎯 Hackathon Theme Alignment: Theme #4 (Self-Improvement)

CodeArena directly tackles **Theme #4: Self-Improvement**. 

Instead of a fixed set of tasks, CodeArena features an **Adaptive Curriculum**. The environment continuously tracks the agent's rolling average reward over the last 10 episodes. If an agent masters easy syntax errors (avg reward > 0.80), the environment automatically escalates the difficulty to algorithmic logic bugs. If the agent struggles, it de-escalates to allow recovery.

The goal is recursive skill amplification: the agent learns to drive its own capability growth without plateauing on memorized, simple solutions.

---

## ✨ Environment Innovation (What makes it special?)

### 1. The Gap Nobody Is Measuring
We have countless environments for generating code (HumanEval, MBPP). CodeArena is the first standardized RL environment for the *debugging loop*. It simulates the real-world workflow: write → test → read error → fix → repeat.

### 2. LLM-as-Judge Hybrid Grader
Most benchmarks ask a binary question: *did the tests pass?* CodeArena uses a rich **Hybrid Grader**. A deterministic test runner checks correctness, while a built-in LLM Judge (powered by TGI/Hugging Face Serverless) scores the fix on security, readability, and algorithmic complexity (O(N) vs O(N²)). This prevents reward-hacking where agents produce syntactically correct but fundamentally broken code just to pass a weak test.

### 3. Complex Shaped Rewards
Rewards are a weighted composite, heavily shaped to encourage professional engineering:
- **Test Pass Ratio (40%)**: Fraction of unit tests passed.
- **LLM Judge Score (30%)**: Correctness + Security + Code Quality.
- **Compile Score (20%)**: Does it run without crashing?
- **Efficiency Score (10%)**: Speed vs optimal runtime.
- **Step Penalty (-0.02/step)**: Rewards faster fixes over meandering trial-and-error.

---

## 📈 Evidence of Training & Rewards

We successfully trained a model using **TRL GRPO** (Group Relative Policy Optimization) on the CodeArena environment. 

Below is the observable evidence of the agent's training progress. The agent started with a low success rate on algorithmic bugs, but as the GRPO training progressed, it learned to systematically read the `error_log` observation and output correct code, resulting in a climbing reward curve.

![Reward Curve](results/reward_curve.png)
*Episode reward over training steps. The rolling 10-step average shows clear learning and improvement.*

![Reward by Task](results/reward_by_task.png)
*Average reward broken down by task category. The agent performs well on syntax and type errors, while Medium/Hard algorithmic tasks remain challenging but improving.*

### 🏃‍♂️ Run the Training Script
We have provided our complete TRL GRPO training pipeline in a Colab notebook so judges can re-run and verify the training process end-to-end:
👉 **[Open Training Script in Google Colab](https://colab.research.google.com/github/havinashpatil/meta/blob/main/train_grpo.ipynb)**

---

## 💻 Try the Live Environment (Hugging Face Space)

We have deployed the fully-functional CodeArena environment, complete with a React frontend dashboard that visualizes the RL process in real-time.

👉 **[Live Demo: CodeArena on Hugging Face Spaces](https://huggingface.co/spaces/ceoavinash/codearena-rl)**

The live space includes a built-in **AI Code Fixer** powered by Hugging Face's Serverless Inference API (using `Qwen2.5-Coder-3B-Instruct`), allowing you to test the agent's repair capabilities directly in your browser.

### Features of the Live Space:
- **Real-time Monitoring**: Watch the agent's compile score, test ratio, and LLM judge scores update live.
- **Sandbox Mode**: Paste your own broken Python code and watch the environment evaluate it.
- **Agent Mode**: Toggle auto-pilot to watch the agent fix code in a continuous loop until optimal.

---

## 🛠️ Architecture & Setup (OpenEnv Compatible)

This benchmark strictly adheres to the **OpenEnv** specification (`openenv.yaml`). 

**Data Flow:** `Agent` → `POST /reset` → `buggy_code` → `POST /step` → `LLM Judge & Test Runner` → `reward` → `Agent`

### Local Development

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```

2. **Generate Task Database:**
   ```bash
   python create_tasks.py
   ```

3. **Run the FastAPI Backend:**
   The backend acts as the OpenEnv entrypoint and serves the compiled React dashboard.
   ```bash
   uvicorn server.app:app --port 7860
   ```

4. **Evaluate a Local Agent (Inference):**
   You can evaluate any local agent (e.g., Ollama or a HuggingFace pipeline) programmatically via `inference.py`.
   ```bash
   export MODEL_NAME="codellama:7b-instruct"
   python inference.py --backend openai
   ```

---

## 🔗 Quick Links

| Resource | URL |
|---|---|
| **Hugging Face Space (Live Demo)** | [CodeArena on HF Spaces](https://huggingface.co/spaces/ceoavinash/codearena-rl) |
| **Colab Training Notebook (TRL)** | [Open in Colab](https://colab.research.google.com/github/havinashpatil/meta/blob/main/train_grpo.ipynb) |
| **OpenEnv Specification** | [openenv.yaml](./openenv.yaml) |
| **Demo Video / Blog Post** | *(Add link to YouTube/HF Blog here if available)* |

---
*Built for the OpenEnv Hackathon India 2026.*
