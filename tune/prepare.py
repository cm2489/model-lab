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
import hashlib
import json
from pathlib import Path

from evals.files import ROOT, read_jsonl
from evals.prompt import build_messages


def title_key():
    """The dataset builder's own title key, so a House bill and its Senate twin count as one title."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_dataset", ROOT / "data" / "build_dataset.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.normalize_title


def to_chat(row: dict) -> dict:
    return {"messages": build_messages(row["title"], "short") + [{"role": "assistant", "content": row["label"]}]}


def stable_order(rows: list[dict], seed: int) -> list[dict]:
    """Order rows by a hash of the seed and the bill id.

    Unlike a shuffle, this order does not depend on which other rows exist. If one
    row is later removed from the dataset, every other row keeps its place, so the
    training files change by that one row and nothing else.
    """
    return sorted(rows, key=lambda r: hashlib.sha256(f"{seed}:{r['id']}".encode()).hexdigest())


def capped(rows: list[dict], per_label: int, seed: int) -> list[dict]:
    by_label = collections.defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)
    out = []
    for label in sorted(by_label):
        out += stable_order(by_label[label], seed)[:per_label]
    return stable_order(out, seed + 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-label", type=int, default=80, help="most training examples kept per label")
    ap.add_argument("--valid", type=int, default=200, help="validation examples kept")
    ap.add_argument("--out", default=str(ROOT / "data" / "lora"))
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)

    train = capped(read_jsonl(ROOT / "data" / "train.jsonl"), args.per_label, args.seed)
    valid = stable_order(read_jsonl(ROOT / "data" / "valid.jsonl"), args.seed)[: args.valid]

    key = title_key()
    golden = {key(r["title"]) for r in read_jsonl(ROOT / "evals" / "golden.jsonl")}
    leaked = [r for r in train + valid if key(r["title"]) in golden]
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
