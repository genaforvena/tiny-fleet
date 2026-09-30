#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from drift_result import Unknown, operate


class DriftResultTests(unittest.TestCase):
    def test_effect_before_receipt_restart_and_changed_input(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo, root = base / "repo", base / "results"
            repo.mkdir(); root.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            for key, value in (("user.email", "test@example.invalid"), ("user.name", "Test")):
                subprocess.run(["git", "-C", str(repo), "config", key, value], check=True)

            def commit(text):
                (repo / "module.py").write_text(text)
                subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
                subprocess.run(["git", "-C", str(repo), "commit", "-qm", "snapshot"], check=True)
                return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

            old = commit("VALUE = 1\n")
            new = commit("VALUE = 2\n")
            self.assertEqual(operate(repo, old, new, root)["status"], "eligible")
            command = [sys.executable, str(Path(__file__).with_name("drift_result.py")),
                       "--repo", str(repo), "--old", old, "--new", new, "--root", str(root),
                       "--publish", "--kill-after-rename"]
            killed = subprocess.run(command, capture_output=True)
            self.assertEqual(killed.returncode, -9)
            first = operate(repo, old, new, root)
            self.assertEqual(first["status"], "settled")
            self.assertEqual(operate(repo, old, new, root, publish=True), first)
            self.assertEqual(len(list(root.glob("*/receipt.json"))), 1)
            self.assertEqual(json.loads(Path(first["receipt"]).read_text())["key"], first["key"])
            later = commit("VALUE = 3\n")
            self.assertEqual(operate(repo, old, later, root)["status"], "eligible")
            (Path(first["receipt"]).parent / "manifest.json").write_text("tampered\n")
            with self.assertRaises(Unknown):
                operate(repo, old, new, root)

    def test_partial_stage_never_looks_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo, root = base / "repo", base / "results"
            repo.mkdir(); root.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "a.py").write_text("x = 1\n")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "one"], check=True)
            commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            key = operate(repo, commit, commit, root)["key"]
            (root / (".pending-" + key)).mkdir()
            with self.assertRaises(Unknown):
                operate(repo, commit, commit, root)


if __name__ == "__main__":
    unittest.main()
