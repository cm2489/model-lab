"""Tests for validate_content.py.

Run from the repo root:  uv run python -m unittest scripts/test_validate_content.py
"""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_content as vc  # noqa: E402

LABS = {
    "track": {"id": "t", "title": "Track"},
    "labs": [
        {"id": "lab-0", "number": 0, "title": "Setup", "aim": "Aim.",
         "artifact": {"title": "Thing", "public": False}, "est_minutes": 45,
         "doc": "labs/00/README.md", "status": "ready",
         "steps": [
             {"id": "lab-0.1", "title": "One", "minutes": 20, "where": "laptop", "anchor": "step-1"},
             {"id": "lab-0.2", "title": "Two", "minutes": 25, "where": "hosted", "anchor": "step-2"}]},
        {"id": "lab-1", "number": 1, "title": "Evals", "aim": "Aim.",
         "artifact": {"title": "Harness", "public": True}, "est_minutes": 30,
         "doc": "labs/01/README.md", "status": "planned",
         "steps": [{"id": "lab-1.1", "title": "Meet", "minutes": 30, "where": "phone", "anchor": "step-1"}]},
    ],
}
DOC = "# Setup\n\n## Step 1: Install\n\ntext\n\n<a id=\"step-2\"></a>\n## Run it\n"
CARDS = [{"id": "lab-0.c1", "lab": "lab-0", "after_step": "lab-0.2", "concept": "c",
          "type": "core", "front": "Q?", "back": "Short answer."}]
FND = [{"id": "fnd-s3.c1", "lab": "foundations", "after_step": None, "concept": "c",
        "type": "nuance", "front": "Q?", "back": "A."}]
PROGRESS = {
    "updated": "2026-10-07T09:30:00-04:00",
    "steps": {"lab-0.1": {"done": "2026-10-07T09:30:00-04:00", "minutes": 25, "note": ""}},
    "sessions": [{"date": "2026-10-07", "minutes": 45, "steps": ["lab-0.1"]}],
    "artifacts": [{"lab": "lab-0", "title": "T", "url": "https://x.example", "shipped": "2026-10-16"}],
}


def write(root: Path, rel: str, content) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.labs, self.cards = copy.deepcopy(LABS), copy.deepcopy(CARDS)
        self.fnd, self.progress, self.doc = copy.deepcopy(FND), copy.deepcopy(PROGRESS), DOC

    def build(self):
        write(self.root, "content/labs.json", self.labs)
        write(self.root, "content/cards.json", self.cards)
        write(self.root, "foundations/cards.json", self.fnd)
        write(self.root, "progress.json", self.progress)
        write(self.root, "labs/00/README.md", self.doc)

    def errors(self):
        self.build()
        return vc.validate(self.root)

    def assertFails(self, needle):
        errs = self.errors()
        self.assertTrue(any(needle in e for e in errs), f"expected {needle!r} in {errs}")

    def lab0(self):
        return self.labs["labs"][0]


class GoodFixture(Base):
    def test_good_passes(self):
        self.assertEqual(self.errors(), [])

    def test_main_exit_codes(self):
        def run():
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return vc.main(["--root", str(self.root)])

        self.build()
        self.assertEqual(run(), 0)
        self.progress["steps"]["nope.1"] = {"done": "2026-10-07T09:30:00-04:00", "minutes": 1, "note": ""}
        self.build()
        self.assertEqual(run(), 1)

    def test_null_updated_is_allowed(self):
        self.progress = {"updated": None, "steps": {}, "sessions": [], "artifacts": []}
        self.assertEqual(self.errors(), [])

    def test_heading_slug_and_explicit_anchor_both_work(self):
        self.doc = "## Step 1\n\n<a name=\"step-2\"></a>\n"
        self.assertEqual(self.errors(), [])
        self.doc = "## Step 1\n\n## Something {#step-2}\n"
        self.assertEqual(self.errors(), [])


