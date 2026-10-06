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


class StrictKey(unittest.TestCase):
    def test_short_title_with_and_without_of_year(self):
        a = {"title": "To expand care for kids.", "display_title": "Accelerating Kids' Access to Care Act of 2025"}
        b = {"title": "A bill to widen care for children.", "display_title": "Accelerating Kids' Access to Care Act"}
        self.assertEqual(bd.strict_short_key(a), bd.strict_short_key(b))
        # The old key leaves "of" behind; that was the bug the cleanup pass fixes.
        self.assertNotEqual(bd.normalize_title(a["display_title"]), bd.normalize_title(b["display_title"]))

    def test_of_without_a_year_stays(self):
        self.assertEqual(bd.strict_title_key("To amend the Department of Energy Act."),
                         "to amend the department of energy act")


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
        bills.append(bill(n, "s", "A bill to support rural clinics with grants.", "Health", "Rural Clinics Act of 2025")); n += 1
        # Reworded companions whose short titles differ only by "of 2025": only cleanup() catches these.
        bills.append(bill(n, "hr", "To speed care for children in clinics.", "Health", "Kids Care Act of 2025")); n += 1
        bills.append(bill(n, "s", "A bill to quicken clinic care for minors.", "Health", "Kids Care Act"))
        return bills

    def test_house_and_senate_companions_never_straddle_splits(self):
        with mock.patch.object(bd, "GOLDEN_SIZE", 9), mock.patch.object(bd, "MIN_GROUPS_FOR_GOLDEN", 5):
            splits = bd.split(self.make_bills(), random.Random(1))
        bd.cleanup(splits)
        self.assertEqual(len(splits["golden"]), 9)
        for pair, n in bd.leakage(splits).items():
            self.assertEqual(n, 0, pair)
        where = {b["id"]: name for name, rows in splits.items() for b in rows}
        for hr, s in (("hr181-119", "s182-119"), ("hr183-119", "s184-119")):
            pair = [where.get(hr), where.get(s)]
            self.assertTrue(None in pair or pair[0] == pair[1], (hr, s, pair))

    def test_cleanup_never_touches_golden(self):
        splits = {"golden": [bill(1, "hr", "To do x.", "Health", "X Act of 2025")],
                  "train": [bill(2, "s", "A bill to do y.", "Health", "X Act")],
                  "valid": [bill(3, "s", "A bill to do z.", "Health")]}
        dropped = bd.cleanup(splits)
        self.assertEqual(dropped, {"train": 1, "valid": 0, "golden": 0})
        self.assertEqual(len(splits["golden"]), 1)


class CommittedFiles(unittest.TestCase):
    """The files in git: no corrected title key in two splits."""

    def test_no_corrected_title_key_in_two_splits(self):
        splits = {name: read_jsonl(path) for name, path in SPLITS.items()}
        keys = {name: {bd.strict_title_key(r["title"]) for r in rows} for name, rows in splits.items()}
        self.assertEqual(len(keys["golden"] & keys["train"]), 0)
        self.assertEqual(len(keys["golden"] & keys["valid"]), 0)
        self.assertEqual(len(keys["train"] & keys["valid"]), 0)

    def test_golden_has_150_unique_bills(self):
        golden = read_jsonl(SPLITS["golden"])
        self.assertEqual(len(golden), 150)
        self.assertEqual(len({r["id"] for r in golden}), 150)


if __name__ == "__main__":
    unittest.main()
