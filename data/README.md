# Data: US bills and their policy areas

## Where it comes from

- **Source:** GovInfo bulk data, bill status files for the 119th Congress (2025 to 2027).
  `https://www.govinfo.gov/bulkdata/BILLSTATUS/119/<type>/BILLSTATUS-119-<type>.zip`.
  Public record, no account or API key.
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
| `data/train.jsonl` | 14,498 | Training (Lab 2). |
| `data/valid.jsonl` | 1,613 | Watching training (Lab 2). |
| `evals/golden.jsonl` | 150 | The test set. Never train on it. |

Each row: `id`, `title`, `label`, `bill_type`, `congress`, `url` (the bill on Congress.gov).

## How it was built (`data/build_dataset.py`)

1. Parse 17,007 bill status files. Drop 396 with no policy area yet (new bills get one later). 16,611 remain.
2. Normalize each title: lowercase, drop years and punctuation. Bills with the same normalized
   title form one group (companion House and Senate bills, reintroductions). 350 bills fold
   into groups, leaving 16,261 distinct titles. 19 groups hold bills with different labels.
   The earliest bill in each group stands for it.
3. Whole groups go to one split, so a title in the test set never appears in training.
4. Golden: 150 titles, stratified. Every label with at least 10 titles gets at least 2 examples.
   The rest are spread in proportion to label size. Valid: 10% of what remains, per label. Train: the rest.
5. Fixed seed (`20261006`). The same download always gives the same files.

## The honest floor

| Baseline | Golden accuracy |
|---|---|
| Always answer the biggest label (Health, 11.4% of train) | 12/150 = 8.0% |
| Guess one of 32 labels at random | about 3% |

The golden set is stratified, so rare labels count for more than they do in real traffic.
That is why the majority baseline is 8.0% here and 11.4% on the natural mix.

## Is title-only too easy or too hard?

Neither, which makes it a good test. Many titles name their topic outright ("To amend the
Internal Revenue Code…"). But the labels follow Congress.gov conventions a model has to learn:
veterans' benefits are "Armed Forces and National Security", tax-code changes are "Taxation"
even when the subject is health. Some titles don't carry enough information at all. A 4B
model with only a prompt scored 59.3% (see `results/README.md`), far above the floor and far below perfect.

## Rebuild it

```bash
make data                                     # uses data/cache/ if it is there
rm -rf data/cache && make data                # download again from GovInfo
```

The bulk data changes every day: new bills arrive and new policy areas are assigned.
A fresh download gives different splits. The labs use the committed files. Rebuild
only on purpose, then re-run every score, because old and new scores are not comparable.

`data/cache/` (gitignored) holds the zips, a `manifest.json` with the fetch times, and
`bills.csv`, the clean table of all 16,611 labelled bills.
