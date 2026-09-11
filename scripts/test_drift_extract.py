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
                           "blob.bin": b"\x00\x01\x02"}, "old")
        (self.repo / "keep.txt").rename(self.repo / "renamed.txt")
        new = self.commit({"added.md": "new\n"}, "new")
        out = Path(tempfile.mkdtemp())
        result = extract(self.repo, old, new, out)
        self.assertEqual(result["delta"]["added_text_paths"], 1)
        self.assertEqual(result["delta"]["deleted_text_paths"], 0)
        self.assertEqual(result["delta"]["renamed_text_paths"], 1)
        self.assertEqual(result["old"]["excluded_paths"], 3)
        self.assertIn("renamed.txt", (out / "new-files.tsv").read_text())
        self.assertIn("added.md", (out / "new-corpus.txt").read_text())

    def test_identical_snapshots_have_zero_delta(self):
        commit = self.commit({"a.py": "print('x')\n"}, "one")
        result = extract(self.repo, commit, commit, Path(tempfile.mkdtemp()))
        self.assertEqual(result["delta"]["changed_text_paths"], 0)
        self.assertEqual(result["delta"]["added_text_paths"], 0)
        self.assertEqual(result["delta"]["deleted_text_paths"], 0)


if __name__ == "__main__":
    unittest.main()
