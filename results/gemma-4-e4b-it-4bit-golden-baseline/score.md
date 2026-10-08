# gemma-4-e4b-it-4bit-golden-baseline

- Model: `mlx-community/gemma-4-e4b-it-4bit` (mlx)
- Split: golden, 150 examples
- Date: 2026-10-07T23:48:16-04:00 (Eastern Time)
- Commit: `06546bc`, prompt v1
- Wall time: 50 s

| Run | Model | Backend | Prompt | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [gemma-4-e4b-it-4bit-golden-baseline](gemma-4-e4b-it-4bit-golden-baseline/score.md) | `mlx-community/gemma-4-e4b-it-4bit` | mlx | list | golden (150) | 60.0% | 0.59 | 1.3% | 0.32 / 0.35 | 96 | $0.00 | 2026-10-07 23:48 | `06546bc` |

Correct 90 of 150. Invalid replies: 2 (counted as wrong).
How replies ended: stop 150. A reply that hit max_tokens was cut off.
Cost: local run: $0 marginal cost (hardware and electricity not counted). Average tokens per bill: 245.6 in, 4.2 out.

## Top confusions (gold → predicted)

| Gold | Predicted | Count |
|---|---|---|
| International Affairs | Foreign Trade and International Finance | 5 |
| Armed Forces and National Security | Social Welfare | 3 |
| Economics and Public Finance | Government Operations and Politics | 3 |
| Health | Social Welfare | 2 |
| Law | Civil Rights and Liberties, Minority Issues | 2 |
| Public Lands and Natural Resources | Science, Technology, Communications | 2 |
| Armed Forces and National Security | Health | 2 |
| Families | Social Welfare | 2 |
| Government Operations and Politics | Commerce | 2 |
| Immigration | INVALID | 1 |

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Health | 0.77 | 0.83 | 0.80 | 12 |
| Armed Forces and National Security | 0.67 | 0.40 | 0.50 | 10 |
| Government Operations and Politics | 0.40 | 0.44 | 0.42 | 9 |
| Taxation | 1.00 | 0.78 | 0.88 | 9 |
| Crime and Law Enforcement | 0.75 | 0.86 | 0.80 | 7 |
| International Affairs | 0.00 | 0.00 | 0.00 | 7 |
| Agriculture and Food | 0.57 | 0.67 | 0.62 | 6 |
| Finance and Financial Sector | 0.62 | 0.83 | 0.71 | 6 |
| Immigration | 1.00 | 0.33 | 0.50 | 6 |
| Transportation and Public Works | 1.00 | 0.50 | 0.67 | 6 |
| Commerce | 0.60 | 0.60 | 0.60 | 5 |
| Education | 1.00 | 1.00 | 1.00 | 5 |
| Environmental Protection | 0.50 | 0.60 | 0.55 | 5 |
| Public Lands and Natural Resources | 0.43 | 0.60 | 0.50 | 5 |
| Science, Technology, Communications | 0.33 | 0.60 | 0.43 | 5 |
| Energy | 1.00 | 0.50 | 0.67 | 4 |
| Labor and Employment | 0.40 | 0.50 | 0.44 | 4 |
| Civil Rights and Liberties, Minority Issues | 0.43 | 1.00 | 0.60 | 3 |
| Congress | 0.75 | 1.00 | 0.86 | 3 |
| Economics and Public Finance | 0.00 | 0.00 | 0.00 | 3 |
| Emergency Management | 0.67 | 0.67 | 0.67 | 3 |
| Families | 1.00 | 0.33 | 0.50 | 3 |
| Foreign Trade and International Finance | 0.17 | 0.33 | 0.22 | 3 |
| Housing and Community Development | 1.00 | 1.00 | 1.00 | 3 |
| Law | 0.00 | 0.00 | 0.00 | 3 |
| Native Americans | 1.00 | 1.00 | 1.00 | 3 |
| Social Welfare | 0.18 | 0.67 | 0.29 | 3 |
| Water Resources Development | 0.50 | 0.33 | 0.40 | 3 |
| Animals | 1.00 | 1.00 | 1.00 | 2 |
| Arts, Culture, Religion | 1.00 | 0.50 | 0.67 | 2 |
| Sports and Recreation | 1.00 | 1.00 | 1.00 | 2 |
