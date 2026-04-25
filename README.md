# CodeArena RL Benchmark

CodeArena is an OpenEnv-compatible reinforcement learning benchmark for autonomous code repair. In this environment, an agent receives buggy Python code, proposes fixes, and is iteratively evaluated based on test execution feedback and LLM-based quality metrics.

## Features

- **Adaptive Curriculum**: The environment supports an `auto` difficulty mode that dynamically scales task complexity (`easy`, `medium`, `hard`) based on the agent's recent rolling average rewards.
- **Complex Shaped Rewards**: Rewards are a weighted composite of:
  - `compile_score` (0.2)
  - `test_pass_ratio` (0.4)
  - `efficiency_score` (0.1)
  - `llm_judge_score` (0.3): Correctness, Security, and Code Quality evaluated via LLM-as-a-judge.
- **Novelty & Step Penalties**: The agent receives penalties for repeating identical failed fixes or taking too many steps.
- **Extensive Task Categories**: Includes standard algorithmic tasks, `type_errors`, and `security_bugs`.
- **Live React Frontend**: Connect a local LLM (like Ollama) or HuggingFace models to interactively visualize step-by-step progress, execution outputs, and live reward components.

## Architecture

- `server/`: FastAPI backend acting as the OpenEnv entrypoint. Handles state, execution sandbox (`executor.py`), and reward grading (`grader.py`).
- `frontend/`: React + Vite frontend for live monitoring and manual intervention.
- `tasks/`: Task definitions stored in OpenEnv-compatible JSON schema.
- `inference.py`: CLI runner for evaluating RL agents, supporting both OpenAI-compatible APIs and native HuggingFace `transformers` pipelines.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```

2. **Generate New Tasks:**
   To populate the extended task categories (`type_errors` and `security_bugs`), run:
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
