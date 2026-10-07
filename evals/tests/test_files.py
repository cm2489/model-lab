import subprocess
import tempfile
import unittest
from pathlib import Path

from evals.files import git_commit


def git(root, *args):
    subprocess.run(["git", "-c", "user.email=test@example.com", "-c", "user.name=test", *args],
                   cwd=root, check=True, capture_output=True)


class GitCommit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        (self.root / "results").mkdir()
        (self.root / "code.py").write_text("x = 1\n")
        (self.root / "results" / "README.md").write_text("table\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "init")

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean(self):
        self.assertNotIn("dirty", git_commit(self.root))

    def test_results_change_is_not_dirty(self):
        (self.root / "results" / "README.md").write_text("table with a new row\n")
        self.assertNotIn("dirty", git_commit(self.root))

    def test_code_change_is_dirty(self):
        (self.root / "code.py").write_text("x = 2\n")
        self.assertTrue(git_commit(self.root).endswith("-dirty"))


if __name__ == "__main__":
    unittest.main()
