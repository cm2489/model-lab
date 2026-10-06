"""Print a sample of wrong predictions, for error analysis.

  uv run python -m evals.misses results/<run>/predictions.jsonl --n 30

The sample is shuffled with a fixed seed, so you and anyone else see the same 30.
Each miss shows the gold label, the model's answer, the title and the Congress.gov link.
"""

from __future__ import annotations

import argparse
import random
import sys

from evals.files import SPLITS, read_jsonl


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("predictions")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--golden", default=str(SPLITS["golden"]))
    args = ap.parse_args(argv)

    gold = {g["id"]: g for g in read_jsonl(args.golden)}
    preds = {p["id"]: p for p in read_jsonl(args.predictions)}
    misses = [(g, preds.get(i, {})) for i, g in gold.items() if preds.get(i, {}).get("pred") != g["label"]]
    random.Random(args.seed).shuffle(misses)

    print(f"{len(misses)} misses out of {len(gold)}. Showing {min(args.n, len(misses))}.\n")
    for k, (g, p) in enumerate(misses[: args.n], 1):
        print(f"{k:2}. {g['id']}")
        print(f"    gold:  {g['label']}")
        print(f"    model: {p.get('pred') or 'INVALID (raw: ' + repr(p.get('raw', ''))[:60] + ')'}")
        print(f"    title: {g['title']}")
        print(f"    {g['url']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
