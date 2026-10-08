# Roadmap

All dates are Eastern Time. Pace: 8 or more hours a week, starting Wednesday October 7, 2026.

Status words: **planned** (not built), **draft** (built, not yet re-run by an independent agent), **ready** (verified, do it), **done**, **blocked**, **proposed** (waits for the owner's OK).

## Track 1 · Open-weight model customization

| Lab | You ship | Hours | Target week | Status |
|---|---|---|---|---|
| 0 · Setup | Your Mac's measured speed and memory | 1.5 | Oct 7 | ready |
| 1 · Evals first | Public eval harness with a pass/fail gate | 4.7 | Oct 7 to 13 | ready |
| 2 · First fine-tune | Fine-tuned model and model card on Hugging Face | 4.8 | Oct 12 to 18 | ready |
| 3 · Hosted fine-tune | Comparison write-up (up to $10) | 4 | Oct 16 to 21 | planned |
| 4 · Serve it | Working endpoint and a cost-per-request table (up to $5) | 3.7 | Oct 21 to 25 | planned |
| 5 · Case study | Case study and a recorded walkthrough | 3.5 | Oct 25 to 28 | planned |

Hours are estimates and have not been measured. Labs 3 to 5 are built after Lab 2 ships, with prices re-checked that week.

**The task.** Tag US bills by policy area. The text and the labels both come from the public record on Congress.gov.

**The models.** Two side by side, labelled by origin: Gemma 4 E4B (Google, Apache-2.0) and Qwen3.5-4B (Alibaba, Apache-2.0).

**The stand-out bar** for the finished work. It must show something a tutorial cannot:

1. Real data from a live product, not a toy dataset.
2. One table: base model, tuned model and a frontier model, scored on accuracy, cost per 1,000 bills and speed.
3. A model swap done in a day (US model for Chinese model, same harness).
4. An eval harness anyone can run with one command.
5. A five-minute walkthrough a non-technical buyer can follow.

## Gates

| Date | Gate | Status |
|---|---|---|
| Thu Oct 8 | State of AI Report 2026 is published. Refresh the landscape research against it. | planned |
| Fri Oct 9 | Decide whether public build-log posts start. | planned |
| Tue Oct 13 | Count sessions for the week. Five or more turns on the weekly landscape run. | planned |

## Waiting on the owner

- Close the API-key exposure on the old course app. Done together in Chrome.
- Turn off the two old scheduled tasks, if they still run. Done together.
- Create a Hugging Face account before Lab 2, step 7.

## Depth phase · approved October 7, 2026, built after Lab 5

After Lab 5, this phase repeats the loop on harder problems, aimed at what open-model job postings ask for. The owner approved this list as written on October 7, 2026. Each item is built as its own lab, in this order unless he changes it.

- Serving under load: vLLM or SGLang, batching, throughput, cost per token.
- Quantization: what each level costs in accuracy, measured on the golden set.
- Preference and reinforcement fine-tuning (DPO, GRPO) on a task with a checkable reward.
- Eval design in depth: error analysis, LLM judges and their biases, regression gates.
- Distillation from an open teacher model.
- A second task: structured extraction, harder than tagging.

## Later tracks · start after Track 1

Short briefs, one to three hours each.

- Security for agents: prompt injection, permissions, supply chain.
- Inference costs.
- The Colorado AI law (SB 26-189) for real-estate work.
- Voice agents, as applied work for travel and real estate.
- Quantum computing: literacy in early 2027, about 10 to 15 hours, with an optional post-quantum cryptography mini-project.

## Landscape research

- `research/2026-10-06/` holds the checked research this roadmap was built on.
- Refreshed on request. A weekly run starts if the October 13 gate is met.
