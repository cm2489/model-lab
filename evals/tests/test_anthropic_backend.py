"""The Anthropic path, tested with a fake client. No network, no API key, no cost."""

import unittest
from types import SimpleNamespace

from evals.backends import AnthropicBackend
from evals.prompt import build_messages, parse_label


class FakeMessages:
    def __init__(self, reply_blocks, stop_reason="end_turn", usage=(250, 40)):
        self.calls = []
        self.reply_blocks = reply_blocks
        self.stop_reason = stop_reason
        self.usage = usage

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=self.reply_blocks,
            stop_reason=self.stop_reason,
            usage=SimpleNamespace(input_tokens=self.usage[0], output_tokens=self.usage[1]),
        )


def fake_client(*args, **kwargs):
    return SimpleNamespace(messages=FakeMessages(*args, **kwargs))


class AnthropicPath(unittest.TestCase):
    def test_request_shape_and_reply(self):
        client = fake_client([SimpleNamespace(type="thinking", thinking=""),
                              SimpleNamespace(type="text", text="Taxation")])
        backend = AnthropicBackend("claude-opus-5-5", client=client)
        msgs = build_messages("To amend the Internal Revenue Code of 1986 to extend a credit.")
        r = backend(msgs)

        call = client.messages.calls[0]
        self.assertEqual(call["model"], "claude-opus-5-5")
        self.assertEqual(call["messages"], msgs)
        self.assertEqual(call["output_config"], {"effort": "low"})
        self.assertEqual(call["max_tokens"], 512)  # one label plus room for low-effort thinking
        self.assertNotIn("thinking", call)  # Opus 5.5 rejects a disabled-thinking setting

        self.assertEqual(r["raw"], "Taxation")  # thinking blocks are not part of the answer
        self.assertEqual((r["input_tokens"], r["output_tokens"]), (250, 40))
        self.assertEqual(parse_label(r["raw"]), ("Taxation", "exact"))

    def test_effort_can_be_omitted(self):
        client = fake_client([SimpleNamespace(type="text", text="Health")])
        AnthropicBackend("claude-haiku-4-5", effort=None, client=client)(build_messages("x"))
        self.assertNotIn("output_config", client.messages.calls[0])

    def test_refusal_is_invalid_not_dropped(self):
        client = fake_client([SimpleNamespace(type="text", text="Health")], stop_reason="refusal")
        r = AnthropicBackend("claude-opus-5-5", client=client)(build_messages("x"))
        self.assertEqual(r["raw"], "[refusal]")
        self.assertEqual(parse_label(r["raw"]), (None, "invalid"))
        self.assertEqual(r["stop"], "refusal")

    def test_non_retryable_error_stops_the_run(self):
        class Boom(Exception):
            pass

        class BadClient:
            class messages:
                @staticmethod
                def create(**kwargs):
                    raise Boom("bad request")

        with self.assertRaises(Boom):
            AnthropicBackend("claude-opus-5-5", client=BadClient())(build_messages("x"))


try:
    import anthropic  # noqa: F401

    HAVE_SDK = True
except ImportError:  # CI runs with no packages installed
    HAVE_SDK = False


@unittest.skipUnless(HAVE_SDK, "needs the anthropic SDK (installed by uv sync)")
class NoRetries(unittest.TestCase):
    def test_default_client_never_retries(self):
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "placeholder-not-a-real-key"}):
            backend = AnthropicBackend("claude-opus-5-5")  # builds the real SDK client; sends nothing
        self.assertEqual(backend.client.max_retries, 0)


class PriceWarning(unittest.TestCase):
    def test_documented_model_and_prices_are_quiet(self):
        from evals.run import price_warning

        self.assertIsNone(price_warning("claude-opus-5-5", 4.0, 20.0))

    def test_other_prices_warn(self):
        from evals.run import price_warning

        self.assertIn("Check today's prices", price_warning("claude-opus-5-5", 5.0, 25.0))

    def test_unknown_model_warns(self):
        from evals.run import price_warning

        self.assertIn("only as good as", price_warning("claude-haiku-4-5", 1.0, 5.0))


