"""Build the bill policy-area dataset from GovInfo bulk data.

Source: GovInfo BILLSTATUS bulk data for the 119th Congress (no API key).
    https://www.govinfo.gov/bulkdata/BILLSTATUS/119/<type>/BILLSTATUS-119-<type>.zip

Output (all deterministic for a given download):
    data/cache/bills.csv  the clean table, one row per labelled bill (not committed)
    data/train.jsonl      training examples (Lab 2 fine-tunes on these)
    data/valid.jsonl      validation examples (Lab 2 watches these during training)
    evals/golden.jsonl    the test set; never train on it

Run:  uv run python data/build_dataset.py            (uses data/cache/ if present)
      uv run python data/build_dataset.py --refresh  (downloads again)
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
CONGRESS = 119
# Bills and joint/concurrent resolutions. Simple resolutions (hres, sres) are left
# out: most are one-chamber statements (commemorations, rules), not policy.
BILL_TYPES = ["hr", "s", "hjres", "sjres", "hconres", "sconres"]
URL = "https://www.govinfo.gov/bulkdata/BILLSTATUS/{c}/{t}/BILLSTATUS-{c}-{t}.zip"

SEED = 20261006
GOLDEN_SIZE = 150
GOLDEN_MIN_PER_LABEL = 2  # every label with enough titles gets at least this many
MIN_GROUPS_FOR_GOLDEN = 10  # a label needs this many distinct titles to be "enough"
VALID_FRACTION = 0.10

ET_TZ = ZoneInfo("America/New_York")


def download(refresh: bool) -> dict:
    """Download one zip per bill type into data/cache/. Returns the fetch manifest."""
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest_path = CACHE / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for t in BILL_TYPES:
        dest = CACHE / f"BILLSTATUS-{CONGRESS}-{t}.zip"
        if dest.exists() and not refresh:
            continue
        url = URL.format(c=CONGRESS, t=t)
        print(f"downloading {url}", file=sys.stderr)
        req = urllib.request.Request(url, headers={"User-Agent": "model-lab dataset builder"})
        with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
            f.write(r.read())
        manifest[t] = {
            "url": url,
            "fetched": datetime.now(ET_TZ).isoformat(timespec="seconds"),
            "bytes": dest.stat().st_size,
        }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def parse_bill(xml_bytes: bytes) -> dict | None:
    """Pull the fields we need out of one BILLSTATUS XML file."""
    bill = ET.fromstring(xml_bytes).find("bill")
    if bill is None:
        return None
    official = None
    for item in bill.findall("titles/item"):
        if item.findtext("titleType") == "Official Title as Introduced":
            official = (item.findtext("title") or "").strip()
            break
    bill_type = (bill.findtext("type") or "").lower()
    number = (bill.findtext("number") or "").strip()
    return {
        "id": f"{bill_type}{number}-{bill.findtext('congress')}",
        "congress": int(bill.findtext("congress") or 0),
        "bill_type": bill_type,
        "number": int(number or 0),
        "title": official or (bill.findtext("title") or "").strip(),
        "display_title": (bill.findtext("title") or "").strip(),
        # Direct child only: related bills carry their own policyArea elsewhere.
        "policy_area": (bill.findtext("policyArea/name") or "").strip(),
        "introduced": bill.findtext("introducedDate") or "",
    }


def load_bills() -> list[dict]:
    rows = []
    for t in BILL_TYPES:
        with zipfile.ZipFile(CACHE / f"BILLSTATUS-{CONGRESS}-{t}.zip") as z:
            for name in sorted(z.namelist()):
                if name.endswith(".xml"):
                    row = parse_bill(z.read(name))
                    if row:
                        rows.append(row)
    return rows


def normalize_title(title: str) -> str:
    """Key used to keep look-alike titles in one split.

    Lowercase, drop years and punctuation, squeeze spaces. Companion bills
    (House and Senate versions) and reintroduced bills share this key.
    """
    t = title.lower()
    t = re.sub(r"\b(19|20)\d\d\b", " ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def congress_url(row: dict) -> str:
    kind = {
        "hr": "house-bill", "s": "senate-bill", "hjres": "house-joint-resolution",
        "sjres": "senate-joint-resolution", "hconres": "house-concurrent-resolution",
        "sconres": "senate-concurrent-resolution",
    }[row["bill_type"]]
    return f"https://www.congress.gov/bill/{row['congress']}th-congress/{kind}/{row['number']}"


def largest_remainder(weights: dict[str, float], total: int) -> dict[str, int]:
    """Split `total` across keys in proportion to `weights` (whole numbers)."""
    s = sum(weights.values())
    raw = {k: total * w / s for k, w in weights.items()}
    out = {k: int(v) for k, v in raw.items()}
    leftover = total - sum(out.values())
    for k in sorted(raw, key=lambda k: (-(raw[k] - out[k]), k))[:leftover]:
        out[k] += 1
    return out


def split(groups: dict[str, list[dict]], rng: random.Random):
    """Assign whole title groups to golden / valid / train, stratified by label."""
    # One representative per group: the earliest bill. Its own label is the target.
    reps = {}
    for key, rows in groups.items():
        rows.sort(key=lambda r: (r["introduced"], BILL_TYPES.index(r["bill_type"]), r["number"]))
        reps[key] = rows[0]

    by_label: dict[str, list[str]] = collections.defaultdict(list)
    for key in sorted(reps):
        by_label[reps[key]["policy_area"]].append(key)
    for keys in by_label.values():
        rng.shuffle(keys)

    eligible = {lab: len(k) for lab, k in by_label.items() if len(k) >= MIN_GROUPS_FOR_GOLDEN}
    floor = {lab: GOLDEN_MIN_PER_LABEL for lab in eligible}
    rest = largest_remainder(eligible, GOLDEN_SIZE - sum(floor.values()))
    golden_n = {lab: floor[lab] + rest[lab] for lab in eligible}

    golden, valid, train = [], [], []
    for lab in sorted(by_label):
        keys = by_label[lab]
        g = golden_n.get(lab, 0)
        v = round((len(keys) - g) * VALID_FRACTION)
        golden += keys[:g]
        valid += keys[g:g + v]
        train += keys[g + v:]
    return reps, golden, valid, train


def to_example(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "label": row["policy_area"],
        "bill_type": row["bill_type"],
        "congress": row["congress"],
        "url": congress_url(row),
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="download the zips again")
    args = ap.parse_args()

    manifest = download(args.refresh)
    bills = load_bills()
    no_area = [b for b in bills if not b["policy_area"]]
    labelled = [b for b in bills if b["policy_area"] and b["title"]]

    # Clean table: one row per bill, every labelled bill.
    with open(CACHE / "bills.csv", "w", newline="") as f:
        cols = ["id", "congress", "bill_type", "number", "introduced", "policy_area", "title", "display_title"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for b in sorted(labelled, key=lambda b: (BILL_TYPES.index(b["bill_type"]), b["number"])):
            w.writerow(b)

    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for b in labelled:
        groups[normalize_title(b["title"])].append(b)
    conflicting = sum(1 for rows in groups.values() if len({r["policy_area"] for r in rows}) > 1)

    rng = random.Random(SEED)
    reps, golden, valid, train = split(groups, rng)
    splits = {"train": train, "valid": valid, "golden": golden}
    paths = {"train": ROOT / "data/train.jsonl", "valid": ROOT / "data/valid.jsonl",
             "golden": ROOT / "evals/golden.jsonl"}
    for name, keys in splits.items():
        rows = sorted((to_example(reps[k]) for k in keys), key=lambda r: r["id"])
        write_jsonl(paths[name], rows)

    # Leakage check: no normalized title may appear in two splits.
    seen = {name: set(keys) for name, keys in splits.items()}
    overlaps = {f"{a}&{b}": len(seen[a] & seen[b]) for a, b in [("train", "valid"), ("train", "golden"), ("valid", "golden")]}
    assert all(v == 0 for v in overlaps.values()), overlaps

    # Summary.
    fetched = min(m["fetched"] for m in manifest.values())
    print(f"source: GovInfo BILLSTATUS bulk data, congress {CONGRESS}, types {','.join(BILL_TYPES)}")
    print(f"fetched (ET): {fetched}")
    print(f"bills parsed: {len(bills)}   no policy area (dropped): {len(no_area)}   labelled: {len(labelled)}")
    print(f"distinct normalized titles: {len(groups)}   duplicate-title bills folded: {len(labelled) - len(groups)}"
          f"   title groups with conflicting labels: {conflicting}")
    print(f"split sizes: train {len(train)}  valid {len(valid)}  golden {len(golden)}")
    print(f"shared normalized titles across splits: {overlaps}")

    label_counts = {name: collections.Counter(reps[k]["policy_area"] for k in keys) for name, keys in splits.items()}
    labels = sorted(set().union(*label_counts.values()), key=lambda l: -sum(c[l] for c in label_counts.values()))
    print(f"\n{'label':45} {'train':>6} {'valid':>6} {'golden':>6}")
    for lab in labels:
        print(f"{lab:45} {label_counts['train'][lab]:6} {label_counts['valid'][lab]:6} {label_counts['golden'][lab]:6}")
    print(f"labels: {len(labels)}")

    top, top_n = label_counts["train"].most_common(1)[0]
    gold_hits = label_counts["golden"][top]
    print(f"\nmajority class (train): {top} ({top_n / len(train):.1%} of train)")
    print(f"majority-class baseline on golden: {gold_hits}/{len(golden)} = {gold_hits / len(golden):.1%}")


if __name__ == "__main__":
    main()
