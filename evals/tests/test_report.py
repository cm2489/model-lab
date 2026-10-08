"""The Model column for Hub ids and for a folder converted here with mlx_lm.convert."""

import tempfile
import unittest
from pathlib import Path

from evals import report, run


class ModelLabel(unittest.TestCase):
    def test_hub_id_unchanged(self):
        self.assertEqual(report.model_label({"model": "mlx-community/gemma-4-e4b-it-4bit"}),
                         "`mlx-community/gemma-4-e4b-it-4bit`")

    def test_converted_folder_names_its_source(self):
        meta = {"model": "models/gemma-4-e4b-it-4bit", "converted_from": "google/gemma-4-E4B-it"}
        self.assertEqual(report.model_label(meta),
                         "`models/gemma-4-e4b-it-4bit` (converted here from `google/gemma-4-E4B-it`)")


class LocalBaseModel(unittest.TestCase):
    def test_reads_base_model_from_convert_readme(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "README.md").write_text(
                "---\nlibrary_name: mlx\nlicense: apache-2.0\nbase_model: google/gemma-4-E4B-it\ntags:\n- mlx\n---\n")
            self.assertEqual(run.local_base_model(d), "google/gemma-4-E4B-it")

    def test_hub_id_or_bare_folder_gives_none(self):
        self.assertIsNone(run.local_base_model("mlx-community/does-not-exist-here"))
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(run.local_base_model(d))


if __name__ == "__main__":
    unittest.main()
