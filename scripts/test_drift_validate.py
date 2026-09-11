#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path

from drift_validate import validate_registration, validate_labels, validate_run


class DriftValidationTests(unittest.TestCase):
    def registration(self):
        return {
            "schema": "tiny-fleet.drift-validation-registration/v1",
            "run_id": "drift-validation-v1",
            "claim": "validate drift metrics against independent change evidence",
            "estimands": ["structural", "lexical", "generative", "behavioral"],
            "repositories": [
                {"repo_id": "r1", "old": "a" * 40, "new": "b" * 40, "license": "MIT", "source_family": "f1"},
                {"repo_id": "r2", "old": "c" * 40, "new": "d" * 40, "license": "MIT", "source_family": "f2"},
                {"repo_id": "r3", "old": "e" * 40, "new": "f" * 40, "license": "MIT", "source_family": "f3"},
            ],
            "label_schema": {
                "labels": ["no_change", "cosmetic", "interface_change", "dependency_change", "behavior_change"],
                "reviewers_required": 2,
                "model_scores_allowed": False,
            },
            "score_reveal": False,
        }

    def labels(self):
        return [
            {"unit_id": "r1:u1", "repo_id": "r1", "evidence_kind": "commit_diff", "change_class": "interface_change", "unit_kind": "architectural", "reviewers": ["alice", "bob"], "adjudication": "interface_change", "evidence": {"old_path": "api.py", "new_path": "api.py", "added_symbols": ["v2"]}},
            {"unit_id": "r2:u1", "repo_id": "r2", "evidence_kind": "native_test", "change_class": "behavior_change", "unit_kind": "architectural", "reviewers": ["alice", "bob"], "adjudication": "behavior_change", "evidence": {"test": "test_new_behavior", "old_exit": 1, "new_exit": 0}},
            {"unit_id": "r3:u1", "repo_id": "r3", "evidence_kind": "release_note", "change_class": "cosmetic", "unit_kind": "cosmetic", "reviewers": ["alice", "bob"], "adjudication": "cosmetic", "evidence": {"summary": "typo fix"}},
        ]

    def test_valid_fixture_is_preliminary_without_model_scores(self):
        validate_registration(self.registration())
        validate_labels(self.registration(), self.labels())
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "registration.json").write_text(json.dumps(self.registration()))
            (root / "labels.jsonl").write_text("\n".join(json.dumps(row) for row in self.labels()) + "\n")
            result = validate_run(root)
        self.assertEqual(result["status"], "preliminary")
        self.assertEqual(result["coverage"]["repositories"], 3)

    def test_cosmetic_and_no_change_cannot_be_architecture_change(self):
        rows = self.labels()
        rows[2]["change_class"] = "interface_change"
        rows[2]["adjudication"] = "interface_change"
        with self.assertRaisesRegex(ValueError, "cosmetic"):
            validate_labels(self.registration(), rows)

    def test_label_leakage_is_rejected(self):
        registration = self.registration()
        registration["label_schema"]["model_scores_allowed"] = False
        rows = self.labels()
        rows[0]["model_score"] = 0.99
        with self.assertRaisesRegex(ValueError, "leakage"):
            validate_labels(registration, rows)

    def test_reviewer_disagreement_is_retained_and_requires_adjudication(self):
        rows = self.labels()
        rows[0]["reviewers"] = ["alice", "bob"]
        rows[0]["reviewer_labels"] = {"alice": "interface_change", "bob": "cosmetic"}
        rows[0]["adjudication"] = None
        with self.assertRaisesRegex(ValueError, "adjudication"):
            validate_labels(self.registration(), rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
