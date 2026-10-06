# Data: US bills and their policy areas

## Where it comes from

- **Source:** GovInfo bulk data, bill status files for the 119th Congress (2025 to 2027).
  `https://www.govinfo.gov/bulkdata/BILLSTATUS/119/<type>/BILLSTATUS-119-<type>.zip`.
  Public record, no account or API key. About 48 MB of zips.
- **Fetched:** 2026-10-06 14:19 Eastern Time (`2026-10-06T14:19:40-04:00`).
- **Bill types used:** `hr`, `s`, `hjres`, `sjres`, `hconres`, `sconres`. Simple resolutions
  (`hres`, `sres`) are left out: most are one-chamber statements, not policy.
- **Input:** the bill's official title as introduced ("To amend the Internal Revenue Code…").
  If a bill has none, its display title is used.
- **Label:** the bill's one policy area (`<bill><policyArea><name>`), assigned by the Library
  of Congress. There are 32 policy areas. 31 appear here: no 119th-Congress bill in these
  types carries "Social Sciences and History".

US government works are public domain. The three JSONL files are committed so the labs work offline.

## The files

| File | Rows | What it is for |
|---|---|---|
| `data/train.jsonl` | 11,647 | Training (Lab 2). |
| `data/valid.jsonl` | 1,280 | Watching training (Lab 2). |
| `evals/golden.jsonl` | 150 | The test set. Never train on it. |

Each row: `id`, `title`, `label`, `bill_type`, `congress`, `url` (the bill on Congress.gov).

## How it was built (`data/build_dataset.py`)

1. Parse 17,007 bill status files. Drop 396 with no policy area yet (new bills get one later). 16,611 remain.
2. **Title key.** House and Senate companions carry the same title apart from boilerplate:
   the Senate writes "A bill to amend…", the House writes "To amend…". The key lowercases,
   drops punctuation and 4-digit years, drops a leading "a bill", "a joint resolution",
   "a concurrent resolution" or "an original bill", and drops a trailing "and for other purposes".
   Bills with the same key are copies; only the earliest is kept.
3. **Split units.** Title keys whose bills share a short title ("Fix Our Forests Act") join into
   one unit. This catches companions whose official titles differ by a few words. A whole unit
   goes to one split. Generic short titles ("SAFE Act") also join unrelated bills; that costs nothing.
4. **Golden.** 150 units, one bill each, stratified: every label with at least 10 units gets at
   least 2, the rest in proportion to label size. A candidate is skipped if any other title in
   the data shares 80% or more of its words (a reworded twin). Valid: 10% of the remaining units
   per label. Train: the rest. Train and valid keep one bill per title key in each unit.
5. Fixed seed (`20261006`). The same download always gives the same files. The script asserts
   that no title key and no short title appears in two splits, checked on the rows as written.

### What was folded, pattern by pattern

Measured on the 16,611 labelled bills, each step on top of the one before:

| Pattern | Rows folded |
|---|---|
| Identical title text | 322 |
| Same up to letter case | 3 |
| Same up to punctuation | 1 |
| Same up to a 4-digit year ("Act of 2025") | 24 |
| Same up to "A bill" / "A joint resolution" / "A concurrent resolution" prefix | 3,095 |
| Same up to a trailing "and for other purposes" | 78 |
| Same up to a session marker ("119th Congress") | 0 (none occur) |
| **Total copies folded** | **3,523** |

That leaves 13,088 title keys. 86 of them hold bills with different labels; the earliest bill's label wins.
Short titles then join the 13,088 keys into 12,411 split units. 12 golden candidates were skipped
for a reworded twin. 11 title keys drop out because their unit went to golden, which keeps one bill per unit.

**What is left, checked by hand.** 9 golden titles share 70% to 80% of their words with a train or
valid title. They are sibling bills amending the same law in different ways ("…title XVIII of the
Social Security Act to allow…" next to "…to provide for…"), not copies. They stay.

## The honest floor

| Baseline | Golden accuracy |
|---|---|
| Always answer the biggest label (Health, 11.0% of train) | 12/150 = 8.0% |
| Guess one of 32 labels at random | about 3% |

The golden set is stratified, so rare labels count for more than they do in real traffic.
That is why the majority baseline is 8.0% here and 11.0% on the natural mix.

## Is title-only too easy or too hard?

Neither, which makes it a good test. Many titles name their topic outright. But the labels follow
Congress.gov conventions a model has to learn: tax-code changes are "Taxation" even when the subject
is housing, a Water Resources Development Act project is "Water Resources Development" even when it
mentions public health. Some titles don't carry enough information at all. A 4B model with only a
prompt scored 56.7% (see `results/README.md`), far above the floor and far below perfect.

## Rebuild it

```bash
make data                                     # uses data/cache/ if it is there
rm -rf data/cache && make data                # download again from GovInfo (about 48 MB)
```

The bulk data changes every day: new bills arrive and new policy areas are assigned.
A fresh download gives different splits. The labs use the committed files. Rebuild
only on purpose, then re-run every score, because old and new scores are not comparable.
The gate pins the golden file's SHA-256 (`GOLDEN_SHA256` in the `Makefile`), so a changed
test set fails CI until that line changes too.

`data/cache/` (gitignored) holds the zips, a `manifest.json` with the fetch times, and
`bills.csv`, the clean table of all 16,611 labelled bills.
