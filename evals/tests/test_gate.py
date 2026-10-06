import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from evals import gate
from evals.files import SPLITS, read_jsonl

FIXTURES = Path(__file__).parent / "fixtures"
PLANTED_BAD = FIXTURES / "planted_bad_predictions.jsonl"


def run_gate(*args) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return gate.main([str(a) for a in args])


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, rows):
        p = self.dir / name
        p.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return p

    def test_perfect_predictions_pass(self):
        golden = read_jsonl(SPLITS["golden"])
        p = self.write("perfect.jsonl", [{"id": g["id"], "pred": g["label"]} for g in golden])
        self.assertEqual(run_gate("--predictions", p, "--min-accuracy", 1.0, "--max-invalid", 0.0), 0)

    def test_planted_bad_file_fails(self):
        # 90/150 correct (0.60) and 10/150 invalid (0.067): fails on accuracy, on invalid rate, and on both.
        self.assertEqual(run_gate("--predictions", PLANTED_BAD, "--min-accuracy", 0.65, "--max-invalid", 0.05), 1)
        self.assertEqual(run_gate("--predictions", PLANTED_BAD, "--min-accuracy", 0.0, "--max-invalid", 0.05), 1)
        self.assertEqual(run_gate("--predictions", PLANTED_BAD, "--min-accuracy", 0.65, "--max-invalid", 1.0), 1)

    def test_one_flipped_prediction_fails_a_tight_bar(self):
        golden = read_jsonl(SPLITS["golden"])
        rows = [{"id": g["id"], "pred": g["label"]} for g in golden]
        rows[0]["pred"] = "Taxation" if golden[0]["label"] != "Taxation" else "Health"
        p = self.write("one_bad.jsonl", rows)
        self.assertEqual(run_gate("--predictions", p, "--min-accuracy", 1.0, "--max-invalid", 0.0), 1)

    def test_gold_comes_from_golden_file_not_predictions(self):
        # A file that rewrites "gold" to match its own wrong predictions must still fail.
        golden = read_jsonl(SPLITS["golden"])
        rows = [{"id": g["id"], "pred": "Health", "gold": "Health"} for g in golden]
        p = self.write("cheat.jsonl", rows)
        self.assertEqual(run_gate("--predictions", p, "--min-accuracy", 0.5, "--max-invalid", 0.0), 1)

    def test_missing_rows_count_as_invalid(self):
        golden = read_jsonl(SPLITS["golden"])
        p = self.write("half.jsonl", [{"id": g["id"], "pred": g["label"]} for g in golden[: len(golden) // 2]])
        self.assertEqual(run_gate("--predictions", p, "--min-accuracy", 0.0, "--max-invalid", 0.1), 1)

    def test_unknown_label_counts_as_invalid(self):
        golden = read_jsonl(SPLITS["golden"])
        p = self.write("made_up.jsonl", [{"id": g["id"], "pred": "Not A Label"} for g in golden])
        ok, c = gate.check(p, SPLITS["golden"], 0.0, 1.0)
        self.assertEqual(c["invalid"], len(golden))


if __name__ == "__main__":
    unittest.main()
