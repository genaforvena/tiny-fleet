#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from drift_extract import extract


class DriftExtractTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, check=True)

    def commit(self, files, message):
        for name, data in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data if isinstance(data, bytes) else data.encode())
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=self.repo, check=True)
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()

    def test_extracts_text_and_counts_exclusions_and_rename(self):
        old = self.commit({"keep.txt": "mesh-chat is a word, not an invocation\n",
                           "generated/out.txt": "ignore\n", "vendor/lib.txt": "ignore\n",
                           "runs/result.json": "ignore\n", "adapters/weights.txt": "ignore\n",
                           "corpus/train.txt": "ignore\n", "blob.bin": b"\x00\x01\x02"}, "old")
        (self.repo / "keep.txt").rename(self.repo / "renamed.txt")
        new = self.commit({"added.md": "new\n"}, "new")
        out = Path(tempfile.mkdtemp())
        result = extract(self.repo, old, new, out)
        self.assertEqual(result["delta"]["added_text_paths"], 1)
        self.assertEqual(result["delta"]["deleted_text_paths"], 0)
        self.assertEqual(result["delta"]["renamed_text_paths"], 1)
        self.assertEqual(result["old"]["excluded_paths"], 6)
        self.assertIn("renamed.txt", (out / "new-files.tsv").read_text())
        self.assertIn("added.md", (out / "new-corpus.txt").read_text())

    def test_changed_content_and_duplicate_renames_are_counted_once(self):
        old = self.commit({"a.txt": "same\n", "b.txt": "same\n",
                           "edit.py": "old\n"}, "old")
        (self.repo / "a.txt").unlink()
        (self.repo / "b.txt").unlink()
        new = self.commit({"c.txt": "same\n", "edit.py": "new\n"}, "new")
        out = Path(tempfile.mkdtemp())
        result = extract(self.repo, old, new, out)
        self.assertEqual(result["delta"], {
            "added_text_paths": 0, "deleted_text_paths": 1,
            "renamed_text_paths": 1, "changed_text_paths": 1})
        table = (out / "structural.tsv").read_text()
        self.assertIn("paths\t3\t2\t-1\n", table)
        self.assertIn("changed_text_paths\t\t\t1\n", table)

    def test_local_import_edges_capture_architecture_not_external_imports(self):
        old = self.commit({"pkg/__init__.py": "",
                           "pkg/core.py": "VALUE = 1\n",
                           "pkg/api.py": "import os\nfrom . import core\n"}, "old")
        new = self.commit({"pkg/api.py": "import os\nfrom . import core\nfrom . import extra\n",
                           "pkg/extra.py": "VALUE = 2\n"}, "new")
        out = Path(tempfile.mkdtemp())
        result = extract(self.repo, old, new, out)
        self.assertEqual(result["architecture"]["old_local_import_edges"], 1)
        self.assertEqual(result["architecture"]["new_local_import_edges"], 2)
        self.assertEqual(result["architecture"]["added_local_import_edges"], 1)
        self.assertEqual(result["architecture"]["removed_local_import_edges"], 0)
        self.assertIn("pkg/api.py\tpkg/extra.py", (out / "new-python-edges.tsv").read_text())

    def test_identical_snapshots_have_zero_delta(self):
        commit = self.commit({"a.py": "print('x')\n"}, "one")
        result = extract(self.repo, commit, commit, Path(tempfile.mkdtemp()))
        self.assertEqual(result["delta"]["changed_text_paths"], 0)
        self.assertEqual(result["delta"]["added_text_paths"], 0)
        self.assertEqual(result["delta"]["deleted_text_paths"], 0)


if __name__ == "__main__":
    unittest.main()
