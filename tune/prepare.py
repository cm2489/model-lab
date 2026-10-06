"""Turn the labelled bills into chat-format training files for mlx_lm.lora.

  uv run python -m tune.prepare

Writes data/lora/train.jsonl and data/lora/valid.jsonl. Each line is one chat:
the short prompt with a bill title, then the policy area as the reply.

Two choices matter here:
- The prompt is the short one (evals.prompt, style "short"), with no label list.
  The model learns the label names from the replies, so it does not need them
  repeated in every prompt. Shorter examples also train faster and use far less memory.
- Rows are capped per label (default 80). Uncapped, "Health" would have about
  50 times the examples of the rarest label and the model would lean on it.

The golden test set is never read here. data/build_dataset.py already keeps
its titles out of train and valid.
"""

from __future__ import annotations

import argparse
import collections
import json
import random
from pathlib import Path

from evals.files import ROOT, read_jsonl
from evals.prompt import build_messages


def to_chat(row: dict) -> dict:
    return {"messages": build_messages(row["title"], "short") + [{"role": "assistant", "content": row["label"]}]}


def capped(rows: list[dict], per_label: int, rng: random.Random) -> list[dict]:
    by_label = collections.defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)
    out = []
    for label in sorted(by_label):
        group = by_label[label]
        rng.shuffle(group)
        out += group[:per_label]
    rng.shuffle(out)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-label", type=int, default=80, help="most training examples kept per label")
    ap.add_argument("--valid", type=int, default=200, help="validation examples kept")
    ap.add_argument("--out", default=str(ROOT / "data" / "lora"))
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    train = capped(read_jsonl(ROOT / "data" / "train.jsonl"), args.per_label, rng)
    valid = read_jsonl(ROOT / "data" / "valid.jsonl")
    rng.shuffle(valid)
    valid = valid[: args.valid]

    golden = {" ".join(r["title"].lower().split()) for r in read_jsonl(ROOT / "evals" / "golden.jsonl")}
    leaked = [r for r in train + valid if " ".join(r["title"].lower().split()) in golden]
    if leaked:
        raise SystemExit(f"{len(leaked)} training titles are also in the golden set. Rebuild the dataset.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train", train), ("valid", valid)):
        with open(out / f"{name}.jsonl", "w") as f:
            for row in rows:
                f.write(json.dumps(to_chat(row), ensure_ascii=False) + "\n")

    counts = collections.Counter(r["label"] for r in train)
    print(f"train: {len(train)} examples, {len(counts)} labels, "
          f"{min(counts.values())} to {max(counts.values())} per label")
    print(f"valid: {len(valid)} examples")
    print(f"golden titles in train or valid: {len(leaked)}")
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}/train.jsonl and valid.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
