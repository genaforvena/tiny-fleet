#!/usr/bin/env python3
"""Acceptance tests for immutable training-run preparation."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_manifest import ManifestError, prepare_run, record_completion, step_count


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RunManifestTests(unittest.TestCase):
    def manifest(self, root: Path, rows: int = 5) -> Path:
        data = root / "train.jsonl"
        data.write_text("".join(json.dumps({"text": f"row-{i}"}) + "\n" for i in range(rows)))
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({
            "schema": "persona-code.manifest/v1",
            "base_model": {"id": "fake/base", "revision": "base-rev"},
            "tokenizer": {"id": "fake/base", "revision": "tok-rev"},
            "domains": {"demo": {"train": {"path": "train.jsonl", "sha256": digest(data), "rows": rows}}},
            "training": {"batch": 2, "gradient_accumulation": 2, "max_length": 128,
                          "epochs": 3, "learning_rate": 0.01},
            "evaluation": {"max_length": 128, "batch": 2},
        }))
        return manifest

    def test_corrupt_input_rejects_before_model_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); manifest = self.manifest(root)
            data = root / "train.jsonl"; data.write_text(data.read_text() + "corrupt\n")
            loaded = []
            with self.assertRaisesRegex(ManifestError, "input hash mismatch"):
                prepare_run(manifest, root / "run", 17, model_loader=lambda: loaded.append(True))
            self.assertEqual(loaded, [])

    def test_batch_accumulation_records_expected_steps(self):
        self.assertEqual(step_count(examples=5, epochs=3, batch=2, accumulation=2), 6)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); manifest = self.manifest(root)
            prepared = prepare_run(manifest, root / "run", 17)
            self.assertEqual(prepared["training"]["expected_optimizer_steps"], 6)
            self.assertEqual(prepared["training"]["examples"], 15)

    def test_seeds_get_distinct_non_overwriting_adapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); manifest = self.manifest(root)
            first = prepare_run(manifest, root / "run-17", 17, arm="demo")
            second = prepare_run(manifest, root / "run-29", 29, arm="demo")
            self.assertNotEqual(first["adapter_dir"], second["adapter_dir"])
            self.assertIn("seed-17", first["adapter_dir"])
            self.assertIn("seed-29", second["adapter_dir"])

    def test_resolved_config_pins_runtime_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); manifest = self.manifest(root)
            config = prepare_run(manifest, root / "run", 43, device="cpu", dtype="float32")
            self.assertEqual(config["base_model"]["revision"], "base-rev")
            self.assertEqual(config["tokenizer"]["revision"], "tok-rev")
            self.assertEqual(config["seeds"], {"python": 43, "numpy": 43, "torch": 43})
            self.assertEqual(config["runtime"], {"device": "cpu", "dtype": "float32"})
            record_completion(root / "run", {"status": "complete"})
            with self.assertRaisesRegex(ManifestError, "completed run"):
                prepare_run(manifest, root / "run", 43)


if __name__ == "__main__":
    unittest.main(verbosity=2)
