# qwen3.5-4b-4bit-tuned-quick-golden

- Model: `mlx-community/Qwen3.5-4B-4bit` (mlx)
- Split: golden, 150 examples
- Date: 2026-10-06T17:48:30-04:00 (Eastern Time)
- Commit: `51465ff-dirty`, prompt short-v1
- Wall time: 40 s

| Run | Model | Backend | Prompt | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3.5-4b-4bit-tuned-quick-golden](qwen3.5-4b-4bit-tuned-quick-golden/score.md) | `mlx-community/Qwen3.5-4B-4bit` + LoRA adapter | mlx | short | golden (150) | 54.0% | 0.49 | 14.7% | 0.23 / 0.29 | 82 | $0.00 | 2026-10-06 17:48 | `51465ff-dirty` |

Correct 81 of 150. Invalid replies: 22 (counted as wrong).
How replies ended: length 6, stop 144. A reply that hit max_tokens was cut off.
Cost: local run: $0 marginal cost (hardware and electricity not counted). Average tokens per bill: 64.8 in, 5.8 out.

## Top confusions (gold → predicted)

| Gold | Predicted | Count |
|---|---|---|
| Finance and Financial Sector | INVALID | 5 |
| Education | INVALID | 4 |
| Commerce | INVALID | 2 |
| Social Welfare | Health | 2 |
| Government Operations and Politics | INVALID | 2 |
| Transportation and Public Works | INVALID | 2 |
| Government Operations and Politics | Labor and Employment | 2 |
| International Affairs | Economics and Public Finance | 2 |
| Public Lands and Natural Resources | Environmental Protection | 2 |
| Health | INVALID | 1 |

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Health | 0.73 | 0.92 | 0.81 | 12 |
| Armed Forces and National Security | 0.83 | 1.00 | 0.91 | 10 |
| Government Operations and Politics | 1.00 | 0.22 | 0.36 | 9 |
| Taxation | 1.00 | 0.67 | 0.80 | 9 |
| Crime and Law Enforcement | 0.70 | 1.00 | 0.82 | 7 |
| International Affairs | 1.00 | 0.29 | 0.44 | 7 |
| Agriculture and Food | 0.33 | 0.17 | 0.22 | 6 |
| Finance and Financial Sector | 0.00 | 0.00 | 0.00 | 6 |
| Immigration | 1.00 | 0.17 | 0.29 | 6 |
| Transportation and Public Works | 0.60 | 0.50 | 0.55 | 6 |
| Commerce | 1.00 | 0.20 | 0.33 | 5 |
| Education | 0.00 | 0.00 | 0.00 | 5 |
| Environmental Protection | 0.45 | 1.00 | 0.62 | 5 |
| Public Lands and Natural Resources | 0.00 | 0.00 | 0.00 | 5 |
| Science, Technology, Communications | 0.33 | 0.60 | 0.43 | 5 |
| Energy | 0.60 | 0.75 | 0.67 | 4 |
| Labor and Employment | 0.38 | 0.75 | 0.50 | 4 |
| Civil Rights and Liberties, Minority Issues | 0.60 | 1.00 | 0.75 | 3 |
| Congress | 0.75 | 1.00 | 0.86 | 3 |
| Economics and Public Finance | 0.33 | 1.00 | 0.50 | 3 |
| Emergency Management | 0.67 | 0.67 | 0.67 | 3 |
| Families | 1.00 | 0.33 | 0.50 | 3 |
| Foreign Trade and International Finance | 0.50 | 0.33 | 0.40 | 3 |
| Housing and Community Development | 0.60 | 1.00 | 0.75 | 3 |
| Law | 0.00 | 0.00 | 0.00 | 3 |
| Native Americans | 1.00 | 1.00 | 1.00 | 3 |
| Social Welfare | 1.00 | 0.33 | 0.50 | 3 |
| Water Resources Development | 1.00 | 0.33 | 0.50 | 3 |
| Animals | 0.00 | 0.00 | 0.00 | 2 |
| Arts, Culture, Religion | 0.00 | 0.00 | 0.00 | 2 |
| Sports and Recreation | 1.00 | 1.00 | 1.00 | 2 |