class SpendGuard(unittest.TestCase):
    """The guard runs before any request. The fake client proves nothing was sent."""

    def run_cli(self, *extra):
        import contextlib
        import io
        import tempfile
        from unittest import mock

        from evals import run

        client = fake_client([SimpleNamespace(type="text", text="Health")])
        backend = AnthropicBackend("claude-opus-5-5", client=client)
        with tempfile.TemporaryDirectory() as d, mock.patch.object(run, "make_backend", return_value=backend), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                run.main(["--backend", "anthropic", "--model", "claude-opus-5-5", "--results-dir", d, *extra])
                code = 0
            except SystemExit as e:
                code = e.code
        return code, client.messages.calls

    PRICES = ["--price-in", "4", "--price-out", "20"]

    def test_worst_case_arithmetic(self):
        from evals.run import worst_case_usd

        # 2 bills, 512 max tokens: output 1,024 x $20/M = $0.02048, plus input.
        ex = [{"title": "x"}, {"title": "y"}]
        worst = worst_case_usd(ex, 512, 4.0, 20.0)
        self.assertGreater(worst, 0.02048)
        self.assertLess(worst, 0.03)

    def test_golden_at_page_settings_fits_under_two_dollars(self):
        from evals.files import SPLITS, read_jsonl
        from evals.run import worst_case_usd

        self.assertLess(worst_case_usd(read_jsonl(SPLITS["golden"]), 512, 4.0, 20.0), 2.0)

    def test_refuses_when_worst_case_is_over_the_cap(self):
        code, calls = self.run_cli(*self.PRICES, "--max-usd", "0.50")
        self.assertNotEqual(code, 0)
        self.assertEqual(calls, [])

    def test_requires_max_usd(self):
        code, calls = self.run_cli(*self.PRICES, "--limit", "2")
        self.assertNotEqual(code, 0)
        self.assertEqual(calls, [])

    def test_requires_prices(self):
        code, calls = self.run_cli("--max-usd", "2", "--limit", "2")
        self.assertNotEqual(code, 0)
        self.assertEqual(calls, [])

    def test_refuses_train_and_valid_without_allow_large(self):
        for split in ("train", "valid"):
            code, calls = self.run_cli(*self.PRICES, "--max-usd", "1000", "--split", split, "--limit", "2")
            self.assertNotEqual(code, 0, split)
            self.assertEqual(calls, [], split)

    def test_allow_large_lets_a_capped_valid_run_through(self):
        code, calls = self.run_cli(*self.PRICES, "--max-usd", "1", "--split", "valid", "--limit", "2", "--allow-large")
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 2)

    def test_refuses_zero_prices(self):
        for prices in (["--price-in", "0", "--price-out", "20"], ["--price-in", "4", "--price-out", "0"]):
            code, calls = self.run_cli(*prices, "--max-usd", "2", "--limit", "2")
            self.assertNotEqual(code, 0, prices)
            self.assertEqual(calls, [], prices)

    def test_refuses_negative_prices(self):
        for prices in (["--price-in", "-4", "--price-out", "20"], ["--price-in", "4", "--price-out", "-20"]):
            code, calls = self.run_cli(*prices, "--max-usd", "2", "--limit", "2")
            self.assertNotEqual(code, 0, prices)
            self.assertEqual(calls, [], prices)

    def test_refuses_a_big_file_with_an_innocent_name(self):
        import json
        import tempfile
        from pathlib import Path

        from evals.files import SPLITS, read_jsonl

        rows = read_jsonl(SPLITS["valid"])[:501]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "my_small_sample.jsonl"
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            code, calls = self.run_cli(*self.PRICES, "--max-usd", "1000", "--data", str(path))
        self.assertNotEqual(code, 0)
        self.assertEqual(calls, [])

    def test_runs_when_under_the_cap(self):
        code, calls = self.run_cli(*self.PRICES, "--max-usd", "2", "--limit", "3")
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
