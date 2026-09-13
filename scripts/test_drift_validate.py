#!/usr/bin/env python3
import copy
import hashlib
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

    def test_objective_interface_subset_does_not_require_invented_reviewers(self):
        registration = self.registration()
        registration["label_schema"]["objective_only"] = True
        registration["semantic_generalization"] = False
        row = self.labels()[0]
        row.update({
            "unit_id": "r1:public-interface",
            "unit_kind": "interface",
            "label_basis": "objective_interface",
            "evidence_kind": "commit_diff",
            "evidence": {
                "old_commit": "a" * 40,
                "new_commit": "b" * 40,
                "old_path": "api.py",
                "new_path": "api.py",
                "changed_public_symbols": ["Client.new_method"],
                "release_note_path": "CHANGELOG.md",
                "old_source_sha256": "0" * 64,
                "new_source_sha256": "1" * 64,
                "release_note_sha256": "2" * 64,
            },
        })
        row.pop("reviewers")
        row.pop("adjudication")
        row.pop("reviewer_labels", None)
        rows = [row]
        for repo in registration["repositories"][1:]:
            next_row = copy.deepcopy(row)
            next_row["unit_id"] = f"{repo['repo_id']}:public-interface"
            next_row["repo_id"] = repo["repo_id"]
            next_row["evidence"]["old_commit"] = repo["old"]
            next_row["evidence"]["new_commit"] = repo["new"]
            rows.append(next_row)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unit_map = {
                "schema": "tiny-fleet.drift-unit-map/v1",
                "units": [
                    {
                        "unit_id": item["unit_id"],
                        "repo_id": item["repo_id"],
                        "old_path": item["evidence"]["old_path"],
                        "new_path": item["evidence"]["new_path"],
                        "selected_symbol": item["evidence"]["changed_public_symbols"][0],
                    }
                    for item in rows
                ],
            }
            unit_map_bytes = (json.dumps(unit_map, sort_keys=True) + "\n").encode()
            (root / "unit-map.json").write_bytes(unit_map_bytes)
            registration["unit_map"] = "unit-map.json"
            registration["unit_map_sha256"] = hashlib.sha256(unit_map_bytes).hexdigest()
            (root / "registration.json").write_text(json.dumps(registration))
            (root / "labels.jsonl").write_text("\n".join(json.dumps(item) for item in rows) + "\n")
            result = validate_run(root)
            decision = (root / "decision.md").read_text()
            (root / "unit-map.json").write_text("{}\n")
            with self.assertRaisesRegex(ValueError, "unit map hash mismatch"):
                validate_run(root)
        self.assertEqual(result["coverage"]["units"], 3)
        self.assertEqual(result["coverage"]["reviewed_units"], 0)
        self.assertTrue(result["coverage"]["objective_only"])
        self.assertIn("semantic generalization is withheld", decision)

    def test_objective_only_cannot_label_semantic_behavior_without_reviewers(self):
        registration = self.registration()
        registration["label_schema"]["objective_only"] = True
        registration["semantic_generalization"] = False
        row = self.labels()[0]
        row.update({"label_basis": "objective_interface", "change_class": "behavior_change"})
        row.pop("reviewers")
        row.pop("adjudication")
        row.pop("reviewer_labels", None)
        with self.assertRaisesRegex(ValueError, "objective interface labels"):
            validate_labels(registration, [row])

    def test_objective_interface_evidence_requires_source_hashes(self):
        registration = self.registration()
        registration["label_schema"]["objective_only"] = True
        registration["semantic_generalization"] = False
        row = copy.deepcopy(self.labels()[0])
        row.update({"label_basis": "objective_interface", "unit_kind": "interface"})
        row.pop("reviewers")
        row.pop("adjudication")
        row["evidence"].update({
            "old_commit": "a" * 40,
            "new_commit": "b" * 40,
            "old_path": "api.py",
            "new_path": "api.py",
            "changed_public_symbols": ["Client.new_method"],
            "release_note_path": "CHANGELOG.md",
            "old_source_sha256": "0" * 64,
            "release_note_sha256": "2" * 64,
        })
        rows = [row]
        for repo in registration["repositories"][1:]:
            next_row = copy.deepcopy(row)
            next_row["unit_id"] = f"{repo['repo_id']}:public-interface"
            next_row["repo_id"] = repo["repo_id"]
            next_row["evidence"]["old_commit"] = repo["old"]
            next_row["evidence"]["new_commit"] = repo["new"]
            next_row["evidence"]["new_source_sha256"] = "1" * 64
            rows.append(next_row)
        with self.assertRaisesRegex(ValueError, "evidence content hashes required"):
            validate_labels(registration, rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
