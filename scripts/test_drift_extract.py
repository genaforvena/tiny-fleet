#!/usr/bin/env python3
import csv
import hashlib
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

    def test_gitlinks_are_excluded_independent_of_target_availability(self):
        base = self.commit({"main.py": "VALUE = 1\n"}, "base")
        missing = "1234567890abcdef1234567890abcdef12345678"
        subprocess.run(["git", "update-index", "--add", "--cacheinfo",
                        f"160000,{missing},missing-module"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "missing gitlink"], cwd=self.repo, check=True)
        missing_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()

        other = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=other, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=other, check=True)
        (other / "module.py").write_text("MODULE = 1\n")
        subprocess.run(["git", "add", "module.py"], cwd=other, check=True)
        subprocess.run(["git", "commit", "-qm", "available target"], cwd=other, check=True)
        available = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=other, text=True).strip()
        (self.repo / ".git/objects/info/alternates").write_text(str(other / ".git/objects") + "\n")
        subprocess.run(["git", "cat-file", "-e", available], cwd=self.repo, check=True)
        subprocess.run(["git", "update-index", "--add", "--cacheinfo",
                        f"160000,{available},available-module"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "available gitlink"], cwd=self.repo, check=True)
        current = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()

        for old, new, expected in ((base, missing_commit, {"missing-module": missing}),
                                   (missing_commit, current,
                                    {"missing-module": missing, "available-module": available})):
            with self.subTest(new=new):
                out = Path(tempfile.mkdtemp())
                result = extract(self.repo, old, new, out)
                with (out / "new-files.tsv").open() as table:
                    rows = {row["path"]: row for row in csv.DictReader(table, delimiter="\t")}
                self.assertEqual(list(rows["main.py"]), [
                    "path", "blob_sha256", "bytes", "units", "language", "status", "reason",
                    "git_object"])
                self.assertEqual(rows["main.py"]["status"], "included")
                self.assertEqual(rows["main.py"]["blob_sha256"],
                                 hashlib.sha256(b"VALUE = 1\n").hexdigest())
                self.assertEqual(rows["main.py"]["git_object"],
                                 subprocess.check_output(
                                     ["git", "rev-parse", f"{new}:main.py"],
                                     cwd=self.repo, text=True).strip())
                for name, target in expected.items():
                    self.assertEqual(rows[name]["status"], "excluded")
                    self.assertEqual(rows[name]["reason"], "gitlink")
                    self.assertEqual(rows[name]["blob_sha256"], "")
                    self.assertEqual(rows[name]["git_object"], target)
                    self.assertNotIn(name, (out / "new-corpus.txt").read_text())
                self.assertEqual(result["new"]["included_paths"], 1)
                self.assertEqual(result["new"]["excluded_paths"], len(expected))
                self.assertEqual(result["delta"], dict.fromkeys((
                    "added_text_paths", "deleted_text_paths", "renamed_text_paths",
                    "changed_text_paths"), 0))

    def test_missing_ordinary_blob_fails_instead_of_becoming_gitlink(self):
        old = self.commit({"main.py": "VALUE = 1\n"}, "base")
        new = self.commit({"missing.txt": "ordinary blob\n"}, "new")
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{new}:missing.txt"], cwd=self.repo, text=True).strip()
        (self.repo / ".git/objects" / blob[:2] / blob[2:]).unlink()
        with self.assertRaises(subprocess.CalledProcessError):
            extract(self.repo, old, new, Path(tempfile.mkdtemp()))

    def test_identical_snapshots_have_zero_delta(self):
        commit = self.commit({"a.py": "print('x')\n"}, "one")
        result = extract(self.repo, commit, commit, Path(tempfile.mkdtemp()))
        self.assertEqual(result["delta"]["changed_text_paths"], 0)
        self.assertEqual(result["delta"]["added_text_paths"], 0)
        self.assertEqual(result["delta"]["deleted_text_paths"], 0)


if __name__ == "__main__":
    unittest.main()
