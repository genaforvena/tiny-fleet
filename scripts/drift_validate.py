#!/usr/bin/env python3
"""Validate preregistered change labels without looking at drift scores."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


SCHEMA = "tiny-fleet.drift-validation-registration/v1"
LABELS = {"no_change", "cosmetic", "interface_change", "dependency_change", "behavior_change"}
ARCHITECTURAL = {"interface_change", "dependency_change", "behavior_change"}
EVIDENCE = {"release_note", "commit_diff", "native_test"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_registration(registration: dict) -> dict:
    _require(registration.get("schema") == SCHEMA, "registration schema")
    _require(registration.get("run_id") and registration.get("claim"), "registration identity")
    _require(set(registration.get("estimands", [])) == {"structural", "lexical", "generative", "behavioral"}, "estimands must remain separate")
    repos = registration.get("repositories", [])
    _require(len(repos) >= 3, "at least three independent repositories required")
    ids = set()
    for repo in repos:
        repo_id = repo.get("repo_id")
        _require(repo_id and repo_id not in ids, "duplicate repository")
        ids.add(repo_id)
        for key in ("old", "new"):
            _require(isinstance(repo.get(key), str) and len(repo[key]) == 40 and all(c in "0123456789abcdef" for c in repo[key]), "snapshot must be immutable 40-hex commit")
        _require(repo["old"] != repo["new"], "snapshot pair must differ")
        _require(repo.get("license") and repo.get("source_family"), "repository provenance")
    schema = registration.get("label_schema", {})
    _require(set(schema.get("labels", [])) == LABELS, "label vocabulary")
    _require(schema.get("reviewers_required") == 2, "two independent reviewers required")
    _require(schema.get("model_scores_allowed") is False, "label leakage policy")
    _require(registration.get("score_reveal") is False, "scores must remain blinded")
    if schema.get("objective_only"):
        _require(registration.get("semantic_generalization") is False, "objective-only labels cannot support semantic generalization")
    return {"repositories": len(repos), "repository_ids": sorted(ids)}


def validate_labels(registration: dict, rows: list[dict]) -> dict:
    validate_registration(registration)
    repo_ids = {repo["repo_id"] for repo in registration["repositories"]}
    _require(rows, "no labels")
    seen = set()
    disagreements = 0
    for row in rows:
        unit = row.get("unit_id")
        _require(unit and unit not in seen, "duplicate label unit")
        seen.add(unit)
        _require(row.get("repo_id") in repo_ids, "label repository is not registered")
        change_class = row.get("change_class")
        adjudication = row.get("adjudication")
        _require(change_class in LABELS and (adjudication in LABELS or adjudication is None), "unknown label")
        _require(row.get("evidence_kind") in EVIDENCE and isinstance(row.get("evidence"), dict) and row["evidence"], "objective evidence required")
        repo = next(repo for repo in registration["repositories"] if repo["repo_id"] == row["repo_id"])
        if registration["label_schema"].get("objective_only"):
            _require(row.get("label_basis") == "objective_interface", "objective-only registration requires objective interface labels")
            _require(row.get("unit_kind") == "interface" and change_class in {"interface_change", "cosmetic", "no_change"}, "objective interface labels cannot claim semantic or dependency changes")
            evidence = row["evidence"]
            _require(row["evidence_kind"] in {"commit_diff", "release_note"}, "objective interface evidence must be a release note or commit diff")
            _require(evidence.get("old_commit") == repo["old"] and evidence.get("new_commit") == repo["new"], "objective evidence snapshot binding")
            _require(isinstance(evidence.get("old_path"), str) and isinstance(evidence.get("new_path"), str), "objective interface source paths required")
            _require(isinstance(evidence.get("changed_public_symbols"), list) and evidence["changed_public_symbols"], "changed public symbols required")
            _require(isinstance(evidence.get("release_note_path"), str) and evidence["release_note_path"], "release note reference required")
            hash_fields = ("old_source_sha256", "new_source_sha256", "release_note_sha256")
            _require(all(isinstance(evidence.get(key), str) and len(evidence[key]) == 64 and all(char in "0123456789abcdef" for char in evidence[key]) for key in hash_fields), "evidence content hashes required")
            if any(evidence.get(key) for key in ("test_path", "test_reference", "test_source_sha256")):
                _require(all(isinstance(evidence.get(key), str) and evidence[key] for key in ("test_path", "test_reference")), "native-test reference incomplete")
                _require(isinstance(evidence.get("test_source_sha256"), str) and len(evidence["test_source_sha256"]) == 64 and all(char in "0123456789abcdef" for char in evidence["test_source_sha256"]), "native-test source hash required")
            _require(not row.get("reviewers") and not row.get("reviewer_labels") and adjudication is None, "objective labels must not impersonate independent reviewers")
        else:
            reviewers = row.get("reviewers", [])
            _require(len(reviewers) == 2 and len(set(reviewers)) == 2, "two distinct reviewers required")
            reviewer_labels = row.get("reviewer_labels")
            if reviewer_labels is not None:
                _require(set(reviewer_labels) == set(reviewers) and all(value in LABELS for value in reviewer_labels.values()), "reviewer labels")
                if len(set(reviewer_labels.values())) > 1:
                    disagreements += 1
                    _require(adjudication is not None, "adjudication required after reviewer disagreement")
            _require(adjudication == change_class, "adjudication does not match final label")
        _require(not any(key in row for key in ("model_score", "drift_score", "prediction", "score")), "label leakage: model scores are forbidden")
        if row.get("unit_kind") in {"no_change", "cosmetic"}:
            _require(change_class not in ARCHITECTURAL and adjudication not in ARCHITECTURAL, "cosmetic/no-change unit cannot be architecture change")
    covered = {row["repo_id"] for row in rows}
    _require(covered == repo_ids, "every registered repository needs labels")
    counts = Counter(row["change_class"] for row in rows)
    return {"units": len(rows), "repositories": len(covered), "counts": dict(sorted(counts.items())), "disagreements": disagreements, "reviewed_units": sum(1 for row in rows if row.get("label_basis") != "objective_interface"), "objective_only": bool(registration["label_schema"].get("objective_only"))}


def validate_run(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    registration_path = run_dir / "registration.json"
    labels_path = run_dir / "labels.jsonl"
    _require(registration_path.is_file() and labels_path.is_file(), "registration or labels artifact missing")
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if registration.get("label_schema", {}).get("objective_only"):
        unit_map_name = registration.get("unit_map")
        _require(isinstance(unit_map_name, str) and Path(unit_map_name).name == unit_map_name, "objective unit map must be a file in the run directory")
        unit_map_path = run_dir / unit_map_name
        _require(unit_map_path.is_file() and registration.get("unit_map_sha256") == _sha256(unit_map_path), "objective unit map hash mismatch")
        unit_map = json.loads(unit_map_path.read_text(encoding="utf-8"))
        _require(unit_map.get("schema") == "tiny-fleet.drift-unit-map/v1", "objective unit map schema")
        mapped_units = {item.get("unit_id"): item for item in unit_map.get("units", [])}
        _require(None not in mapped_units and len(mapped_units) == len(unit_map.get("units", [])), "duplicate or missing objective unit id")
        for row in rows:
            mapped = mapped_units.get(row.get("unit_id"))
            _require(mapped is not None and mapped.get("repo_id") == row.get("repo_id"), "label unit is absent from objective unit map")
            evidence = row.get("evidence", {})
            _require(mapped.get("old_path") == evidence.get("old_path") and mapped.get("new_path") == evidence.get("new_path"), "label paths do not match objective unit map")
            _require(mapped.get("selected_symbol") in evidence.get("changed_public_symbols", []), "label symbol does not match objective unit map")
    summary = validate_labels(registration, rows)
    result = {"schema": "tiny-fleet.drift-validation-run/v1", "run_id": registration["run_id"], "status": "preliminary", "reason": "model scores are blinded and external association is not computed", "registration_sha256": _sha256(registration_path), "labels_sha256": _sha256(labels_path), "coverage": summary, "estimands": registration["estimands"], "semantic_generalization": registration.get("semantic_generalization", True)}
    (run_dir / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if summary["objective_only"]:
        decision = (
            f"# Drift validation {registration['run_id']}\n\nStatus: `preliminary`\n\n"
            f"Frozen {summary['units']} objective public-interface labels from immutable source diffs and release-note evidence. "
            "No independent reviewers are claimed; semantic generalization is withheld. "
            "Behavioral and generative scores remain blinded and no cross-repository association is computed. "
            "The next gate is independent D04-V verification before any score comparison.\n"
        )
    else:
        decision = (
            f"# Drift validation {registration['run_id']}\n\nStatus: `preliminary`\n\n"
            "Labels are frozen from independent repository evidence. Model scores and cross-repository associations remain "
            "blinded and are not claimed by this fixture. The next action is an independent D04-V review before any score comparison.\n"
        )
    (run_dir / "decision.md").write_text(decision, encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(validate_run(args.run_dir), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
