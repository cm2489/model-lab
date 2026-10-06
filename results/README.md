# Score table

Every run of `evals.run` adds a row. Built by `evals/report.py` from `results/*/metrics.json`; do not edit by hand.

- Accuracy counts invalid replies as wrong.
- Cost per 1,000 bills uses the measured token counts and the prices given on the command line.
  Local runs show $0.00: marginal cost only, hardware and electricity not counted.
- tok/s is generation speed reported by the local runtime. API runs leave it blank.
- Dates are Eastern Time.

| Run | Model | Backend | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3.5-4b-4bit-golden-baseline](qwen3.5-4b-4bit-golden-baseline/score.md) | `mlx-community/Qwen3.5-4B-4bit` | mlx | golden (150) | 59.3% | 0.60 | 0.0% | 0.45 / 0.49 | 116 | $0.00 | 2026-10-06 14:25 | `e7e0746` |
