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
            "schema": "tiny-fleet.deep-eval.manifest/v2",
            "run_id": "fixture-001",
            "git_commit": "a" * 40,
            "base_model": {"id": "base", "revision": "r1"},
            "candidate": {"id": "candidate", "revision": "b" * 64},
            "controls": ["base"], "seed": 17,
            "prediction_matrix": {"models": ["base", "candidate"], "seeds": [17], "repetitions": [0]},
            "raw_output_schema": "tiny-fleet.predictions/v1",
            "migration_report": {"status": "none"},
            "rendering": {"template_sha256": "e" * 64, "config_sha256": ""},
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
            "temporal": {"train_end": "2026-08-01T00:00:00Z", "heldout_start": "2026-08-01T00:00:00Z"},
        }))
        row = lambda split, case: {
            "case_id": case, "source_id": f"source-{case}",
            "created_at": "2026-08-01T00:00:00Z", "domain": "fixture",
            "language": "en", "split": split, "expected_route": "specialist:fixture",
            "expected_action": "answer",
            "prompt": f"Prompt for {case}", "reference": f"Reference for {case}",
            "source_family": f"family-{case}",
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
        predictions = []
        for case in ("heldout-1", "adversarial-1"):
            for model in ("base", "candidate"):
                prompt = f"Prompt for {case}"
                rendered = f"{model}: {prompt}"
                predictions.append({
                    "case_id": case, "model": model, "seed": 17, "repetition": 0,
                    "case_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "rendered_input": rendered,
                    "rendered_input_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
                    "output": "answer", "route": "specialist:fixture", "action": "answer",
                    "confidence": 0.75, "confidence_kind": "heuristic", "latency_ms": 2.5,
                    "status": "ok",
                })
        (root / "predictions.jsonl").write_text("\n".join(json.dumps(p) for p in predictions) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["config_sha256"] = hashlib.sha256((root / "config.json").read_bytes()).hexdigest()
        manifest["rendering"]["config_sha256"] = manifest["config_sha256"]
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
        with self.assertRaisesRegex(ValidationError, r"^REJECT prediction-schema"):
            validate_run(root)

    def test_rejects_duplicate_prediction_pair(self):
        root = self.make_run()
        lines = (root / "predictions.jsonl").read_text().splitlines()
        lines.append(lines[0])
        (root / "predictions.jsonl").write_text("\n".join(lines) + "\n")
        with self.assertRaisesRegex(ValidationError, r"^REJECT prediction-cardinality.*duplicate"):
            validate_run(root)

    def test_rejects_unknown_model_and_duplicate_model_ids(self):
        root = self.make_run()
        prediction = json.loads((root / "predictions.jsonl").read_text().splitlines()[0])
        prediction["model"] = "unknown"
        (root / "predictions.jsonl").write_text(json.dumps(prediction) + "\n")
        with self.assertRaisesRegex(ValidationError, r"^REJECT prediction-cardinality.*unknown model"):
            validate_run(root)
        root = self.make_run()
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["prediction_matrix"]["models"] = ["base", "base"]
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT manifest-mismatch.*duplicate model"):
            validate_run(root)

    def test_rejects_stale_input_hashes(self):
        root = self.make_run()
        prediction = json.loads((root / "predictions.jsonl").read_text().splitlines()[0])
        prediction["case_prompt_sha256"] = "0" * 64
        (root / "predictions.jsonl").write_text(json.dumps(prediction) + "\n")
        with self.assertRaisesRegex(ValidationError, r"^REJECT prediction-input.*case_prompt_sha256"):
            validate_run(root)

    def test_rejects_invalid_types_and_missing_status_fields(self):
        mutations = (("confidence", float("nan"), "confidence"),
                      ("latency_ms", -1, "latency"),
                      ("output", None, "output"))
        for field, value, label in mutations:
            with self.subTest(field=field):
                root = self.make_run()
                prediction = json.loads((root / "predictions.jsonl").read_text().splitlines()[0])
                prediction[field] = value
                (root / "predictions.jsonl").write_text(json.dumps(prediction) + "\n")
                with self.assertRaisesRegex(ValidationError, rf"^REJECT prediction-schema.*{label}"):
                    validate_run(root)

    def test_rejects_absent_timeout_row(self):
        root = self.make_run()
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["prediction_matrix"]["repetitions"] = [0, 1]
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT prediction-cardinality"):
            validate_run(root)

    def test_accepts_typed_timeout_row(self):
        root = self.make_run()
        lines = (root / "predictions.jsonl").read_text().splitlines()
        prediction = json.loads(lines[0])
        prediction.update({"status": "timeout", "output": None, "confidence": None,
                           "latency_ms": None, "unavailable_reason": "backend timeout"})
        lines[0] = json.dumps(prediction)
        (root / "predictions.jsonl").write_text("\n".join(lines) + "\n")
        self.assertEqual(validate_run(root), "ACCEPT")

    def test_rejects_duplicate_ids_within_split(self):
        root = self.make_run()
        rows = [json.loads(line) for line in (root / "train.jsonl").read_text().splitlines()]
        rows.append(rows[0])
        (root / "train.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["train"]["rows"] = 2
        manifest["datasets"]["train"]["sha256"] = hashlib.sha256((root / "train.jsonl").read_bytes()).hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT manifest-mismatch.*duplicate case_id"):
            validate_run(root)

    def test_rejects_normalized_prompt_cross_split(self):
        root = self.make_run()
        row = json.loads((root / "validation.jsonl").read_text())
        row["prompt"] = "  PROMPT   FOR   train-1 "
        (root / "validation.jsonl").write_text(json.dumps(row) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["validation"]["sha256"] = hashlib.sha256((root / "validation.jsonl").read_bytes()).hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT leakage.*normalized prompt"):
            validate_run(root)

    def test_rejects_source_family_overlap(self):
        root = self.make_run()
        row = json.loads((root / "heldout.jsonl").read_text())
        row["source_family"] = "family-validation-1"
        (root / "heldout.jsonl").write_text(json.dumps(row) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["heldout"]["sha256"] = hashlib.sha256((root / "heldout.jsonl").read_bytes()).hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT split-boundary.*source_family"):
            validate_run(root)

    def test_rejects_required_empty_split(self):
        root = self.make_run()
        (root / "validation.jsonl").write_text("")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["validation"]["rows"] = 0
        manifest["datasets"]["validation"]["sha256"] = hashlib.sha256(b"").hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT manifest-mismatch.*empty validation"):
            validate_run(root)

    def test_rejects_malformed_typed_row(self):
        root = self.make_run()
        row = json.loads((root / "train.jsonl").read_text())
        row["prompt"] = 12
        (root / "train.jsonl").write_text(json.dumps(row) + "\n")
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["train"]["sha256"] = hashlib.sha256((root / "train.jsonl").read_bytes()).hexdigest()
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT manifest-mismatch.*prompt"):
            validate_run(root)

    def test_rejects_symlink_escape_without_opening_target(self):
        root = self.make_run()
        outside = Path(tempfile.mkdtemp()) / "outside.jsonl"
        outside.write_text(json.dumps({"secret": True}) + "\n")
        link = root / "escape.jsonl"
        link.symlink_to(outside)
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["datasets"]["validation"]["path"] = "escape.jsonl"
        manifest["datasets"]["validation"]["sha256"] = "0" * 64
        (root / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValidationError, r"^REJECT manifest-mismatch.*outside run"):
            validate_run(root)


if __name__ == "__main__":
    unittest.main()
