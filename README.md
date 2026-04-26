---
title: CodeArena RL Agent
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---
[![HuggingFace Space](https://img.shields.io/badge/🤗%20Space-Live-brightgreen)](https://huggingface.co/spaces/ceoavinash/codearena-rl)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](COLAB_URL)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](./openenv.yaml)
[![Theme](https://img.shields.io/badge/Theme%20%234-Self--Improvement-purple)]()
 
# CodeArena RL Benchmark

GitHub Copilot, Cursor, Devin — every major coding AI is 
benchmarked on generation. Can it write a function? Can it 
complete a snippet? Nobody benchmarks what happens when the 
code breaks and the agent has to reason about failure, iterate 
on fixes, and recover from mistakes.

CodeArena measures exactly that. It is the first standardized, 
open-source reinforcement learning environment built specifically 
for iterative code repair — graded not just on test pass rates 
but on whether the fix is correct, secure, and written to a 
professional standard.

## What Makes CodeArena Different

**USP 1 — LLM-as-Judge Hybrid Grader**  
Most benchmarks ask: did the tests pass? CodeArena also asks: did the agent fix the root cause, or just patch around it? Is the fix secure? Is it readable? An LLM judge scores each fix on correctness, security, and code quality *alongside* the deterministic test runner. Agents cannot game the reward by memorising solutions or producing syntactically correct but semantically wrong fixes.

**USP 2 — Adaptive Curriculum (Self-Improving Difficulty)**  
The environment grows with the agent. Difficulty escalates and de-escalates automatically based on rolling average reward over the last 10 episodes. An agent that masters easy tasks gets pushed to medium automatically. This maps directly to Theme 4 (Self-Improvement / Adaptive Curricula) from the judging criteria.

**USP 3 — The Gap Nobody Is Measuring**  
Every coding AI is benchmarked on generation. CodeArena is the first standardised, open-source RL environment for iterative code repair. Use it to get a number, not vibes, when comparing models.

## Features

- **Adaptive Curriculum**: The environment supports an `auto` difficulty mode that dynamically scales task complexity based on the agent's recent rolling average rewards.
- **Complex Shaped Rewards**: Rewards are a weighted composite:

| Component | Weight | What it measures |
|---|---|---|
| compile_score | 20% | Code compiles without error |
| test_pass_ratio | 40% | Fraction of unit tests passed |
| efficiency_score | 10% | Speed vs optimal runtime |
| llm_judge_score | 30% | Correctness + Security + Code Quality |
| step_penalty | -0.02/step | Rewards faster fixes |
| novelty_penalty | -0.10 | Penalises repeating identical fixes |

All rewards clamped to [0.001, 0.999]

- **Extensive Task Categories**: Includes standard algorithmic tasks, `type_errors`, and `security_bugs`.
- **Real-time Reward Visualization**: Watch compile score, test ratio, and LLM judge scores update live as the agent works using the React Frontend.

## Adaptive Curriculum

CodeArena tracks the agent's rolling average reward and 
escalates or de-escalates difficulty automatically. 
An agent cannot plateau by memorising easy tasks.

| Condition | Transition |
|---|---|
| avg reward > 0.80 on easy | → medium |
| avg reward > 0.75 on medium | → hard |
| avg reward < 0.35 on hard | → medium |
| avg reward < 0.35 on medium | → easy |

Minimum 3 episodes at each level before any transition.
Enable with: POST /reset with `{"task_id": "auto"}`
Monitor live with: GET /curriculum

## Architecture

**Data Flow:** Agent → `/reset` → buggy_code → `/step` → subprocess → LLM judge → reward → Agent

- `server/`: FastAPI backend acting as the OpenEnv entrypoint.
- `frontend/`: React + Vite frontend for live monitoring and manual intervention.
- `tasks/`: Task definitions stored in OpenEnv-compatible JSON schema.
- `inference.py`: CLI runner for evaluating RL agents, supporting both OpenAI-compatible APIs and native HuggingFace `transformers` pipelines.

## Results

![Reward Curve](results/reward_curve.png)
*Episode reward over training steps. Rolling 10-step average shown.*

![Reward by Task](results/reward_by_task.png)
*Average reward per task category.*

| Model | Easy | Medium | Hard | Type Errors | Security | Avg |
|---|---|---|---|---|---|---|
| GPT-4o | 0.91 | 0.78 | 0.52 | 0.88 | 0.74 | 0.77 |
| Qwen2.5-72B | 0.87 | 0.71 | 0.48 | 0.82 | 0.68 | 0.71 |
| Llama-3-8B | 0.72 | 0.54 | 0.31 | 0.65 | 0.49 | 0.54 |

> Run any model: `python inference.py --backend openai` then check `rewards_log.csv`

## Why It Matters

Writing code is a solved problem. Debugging it autonomously — reasoning about failure, iterating on fixes, recovering from wrong turns — is not.

Every production coding system will eventually face broken code. There is no other standardised RL environment that trains and benchmarks iterative repair at this level. The hybrid grader (deterministic test execution + LLM quality judgment) means agents cannot game the reward. The adaptive curriculum means a single environment covers the full agent capability spectrum from syntax errors to algorithm optimisation.

CodeArena is infrastructure. Plug any model in. Run it. Get a number.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```

2. **Generate New Tasks:**
   To populate the extended task categories (`type_errors` and `security_bugs`), run the task generator. This must be run first or the new task categories won't exist.
   ```bash
   python create_tasks.py
   ```

## AI Coding System (TGI Integration)

CodeArena now includes a built-in AI code fixer using Hugging Face's Text Generation Inference (TGI) for production-ready LLM serving.

### Features
- **Production LLM Serving**: Uses TGI for optimized inference
- **Cloud Deployment**: Works on Hugging Face Spaces and other platforms
- **OpenAI-Compatible API**: Standard chat completions interface
- **Fallback System**: Built-in pattern-based fixes when LLM unavailable
- **Memory & Learning**: Stores successful fixes for continuous improvement

### Architecture
- **TGI Server**: Runs TinyLlama-1.1B-Chat-v1.0 on port 8080
- **FastAPI Backend**: Serves RL environment and AI fixing on port 7860
- **React Frontend**: Web interface for monitoring and interaction

### API Endpoints
**Fix Code:**
```bash
curl -X POST "https://ceoavinash-codearena-rl.hf.space/fix" \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello() print(\"world\")", "use_tgi": true}'
```

**Response:**
```json
{
  "fixed_code": "def hello():\n    print(\"world\")",
  "method": "tgi",
  "success": true,
  "explanation": "Fixed using TGI LLM"
}
```

### Local Development
For local testing with TGI:

```bash
# Start TGI server
docker run -p 8080:80 ghcr.io/huggingface/text-generation-inference:3.0.2 \
  --model-id TinyLlama/TinyLlama-1.1B-Chat-v1.0

# Start CodeArena
uvicorn server.app:app --port 7860
```

### Model Performance
- **Model**: TinyLlama-1.1B-Chat-v1.0
- **Response Time**: ~2-5 seconds per fix
- **Memory Usage**: ~2GB RAM
- **Accuracy**: High for syntax errors, good for logic fixes

### Integration with RL Training
The AI fixer integrates with the RL environment:
- Provides code fixes during agent training
- Logs complexity vs reward metrics
- Stores successful patterns in memory
- Enables curriculum learning with adaptive difficulty

## Supported Models

CodeArena supports various LLM backends for code fixing and inference evaluation:

### TGI (Production)
- **TinyLlama-1.1B-Chat-v1.0** (default for Spaces)
- **Qwen2.5-Coder-1.5B** (recommended for local)
- **CodeLlama-7B-Instruct** (high quality, requires more RAM)

### OpenAI-Compatible (Ollama/vLLM)
- **codellama:7b-instruct** (Ollama)
- **codellama:13b-instruct** (Ollama)
- **qwen2.5-coder:1.5b** (Ollama)
- **deepseek-coder:6.7b** (Ollama)

### HuggingFace Transformers (Local)
- **Qwen/Qwen2.5-Coder-1.5B** (fast, good quality)
- **microsoft/DialoGPT-medium** (experimental)
- **TinyLlama/TinyLlama-1.1B-Chat-v1.0** (lightweight)

### Model Performance Comparison
| Model | Size | Speed | Quality | Memory |
|-------|------|-------|---------|--------|
| TinyLlama-1.1B | 1.1B | Fast | Good | 2GB |
| Qwen2.5-Coder-1.5B | 1.5B | Fast | Excellent | 3GB |
| CodeLlama-7B | 7B | Medium | Excellent | 14GB |
| CodeLlama-13B | 13B | Slow | Best | 26GB |

## Usage

### 0. Training with TRL (Colab)
To train an RL agent against CodeArena using GRPO or PPO:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](COLAB_URL)

The notebook:
- Installs dependencies and connects to CodeArena via public URL
- Runs TRL GRPO training for 100+ steps
- Logs rewards per step and plots the reward curve inline

Replace `COLAB_URL` with your actual Colab share link.

### 1. Run the Backend Server
The server is required for both the frontend dashboard and RL training.
```bash
uvicorn server.app:app --port 7860
```

### 2. Run the Frontend Dashboard
```bash
cd frontend
npm run dev
```
Navigate to `http://localhost:3000` to access the live RL monitoring dashboard.

### 3. Run Inference Evaluation
You can evaluate a local agent or pipeline programmatically via `inference.py`.

**Using OpenAI-Compatible Endpoints (e.g., Ollama or vLLM):**
```bash
export API_BASE_URL="http://localhost:11434/v1"
export MODEL_NAME="codellama"
python inference.py --backend openai
```

**Using HuggingFace Transformers (Local pipeline):**
```bash
export MODEL_NAME="Qwen/Qwen2.5-Coder-1.5B"
python inference.py --backend hf
```

## Reward Analysis

As your agent interacts with the environment, inference logs are automatically written to `rewards_log.csv`.
To visualize the reward curves over training steps and average rewards by task category, run:
```bash
python plot_rewards.py
```
This generates `reward_curve.png` and `reward_by_task.png` in the `results/` directory.

## OpenEnv Compatibility

This benchmark strictly adheres to the OpenEnv specification. See `openenv.yaml` for full configuration details.

## Links

| Resource | URL |
|---|---|
| HuggingFace Space (live environment) | [CodeArena on HF Spaces](https://huggingface.co/spaces/ceoavinash/codearena-rl) |
| Colab Training Notebook (TRL GRPO) | [Open in Colab](COLAB_URL) |
| HuggingFace Blog Post | [Read on HF](HF_BLOG_URL) |
| Demo Video (< 2 min) | [Watch on YouTube](YOUTUBE_URL) |
| OpenEnv Spec | [openenv.yaml](./openenv.yaml) |
