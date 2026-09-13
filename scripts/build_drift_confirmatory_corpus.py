#!/usr/bin/env python3
"""Build six license-filtered training corpora from the frozen confirmatory archives."""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath

from build_drift_train_corpus import classify_file, split_paths


RUN = Path("runs/drift-confirmatory-v1")
REGISTRATION = RUN / "registration.json"
HELDOUT = RUN / "heldout-excerpts/heldout-excerpts.json"
BASE_MODEL = {"id": "HuggingFaceTB/SmolLM2-360M-Instruct", "revision": "a10cc1512eabd3dde888204e902eca88bddb4951"}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_repo_path(repo_root: Path, value: str) -> Path:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"registered path escapes repository: {value}")
    return repo_root.joinpath(*path.parts)


def build_snapshot(repo_root, output_root, registration, heldout, repo_id, snapshot):
    repo_root, output_root = Path(repo_root), Path(output_root)
    repo_row = next(row for row in registration["repositories"] if row["repo_id"] == repo_id)
    source = next(row for row in repo_row["snapshots"] if row["label"] == snapshot)
    prompt = next(row for row in heldout["prompts"] if row["repo"] == repo_id and row["snapshot"] == snapshot)
    archive_path = safe_repo_path(repo_root, source["archive"])
    archive_bytes = archive_path.read_bytes()
    archive_digest = sha256(archive_bytes)
    if archive_digest != source["archive_sha256"]:
        raise ValueError(f"archive hash mismatch: {repo_id}/{snapshot}")
    license_path = safe_repo_path(repo_root, source["license_copy"])
    license_bytes = license_path.read_bytes()
    if sha256(license_bytes) != source["license_sha256"]:
        raise ValueError(f"root license hash mismatch: {repo_id}/{snapshot}")

    heldout_source = PurePosixPath(prompt["source_path"])
    if heldout_source.is_absolute() or ".." in heldout_source.parts or len(heldout_source.parts) < 2:
        raise ValueError(f"invalid held-out source path: {prompt['source_path']}")
    package_root = heldout_source.parent
    inventory, contents = [], {}
    with tarfile.open(archive_path, "r:*") as archive:
        members = archive.getmembers()
        names = [member.name for member in members if member.name.rstrip("/")]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate archive member: {repo_id}/{snapshot}")
        exact_heldout = [member for member in members if PurePosixPath(member.name).as_posix() == heldout_source.as_posix()]
        wrapped_heldout = [member for member in members if len(PurePosixPath(member.name).parts) > 1
                           and PurePosixPath(*PurePosixPath(member.name).parts[1:]).as_posix() == heldout_source.as_posix()]
        if len(exact_heldout) == 1:
            archive_prefix = None
        elif not exact_heldout and len(wrapped_heldout) == 1:
            archive_prefix = PurePosixPath(wrapped_heldout[0].name).parts[0]
        else:
            raise ValueError(f"cannot uniquely bind held-out module to archive: {repo_id}/{snapshot}")
        for member in members:
            member_path = PurePosixPath(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(f"unsafe archive member: {member.name}")
            if not member_path.parts or member.isdir():
                continue
            if archive_prefix is not None:
                if member_path.parts[0] != archive_prefix:
                    raise ValueError(f"archive member outside single root: {member.name}")
                relative = PurePosixPath(*member_path.parts[1:])
            else:
                relative = member_path
            if not relative.parts:
                continue
            data = archive.extractfile(member).read() if member.isfile() else b""
            if member.isfile():
                mode = "100755" if member.mode & 0o111 else "100644"
            elif member.issym() or member.islnk():
                mode = "120000"
            else:
                mode = "100644"
            included, reason = classify_file(
                relative.as_posix(), mode, data, package_root=package_root.as_posix(),
                license_spdx=repo_row["license_spdx"], heldout_path=heldout_source.as_posix(),
            )
            row = {"path": relative.as_posix(), "mode": mode, "kind": "file" if member.isfile() else member.type.decode("ascii", "replace"),
                   "bytes": len(data), "sha256": sha256(data), "status": "included" if included else "excluded", "reason": reason}
            inventory.append(row)
            if included:
                contents[relative.as_posix()] = data.decode("utf-8")
    heldout_row = next((row for row in inventory if row["path"] == heldout_source.as_posix()), None)
    if heldout_row is None or heldout_row["sha256"] != prompt["source_file_sha256"]:
        raise ValueError(f"held-out source hash mismatch: {repo_id}/{snapshot}")
    inventory.sort(key=lambda row: row["path"])
    train_paths, validation_paths = split_paths(repo_id, snapshot, list(contents))
    target = output_root / f"{repo_id}-{snapshot}"
    target.mkdir(parents=True, exist_ok=True)
    (target / "LICENSE.txt").write_bytes(license_bytes)
    inventory_bytes = "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in inventory).encode()
    (target / "inventory.jsonl").write_bytes(inventory_bytes)

    def write_split(name, paths):
        records = [{"source_path": path, "source_file_sha256": next(row["sha256"] for row in inventory if row["path"] == path),
                    "text": f"### {path}\n{contents[path]}"} for path in paths]
        payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records).encode("utf-8")
        (target / f"{name}.jsonl").write_bytes(payload)
        return {"path": (target / f"{name}.jsonl").relative_to(repo_root).as_posix(), "rows": len(records), "sha256": sha256(payload)}

    train, validation = write_split("train", train_paths), write_split("validation", validation_paths)
    manifest = {
        "schema": "tiny-fleet.drift-confirmatory-training-corpus/v1",
        "run_id": registration["run_id"], "repo": repo_id, "snapshot": snapshot,
        "source_commit": source["commit"], "source_tag": source["tag"],
        "source_archive": source["archive"], "source_archive_sha256": archive_digest,
        "package_root": package_root.as_posix(),
        "license": {"spdx": repo_row["license_spdx"], "source_path": repo_row["license_path"],
                    "saved_path": (target / "LICENSE.txt").relative_to(repo_root).as_posix(),
                    "sha256": source["license_sha256"]},
        "sample_registration": {"path": REGISTRATION.as_posix(), "sha256": sha256((repo_root / REGISTRATION).read_bytes())},
        "heldout_excerpt_ledger": {"path": HELDOUT.as_posix(), "sha256": sha256((repo_root / HELDOUT).read_bytes()),
                                    "source_path_excluded": heldout_source.as_posix(),
                                    "source_file_sha256": prompt["source_file_sha256"]},
        "selection": {"allow": "regular UTF-8 Python source under package_root covered by the verified root license",
                      "exclude": ["tests", "test_*.py and *_test.py", "generated/vendor trees", "non-Python files", "symlinks and non-regular objects", "binary or malformed UTF-8", "selected held-out module"],
                      "validation_split": "ceil(10% of eligible files), deterministic SHA256(repo + NUL + snapshot + NUL + path) ranking",
                      "corpus_scope": "adaptation training only; every archive member file is listed in the inventory"},
        "inventory": {"path": (target / "inventory.jsonl").relative_to(repo_root).as_posix(), "rows": len(inventory),
                      "included": sum(row["status"] == "included" for row in inventory),
                      "excluded": sum(row["status"] == "excluded" for row in inventory), "sha256": sha256(inventory_bytes)},
        "corpus_builder": {"path": "scripts/build_drift_confirmatory_corpus.py",
                           "source_sha256": sha256((repo_root / "scripts/build_drift_confirmatory_corpus.py").read_bytes())},
        "train": train, "validation": validation,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["manifest_sha256"] = sha256(manifest_path.read_bytes())
    return manifest


def build_all(repo_root, output_root):
    repo_root = Path(repo_root).resolve()
    output_root = Path(output_root).resolve()
    registration_bytes = (repo_root / REGISTRATION).read_bytes()
    heldout_bytes = (repo_root / HELDOUT).read_bytes()
    registration, heldout = json.loads(registration_bytes), json.loads(heldout_bytes)
    if registration.get("schema") != "tiny-fleet.drift-confirmatory-registration/v1" or registration.get("status") != "frozen_pending_independent_verification":
        raise ValueError("confirmatory sample registration is not frozen")
    if heldout.get("sample_manifest_sha256") != sha256(registration_bytes):
        raise ValueError("held-out ledger is not bound to the current sample registration")
    if len(registration.get("repositories", [])) != 3 or len(heldout.get("prompts", [])) != 6:
        raise ValueError("confirmatory sample must contain three repository pairs and six excerpts")
    records = [build_snapshot(repo_root, output_root, registration, heldout, repo["repo_id"], snap["label"])
               for repo in sorted(registration["repositories"], key=lambda item: item["repo_id"])
               for snap in sorted(repo["snapshots"], key=lambda item: item["label"])]
    runner_path = repo_root / "scripts/train_drift_adapters.py"
    plan = {
        "schema": "tiny-fleet.drift-confirmatory-adapter-training-plan/v1",
        "status": "corpora-built-no-training-run-yet",
        "sample_registration": {"path": REGISTRATION.as_posix(), "sha256": sha256(registration_bytes)},
        "heldout_excerpt_ledger": {"path": HELDOUT.as_posix(), "sha256": sha256(heldout_bytes)},
        "corpus_builder": {"path": "scripts/build_drift_confirmatory_corpus.py",
                           "source_sha256": sha256((repo_root / "scripts/build_drift_confirmatory_corpus.py").read_bytes())},
        "training_runner": {"path": "scripts/train_drift_adapters.py", "source_sha256": sha256(runner_path.read_bytes())},
        "base_model": BASE_MODEL,
        "training": {"seed": 17, "epochs": 1, "max_sequence_length": 256,
                     "train_token_budget_per_adapter": 16384, "validation_token_budget_per_adapter": 4096,
                     "sequence_sampling": "non-overlapping 256-token chunks, ranked by SHA256(repo + NUL + snapshot + NUL + source path + NUL + chunk index), then take the lowest ranks up to the budget",
                     "batch_size": 1, "gradient_accumulation": 4, "learning_rate": 0.0002,
                     "weight_decay": 0.01, "max_gradient_norm": 1.0,
                     "lora": {"rank": 8, "alpha": 16, "dropout": 0.05,
                              "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]},
                     "validation": "token-weighted causal-language-model loss on the file-disjoint deterministic 10% split; adaptation diagnostic only",
                     "resource_admission": "GPU required; mesh-heavy-run RAM ceiling 8192 MiB, minimum free VRAM 8192 MiB, preempt enabled, lease TTL 1800s; exact managed-service restoration must be recorded"},
        "corpora": [{"repo": row["repo"], "snapshot": row["snapshot"],
                     "manifest_path": f"{Path(output_root).relative_to(repo_root).as_posix()}/{row['repo']}-{row['snapshot']}/manifest.json",
                     "manifest_sha256": row["manifest_sha256"], "train": row["train"], "validation": row["validation"],
                     "inventory": row["inventory"]} for row in records],
    }
    plan_path = Path(output_root) / "training-plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": plan_path.relative_to(repo_root).as_posix(), "corpora": len(records),
            "sha256": sha256(plan_path.read_bytes()),
            "included_files": sum(row["inventory"]["included"] for row in records),
            "excluded_files": sum(row["inventory"]["excluded"] for row in records)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build_all(args.repo_root, args.output_root), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
