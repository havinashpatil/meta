# Fine-tuning Guide: XCoder-80K Dataset

This guide explains how to fine-tune Ollama models on the XCoder-80K code dataset.

## Overview

The `finetune_models.py` script fine-tunes open-source code models on the XCoder-80K dataset from Hugging Face:

| Ollama Model | HuggingFace Model | Size | Recommended |
|---|---|---|---|
| `llama3.2:latest` | meta-llama/Llama-2-7b-hf | 7B | ✓ Best for code |
| `gemma3:4b` | google/gemma-7b | 7B | ✓ Good alternative |
| `gemma3:1b` | google/gemma-2b | 2B | Lightweight option |
| `llava:latest` | Not suitable | Multimodal | ✗ Skip (vision-only) |

**Dataset:** [banksy235/XCoder-80K](https://huggingface.co/datasets/banksy235/XCoder-80K)
- 80,000 code examples
- Covers multiple programming languages
- Suitable for code generation and repair

## Installation

### Quick Install (Recommended)

**Windows:**
```bash
install_finetune.bat
```

**Linux/macOS:**
```bash
bash install_finetune.sh
```

### Manual Installation

1. **Install PyTorch with CUDA 12.1 support:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

2. **Install fine-tuning dependencies:**
```bash
pip install -r requirements-finetune.txt
```

3. **Verify installation:**
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'GPU: {torch.cuda.is_available()}')"
```

### Install Hugging Face CLI (Optional)

For easier dataset management:
```bash
# macOS/Linux
curl -LsSf https://hf.co/cli/install.sh | bash -s

# Or via pip
pip install huggingface_hub

# Login (for private datasets)
huggingface-cli login
```

## Usage

### Option 1: Fine-tune Single Model

Fine-tune Llama-2-7b on XCoder-80K (recommended for fastest start):
```bash
python finetune_models.py --model llama3.2 \
  --num-epochs 3 \
  --batch-size 4 \
  --learning-rate 2e-4
```

### Option 2: Fine-tune All Models Sequentially

```bash
python finetune_models.py --all-models \
  --num-epochs 3 \
  --batch-size 4 \
  --max-samples 5000
```

### Option 3: Custom Configuration

```bash
python finetune_models.py \
  --model llama3.2 \
  --output-dir ./my_finetuned_models \
  --num-epochs 5 \
  --batch-size 8 \
  --learning-rate 1e-4 \
  --max-samples 10000 \
  --no-lora  # Disable LoRA (full fine-tuning)
```

## Training Arguments Explained

| Argument | Default | Description |
|---|---|---|
| `--model` | `llama3.2` | Model to fine-tune |
| `--all-models` | False | Fine-tune all available models |
| `--output-dir` | `./finetuned_models` | Where to save fine-tuned models |
| `--num-epochs` | 3 | Training epochs (more = longer training) |
| `--batch-size` | 4 | Batch size (larger = more VRAM needed) |
| `--learning-rate` | 2e-4 | Learning rate (lower = slower updates) |
| `--max-samples` | None | Limit samples (None = use all 80K) |
| `--no-lora` | False | Disable LoRA (full fine-tuning) |
| `--no-gradient-checkpointing` | False | Disable gradient checkpointing |

## Output

After training, models are saved to:
```
finetuned_models/
├── llama3_2/
│   ├── final/
│   │   ├── pytorch_model.bin
│   │   ├── config.json
│   │   └── tokenizer.json
│   └── metadata.json
├── gemma3_4b/
│   └── ...
└── gemma3_1b/
    └── ...
```

## Using Fine-tuned Models with Ollama

After fine-tuning, you can create custom Ollama models. Create a `Modelfile`:

```dockerfile
FROM llama3.2:latest

# Replace the base model with fine-tuned weights
COPY ./finetuned_models/llama3_2/final /model

# Optional: Set parameters
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
```

Then create and run:
```bash
ollama create my-finetuned-llama -f Modelfile
ollama run my-finetuned-llama "your prompt here"
```

Or use directly in Python:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "./finetuned_models/llama3_2/final"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

# Use the model
inputs = tokenizer("def fibonacci", return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

## Hardware Requirements

| Configuration | VRAM | Training Speed | Recommended |
|---|---|---|---|
| RTX 4090 (24GB) | 24GB | ~2 hours | ✓ Excellent |
| RTX 4080 (16GB) | 16GB | ~3-4 hours | ✓ Good |
| RTX 4070 (12GB) | 12GB | ~5-6 hours | Acceptable |
| Tesla T4 (16GB) | 16GB | ~4-5 hours | Cloud-friendly |
| CPU only | N/A | ~1-2 days | Not recommended |

**Optimization Tips:**
- Use `--batch-size 2` for GPUs with <12GB VRAM
- Enable `--max-samples 1000` to train on subset first
- LoRA (default) uses 70% less VRAM than full fine-tuning
- Gradient checkpointing (default) reduces VRAM by 30%

## Integration with CodeArena RL

To use fine-tuned models with the CodeArena RL environment:

1. **Export to Ollama** (see above)
2. **Update Dashboard.jsx** to use the new model:
   ```javascript
   const [ollamaModel, setOllamaModel] = useState('my-finetuned-llama');
   ```
3. **Or update ollama_rl_rollout.py:**
   ```bash
   python ollama_rl_rollout.py --ollama-model my-finetuned-llama
   ```

## Monitoring Training

Training logs are saved to TensorBoard format:
```bash
tensorboard --logdir ./finetuned_models/llama3_2
```

Open http://localhost:6006 to monitor:
- Training loss
- Learning rate schedules
- GPU usage

## Troubleshooting

### Out of Memory (OOM)
```bash
# Reduce batch size
python finetune_models.py --batch-size 2

# Or limit samples
python finetune_models.py --max-samples 1000
```

### Slow Training
- Ensure GPU is being used: `nvidia-smi`
- Use smaller model: `--model gemma3:1b`
- Reduce max_length in tokenization (in code)

### Dataset Not Found
```bash
# Download manually first
python -c "from datasets import load_dataset; load_dataset('banksy235/XCoder-80K')"

# Or use Hugging Face CLI
hf download banksy235/XCoder-80K
```

## Dataset Structure

The XCoder-80K dataset contains code examples with metadata. The script automatically handles:
- Multi-language code (Python, JavaScript, Java, C++, etc.)
- Code with comments and docstrings
- Various programming tasks (algorithms, utilities, etc.)

## Next Steps

1. **Run fine-tuning:** `python finetune_models.py --model llama3.2`
2. **Monitor training:** `tensorboard --logdir ./finetuned_models/llama3_2`
3. **Export to Ollama:** Create custom Modelfile and `ollama create`
4. **Test in CodeArena:** Update dashboard to use fine-tuned model
5. **Measure improvements:** Run `python plot_rewards.py` to see RL performance gains

## References

- [XCoder-80K Dataset](https://huggingface.co/datasets/banksy235/XCoder-80K)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [TRL (Transformer Reinforcement Learning)](https://github.com/huggingface/trl)
- [Ollama Documentation](https://ollama.ai)
- [PEFT (Parameter-Efficient Fine-Tuning)](https://github.com/huggingface/peft)