class LabsBad(Base):
    def test_missing_key(self):
        del self.lab0()["aim"]
        self.assertFails("missing key 'aim'")

    def test_duplicate_lab_id(self):
        self.labs["labs"][1]["id"] = "lab-0"
        self.assertFails("duplicate lab id")

    def test_duplicate_step_id(self):
        self.lab0()["steps"][1]["id"] = "lab-0.1"
        self.assertFails("duplicate step id")

    def test_step_id_prefix(self):
        self.lab0()["steps"][1]["id"] = "lab-9.2"
        self.assertFails("must start with its lab id")

    def test_bad_status(self):
        self.lab0()["status"] = "done"
        self.assertFails("status 'done'")

    def test_bad_where(self):
        self.lab0()["steps"][0]["where"] = "cloud"
        self.assertFails("where 'cloud'")

    def test_minutes_sum(self):
        self.lab0()["est_minutes"] = 50
        self.assertFails("steps add up to 45")

    def test_ready_doc_missing(self):
        self.build()
        (self.root / "labs/00/README.md").unlink()
        self.assertTrue(any("does not exist" in e for e in vc.validate(self.root)))

    def test_ready_anchor_missing(self):
        self.doc = "## Step 1\n"
        self.assertFails("anchor 'step-2' has no heading")

    def test_draft_also_checked_but_planned_is_not(self):
        self.lab0()["status"] = "draft"
        self.doc = "## Step 1\n"
        self.assertFails("anchor 'step-2'")
        self.lab0()["status"] = "planned"
        self.assertEqual(self.errors(), [])

    def test_bad_json(self):
        self.build()
        (self.root / "content/labs.json").write_text("{nope", encoding="utf-8")
        self.assertTrue(any("not valid JSON" in e for e in vc.validate(self.root)))


class CardsBad(Base):
    def test_duplicate_id_across_files(self):
        self.fnd[0]["id"] = "lab-0.c1"
        self.assertFails("duplicate card id")

    def test_unknown_lab(self):
        self.cards[0]["lab"] = "lab-7"
        self.assertFails("is not a lab id")

    def test_unknown_after_step(self):
        self.cards[0]["after_step"] = "lab-0.9"
        self.assertFails("after_step 'lab-0.9'")

    def test_empty_front_and_back(self):
        self.cards[0]["front"] = " "
        self.cards[0]["back"] = ""
        errs = self.errors()
        self.assertTrue(any("'front' must be" in e for e in errs))
        self.assertTrue(any("'back' must be" in e for e in errs))

    def test_core_back_too_long(self):
        self.cards[0]["back"] = " ".join(["word"] * 26)
        self.assertFails("26 words")

    def test_core_back_at_limit_ok_and_nuance_not_limited(self):
        self.cards[0]["back"] = " ".join(["word"] * 25)
        self.fnd[0]["back"] = " ".join(["word"] * 40)
        self.assertEqual(self.errors(), [])

    def test_not_a_list(self):
        self.cards = {"a": 1}
        self.assertFails("top level must be a list")

    def test_missing_foundations_file(self):
        self.build()
        (self.root / "foundations/cards.json").unlink()
        self.assertTrue(any("foundations/cards.json: file not found" in e for e in vc.validate(self.root)))


class ProgressBad(Base):
    def test_unknown_step(self):
        self.progress["steps"]["lab-9.1"] = {"done": "2026-10-07T09:30:00-04:00", "minutes": 1, "note": ""}
        self.assertFails("unknown step id")

    def test_unknown_session_step(self):
        self.progress["sessions"][0]["steps"] = ["lab-0.9"]
        self.assertFails("unknown step id 'lab-0.9'")

    def test_unknown_artifact_lab(self):
        self.progress["artifacts"][0]["lab"] = "lab-8"
        self.assertFails("unknown lab id")

    def test_timestamp_without_offset(self):
        self.progress["steps"]["lab-0.1"]["done"] = "2026-10-07T09:30:00"
        self.assertFails("no UTC offset")

    def test_timestamp_unparseable(self):
        self.progress["updated"] = "yesterday"
        self.assertFails("not an ISO 8601 timestamp")

    def test_bad_session_date(self):
        self.progress["sessions"][0]["date"] = "2026-13-01"
        self.assertFails("not a YYYY-MM-DD date")

    def test_missing_top_key(self):
        del self.progress["sessions"]
        self.assertFails("missing key 'sessions'")


if __name__ == "__main__":
    unittest.main()
