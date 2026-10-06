# Model Lab: one-command entry points.
#   make data   rebuild the dataset from GovInfo (uses data/cache/ if present)
#   make eval   score the local base model on the golden set
#   make test   unit tests (no model, no network)
#   make gate   the pass/fail gate on the committed baseline predictions (what CI runs)

PY ?= uv run python
MODEL ?= mlx-community/Qwen3.5-4B-4bit
SPLIT ?= golden

# The gate's bar, set from the committed baseline (89/150 = 0.5933, 0 invalid).
# 0.593 sits just under 89/150, so one more miss (88/150 = 0.5867) fails.
# Raise the bar when a better model's predictions become the baseline.
BASELINE ?= results/qwen3.5-4b-4bit-golden-baseline/predictions.jsonl
MIN_ACCURACY ?= 0.593
MAX_INVALID ?= 0.0

# The test set's SHA-256. If evals/golden.jsonl changes, the gate fails until this
# line changes in the same commit, so a reviewer sees the test set moved.
GOLDEN_SHA256 ?= a717155c2c2b268b0cbff56ac57b5428272aaa840aa17c1d3360ef48abd8f319

.PHONY: data eval test gate

data:
	$(PY) data/build_dataset.py

eval:
	$(PY) -m evals.run --backend mlx --model $(MODEL) --split $(SPLIT)

test:
	$(PY) -m unittest discover -s evals/tests -t . -v

gate:
	$(PY) -m evals.gate --predictions $(BASELINE) --min-accuracy $(MIN_ACCURACY) --max-invalid $(MAX_INVALID) --golden-sha256 $(GOLDEN_SHA256)
