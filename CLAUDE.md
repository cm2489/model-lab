# CLAUDE.md · Model Lab

The owner's session contract (in his global `~/.claude/CLAUDE.md`) applies in this project. This file adds this project's rules. Only the owner changes this file.

## Named files

- **Rule file:** this `CLAUDE.md`.
- **Roadmap:** `ROADMAP.md`.
- **Content contract:** `content/SCHEMA.md`.

## What the owner settled on 2026-10-06

His words, from the Model Lab Report:

> "I don't care about the look on this so you can take over that without my approval. I don't mind if this is public since it's just my learning unless you think otherwise. I don't want to hold you back by anything like that since this is all just for my learning for now."

> "I'd also like to make the time in everything we do my time zone not UTC."

What that changes here. These four lines are Claude's reading of his words, and he can strike any of them.

1. **Look and wording.** In this project, design and wording changes do not wait for his eyes. They merge when checks pass and an agent that did not write them has verified them.
2. **Public.** This repository is public.
3. **Lab sittings.** `/lab` is a standing routine. A lab sitting needs no question round, no plan and no Report. It may write `progress.json` and `labs/*/NOTES.md` on a `progress/<date>` branch and merge that pull request itself once checks pass.
4. **Times.** Every date and time is Eastern Time.

## Rules that stay strict

1. **Privacy.** The repository is public. Nothing about the owner's job search, income, health, other projects or clients goes in it. `private/` is local and never committed. No keys, tokens or secrets. Agents never read `.env` files.
2. **Training data.** Outputs of closed models (Claude, GPT, Gemini) are never used as training targets. Labels come from public records or from people.
3. **Models.** Download only from organization accounts that can be identified (for example `google`, `Qwen`, `mlx-community`, `unsloth`, `meta-models`). Read the license before a model enters a lab. Apache-2.0 or MIT unless he says otherwise.
4. **Money.** He pays from his own accounts. The cap through December 11, 2026 is $25: hosted fine-tune up to $10, rented GPU up to $5, frontier-model baseline up to $2. Any other spend is told to him first and does not happen until he says yes.
5. **A lab is `ready` only when** its builder ran every step and a different agent re-ran every step from the page. A step that needs his paid accounts or tokens is marked "not verified" until he runs it.
6. **Disk.** One small 4-bit model at a time until the disk has room. Check free space before any download over 1 GB.
7. **Claims.** Nothing is described as shipped, here or anywhere else, until it is public and working.
8. **The old course.** `~/Documents/Claude/Projects/AI/ML Guided Learning` is read-only reference material.

## How to work here

- Python runs through uv: `uv sync`, then `uv run …`. Python 3.12.
- Checks before any merge: `uv run python scripts/validate_content.py`, `make test`, and `node --test` in `bench/`.
- Lab pages are written for a reader who wants the action first: lead with the action, one bounded action per numbered step, a time estimate, the exact command, a "You should see" block pasted from a real run, one check question, and a "Done when" line.
- A step the learner will run by hand is never handed over unverified.
