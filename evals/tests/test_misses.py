import contextlib
import io
import unittest
from pathlib import Path

from evals import misses

PLANTED_BAD = Path(__file__).parent / "fixtures" / "planted_bad_predictions.jsonl"


class Misses(unittest.TestCase):
    def test_prints_a_fixed_sample_of_misses(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            misses.main([str(PLANTED_BAD), "--n", "5"])
        text = out.getvalue()
        self.assertIn("90 misses out of 150. Showing 5.", text)
        self.assertEqual(text.count("gold:"), 5)

    def test_same_sample_every_time(self):
        runs = []
        for _ in range(2):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                misses.main([str(PLANTED_BAD), "--n", "10"])
            runs.append(out.getvalue())
        self.assertEqual(runs[0], runs[1])


if __name__ == "__main__":
    unittest.main()
