"""The training files are chat-shaped, capped per label, and never contain a golden title."""

import collections
import json
import tempfile
import unittest
from pathlib import Path

from evals.files import ROOT, read_jsonl
from tune import prepare


class Prepare(unittest.TestCase):
    def test_files_are_capped_chat_examples_without_golden_titles(self):
        with tempfile.TemporaryDirectory() as tmp:
            prepare.main(["--per-label", "5", "--valid", "20", "--out", tmp])
            train = [json.loads(line) for line in (Path(tmp) / "train.jsonl").read_text().splitlines()]
            valid = [json.loads(line) for line in (Path(tmp) / "valid.jsonl").read_text().splitlines()]
        self.assertEqual(len(valid), 20)
        counts = collections.Counter(row["messages"][1]["content"] for row in train)
        self.assertLessEqual(max(counts.values()), 5)
        for row in train + valid:
            roles = [m["role"] for m in row["messages"]]
            self.assertEqual(roles, ["user", "assistant"])
            self.assertNotIn("Policy areas:", row["messages"][0]["content"])
        key = prepare.title_key()
        golden = {key(r["title"]) for r in read_jsonl(ROOT / "evals" / "golden.jsonl")}
        titles = {key(row["messages"][0]["content"].rsplit("Bill title:\n", 1)[1]) for row in train + valid}
        self.assertFalse(titles & golden)

    def test_removing_one_row_changes_only_that_row(self):
        rows = [{"id": f"hr{i}-119", "title": f"Bill {i}", "label": "Health" if i % 2 else "Taxation"} for i in range(400)]
        before = {r["id"] for r in prepare.capped(rows, 50, 7)}
        dropped = sorted(before)[0]
        after = {r["id"] for r in prepare.capped([r for r in rows if r["id"] != dropped], 50, 7)}
        self.assertEqual(len(before - after), 1)   # only the removed row left the sample
        self.assertEqual(len(after - before), 1)   # and exactly one row took its place

    def test_title_key_joins_house_and_senate_twins(self):
        key = prepare.title_key()
        self.assertEqual(key("A bill to amend the Clean Air Act, and for other purposes."),
                         key("To amend the Clean Air Act."))


if __name__ == "__main__":
    unittest.main()
