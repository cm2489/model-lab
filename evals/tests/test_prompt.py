import unittest

from evals.labels import LABELS
from evals.prompt import build_messages, parse_label, strip_thinking


class ParseLabel(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(parse_label("Health"), ("Health", "exact"))

    def test_case_spaces_and_period(self):
        self.assertEqual(parse_label("  taxation.\n"), ("Taxation", "exact"))

    def test_quotes_and_prefix(self):
        self.assertEqual(parse_label('Policy area: "Energy"'), ("Energy", "exact"))

    def test_label_with_commas(self):
        self.assertEqual(parse_label("Arts, Culture, Religion"), ("Arts, Culture, Religion", "exact"))

    def test_contained_in_sentence(self):
        self.assertEqual(parse_label("The answer is Immigration."), ("Immigration", "contained"))

    def test_longest_match_wins(self):
        # "Law" is inside "Crime and Law Enforcement"; that must not count as two labels.
        self.assertEqual(parse_label("It is Crime and Law Enforcement"), ("Crime and Law Enforcement", "contained"))

    def test_law_alone(self):
        self.assertEqual(parse_label("Law"), ("Law", "exact"))

    def test_two_labels_is_invalid(self):
        self.assertEqual(parse_label("Health or Taxation"), (None, "invalid"))

    def test_no_label_is_invalid(self):
        self.assertEqual(parse_label("I am not sure."), (None, "invalid"))

    def test_empty_is_invalid(self):
        self.assertEqual(parse_label(""), (None, "invalid"))

    def test_word_boundaries(self):
        # "Energy" must not match inside a longer word.
        self.assertEqual(parse_label("Energyish"), (None, "invalid"))


class Thinking(unittest.TestCase):
    def test_closed_think_block_is_removed(self):
        self.assertEqual(parse_label("<think>\nmaybe Health?\n</think>\n\nTaxation"), ("Taxation", "exact"))

    def test_only_closing_tag(self):
        # Thinking on: the template opens <think> in the prompt, so the reply has only </think>.
        self.assertEqual(parse_label("Health or Energy...\n</think>\n\nEnergy"), ("Energy", "exact"))

    def test_unclosed_think_is_invalid(self):
        # Cut off mid-reasoning: a label mentioned while thinking is not an answer.
        self.assertEqual(parse_label("<think>\nThis looks like Health"), (None, "invalid"))

    def test_strip_thinking_plain_text(self):
        self.assertEqual(strip_thinking("Health"), "Health")


class Prompt(unittest.TestCase):
    def test_prompt_lists_every_label_and_the_title(self):
        msgs = build_messages("To amend the Internal Revenue Code.")
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["role"], "user")
        for label in LABELS:
            self.assertIn(f"- {label}\n", msgs[0]["content"] + "\n")
        self.assertIn("To amend the Internal Revenue Code.", msgs[0]["content"])

    def test_32_labels(self):
        self.assertEqual(len(LABELS), 32)
        self.assertEqual(len(set(LABELS)), 32)


class ShortStyle(unittest.TestCase):
    def test_short_prompt_has_no_label_list(self):
        from evals.labels import LABELS
        from evals.prompt import build_messages, prompt_version

        full = build_messages("A bill about bees.")[0]["content"]
        short = build_messages("A bill about bees.", "short")[0]["content"]
        self.assertIn("A bill about bees.", short)
        self.assertTrue(all(label in full for label in LABELS))
        self.assertFalse(any(f"- {label}" in short for label in LABELS))
        self.assertLess(len(short), len(full) / 4)
        self.assertNotEqual(prompt_version("short"), prompt_version("list"))

    def test_unknown_style_is_an_error(self):
        from evals.prompt import build_messages

        with self.assertRaises(ValueError):
            build_messages("x", "tiny")


if __name__ == "__main__":
    unittest.main()
