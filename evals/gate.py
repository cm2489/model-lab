"""The pass/fail gate. Exits 1 when a predictions file misses the bar.

  uv run python -m evals.gate --predictions results/<run>/predictions.jsonl \\
      --min-accuracy 0.60 --max-invalid 0.02 --golden-sha256 <pinned hash>

Gold labels come from the golden file, not from the predictions file.
Every golden example must have a prediction; a missing one counts as invalid.
Duplicate prediction ids fail the gate.
--golden-sha256 pins the test set: if evals/golden.jsonl changes, the gate fails
until the pinned hash is updated too, so the change shows up in review.
Standard library only, so CI runs it with no packages installed.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from evals import metrics
from evals.files import ROOT, SPLITS, read_jsonl
from evals.labels import LABELS


def check(predictions_path, golden_path, min_accuracy: float, max_invalid: float) -> tuple[bool, dict]:
    golden = read_jsonl(golden_path)
    known = set(LABELS)
    preds = [{**p, "pred": p.get("pred") if p.get("pred") in known else None} for p in read_jsonl(predictions_path)]
    c = metrics.classification(metrics.join(golden, preds))
    ok = c["accuracy"] >= min_accuracy and c["invalid_rate"] <= max_invalid
    return ok, c


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--golden", default=str(SPLITS["golden"]))
    ap.add_argument("--min-accuracy", type=float, required=True, help="fail below this (0 to 1)")
    ap.add_argument("--max-invalid", type=float, required=True, help="fail above this invalid rate (0 to 1)")
    ap.add_argument("--golden-sha256", help="fail unless the golden file has exactly this SHA-256")
    args = ap.parse_args(argv)

    digest = sha256(args.golden)
    shown = Path(args.golden).resolve()
    shown = shown.relative_to(ROOT) if shown.is_relative_to(ROOT) else shown
    print(f"golden file  {shown}  sha256 {digest[:16]}...")
    if args.golden_sha256 and digest != args.golden_sha256:
        print(f"gate: FAIL (golden file changed: expected sha256 {args.golden_sha256})")
        return 1
    try:
        ok, c = check(args.predictions, args.golden, args.min_accuracy, args.max_invalid)
    except ValueError as e:
        print(f"gate: FAIL (bad predictions file: {e})")
        return 1
    acc_ok = c["accuracy"] >= args.min_accuracy
    inv_ok = c["invalid_rate"] <= args.max_invalid
    print(f"accuracy     {c['accuracy']:.4f}  need >= {args.min_accuracy:.4f}  {'PASS' if acc_ok else 'FAIL'}")
    print(f"invalid rate {c['invalid_rate']:.4f}  need <= {args.max_invalid:.4f}  {'PASS' if inv_ok else 'FAIL'}")
    print(f"gate: {'PASS' if ok else 'FAIL'} ({c['correct']}/{c['n']} correct, {c['invalid']} invalid)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
