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
    return {"units": len(rows), "repositories": len(covered), "counts": dict(sorted(counts.items())), "disagreements": disagreements}


def validate_run(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    registration_path = run_dir / "registration.json"
    labels_path = run_dir / "labels.jsonl"
    _require(registration_path.is_file() and labels_path.is_file(), "registration or labels artifact missing")
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = validate_labels(registration, rows)
    result = {"schema": "tiny-fleet.drift-validation-run/v1", "status": "preliminary", "reason": "model scores are blinded and external association is not computed", "registration_sha256": _sha256(registration_path), "labels_sha256": _sha256(labels_path), "coverage": summary, "estimands": registration["estimands"]}
    (run_dir / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "decision.md").write_text("# Drift validation v1\n\nStatus: `preliminary`\n\nLabels are frozen from independent repository evidence. Model scores and cross-repository associations remain blinded and are not claimed by this fixture. The next action is an independent D04-V review before any score comparison.\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(validate_run(args.run_dir), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
