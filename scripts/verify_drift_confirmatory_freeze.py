#!/usr/bin/env python3
"""Verify the frozen confirmatory sample without unpacking or changing snapshots."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REG_PATH = ROOT / "runs/drift-confirmatory-v1/registration.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def tar_file_hash(archive: Path, member: str) -> str:
    with tarfile.open(archive, "r:") as bundle:
        entry = bundle.extractfile(member)
        if entry is None:
            raise AssertionError(f"{archive}: missing regular member {member}")
        return sha(entry.read())


def main() -> int:
    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    assert reg["schema"] == "tiny-fleet.drift-confirmatory-registration/v1"
    assert reg["status"] == "frozen_pending_independent_verification"
    assert reg["comparison_authorized"] is False
    assert reg["model_scores_allowed"] is False

    selection_path = ROOT / reg["selection"]["path"]
    code_path = ROOT / reg["selection"]["code_path"]
    metadata_path = ROOT / reg["repository_metadata"]["path"]
    labels_path = ROOT / reg["labels"]["path"]
    assert file_sha(selection_path) == reg["selection"]["sha256"]
    assert file_sha(code_path) == reg["selection"]["code_sha256"]
    assert file_sha(metadata_path) == reg["repository_metadata"]["sha256"]
    assert file_sha(labels_path) == reg["labels"]["sha256"]

    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    selection_by_repo = {row["repo_id"]: row for row in selection["repositories"]}
    metadata_by_repo = {
        row["full_name"].rsplit("/", 1)[-1]: row for row in metadata["records"]
    }
    assert len(reg["repositories"]) == 3
    assert len({row["owner_namespace"] for row in reg["repositories"]}) == 3
    labels = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines()]
    assert len(labels) == reg["labels"]["count"] == 3
    assert {row["repo_id"] for row in labels} == {row["repo_id"] for row in reg["repositories"]}

    snapshots_by_repo = {}
    for repository in reg["repositories"]:
        assert repository["metadata"]["fork"] is False
        assert repository["metadata"]["archived"] is False
        assert repository["metadata"]["spdx"] == repository["license_spdx"]
        api_record = metadata_by_repo[repository["repo_id"]]
        assert repository["metadata"] == {
            "full_name": api_record["full_name"],
            "fork": api_record["fork"],
            "archived": api_record["archived"],
            "spdx": api_record["spdx"],
        }
        selected = selection_by_repo[repository["repo_id"]]
        assert selected["identity"] == repository["source_url"].removesuffix(".git")
        assert selected["owner_namespace"] == repository["owner_namespace"]
        assert len(repository["snapshots"]) == 2
        snapshots_by_repo[repository["repo_id"]] = {item["label"]: item for item in repository["snapshots"]}

        selected_snapshots = {item["label"]: item for item in selected["snapshots"]}
        for snapshot in repository["snapshots"]:
            assert snapshot["commit"] == selected_snapshots[snapshot["label"]]["commit"]
            archive = ROOT / snapshot["archive"]
            license_copy = ROOT / snapshot["license_copy"]
            assert archive.stat().st_size == snapshot["archive_bytes"]
            assert file_sha(archive) == snapshot["archive_sha256"]
            assert file_sha(license_copy) == snapshot["license_sha256"]
            assert tar_file_hash(archive, repository["license_path"]) == snapshot["license_sha256"]

    for label in labels:
        repository = next(row for row in reg["repositories"] if row["repo_id"] == label["repo_id"])
        pair = snapshots_by_repo[label["repo_id"]]
        evidence = label["evidence"]
        assert evidence["old_commit"] == pair["old"]["commit"]
        assert evidence["new_commit"] == pair["new"]["commit"]
        assert tar_file_hash(ROOT / pair["old"]["archive"], evidence["old_path"]) == evidence["old_source_sha256"]
        assert tar_file_hash(ROOT / pair["new"]["archive"], evidence["new_path"]) == evidence["new_source_sha256"]
        assert tar_file_hash(ROOT / pair["new"]["archive"], evidence["release_note_path"]) == evidence["release_note_sha256"]
        if "test_path" in evidence:
            assert tar_file_hash(ROOT / pair["old"]["archive"], evidence["test_path"]) == evidence["old_test_source_sha256"]
            assert tar_file_hash(ROOT / pair["new"]["archive"], evidence["test_path"]) == evidence["new_test_source_sha256"]
        if "public_export_path" in evidence:
            assert tar_file_hash(ROOT / pair["old"]["archive"], evidence["public_export_path"]) == evidence["old_public_export_sha256"]
            assert tar_file_hash(ROOT / pair["new"]["archive"], evidence["public_export_path"]) == evidence["new_public_export_sha256"]
        if "old_public_export_path" in evidence:
            assert tar_file_hash(ROOT / pair["old"]["archive"], evidence["old_public_export_path"]) == evidence["old_public_export_sha256"]
            assert tar_file_hash(ROOT / pair["new"]["archive"], evidence["new_public_export_path"]) == evidence["new_public_export_sha256"]

    for preserved in reg["prior_registration_preserved"]:
        assert file_sha(ROOT / preserved["path"]) == preserved["sha256"], preserved["path"]

    prior_sample = json.loads(
        (ROOT / "docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json").read_text(encoding="utf-8")
    )
    prior_repo_ids = {row["repo_id"] for row in prior_sample["repositories"]}
    assert not ({row["repo_id"] for row in reg["repositories"]} & prior_repo_ids)

    print(
        "verify_drift_confirmatory_freeze: PASS "
        f"(3 repositories, 6 immutable archives, {len(labels)} source-backed labels, "
        "all license/source/release/test hashes and prior registrations verified; no inference)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
