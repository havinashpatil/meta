---
title: CodeArena RL Benchmark
emoji: 🏟️
colorFrom: green
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

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

| Model | Easy | Medium | Hard | Avg |
|---|---|---|---|---|
| GPT-4o | - | - | - | - |
| Qwen-72B | - | - | - | - |
| Llama-3-8B | - | - | - | - |

## Why It Matters

Every production coding AI needs to debug, not just write. 
There is no other standardized RL environment that trains 
and benchmarks iterative repair. The hybrid grader — 
deterministic test execution plus LLM quality judgment — 
means agents cannot game the reward by memorising solutions 
or producing syntactically correct but semantically wrong fixes.

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

## Usage

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
- HuggingFace Space: https://huggingface.co/spaces/adityanaikhpt/codearena
- Colab Training Notebook: [URL]
- HuggingFace Blog Post: [URL]
- Demo Video: [URL]
