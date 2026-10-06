# Model Lab: one-command entry points.
#   make data   rebuild the dataset from GovInfo (uses data/cache/ if present)
#   make eval   score the local base model on the golden set
#   make test   unit tests (no model, no network)
#   make tune-data   build the chat-format training files for Lab 2
#   make tune        fine-tune with LoRA (Lab 2 defaults: batch 1, 1,200 steps)
#   make eval-tuned  score the tuned model on the golden set with the short prompt
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

ADAPTER ?= adapters/policy-area

.PHONY: data eval test gate tune-data tune eval-tuned

data:
	$(PY) data/build_dataset.py

eval:
	$(PY) -m evals.run --backend mlx --model $(MODEL) --split $(SPLIT)

test:
	$(PY) -m unittest discover -s evals/tests -t . -v
	$(PY) -m unittest tune.test_prepare -v

gate:
	$(PY) -m evals.gate --predictions $(BASELINE) --min-accuracy $(MIN_ACCURACY) --max-invalid $(MAX_INVALID)

tune-data:
	$(PY) -m tune.prepare

tune:
	$(PY) -m tune.train

eval-tuned:
	$(PY) -m evals.run --backend mlx --model $(MODEL) --adapter-path $(ADAPTER) --prompt short --split $(SPLIT)
