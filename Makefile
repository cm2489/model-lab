# Model Lab: one-command entry points.
#   make data   rebuild the dataset from GovInfo (uses data/cache/ if present)
#   make eval   score the local base model on the golden set
#   make test   unit tests (no model, no network)
#   make gate   the pass/fail gate on the committed baseline predictions (what CI runs)

PY ?= uv run python
MODEL ?= mlx-community/Qwen3.5-4B-4bit
SPLIT ?= golden

# The gate's bar. Set from the committed baseline run; see results/README.md.
BASELINE ?= results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl
MIN_ACCURACY ?= 0.0
MAX_INVALID ?= 1.0

.PHONY: data eval test gate

data:
	$(PY) data/build_dataset.py

eval:
	$(PY) -m evals.run --backend mlx --model $(MODEL) --split $(SPLIT)

test:
	$(PY) -m unittest discover -s evals/tests -t . -v

gate:
	$(PY) -m evals.gate --predictions $(BASELINE) --min-accuracy $(MIN_ACCURACY) --max-invalid $(MAX_INVALID)
