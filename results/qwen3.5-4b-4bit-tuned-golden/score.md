# qwen3.5-4b-4bit-tuned-golden

- Model: `mlx-community/Qwen3.5-4B-4bit` (mlx)
- Split: golden, 150 examples
- Date: 2026-10-06T17:43:22-04:00 (Eastern Time)
- Commit: `51465ff-dirty`, prompt short-v1
- Wall time: 36 s

| Run | Model | Backend | Prompt | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3.5-4b-4bit-tuned-golden](qwen3.5-4b-4bit-tuned-golden/score.md) | `mlx-community/Qwen3.5-4B-4bit` + LoRA adapter | mlx | short | golden (150) | 74.7% | 0.75 | 0.7% | 0.21 / 0.27 | 97 | $0.00 | 2026-10-06 17:43 | `51465ff-dirty` |

Correct 112 of 150. Invalid replies: 1 (counted as wrong).
How replies ended: stop 150. A reply that hit max_tokens was cut off.
Cost: local run: $0 marginal cost (hardware and electricity not counted). Average tokens per bill: 64.8 in, 4.0 out.

## Top confusions (gold → predicted)

| Gold | Predicted | Count |
|---|---|---|
| Science, Technology, Communications | Energy | 1 |
| Agriculture and Food | Environmental Protection | 1 |
| Social Welfare | Health | 1 |
| Commerce | Science, Technology, Communications | 1 |
| Government Operations and Politics | Congress | 1 |
| Government Operations and Politics | Education | 1 |
| Science, Technology, Communications | Public Lands and Natural Resources | 1 |
| Taxation | Congress | 1 |
| Health | Native Americans | 1 |
| Labor and Employment | Finance and Financial Sector | 1 |

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Health | 0.79 | 0.92 | 0.85 | 12 |
| Armed Forces and National Security | 0.89 | 0.80 | 0.84 | 10 |
| Government Operations and Politics | 0.83 | 0.56 | 0.67 | 9 |
| Taxation | 1.00 | 0.78 | 0.88 | 9 |
| Crime and Law Enforcement | 0.86 | 0.86 | 0.86 | 7 |
| International Affairs | 1.00 | 0.86 | 0.92 | 7 |
| Agriculture and Food | 0.75 | 0.50 | 0.60 | 6 |
| Finance and Financial Sector | 0.80 | 0.67 | 0.73 | 6 |
| Immigration | 1.00 | 1.00 | 1.00 | 6 |
| Transportation and Public Works | 1.00 | 0.50 | 0.67 | 6 |
| Commerce | 1.00 | 0.40 | 0.57 | 5 |
| Education | 0.40 | 0.80 | 0.53 | 5 |
| Environmental Protection | 0.50 | 0.80 | 0.62 | 5 |
| Public Lands and Natural Resources | 0.67 | 0.40 | 0.50 | 5 |
| Science, Technology, Communications | 0.50 | 0.60 | 0.55 | 5 |
| Energy | 0.50 | 1.00 | 0.67 | 4 |
| Labor and Employment | 0.67 | 0.50 | 0.57 | 4 |
| Civil Rights and Liberties, Minority Issues | 0.75 | 1.00 | 0.86 | 3 |
| Congress | 0.33 | 0.33 | 0.33 | 3 |
| Economics and Public Finance | 1.00 | 1.00 | 1.00 | 3 |
| Emergency Management | 1.00 | 0.67 | 0.80 | 3 |
| Families | 1.00 | 1.00 | 1.00 | 3 |
| Foreign Trade and International Finance | 0.50 | 0.33 | 0.40 | 3 |
| Housing and Community Development | 0.60 | 1.00 | 0.75 | 3 |
| Law | 0.67 | 0.67 | 0.67 | 3 |
| Native Americans | 0.75 | 1.00 | 0.86 | 3 |
| Social Welfare | 1.00 | 0.67 | 0.80 | 3 |
| Water Resources Development | 0.60 | 1.00 | 0.75 | 3 |
| Animals | 1.00 | 1.00 | 1.00 | 2 |
| Arts, Culture, Religion | 1.00 | 1.00 | 1.00 | 2 |
| Sports and Recreation | 1.00 | 1.00 | 1.00 | 2 |
