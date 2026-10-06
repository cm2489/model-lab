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
        self.assertGreaterEqual(call["max_tokens"], 1024)  # room for thinking tokens
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


if __name__ == "__main__":
    unittest.main()
