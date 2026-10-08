---
base_model: Qwen/Qwen3.5-4B
library_name: mlx
license: apache-2.0
tags:
  - lora
  - text-classification
  - legislation
language:
  - en
---

# Policy-area tagger for US bills (LoRA adapter for Qwen3.5-4B)

One sentence: what this is and who it is for.

## What it does

Given the official title of a US bill, it replies with one Congress.gov policy area (for example "Health" or "Taxation").

- **Base model:** `Qwen/Qwen3.5-4B` (Apache-2.0), run as `mlx-community/Qwen3.5-4B-4bit` on Apple silicon.
- **This repository holds:** a LoRA adapter only. It is FILL_IN MB. The base model is unchanged.
- **Prompt it was trained with:**

  ```
  Which Congress.gov policy area does this bill belong to? Reply with the policy area only.

  Bill title:
  <the title>
  ```

## Results

Scored on 150 held-out bills that the model never trained on. Invalid replies count as wrong.

| Model | Prompt | Accuracy | Macro-F1 | Invalid | Seconds per bill (p50) | Prompt tokens per bill |
|---|---|---|---|---|---|---|
| Qwen3.5-4B, 4-bit, no tuning | lists all 32 labels | FILL_IN | FILL_IN | FILL_IN | FILL_IN | FILL_IN |
| Qwen3.5-4B, 4-bit, no tuning | short, no label list | FILL_IN | FILL_IN | FILL_IN | FILL_IN | FILL_IN |
| **This adapter** | short, no label list | FILL_IN | FILL_IN | FILL_IN | FILL_IN | FILL_IN |
| Frontier model (name it) | lists all 32 labels | FILL_IN | FILL_IN | FILL_IN | FILL_IN | FILL_IN |

The harness, the test set and every prediction are public: https://github.com/cm2489/model-lab

## Training

- **Data:** official titles and policy areas of bills in the 119th Congress, from GovInfo bulk data (public record). FILL_IN training examples, at most 80 per label. No model-written text was used as a training target.
- **Method:** LoRA, rank 8, 8 layers, batch size 1 with gradient accumulation 4, learning rate 1e-4, FILL_IN steps, loss on the reply only.
- **Hardware and time:** FILL_IN (your Mac), FILL_IN minutes, FILL_IN GB peak memory.

## Limits

Write these honestly. A reader trusts a card that names its limits.

- It reads the title only. Titles that say little ("A bill to amend title 5…") are guesses.
- It learned the 119th Congress. Older or state bills are untested.
- Labels with few examples are weaker. Name the two worst labels from your per-label table.
- FILL_IN: one failure you saw yourself.

## How to run it

```bash
uv run mlx_lm.generate --model mlx-community/Qwen3.5-4B-4bit \
  --adapter-path <folder with this adapter> \
  --chat-template-config '{"enable_thinking": false}' --max-tokens 24 \
  --prompt "Which Congress.gov policy area does this bill belong to? Reply with the policy area only.

Bill title:
Health Care for Homeless Veterans Act"
```
