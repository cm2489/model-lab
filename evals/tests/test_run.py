"""End to end through the CLI with a fake backend and the predictions backend. No model needed."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import run


class FakeBackend:
    local = True

    def __call__(self, messages):
        title = messages[0]["content"].rsplit("Bill title:\n", 1)[1]
        raw = "Taxation" if "Revenue" in title else "Health"
        return {"raw": raw, "input_tokens": 200, "output_tokens": 2, "gen_tps": 150.0, "stop": "stop"}


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class RunCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_model_run_writes_all_outputs(self):
        with mock.patch.object(run, "make_backend", return_value=FakeBackend()):
            quiet(run.main, ["--backend", "mlx", "--model", "fake/model", "--limit", "10",
                             "--run-name", "fake", "--results-dir", str(self.dir)])
        out = self.dir / "fake"
        preds = [json.loads(line) for line in (out / "predictions.jsonl").read_text().splitlines()]
        self.assertEqual(len(preds), 10)
        for key in ("id", "gold", "pred", "parse", "raw", "latency_s", "input_tokens", "output_tokens"):
            self.assertIn(key, preds[0])
        m = json.loads((out / "metrics.json").read_text())
        self.assertEqual(m["classification"]["n"], 10)
        self.assertEqual(m["cost"]["cost_per_1k_usd"], 0.0)
        self.assertEqual(m["meta"]["model"], "fake/model")
        self.assertRegex(m["meta"]["date"], r"[+-]\d\d:\d\d$")  # Eastern Time, with its offset
        self.assertIn("fake/score.md", (self.dir / "README.md").read_text())

    def test_predictions_backend_rescores_a_file(self):
        with mock.patch.object(run, "make_backend", return_value=FakeBackend()):
            quiet(run.main, ["--backend", "mlx", "--model", "fake/model", "--run-name", "a",
                             "--results-dir", str(self.dir)])
        quiet(run.main, ["--backend", "predictions", "--predictions", str(self.dir / "a" / "predictions.jsonl"),
                         "--run-name", "b", "--results-dir", str(self.dir), "--price-in", "1", "--price-out", "5"])
        a = json.loads((self.dir / "a" / "metrics.json").read_text())["classification"]
        b = json.loads((self.dir / "b" / "metrics.json").read_text())
        self.assertEqual(a["accuracy"], b["classification"]["accuracy"])
        self.assertEqual(b["meta"]["model"], "fake/model")
        # 200 in x $1/M + 2 out x $5/M = $0.00021 per bill -> $0.21 per 1,000
        self.assertEqual(b["cost"]["cost_per_1k_usd"], 0.21)

    def test_short_prompt_and_adapter_are_recorded(self):
        seen = {}

        class Spy(FakeBackend):
            def __call__(self, messages):
                seen["prompt"] = messages[0]["content"]
                return super().__call__(messages)

        with mock.patch.object(run, "make_backend", return_value=Spy()):
            quiet(run.main, ["--backend", "mlx", "--model", "fake/model", "--limit", "3", "--prompt", "short",
                             "--adapter-path", "adapters/x", "--run-name", "t", "--results-dir", str(self.dir)])
        self.assertNotIn("Policy areas:", seen["prompt"])
        m = json.loads((self.dir / "t" / "metrics.json").read_text())["meta"]
        self.assertEqual(m["prompt_style"], "short")
        self.assertEqual(m["prompt_version"], "short-v1")
        self.assertEqual(m["adapter"], "adapters/x")
        table = (self.dir / "README.md").read_text()
        self.assertIn("LoRA adapter", table)
        self.assertIn("| short |", table)


if __name__ == "__main__":
    unittest.main()
