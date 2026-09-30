#!/usr/bin/env python3
import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from build_drift_confirmatory_corpus import build_snapshot


class ConfirmatoryCorpusTests(unittest.TestCase):
    def make_sample(self, root):
        archive = root / "snapshot.tar"
        files = {
            "attrs-src/src/attr/filters.py": b"# SPDX-License-Identifier: MIT\ndef include(): pass\n",
            "attrs-src/src/attr/core.py": b"# SPDX-License-Identifier: MIT\ndef core(): pass\n",
            "attrs-src/src/attr/tests/test_filters.py": b"def test_include(): pass\n",
            "attrs-src/src/attr/cli.py": b"# held out source\n",
            "attrs-src/README.md": b"attrs sample\n",
        }
        with tarfile.open(archive, "w") as tar:
            for name, data in files.items():
                item = tarfile.TarInfo(name)
                item.size = len(data)
                tar.addfile(item, io.BytesIO(data))
        license_bytes = b"MIT License\n"
        license_path = root / "license.txt"
        license_path.write_bytes(license_bytes)
        archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        license_hash = hashlib.sha256(license_bytes).hexdigest()
        registration = {
            "schema": "tiny-fleet.drift-confirmatory-registration/v1",
            "run_id": "drift-confirmatory-v1",
            "repositories": [{
                "repo_id": "attrs",
                "license_spdx": "MIT",
                "license_path": "LICENSE",
                "snapshots": [{
                    "label": "old", "tag": "1.0.0", "commit": "a" * 40,
                    "archive": "snapshot.tar", "archive_sha256": archive_hash,
                    "license_copy": "license.txt", "license_sha256": license_hash,
                }],
            }],
        }
        heldout = {"prompts": [{
            "repo": "attrs", "snapshot": "old", "source_path": "src/attr/cli.py",
            "source_file_sha256": hashlib.sha256(files["attrs-src/src/attr/cli.py"]).hexdigest(),
        }]}
        (root / "runs/drift-confirmatory-v1").mkdir(parents=True)
        (root / "runs/drift-confirmatory-v1/registration.json").write_text(json.dumps(registration))
        (root / "runs/drift-confirmatory-v1/heldout-excerpts").mkdir()
        (root / "runs/drift-confirmatory-v1/heldout-excerpts/heldout-excerpts.json").write_text(json.dumps(heldout))
        (root / "scripts").mkdir(exist_ok=True)
        (root / "scripts/build_drift_confirmatory_corpus.py").write_text("# fixture builder\n")
        return registration, heldout, archive

    def test_builds_hash_bound_splits_excluding_the_registered_heldout_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registration, heldout, _archive = self.make_sample(root)
            result = build_snapshot(root, root / "out", registration, heldout, "attrs", "old")
            self.assertEqual(result["source_commit"], "a" * 40)
            self.assertEqual(result["source_archive_sha256"], registration["repositories"][0]["snapshots"][0]["archive_sha256"])
            self.assertEqual(result["train"]["rows"] + result["validation"]["rows"], 2)
            manifest_path = root / "out/attrs-old/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["heldout_excerpt_ledger"]["source_path_excluded"], "src/attr/cli.py")
            train_paths = [root / "out/attrs-old" / key for key in ("train.jsonl", "validation.jsonl")]
            combined = "\n".join(path.read_text() for path in train_paths)
            self.assertNotIn("cli.py", combined)
            self.assertNotIn("tests/test_filters.py", combined)
            self.assertEqual(manifest["train"]["sha256"], hashlib.sha256(train_paths[0].read_bytes()).hexdigest())

    def test_rejects_an_archive_that_does_not_match_the_frozen_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registration, heldout, archive = self.make_sample(root)
            archive.write_bytes(archive.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "archive hash mismatch"):
                build_snapshot(root, root / "out", registration, heldout, "attrs", "old")


if __name__ == "__main__":
    unittest.main(verbosity=2)
