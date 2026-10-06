"""Leakage tests for the splits. Standard library only; no download needed."""

import random
import unittest
from unittest import mock

from data import build_dataset as bd
from evals.files import SPLITS, read_jsonl


def bill(n, chamber, title, label, short=None):
    return {"id": f"{chamber}{n}-119", "bill_type": chamber, "number": n, "congress": 119,
            "introduced": f"2025-01-{(n % 28) + 1:02d}", "title": title, "policy_area": label,
            "display_title": short or title}


class TitleKey(unittest.TestCase):
    def test_house_and_senate_companions_share_a_key(self):
        house = "To amend the Internal Revenue Code of 1986 to extend a credit, and for other purposes."
        senate = "A bill to amend the Internal Revenue Code of 1986 to extend a credit."
        self.assertEqual(bd.normalize_title(house), bd.normalize_title(senate))

    def test_resolution_prefixes(self):
        self.assertEqual(bd.normalize_title("A joint resolution providing for congressional disapproval of X."),
                         bd.normalize_title("Providing for congressional disapproval of X."))
        self.assertEqual(bd.normalize_title("A concurrent resolution expressing support for Y."),
                         bd.normalize_title("Expressing support for Y."))
        self.assertEqual(bd.normalize_title("An original bill to authorize Z."),
                         bd.normalize_title("To authorize Z."))

    def test_case_punctuation_and_years(self):
        self.assertEqual(bd.normalize_title("To Reauthorize the Act of 2024."),
                         bd.normalize_title("to reauthorize the act of 2026"))

    def test_different_bills_differ(self):
        self.assertNotEqual(bd.normalize_title("To amend the Clean Air Act."),
                            bd.normalize_title("To amend the Clean Water Act."))


class Split(unittest.TestCase):
    def make_bills(self):
        bills, n = [], 1
        for label in ("Health", "Taxation", "Energy"):
            for i in range(30):
                topic = f"{label.lower()} aa{i}{label} bb{i}{label} cc{i}{label} dd{i}{label}"
                # House and Senate companions: same title apart from chamber boilerplate.
                bills.append(bill(n, "hr", f"To {topic}, and for other purposes.", label)); n += 1
                bills.append(bill(n, "s", f"A bill to {topic}.", label)); n += 1
        # Reworded companions joined only by their short title.
        bills.append(bill(n, "hr", "To fund rural clinics through grants.", "Health", "Rural Clinics Act of 2025")); n += 1
        bills.append(bill(n, "s", "A bill to support rural clinics with grants.", "Health", "Rural Clinics Act of 2025"))
        return bills

    def test_companions_never_straddle_splits(self):
        with mock.patch.object(bd, "GOLDEN_SIZE", 9), mock.patch.object(bd, "MIN_GROUPS_FOR_GOLDEN", 5):
            splits = bd.split(self.make_bills(), random.Random(1))
        self.assertEqual(len(splits["golden"]), 9)
        leaks = bd.leakage(splits)
        for kind, pairs in leaks.items():
            for pair, n in pairs.items():
                self.assertEqual(n, 0, f"{kind} {pair}")
        where = {b["id"]: name for name, rows in splits.items() for b in rows}
        # The two short-title companions: at most one is kept, never one in golden and one elsewhere.
        rural = [where.get(i) for i in (f"hr{181}-119", f"s{182}-119")]
        self.assertTrue(None in rural or rural[0] == rural[1], rural)


class CommittedFiles(unittest.TestCase):
    """The files in git: no House/Senate companion title key in two splits."""

    def test_no_title_key_in_two_splits(self):
        splits = {name: read_jsonl(path) for name, path in SPLITS.items()}
        keys = {name: {bd.normalize_title(r["title"]) for r in rows} for name, rows in splits.items()}
        self.assertEqual(len(keys["golden"] & keys["train"]), 0)
        self.assertEqual(len(keys["golden"] & keys["valid"]), 0)
        self.assertEqual(len(keys["train"] & keys["valid"]), 0)

    def test_golden_has_150_unique_bills(self):
        golden = read_jsonl(SPLITS["golden"])
        self.assertEqual(len(golden), 150)
        self.assertEqual(len({r["id"] for r in golden}), 150)


if __name__ == "__main__":
    unittest.main()
