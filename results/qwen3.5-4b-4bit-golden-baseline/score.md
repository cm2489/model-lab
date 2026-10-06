# qwen3.5-4b-4bit-golden-baseline

- Model: `mlx-community/Qwen3.5-4B-4bit` (mlx)
- Split: golden, 150 examples
- Date: 2026-10-06T14:57:57-04:00 (Eastern Time)
- Commit: `6d9165d`, prompt v1
- Wall time: 69 s

| Run | Model | Backend | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3.5-4b-4bit-golden-baseline](qwen3.5-4b-4bit-golden-baseline/score.md) | `mlx-community/Qwen3.5-4B-4bit` | mlx | golden (150) | 56.7% | 0.54 | 1.3% | 0.44 / 0.48 | 116 | $0.00 | 2026-10-06 14:57 | `6d9165d` |

Correct 85 of 150. Invalid replies: 2 (counted as wrong).
How replies ended: stop 150. A reply that hit max_tokens was cut off.
Cost: local run: $0 marginal cost (hardware and electricity not counted). Average tokens per bill: 249.8 in, 4.7 out.

## Top confusions (gold → predicted)

| Gold | Predicted | Count |
|---|---|---|
| Taxation | Economics and Public Finance | 5 |
| International Affairs | Armed Forces and National Security | 3 |
| International Affairs | Foreign Trade and International Finance | 2 |
| Law | Civil Rights and Liberties, Minority Issues | 2 |
| Immigration | Armed Forces and National Security | 2 |
| Congress | Arts, Culture, Religion | 1 |
| Water Resources Development | Public Lands and Natural Resources | 1 |
| Immigration | Transportation and Public Works | 1 |
| Animals | Environmental Protection | 1 |
| Science, Technology, Communications | Transportation and Public Works | 1 |

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Health | 0.77 | 0.83 | 0.80 | 12 |
| Armed Forces and National Security | 0.67 | 1.00 | 0.80 | 10 |
| Government Operations and Politics | 0.43 | 0.33 | 0.38 | 9 |
| Taxation | 0.00 | 0.00 | 0.00 | 9 |
| Crime and Law Enforcement | 0.83 | 0.71 | 0.77 | 7 |
| International Affairs | 0.00 | 0.00 | 0.00 | 7 |
| Agriculture and Food | 0.67 | 0.67 | 0.67 | 6 |
| Finance and Financial Sector | 0.80 | 0.67 | 0.73 | 6 |
| Immigration | 0.50 | 0.17 | 0.25 | 6 |
| Transportation and Public Works | 0.57 | 0.67 | 0.62 | 6 |
| Commerce | 0.40 | 0.40 | 0.40 | 5 |
| Education | 0.80 | 0.80 | 0.80 | 5 |
| Environmental Protection | 0.67 | 0.80 | 0.73 | 5 |
| Public Lands and Natural Resources | 0.33 | 0.60 | 0.43 | 5 |
| Science, Technology, Communications | 0.43 | 0.60 | 0.50 | 5 |
| Energy | 1.00 | 0.50 | 0.67 | 4 |
| Labor and Employment | 0.40 | 0.50 | 0.44 | 4 |
| Civil Rights and Liberties, Minority Issues | 0.50 | 1.00 | 0.67 | 3 |
| Congress | 0.50 | 0.33 | 0.40 | 3 |
| Economics and Public Finance | 0.12 | 0.33 | 0.18 | 3 |
| Emergency Management | 1.00 | 1.00 | 1.00 | 3 |
| Families | 0.75 | 1.00 | 0.86 | 3 |
| Foreign Trade and International Finance | 0.20 | 0.33 | 0.25 | 3 |
| Housing and Community Development | 0.75 | 1.00 | 0.86 | 3 |
| Law | 0.00 | 0.00 | 0.00 | 3 |
| Native Americans | 0.67 | 0.67 | 0.67 | 3 |
| Social Welfare | 0.33 | 0.67 | 0.44 | 3 |
| Water Resources Development | 0.00 | 0.00 | 0.00 | 3 |
| Animals | 1.00 | 0.50 | 0.67 | 2 |
| Arts, Culture, Religion | 0.67 | 1.00 | 0.80 | 2 |
| Sports and Recreation | 1.00 | 1.00 | 1.00 | 2 |
