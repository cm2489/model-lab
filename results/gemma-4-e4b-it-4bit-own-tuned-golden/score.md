# gemma-4-e4b-it-4bit-own-tuned-golden

- Model: `models/gemma-4-e4b-it-4bit` (converted here from `google/gemma-4-E4B-it`) (mlx)
- Split: golden, 150 examples
- Date: 2026-10-08T06:33:58-04:00 (Eastern Time)
- Commit: `48fce74-dirty`, prompt short-v1
- Wall time: 29 s

| Run | Model | Backend | Prompt | Split (n) | Accuracy | Macro-F1 | Invalid | p50 / p90 s | tok/s | $ per 1k bills | Date (ET) | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [gemma-4-e4b-it-4bit-own-tuned-golden](gemma-4-e4b-it-4bit-own-tuned-golden/score.md) | `models/gemma-4-e4b-it-4bit` (converted here from `google/gemma-4-E4B-it`) + LoRA `policy-area-gemma-own` | mlx | short | golden (150) | 70.7% | 0.68 | 0.0% | 0.17 / 0.22 | 83 | $0.00 | 2026-10-08 06:33 | `48fce74-dirty` |

Correct 106 of 150. Invalid replies: 0 (counted as wrong).
How replies ended: stop 150. A reply that hit max_tokens was cut off.
Cost: local run: $0 marginal cost (hardware and electricity not counted). Average tokens per bill: 62.6 in, 3.7 out.

## Top confusions (gold → predicted)

| Gold | Predicted | Count |
|---|---|---|
| Health | Social Welfare | 3 |
| Arts, Culture, Religion | Congress | 2 |
| International Affairs | Foreign Trade and International Finance | 2 |
| Government Operations and Politics | Congress | 2 |
| Law | Congress | 2 |
| Armed Forces and National Security | Congress | 2 |
| Water Resources Development | Public Lands and Natural Resources | 1 |
| Immigration | Transportation and Public Works | 1 |
| Science, Technology, Communications | Congress | 1 |
| Agriculture and Food | Environmental Protection | 1 |

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Health | 0.90 | 0.75 | 0.82 | 12 |
| Armed Forces and National Security | 1.00 | 0.70 | 0.82 | 10 |
| Government Operations and Politics | 1.00 | 0.56 | 0.71 | 9 |
| Taxation | 1.00 | 0.78 | 0.88 | 9 |
| Crime and Law Enforcement | 0.86 | 0.86 | 0.86 | 7 |
| International Affairs | 1.00 | 0.43 | 0.60 | 7 |
| Agriculture and Food | 0.57 | 0.67 | 0.62 | 6 |
| Finance and Financial Sector | 0.83 | 0.83 | 0.83 | 6 |
| Immigration | 0.80 | 0.67 | 0.73 | 6 |
| Transportation and Public Works | 0.75 | 0.50 | 0.60 | 6 |
| Commerce | 1.00 | 0.60 | 0.75 | 5 |
| Education | 0.83 | 1.00 | 0.91 | 5 |
| Environmental Protection | 0.67 | 0.80 | 0.73 | 5 |
| Public Lands and Natural Resources | 0.57 | 0.80 | 0.67 | 5 |
| Science, Technology, Communications | 0.67 | 0.40 | 0.50 | 5 |
| Energy | 0.50 | 1.00 | 0.67 | 4 |
| Labor and Employment | 0.75 | 0.75 | 0.75 | 4 |
| Civil Rights and Liberties, Minority Issues | 1.00 | 1.00 | 1.00 | 3 |
| Congress | 0.18 | 1.00 | 0.30 | 3 |
| Economics and Public Finance | 0.60 | 1.00 | 0.75 | 3 |
| Emergency Management | 1.00 | 0.67 | 0.80 | 3 |
| Families | 1.00 | 1.00 | 1.00 | 3 |
| Foreign Trade and International Finance | 0.33 | 0.33 | 0.33 | 3 |
| Housing and Community Development | 1.00 | 1.00 | 1.00 | 3 |
| Law | 0.00 | 0.00 | 0.00 | 3 |
| Native Americans | 1.00 | 1.00 | 1.00 | 3 |
| Social Welfare | 0.43 | 1.00 | 0.60 | 3 |
| Water Resources Development | 0.00 | 0.00 | 0.00 | 3 |
| Animals | 1.00 | 1.00 | 1.00 | 2 |
| Arts, Culture, Religion | 0.00 | 0.00 | 0.00 | 2 |
| Sports and Recreation | 1.00 | 1.00 | 1.00 | 2 |
