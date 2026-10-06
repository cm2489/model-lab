# Score table

Every run of `evals.run` adds a row. Built by `evals/report.py` from `results/*/metrics.json`; do not edit by hand.

- Accuracy counts invalid replies as wrong.
- Cost per 1,000 bills uses the measured token counts and the prices given on the command line.
  Local runs show $0.00: marginal cost only, hardware and electricity not counted.
- tok/s is generation speed reported by the local runtime. API runs leave it blank.
- Dates are Eastern Time.

| Run | Model | Backend | Prompt | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3.5-4b-4bit-golden-baseline](qwen3.5-4b-4bit-golden-baseline/score.md) | `mlx-community/Qwen3.5-4B-4bit` | mlx | list | golden (150) | 56.7% | 0.54 | 1.3% | 0.44 / 0.48 | 116 | $0.00 | 2026-10-06 14:57 | `6d9165d` |
| [qwen3.5-4b-4bit-tuned-golden](qwen3.5-4b-4bit-tuned-golden/score.md) | `mlx-community/Qwen3.5-4B-4bit` + LoRA `policy-area` | mlx | short | golden (150) | 74.7% | 0.75 | 0.7% | 0.21 / 0.27 | 97 | $0.00 | 2026-10-06 17:43 | `51465ff-dirty` |
| [qwen3.5-4b-4bit-golden-short-prompt](qwen3.5-4b-4bit-golden-short-prompt/score.md) | `mlx-community/Qwen3.5-4B-4bit` | mlx | short | golden (150) | 10.7% | 0.09 | 86.7% | 0.18 / 0.22 | 142 | $0.00 | 2026-10-06 17:43 | `51465ff-dirty` |
| [qwen3.5-4b-4bit-tuned-quick-golden](qwen3.5-4b-4bit-tuned-quick-golden/score.md) | `mlx-community/Qwen3.5-4B-4bit` + LoRA `quick` | mlx | short | golden (150) | 54.0% | 0.49 | 14.7% | 0.23 / 0.29 | 82 | $0.00 | 2026-10-06 17:48 | `51465ff-dirty` |
