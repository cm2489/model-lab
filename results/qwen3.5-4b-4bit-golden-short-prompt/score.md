# qwen3.5-4b-4bit-golden-short-prompt

- Model: `mlx-community/Qwen3.5-4B-4bit` (mlx)
- Split: golden, 150 examples
- Date: 2026-10-06T17:43:57-04:00 (Eastern Time)
- Commit: `51465ff-dirty`, prompt short-v1
- Wall time: 30 s

| Run | Model | Backend | Prompt | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3.5-4b-4bit-golden-short-prompt](qwen3.5-4b-4bit-golden-short-prompt/score.md) | `mlx-community/Qwen3.5-4B-4bit` | mlx | short | golden (150) | 10.7% | 0.09 | 86.7% | 0.18 / 0.22 | 142 | $0.00 | 2026-10-06 17:43 | `51465ff-dirty` |

Correct 16 of 150. Invalid replies: 130 (counted as wrong).
How replies ended: stop 150. A reply that hit max_tokens was cut off.
Cost: local run: $0 marginal cost (hardware and electricity not counted). Average tokens per bill: 64.8 in, 3.6 out.

## Top confusions (gold → predicted)

| Gold | Predicted | Count |
|---|---|---|
| Armed Forces and National Security | INVALID | 9 |
| Government Operations and Politics | INVALID | 9 |
| International Affairs | INVALID | 7 |
| Crime and Law Enforcement | INVALID | 6 |
| Transportation and Public Works | INVALID | 6 |
| Finance and Financial Sector | INVALID | 6 |
| Taxation | INVALID | 6 |
| Commerce | INVALID | 5 |
| Immigration | INVALID | 5 |
| Health | INVALID | 5 |

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Health | 0.88 | 0.58 | 0.70 | 12 |
| Armed Forces and National Security | 0.00 | 0.00 | 0.00 | 10 |
| Government Operations and Politics | 0.00 | 0.00 | 0.00 | 9 |
| Taxation | 1.00 | 0.33 | 0.50 | 9 |
| Crime and Law Enforcement | 0.00 | 0.00 | 0.00 | 7 |
| International Affairs | 0.00 | 0.00 | 0.00 | 7 |
| Agriculture and Food | 0.00 | 0.00 | 0.00 | 6 |
| Finance and Financial Sector | 0.00 | 0.00 | 0.00 | 6 |
| Immigration | 1.00 | 0.17 | 0.29 | 6 |
| Transportation and Public Works | 0.00 | 0.00 | 0.00 | 6 |
| Commerce | 0.00 | 0.00 | 0.00 | 5 |
| Education | 0.67 | 0.80 | 0.73 | 5 |
| Environmental Protection | 0.00 | 0.00 | 0.00 | 5 |
| Public Lands and Natural Resources | 0.00 | 0.00 | 0.00 | 5 |
| Science, Technology, Communications | 0.00 | 0.00 | 0.00 | 5 |
| Energy | 0.00 | 0.00 | 0.00 | 4 |
| Labor and Employment | 0.00 | 0.00 | 0.00 | 4 |
| Civil Rights and Liberties, Minority Issues | 0.00 | 0.00 | 0.00 | 3 |
| Congress | 0.00 | 0.00 | 0.00 | 3 |
| Economics and Public Finance | 0.00 | 0.00 | 0.00 | 3 |
| Emergency Management | 0.00 | 0.00 | 0.00 | 3 |
| Families | 0.00 | 0.00 | 0.00 | 3 |
| Foreign Trade and International Finance | 0.00 | 0.00 | 0.00 | 3 |
| Housing and Community Development | 1.00 | 0.33 | 0.50 | 3 |
| Law | 0.00 | 0.00 | 0.00 | 3 |
| Native Americans | 0.00 | 0.00 | 0.00 | 3 |
| Social Welfare | 0.00 | 0.00 | 0.00 | 3 |
| Water Resources Development | 0.00 | 0.00 | 0.00 | 3 |
| Animals | 0.00 | 0.00 | 0.00 | 2 |
| Arts, Culture, Religion | 0.00 | 0.00 | 0.00 | 2 |
| Sports and Recreation | 0.00 | 0.00 | 0.00 | 2 |
