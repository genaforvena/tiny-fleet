#!/usr/bin/env python3
"""Contract tests for the dependency-free deep-evaluation validator."""

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from deep_evaluation import ValidationError, validate_run


class DeepEvaluationValidatorTests(unittest.TestCase):
    def make_run(self):
        root = Path(tempfile.mkdtemp())
        (root / "manifest.json").write_text(json.dumps({
            "schema": "tiny-fleet.deep-eval.manifest/v1",
            "run_id": "fixture-001",
            "git_commit": "a" * 40,
            "base_model": {"id": "base", "revision": "r1"},
            "candidate": {"id": "candidate", "revision": "b" * 64},
            "controls": ["base"], "seed": 17,
            "config_sha256": "c" * 64,
            "created_at": "2026-09-06T00:00:00Z",
            "cutoff": "2026-09-01T00:00:00Z",
            "datasets": {
                "train": {"path": "train.jsonl", "rows": 1, "sha256": ""},
                "validation": {"path": "validation.jsonl", "rows": 1, "sha256": ""},
                "heldout": {"path": "heldout.jsonl", "rows": 1, "sha256": ""},
                "adversarial": {"path": "adversarial.jsonl", "rows": 1, "sha256": ""},
            },
            "slices": ["domain"],
            "evaluation": {"bootstrap_replicates": 10, "confidence": 0.95},
        }))
        row = lambda split, case: {
            "case_id": case, "source_id": f"source-{case}",
            "created_at": "2026-08-01T00:00:00Z", "domain": "fixture",
            "language": "en", "split": split, "expected_route": "specialist:fixture",
            "expected_action": "answer",
            "provenance": {"kind": "synthetic", "source": "test", "redacted": True},
        }
        for name, split, case in (("train", "train", "train-1"),
                                  ("validation", "validation", "validation-1"),
                                  ("heldout", "heldout", "heldout-1"),
                                  ("adversarial", "adversarial", "adversarial-1")):
            (root / f"{name}.jsonl").write_text(json.dumps(row(split, case)) + "\n")
        for name in ("config.json", "environment.txt", "scores.json", "slices.tsv",
                     "calibration.tsv", "routing.tsv", "adversarial.tsv", "cost.tsv", "decision.md"):
            (root / name).write_text("fixture\n")
        (root / "predictions.jsonl").write_text("\n".join(
            json.dumps({"case_id": case, "model": model})
            for case in ("heldout-1", "adversarial-1")
            for model in ("base", "candidate")) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["config_sha256"] = hashlib.sha256((root / "config.json").read_bytes()).hexdigest()
        for split in ("train", "validation", "heldout", "adversarial"):
            path = root / f"{split}.jsonl"
            manifest["datasets"][split]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        return root

    def test_accepts_complete_fixture(self):
        self.assertEqual(validate_run(self.make_run()), "ACCEPT")

    def test_rejects_missing_artifact(self):
        root = self.make_run()
        (root / "environment.txt").unlink()
        with self.assertRaisesRegex(ValidationError, r"^REJECT missing-artifact environment.txt$"):
            validate_run(root)

    def test_rejects_case_leakage(self):
        root = self.make_run()
        row = json.loads((root / "train.jsonl").read_text())
        row["case_id"] = "heldout-1"
        (root / "train.jsonl").write_text(json.dumps(row) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["train"]["sha256"] = hashlib.sha256((root / "train.jsonl").read_bytes()).hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT leakage"):
            validate_run(root)

    def test_rejects_split_boundary(self):
        root = self.make_run()
        row = json.loads((root / "heldout.jsonl").read_text())
        row["source_id"] = "source-train"
        row["created_at"] = "2026-09-02T00:00:00Z"
        (root / "heldout.jsonl").write_text(json.dumps(row) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["heldout"]["sha256"] = hashlib.sha256((root / "heldout.jsonl").read_bytes()).hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT split-boundary"):
            validate_run(root)

    def test_rejects_manifest_mismatch(self):
        root = self.make_run()
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["train"]["sha256"] = "d" * 64
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT manifest-mismatch"):
            validate_run(root)

    def test_rejects_prediction_cardinality(self):
        root = self.make_run()
        (root / "predictions.jsonl").write_text(json.dumps({"case_id": "unknown", "model": "base"}) + "\n")
        with self.assertRaisesRegex(ValidationError, r"^REJECT prediction-cardinality"):
            validate_run(root)


if __name__ == "__main__":
    unittest.main()
