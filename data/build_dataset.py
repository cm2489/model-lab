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
NEAR_TWIN = 0.8  # a golden title may share at most this word overlap with any other title

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

    Companion bills share a title except for chamber boilerplate: the Senate
    writes "A bill to amend...", the House writes "To amend...". So the key:
      1. lowercases, drops 4-digit years and punctuation, squeezes spaces;
      2. drops a leading "a bill", "a joint resolution", "a concurrent resolution",
         "an original bill" (and the like);
      3. drops a trailing "and for other purposes".
    Companion and reintroduced bills then share one key and land in one split.
    """
    t = title.lower()
    t = re.sub(r"\b(19|20)\d\d\b", " ", t)
    t = " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())
    t = _PREFIX.sub("", t)
    t = _SUFFIX.sub("", t)
    return t.strip()


_PREFIX = re.compile(r"^an? (original )?(bill|joint resolution|concurrent resolution|resolution)\b\s*")
_SUFFIX = re.compile(r"\s*\band for other purposes$")


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


def short_title_key(row: dict) -> str | None:
    """The bill's short title ("Fix Our Forests Act"), normalized, or None if it has none.

    A bill with no short title shows its official title as its display title.
    """
    short = normalize_title(row.get("display_title") or "")
    return short if short and short != normalize_title(row["title"]) else None


def _earliest(rows: list[dict]) -> dict:
    return min(rows, key=lambda r: (r["introduced"], BILL_TYPES.index(r["bill_type"]), r["number"]))


def build_units(bills: list[dict]) -> list[list[dict]]:
    """Group bills that must share a split.

    Step 1: same title key (normalize_title) -> one title group. Only the earliest
            bill of a group is kept; the rest are copies of it.
    Step 2: title groups whose bills share a short title are joined into one unit.
            This catches companions whose official titles differ by a few words.
            Generic short titles ("SAFE Act") also join unrelated bills; that costs
            nothing but keeps them in one split.
    Returns units as lists of title-group representatives, in a fixed order.
    """
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for b in bills:
        groups[normalize_title(b["title"])].append(b)

    parent = {k: k for k in groups}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    by_short: dict[str, str] = {}
    for key in sorted(groups):
        for b in groups[key]:
            s = short_title_key(b)
            if s is None:
                continue
            if s in by_short:
                a, c = find(by_short[s]), find(key)
                if a != c:
                    parent[max(a, c)] = min(a, c)
            else:
                by_short[s] = key

    units: dict[str, list[dict]] = collections.defaultdict(list)
    for key in sorted(groups):
        units[find(key)].append(_earliest(groups[key]))
    return [units[k] for k in sorted(units)]


def split(bills: list[dict], rng: random.Random) -> dict[str, list[dict]]:
    """Assign whole units to golden / valid / train, stratified by label.

    Golden takes one bill per unit (the earliest), so no two golden bills are
    companions. Train and valid keep one bill per distinct title in the unit.
    """
    units = build_units(bills)
    by_label: dict[str, list[int]] = collections.defaultdict(list)
    for i, unit in enumerate(units):
        by_label[_earliest(unit)["policy_area"]].append(i)
    for ids in by_label.values():
        rng.shuffle(ids)

    eligible = {lab: len(ids) for lab, ids in by_label.items() if len(ids) >= MIN_GROUPS_FOR_GOLDEN}
    floor = {lab: GOLDEN_MIN_PER_LABEL for lab in eligible}
    rest = largest_remainder(eligible, GOLDEN_SIZE - sum(floor.values()))
    golden_n = {lab: floor[lab] + rest[lab] for lab in eligible}

    # Word sets of every title, to keep reworded twins out of golden.
    words = [[set(normalize_title(b["title"]).split()) for b in unit] for unit in units]

    def has_twin(i: int) -> bool:
        """True if another unit holds a title sharing >= NEAR_TWIN of its words (Jaccard)."""
        mine = set(normalize_title(_earliest(units[i])["title"]).split())
        for j, ws in enumerate(words):
            if j != i and any(len(mine & w) >= NEAR_TWIN * len(mine | w) for w in ws):
                return True
        return False

    out = {"train": [], "valid": [], "golden": []}
    twins_skipped = 0
    for lab in sorted(by_label):
        ids = by_label[lab]
        g = golden_n.get(lab, 0)
        golden_ids = []
        for i in ids:
            if len(golden_ids) == g:
                break
            if has_twin(i):
                twins_skipped += 1
            else:
                golden_ids.append(i)
        rest_ids = [i for i in ids if i not in golden_ids]
        v = round(len(rest_ids) * VALID_FRACTION)
        out["golden"] += [_earliest(units[i]) for i in golden_ids]
        out["valid"] += [b for i in rest_ids[:v] for b in units[i]]
        out["train"] += [b for i in rest_ids[v:] for b in units[i]]
    split.twins_skipped = twins_skipped
    return out


def leakage(splits: dict[str, list[dict]]) -> dict[str, dict[str, int]]:
    """For each pair of splits, how many title keys and short-title keys they share. All must be 0."""
    out = {}
    for kind, fn in [("title", lambda r: normalize_title(r["title"])), ("short_title", short_title_key)]:
        keys = {name: {fn(r) for r in rows} - {None} for name, rows in splits.items()}
        names = sorted(keys)
        out[kind] = {f"{a}&{b}": len(keys[a] & keys[b]) for i, a in enumerate(names) for b in names[i + 1:]}
    return out


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

    title_keys = collections.defaultdict(set)
    for b in labelled:
        title_keys[normalize_title(b["title"])].add(b["policy_area"])
    conflicting = sum(1 for labs in title_keys.values() if len(labs) > 1)

    rng = random.Random(SEED)
    splits = split(labelled, rng)
    paths = {"train": ROOT / "data/train.jsonl", "valid": ROOT / "data/valid.jsonl",
             "golden": ROOT / "evals/golden.jsonl"}
    for name, rows in splits.items():
        write_jsonl(paths[name], sorted((to_example(r) for r in rows), key=lambda r: r["id"]))

    # Leakage check on the bills as written: no title key and no short title in two splits.
    overlaps = leakage(splits)
    assert all(v == 0 for d in overlaps.values() for v in d.values()), overlaps

    # Summary.
    fetched = min(m["fetched"] for m in manifest.values())
    n_units = len(build_units(labelled))
    print(f"source: GovInfo BILLSTATUS bulk data, congress {CONGRESS}, types {','.join(BILL_TYPES)}")
    print(f"fetched (ET): {fetched}")
    print(f"bills parsed: {len(bills)}   no policy area (dropped): {len(no_area)}   labelled: {len(labelled)}")
    print(f"distinct title keys: {len(title_keys)}   copies folded: {len(labelled) - len(title_keys)}"
          f"   title keys with conflicting labels: {conflicting}")
    print(f"split units (title keys joined by short title): {n_units}"
          f"   golden candidates skipped for a near-twin title: {split.twins_skipped}")
    print(f"split sizes: train {len(splits['train'])}  valid {len(splits['valid'])}  golden {len(splits['golden'])}")
    print(f"shared across splits: {overlaps}")

    label_counts = {name: collections.Counter(r["policy_area"] for r in rows) for name, rows in splits.items()}
    labels = sorted(set().union(*label_counts.values()), key=lambda l: -sum(c[l] for c in label_counts.values()))
    print(f"\n{'label':45} {'train':>6} {'valid':>6} {'golden':>6}")
    for lab in labels:
        print(f"{lab:45} {label_counts['train'][lab]:6} {label_counts['valid'][lab]:6} {label_counts['golden'][lab]:6}")
    print(f"labels: {len(labels)}")

    top, top_n = label_counts["train"].most_common(1)[0]
    gold_hits = label_counts["golden"][top]
    n_train, n_gold = len(splits["train"]), len(splits["golden"])
    print(f"\nmajority class (train): {top} ({top_n / n_train:.1%} of train)")
    print(f"majority-class baseline on golden: {gold_hits}/{n_gold} = {gold_hits / n_gold:.1%}")


if __name__ == "__main__":
    main()
