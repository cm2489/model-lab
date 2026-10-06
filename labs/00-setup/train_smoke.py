"""Lab 0, step 3: a 20-step LoRA training test.

It runs the same thing as this command, then prints the two numbers the
command does not: wall time and peak memory.

    uv run mlx_lm.lora --model mlx-community/Qwen3.5-4B-4bit --train \
        --data labs/00-setup/smoke --iters 20 --batch-size 1 --num-layers 8 \
        --steps-per-report 5 --steps-per-eval 20 --val-batches 5 \
        --adapter-path adapters/smoke
"""
import sys
import time

import mlx.core as mx
from mlx_lm import lora

MODEL = sys.argv[1] if len(sys.argv) > 1 else "mlx-community/Qwen3.5-4B-4bit"

ARGS = [
    "--model", MODEL,
    "--train",
    "--data", "labs/00-setup/smoke",
    "--iters", "20",
    "--batch-size", "1",
    "--num-layers", "8",
    "--steps-per-report", "5",
    "--steps-per-eval", "20",
    "--val-batches", "5",
    "--adapter-path", "adapters/smoke",
]

start = time.time()
sys.argv = ["mlx_lm.lora", *ARGS]
lora.main()
elapsed = time.time() - start

print()
print(f"Model:       {MODEL}")
print(f"Wall time:   {elapsed:.0f} seconds for 20 steps (includes loading the model)")
print(f"Peak memory: {mx.get_peak_memory() / 1e9:.2f} GB")
