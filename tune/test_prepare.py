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
        golden = {" ".join(r["title"].lower().split()) for r in read_jsonl(ROOT / "evals" / "golden.jsonl")}
        titles = {" ".join(row["messages"][0]["content"].rsplit("Bill title:\n", 1)[1].lower().split())
                  for row in train + valid}
        self.assertFalse(titles & golden)


if __name__ == "__main__":
    unittest.main()
