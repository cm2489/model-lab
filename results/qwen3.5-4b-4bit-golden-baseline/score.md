# qwen3.5-4b-4bit-golden-baseline

- Model: `mlx-community/Qwen3.5-4B-4bit` (mlx)
- Split: golden, 150 examples
- Date: 2026-10-06T14:25:44-04:00 (Eastern Time)
- Commit: `e7e0746`, prompt v1
- Wall time: 70 s

| Run | Model | Backend | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [qwen3.5-4b-4bit-golden-baseline](qwen3.5-4b-4bit-golden-baseline/score.md) | `mlx-community/Qwen3.5-4B-4bit` | mlx | golden (150) | 59.3% | 0.60 | 0.0% | 0.45 / 0.49 | 116 | $0.00 | 2026-10-06 14:25 | `e7e0746` |

Correct 89 of 150. Invalid replies: 0 (counted as wrong).
Cost: local run: $0 marginal cost (hardware and electricity not counted). Average tokens per bill: 250.2 in, 4.4 out.

## Top confusions (gold → predicted)

| Gold | Predicted | Count |
|---|---|---|
| International Affairs | Armed Forces and National Security | 5 |
| Taxation | Economics and Public Finance | 4 |
| Taxation | Health | 2 |
| Commerce | Economics and Public Finance | 2 |
| Public Lands and Natural Resources | Arts, Culture, Religion | 2 |
| Families | Social Welfare | 2 |
| Government Operations and Politics | Labor and Employment | 2 |
| Government Operations and Politics | Congress | 1 |
| Armed Forces and National Security | Education | 1 |
| Immigration | Health | 1 |

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Health | 0.62 | 0.83 | 0.71 | 12 |
| Armed Forces and National Security | 0.33 | 0.56 | 0.42 | 9 |
| Government Operations and Politics | 0.50 | 0.33 | 0.40 | 9 |
| Taxation | 1.00 | 0.22 | 0.36 | 9 |
| Crime and Law Enforcement | 0.80 | 0.57 | 0.67 | 7 |
| International Affairs | 1.00 | 0.14 | 0.25 | 7 |
| Agriculture and Food | 0.71 | 0.83 | 0.77 | 6 |
| Finance and Financial Sector | 0.67 | 0.67 | 0.67 | 6 |
| Immigration | 0.75 | 0.50 | 0.60 | 6 |
| Public Lands and Natural Resources | 0.75 | 0.50 | 0.60 | 6 |
| Transportation and Public Works | 0.83 | 0.83 | 0.83 | 6 |
| Commerce | 0.75 | 0.60 | 0.67 | 5 |
| Education | 0.56 | 1.00 | 0.71 | 5 |
| Environmental Protection | 0.67 | 0.80 | 0.73 | 5 |
| Science, Technology, Communications | 0.80 | 0.80 | 0.80 | 5 |
| Energy | 0.50 | 0.50 | 0.50 | 4 |
| Labor and Employment | 0.33 | 0.50 | 0.40 | 4 |
| Civil Rights and Liberties, Minority Issues | 0.75 | 1.00 | 0.86 | 3 |
| Congress | 0.50 | 0.33 | 0.40 | 3 |
| Economics and Public Finance | 0.10 | 0.33 | 0.15 | 3 |
| Emergency Management | 1.00 | 1.00 | 1.00 | 3 |
| Families | 0.00 | 0.00 | 0.00 | 3 |
| Foreign Trade and International Finance | 0.50 | 0.33 | 0.40 | 3 |
| Housing and Community Development | 0.75 | 1.00 | 0.86 | 3 |
| Law | 1.00 | 0.33 | 0.50 | 3 |
| Native Americans | 1.00 | 1.00 | 1.00 | 3 |
| Social Welfare | 0.40 | 0.67 | 0.50 | 3 |
| Water Resources Development | 1.00 | 0.33 | 0.50 | 3 |
| Animals | 1.00 | 0.50 | 0.67 | 2 |
| Arts, Culture, Religion | 0.50 | 1.00 | 0.67 | 2 |
| Sports and Recreation | 1.00 | 1.00 | 1.00 | 2 |
