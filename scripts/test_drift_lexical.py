#!/usr/bin/env python3
import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from drift_extract import extract
from drift_lexical import analyze, tokenize


class DriftLexicalTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)

    def commit(self, files, message):
        for name, data in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-qm", message], cwd=self.repo, check=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()

    def run_analysis(self, old_files, new_files):
        old = self.commit(old_files, "old")
        new = self.commit(new_files, "new")
        out = Path(tempfile.mkdtemp())
        extract(self.repo, old, new, out)
        result = analyze(out)
        return out, result

    def test_tokenizer_is_declared_and_unicode_language_independent(self):
        self.assertEqual(tokenize("Gate Модель gate_2"), ["gate", "модель", "gate_2"])

    def test_no_change_is_zero(self):
        out, result = self.run_analysis({"a.md": "model gate\n"}, {"a.md": "model gate\n"})
        self.assertEqual(result["delta_concepts"], 0)
        controls = list(csv.DictReader((out / "controls.tsv").open(), delimiter="\t"))
        self.assertEqual(controls[0]["verdict"], "NO_CHANGE")

    def test_duplication_changes_raw_but_not_rate(self):
        out, result = self.run_analysis({"a.md": "model gate\n"}, {"a.md": "model gate\n", "b.md": "model gate\n"})
        rows = list(csv.DictReader((out / "lexical.tsv").open(), delimiter="\t"))
        model = {(row["snapshot"], row["category"], row["concept"]): row for row in rows}["old", "all", "model"], {(row["snapshot"], row["category"], row["concept"]): row for row in rows}["new", "all", "model"]
        self.assertGreater(int(model[1]["raw_count"]), int(model[0]["raw_count"]))
        self.assertEqual(model[0]["rate_per_10000"], model[1]["rate_per_10000"])
        self.assertEqual(result["controls"]["duplication"]["verdict"], "NO_NORMALIZED_CHANGE")

    def test_rename_is_reported_as_lexical_only(self):
        out, result = self.run_analysis({"a.py": "model gate\n"}, {"renamed.py": "model gate\n"})
        self.assertEqual(result["controls"]["rename"]["verdict"], "LEXICAL_ONLY")
        controls = list(csv.DictReader((out / "controls.tsv").open(), delimiter="\t"))
        self.assertIn("LEXICAL_ONLY", {row["verdict"] for row in controls})

    def test_dictionary_is_versioned_with_ambiguity_examples(self):
        data = json.loads(Path(__file__).parents[1].joinpath("docs/concepts-v1.json").read_text())
        self.assertEqual(data["version"], "concepts-v1")
        self.assertTrue(data["terms"])
        self.assertTrue(data["ambiguous_examples"])


if __name__ == "__main__":
    unittest.main()
