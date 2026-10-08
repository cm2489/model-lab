# Model Lab

Hands-on labs for customizing open-weight language models: run one, test it, fine-tune it, serve it, and write up what the numbers say.

Every lab ends in something public. The work runs on a 32 GB Apple-silicon Mac plus a few dollars of rented compute.

## The task

Read the official title of a US bill and name its policy area: one of 32 fixed labels from Congress.gov, such as "Health" or "Taxation". The titles and the labels both come from the public record, so anyone can rebuild the dataset with one command.

## The labs

| Lab | You ship | Status |
|---|---|---|
| [0 · Setup](labs/00-setup/README.md) | Your Mac's measured speed and memory | ready |
| [1 · Evals first](labs/01-evals-first/README.md) | A public eval harness with a pass/fail gate | ready |
| [2 · First fine-tune](labs/02-first-fine-tune/README.md) | A fine-tuned model and model card | ready |
| 3 · Hosted fine-tune | A cost, quality and speed comparison | planned |
| 4 · Serve it | A working endpoint and a cost-per-request table | planned |
| 5 · Case study | A case study and a recorded walkthrough | planned |

"Ready" means every step that can run without your own accounts was run by the lab's builder and re-run from the page by an agent that did not write it. Steps that need your accounts are marked on the page. See [`ROADMAP.md`](ROADMAP.md).

## Scores so far

The live table is [`results/README.md`](results/README.md). Every row links to its score card, and each run folder holds its predictions.

## Run it yourself

```bash
git clone https://github.com/cm2489/model-lab.git
cd model-lab
uv sync                 # Python 3.12 and mlx-lm
make test               # unit tests, no model needed
make gate               # re-score the committed predictions against the test set
make eval               # score the local base model (downloads 3 GB the first time)
```

`make data` rebuilds the dataset from GovInfo bulk data. No API key is needed.

## What is in here

- `labs/`: the lab pages. Each step has the command, real output from a real run, and a "done when" line.
- `evals/`: the harness. A fixed, named prompt per run, a strict label parser, metrics, and the gate CI runs.
- `tune/`: data preparation and the LoRA training wrapper.
- `data/`: the dataset builder and the train and validation splits. The test set is `evals/golden.jsonl`.
- `results/`: every scored run, with its predictions.
- `bench/`: a small phone page that shows the next step, the flashcards due, and what has shipped.
- `foundations/`: four optional background sessions on how neural networks, training, tokenization and transformers work.
- `research/`: dated, source-linked briefs on the open-weight model landscape and tooling.
- `content/`: the JSON that drives the bench and the `/lab` tutor command.

## Ground rules

- Labels come from public records. No model-written text is used as a training target.
- Models are downloaded only from accounts that can be identified, and the license is read on the original.
- A number in a lab page is copied from a real run. Anything the builder could not run is marked "not verified".
