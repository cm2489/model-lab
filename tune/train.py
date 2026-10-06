"""Fine-tune with LoRA, with a disk check first and a summary after.

  uv run python -m tune.train                      # the lab's default run
  uv run python -m tune.train --iters 300 --name quick

It runs mlx_lm.lora with the settings below, then prints wall time and peak
memory, which the tool itself does not print. The equivalent command is:

  uv run mlx_lm.lora --model mlx-community/Qwen3.5-4B-4bit --train --data data/lora \
      --iters 1200 --batch-size 1 --grad-accumulation-steps 4 --num-layers 8 \
      --learning-rate 1e-4 --mask-prompt --max-seq-length 512 \
      --steps-per-report 100 --steps-per-eval 400 --val-batches 100 \
      --adapter-path adapters/policy-area

Why batch size 1: on a 32 GB Mac, memory grows fast with the number of tokens
in a batch. A batch of 4 short examples pushed this machine into swap, and a
batch of 2 long ones peaked at 23 GB. Batch 1 with gradient accumulation 4
updates the weights every 4 examples, like a batch of 4, at the memory cost of 1.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time

from evals.files import ROOT

MIN_FREE_GB = 5


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="mlx-community/Qwen3.5-4B-4bit")
    ap.add_argument("--data", default=str(ROOT / "data" / "lora"))
    ap.add_argument("--name", default="policy-area", help="adapter folder name under adapters/")
    ap.add_argument("--iters", type=int, default=1200)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accumulation-steps", type=int, default=4)
    ap.add_argument("--num-layers", type=int, default=8)
    ap.add_argument("--learning-rate", default="1e-4")
    args = ap.parse_args(argv)

    free_gb = shutil.disk_usage(str(ROOT)).free / 1e9
    if free_gb < MIN_FREE_GB:
        print(f"Only {free_gb:.1f} GB of disk is free. Training needs room for swap. "
              f"Free at least {MIN_FREE_GB} GB, then run this again.")
        return 1
    if args.batch_size > 1:
        print(f"Batch size {args.batch_size}: this needs much more memory than batch 1. "
              "Watch Activity Monitor, and stop the run if memory pressure turns red.")

    import mlx.core as mx
    from mlx_lm import lora

    adapter = ROOT / "adapters" / args.name
    sys.argv = ["mlx_lm.lora", "--model", args.model, "--train", "--data", args.data,
                "--iters", str(args.iters), "--batch-size", str(args.batch_size),
                "--grad-accumulation-steps", str(args.grad_accumulation_steps),
                "--num-layers", str(args.num_layers), "--learning-rate", str(args.learning_rate),
                "--mask-prompt", "--max-seq-length", "512",
                "--steps-per-report", "100", "--steps-per-eval", "400", "--val-batches", "100",
                "--adapter-path", str(adapter)]
    start = time.time()
    lora.main()
    elapsed = time.time() - start

    print()
    print(f"Model:       {args.model}")
    print(f"Adapter:     {adapter.relative_to(ROOT)}")
    print(f"Wall time:   {elapsed / 60:.1f} minutes for {args.iters} steps")
    print(f"Peak memory: {mx.get_peak_memory() / 1e9:.2f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
