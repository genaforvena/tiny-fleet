#!/usr/bin/env python3
"""Freeze source-only excerpts from the registered confirmatory-v1 archives.

This selector opens only the immutable sample registration and source archives.
It checks the objective-label ledger digest without reading its contents.
"""
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/drift-confirmatory-v1"
REGISTRATION = RUN / "registration.json"
LABELS = RUN / "labels.jsonl"
OUTPUT = RUN / "heldout-excerpts"
EXPECTED_REGISTRATION = "f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8"
EXPECTED_LABELS = "8bbb3047ebe375d5d0077e563b72d6d74578dfb21e1805fb6df1865038aeb5db"
PACKAGE_ROOTS = {"httpx": "httpx", "attrs": "src/attr", "pytest": "src/_pytest"}
LINES = 80
PROMPT_ID = "snapshot-component-description-v1"
PROMPT = (
    "Using only the supplied snapshot excerpt, describe the module's documented public responsibility "
    "and explicit behavioral guarantees. Cite the supplied path. Do not infer changes outside the "
    "excerpt; say 'not stated' when evidence is absent."
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def eligible(relative: PurePosixPath) -> bool:
    if relative.suffix != ".py":
        return False
    parts = [part.lower() for part in relative.parts]
    if any(part in {"test", "tests", "testing"} for part in parts):
        return False
    if any(part in {"vendor", "vendors", "generated", "_generated"} for part in parts):
        return False
    return not relative.name.startswith("test_") and not relative.name.endswith("_test.py")


def archive_members(path: Path) -> dict[str, tuple[tarfile.TarInfo, bytes]]:
    result = {}
    with tarfile.open(path, "r") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            stream = archive.extractfile(member)
            if stream is not None:
                result[member.name] = (member, stream.read())
    return result


def module_map(files: dict[str, tuple[tarfile.TarInfo, bytes]], root: str):
    prefix = PurePosixPath(root)
    result = {}
    for name in files:
        path = PurePosixPath(name)
        # GitHub source archives add one top-level repository directory.
        parts = path.parts
        offsets = [i for i in range(len(parts)) if PurePosixPath(*parts[i:]).parts[:len(prefix.parts)] == prefix.parts]
        if not offsets:
            continue
        start = offsets[0]
        suffix = PurePosixPath(*parts[start:])
        if suffix != prefix and prefix not in suffix.parents:
            continue
        relative = suffix.relative_to(prefix)
        if eligible(relative):
            result[relative.as_posix()] = name
    return result


def main() -> int:
    registration_bytes = REGISTRATION.read_bytes()
    labels_bytes = LABELS.read_bytes()
    if sha(registration_bytes) != EXPECTED_REGISTRATION:
        raise SystemExit("confirmatory registration hash mismatch")
    if sha(labels_bytes) != EXPECTED_LABELS:
        raise SystemExit("objective-label ledger hash mismatch")
    registration = json.loads(registration_bytes)
    repos = {row["repo_id"]: row for row in registration["repositories"]}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    prompts = []
    archives = []
    for repo_id in sorted(PACKAGE_ROOTS):
        repo = repos[repo_id]
        snapshots = {row["label"]: row for row in repo["snapshots"]}
        files = {}
        maps = {}
        for snapshot in ("old", "new"):
            row = snapshots[snapshot]
            archive_path = ROOT / row["archive"]
            archive_bytes = archive_path.read_bytes()
            if len(archive_bytes) != row["archive_bytes"] or sha(archive_bytes) != row["archive_sha256"]:
                raise SystemExit(f"registered archive mismatch: {repo_id}/{snapshot}")
            files[snapshot] = archive_members(archive_path)
            maps[snapshot] = module_map(files[snapshot], PACKAGE_ROOTS[repo_id])
            archives.append({"repo": repo_id, "snapshot": snapshot, "path": row["archive"],
                             "bytes": len(archive_bytes), "sha256": sha(archive_bytes)})
        common = sorted(set(maps["old"]) & set(maps["new"]))
        if not common:
            raise SystemExit(f"no common source modules: {repo_id}")
        relative = min(common, key=lambda value: sha(f"{repo_id}\0{value}".encode()))
        selection_key = sha(f"{repo_id}\0{relative}".encode())
        for snapshot in ("old", "new"):
            source_path = maps[snapshot][relative]
            source = files[snapshot][source_path][1]
            try:
                text = source.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SystemExit(f"selected source is not UTF-8: {repo_id}/{snapshot}: {exc}")
            excerpt = "\n".join(text.splitlines()[:LINES])
            if not excerpt.strip():
                raise SystemExit(f"empty excerpt: {repo_id}/{snapshot}")
            excerpt_bytes = excerpt.encode("utf-8")
            filename = f"{repo_id}-{snapshot}.txt"
            (OUTPUT / filename).write_bytes(excerpt_bytes)
            prompts.append({
                "repo": repo_id,
                "source_family": repo["owner_namespace"],
                "snapshot": snapshot,
                "source_commit": snapshots[snapshot]["commit"],
                "source_path": source_path,
                "source_file_sha256": sha(source),
                "prompt_id": PROMPT_ID,
                "snapshot_excerpt": excerpt,
                "snapshot_excerpt_sha256": sha(excerpt_bytes),
                "excerpt_path": f"runs/drift-confirmatory-v1/heldout-excerpts/{filename}",
                "selection_key_sha256": selection_key,
                "lora_adapter": None,
            })
    output = {
        "schema": "tiny-fleet.drift-heldout-excerpts/v1",
        "sample_manifest_path": "runs/drift-confirmatory-v1/registration.json",
        "sample_manifest_sha256": EXPECTED_REGISTRATION,
        "objective_label_ledger_path": "runs/drift-confirmatory-v1/labels.jsonl",
        "objective_label_ledger_sha256": EXPECTED_LABELS,
        "selection_policy": {
            "candidate_set": "common native Python modules under the registered package root in each old/new archive; test, vendor, and generated trees excluded",
            "ranking": "minimum SHA256(repo_id + NUL + normalized module path)",
            "excerpt": f"first {LINES} UTF-8 source lines from the selected common module at each exact registered commit",
            "label_access": "the selector verifies the frozen label-ledger digest but never reads label contents",
        },
        "prompt_id": PROMPT_ID,
        "prompt_template": PROMPT,
        "prompt_template_sha256": sha(PROMPT.encode()),
        "lines_per_excerpt": LINES,
        "archives": archives,
        "prompts": prompts,
        "status": "excerpts-frozen-no-model-run",
        "temporal_limit": "selection follows the objective-only label freeze; selection is deterministic and label-content-blind, but it is not a pre-label freeze",
    }
    out = OUTPUT / "heldout-excerpts.json"
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(out.relative_to(ROOT)), "sha256": sha(out.read_bytes()), "excerpts": len(prompts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
