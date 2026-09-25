#!/usr/bin/env python3
"""Behavioral checks for pinned static local-import edge deltas."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from drift_extract import extract


class EdgeDeltaTests(unittest.TestCase):
    def test_added_removed_edges_hashes_and_identical_control(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)

            def commit(files):
                for name, content in files.items():
                    path = repo / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
                subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
                subprocess.run(["git", "-C", str(repo), "commit", "-qm", "snapshot"], check=True)
                return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

            old = commit({"pkg/__init__.py": "", "pkg/core.py": "VALUE = 1\n",
                          "pkg/api.py": "import os\nfrom . import core\n",
                          "pkg/broken.py": "def (\n"})
            new = commit({"pkg/api.py": "import os\nfrom . import extra\n",
                          "pkg/extra.py": "VALUE = 2\n"})
            a, b, same = (Path(root) / name for name in ("a", "b", "same"))
            first = extract(repo, old, new, a)
            second = extract(repo, old, new, b)
            extract(repo, new, new, same)

            header = "change\tside\tsource\ttarget\tsource_blob_sha256\ttarget_blob_sha256\n"
            def inventory(side):
                rows = (a / f"{side}-files.tsv").read_text().splitlines()[1:]
                return {fields[0]: fields[1] for row in rows if (fields := row.split("\t"))[5] == "included"}

            old_hashes, new_hashes = inventory("old"), inventory("new")
            expected = header + "".join(
                "\t".join((change, side, "pkg/api.py", target,
                           hashes["pkg/api.py"], hashes[target])) + "\n"
                for change, side, target, hashes in (
                    ("added", "new", "pkg/extra.py", new_hashes),
                    ("removed", "old", "pkg/core.py", old_hashes)))
            self.assertEqual((a / "python-edge-delta.tsv").read_text(), expected)
            self.assertEqual((a / "old-python-edges.tsv").read_text(),
                             "source\ttarget\npkg/api.py\tpkg/core.py\n")
            self.assertEqual((a / "new-python-edges.tsv").read_text(),
                             "source\ttarget\npkg/api.py\tpkg/extra.py\n")
            self.assertNotEqual(old_hashes["pkg/api.py"], new_hashes["pkg/api.py"])
            self.assertEqual(first["architecture"]["added_local_import_edges"], 1)
            self.assertEqual(first["architecture"]["removed_local_import_edges"], 1)
            self.assertEqual(first["architecture"]["old_parse_failures"], ["pkg/broken.py"])
            self.assertEqual(first["architecture"]["new_parse_failures"], ["pkg/broken.py"])
            self.assertEqual(first, second)
            self.assertEqual({p.name: p.read_bytes() for p in a.iterdir()},
                             {p.name: p.read_bytes() for p in b.iterdir()})
            self.assertEqual((same / "python-edge-delta.tsv").read_text(), header)
            self.assertEqual(json.loads((same / "manifest.json").read_text())["architecture"]["added_local_import_edges"], 0)
            self.assertEqual(json.loads((same / "manifest.json").read_text())["architecture"]["removed_local_import_edges"], 0)


if __name__ == "__main__":
    unittest.main()
