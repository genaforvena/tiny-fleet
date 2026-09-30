#!/usr/bin/env python3
"""Build hashed, license-filtered source corpora for six frozen drift snapshots."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path, PurePosixPath


SAMPLE_PATH = Path("docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json")
SAMPLE_SHA256 = "07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59"
SCORER_REGISTRATION_PATH = Path("runs/drift-generative-v2/execution-scorer.json")
HELDOUT_PATH = Path("runs/drift-generative-v2/heldout-excerpts/heldout-excerpts.json")
HELDOUT_SHA256 = "ef117c462697932c461645c356302907ad3ab9275d49ab0be5ccf52b358ccba6"
PACKAGE_ROOTS = {
    "flask": {"old": "src/flask", "new": "src/flask"},
    "requests": {"old": "requests", "new": "src/requests"},
    "pydantic": {"old": "pydantic", "new": "pydantic"},
}
BASE_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
BASE_REVISION = "a10cc1512eabd3dde888204e902eca88bddb4951"
SPDX = re.compile(r"SPDX-License-Identifier:\s*([^\s*]+)", re.IGNORECASE)
EXCLUDED_DIRS = {
    "build", "dist", "generated", "node_modules", "third_party", "vendor", "vendored",
    "_vendor", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
TEST_DIRS = {"test", "tests", "testing"}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def classify_file(path, mode, data, *, package_root, license_spdx, heldout_path):
    path = PurePosixPath(path)
    root = PurePosixPath(package_root)
    if mode not in {"100644", "100755"}:
        return False, "non-regular-file"
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False, "outside-native-package"
    if path.as_posix() == PurePosixPath(heldout_path).as_posix():
        return False, "heldout-source-file"
    if any(part.lower() in TEST_DIRS for part in relative.parts):
        return False, "test-tree"
    if path.name.lower().startswith("test_") or path.name.lower().endswith("_test.py"):
        return False, "test-source-file"
    if any(part.lower() in EXCLUDED_DIRS for part in relative.parts):
        return False, "generated-or-vendored"
    if path.suffix.lower() != ".py":
        return False, "non-python-file"
    if b"\0" in data:
        return False, "binary"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False, "malformed-utf8"
    declared = {match.group(1).rstrip(".,;") for match in SPDX.finditer(text[:4096])}
    if declared and declared != {license_spdx}:
        return False, "file-license-mismatch"
    return True, ""


def split_paths(repo, snapshot, paths, validation_fraction=0.1):
    ordered = sorted(set(paths))
    if not ordered:
        raise ValueError("no eligible training source files")
    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation fraction must be in [0, 1)")
    validation_count = min(len(ordered) - 1, math.ceil(len(ordered) * validation_fraction))
    if validation_count <= 0:
        return ordered, []
    ranked = sorted(ordered, key=lambda path: hashlib.sha256(f"{repo}\0{snapshot}\0{path}".encode()).hexdigest())
    validation = set(ranked[:validation_count])
    return [path for path in ordered if path not in validation], [path for path in ordered if path in validation]


def git(repo_dir, *args):
    return subprocess.run(["git", f"--git-dir={repo_dir}", *args], check=True, capture_output=True).stdout


def read_blob(repo_dir, commit, path):
    return git(repo_dir, "show", f"{commit}:{path}")


def tree_rows(repo_dir, commit):
    raw = git(repo_dir, "ls-tree", "-r", "-l", "-z", commit)
    for item in raw.split(b"\0"):
        if not item:
            continue
        header, path_bytes = item.split(b"\t", 1)
        mode, kind, object_id, size = header.decode("ascii").split()
        path = path_bytes.decode("utf-8")
        data = git(repo_dir, "cat-file", "blob", object_id) if kind == "blob" else b""
        yield {"path": path, "mode": mode, "kind": kind, "object_id": object_id,
               "bytes": int(size), "data": data, "sha256": sha256(data)}


def verify_frozen_inputs(repo_root):
    repo_root = Path(repo_root)
    sample_path = repo_root / SAMPLE_PATH
    heldout_path = repo_root / HELDOUT_PATH
    sample_bytes, heldout_bytes = sample_path.read_bytes(), heldout_path.read_bytes()
    if sha256(sample_bytes) != SAMPLE_SHA256:
        raise ValueError("frozen sample manifest hash mismatch")
    if sha256(heldout_bytes) != HELDOUT_SHA256:
        raise ValueError("held-out excerpt ledger hash mismatch")
    return json.loads(sample_bytes), json.loads(heldout_bytes)


def build_snapshot(repo_root, repo_cache_dir, output_root, sample, heldout, repo_id, snapshot):
    repo_root, repo_cache_dir, output_root = Path(repo_root), Path(repo_cache_dir), Path(output_root)
    sample_repo = next(row for row in sample["repositories"] if row["repo_id"] == repo_id)
    snapshot_row = next(row for row in sample_repo["snapshots"] if row["label"] == snapshot)
    commit = snapshot_row["commit"]
    license_row = next(row for row in sample_repo["license"]["snapshots"] if row["commit"] == commit)
    roots = PACKAGE_ROOTS[repo_id]
    package_root = roots[snapshot]
    prompt = next(row for row in heldout["prompts"] if row["repo"] == repo_id and row["snapshot"] == snapshot)
    heldout_source = prompt["source_path"]
    repo_dir = repo_cache_dir / f"{repo_id}.git"
    license_bytes = read_blob(repo_dir, commit, license_row["path"])
    if sha256(license_bytes) != license_row["sha256"]:
        raise ValueError(f"root license hash mismatch: {repo_id}/{snapshot}")

    inventory = []
    contents = {}
    for row in tree_rows(repo_dir, commit):
        if row["kind"] != "blob":
            included, reason = False, "non-blob-object"
        else:
            included, reason = classify_file(
                row["path"], row["mode"], row["data"], package_root=package_root,
                license_spdx=sample_repo["license"]["spdx"], heldout_path=heldout_source,
            )
        entry = {key: row[key] for key in ("path", "mode", "kind", "object_id", "bytes", "sha256")}
        entry.update(status="included" if included else "excluded", reason=reason)
        inventory.append(entry)
        if included:
            contents[row["path"]] = row["data"].decode("utf-8")
    inventory.sort(key=lambda row: row["path"])
    train_paths, validation_paths = split_paths(repo_id, snapshot, list(contents))
    target = output_root / f"{repo_id}-{snapshot}"
    target.mkdir(parents=True, exist_ok=True)
    (target / "LICENSE.txt").write_bytes(license_bytes)
    (target / "inventory.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in inventory),
        encoding="utf-8",
    )

    def write_split(name, paths):
        records = [{"source_path": path, "source_file_sha256": next(row["sha256"] for row in inventory if row["path"] == path),
                    "text": f"### {path}\n{contents[path]}"} for path in paths]
        payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records).encode("utf-8")
        out_path = target / f"{name}.jsonl"
        out_path.write_bytes(payload)
        return {"path": out_path.relative_to(repo_root).as_posix(), "rows": len(records), "sha256": sha256(payload)}

    train = write_split("train", train_paths)
    validation = write_split("validation", validation_paths)
    inventory_path = target / "inventory.jsonl"
    license_path = target / "LICENSE.txt"
    record = {
        "schema": "tiny-fleet.drift-training-corpus/v1",
        "repo": repo_id,
        "snapshot": snapshot,
        "source_commit": commit,
        "package_root": package_root,
        "license": {"spdx": sample_repo["license"]["spdx"], "source_path": license_row["path"],
                    "source_sha256": license_row["sha256"], "saved_path": license_path.relative_to(repo_root).as_posix(),
                    "saved_sha256": sha256(license_bytes)},
        "selection": {
            "allow": "regular UTF-8 Python source under the native package root, covered by the verified root license",
            "file_level_license": "include only absent SPDX markers or markers exactly equal to the root SPDX identifier; otherwise exclude",
            "exclude": ["outside native package", "tests directories and test_*.py/*_test.py files", "generated/vendor trees", "non-Python files", "symlinks and non-regular objects", "binary or malformed UTF-8", "selected held-out source module"],
            "heldout_source_excluded": heldout_source,
            "validation_split": "ceil(10% of eligible files), chosen by ascending SHA256(repo + NUL + snapshot + NUL + path); file groups stay intact",
            "corpus_scope": "training adaptation corpus, not a complete repository archive; every tracked path is hash-accounted in inventory.jsonl"
        },
        "inventory": {"path": (target / "inventory.jsonl").relative_to(repo_root).as_posix(), "rows": len(inventory), "included": sum(row["status"] == "included" for row in inventory),
                      "excluded": sum(row["status"] == "excluded" for row in inventory), "sha256": sha256((target / "inventory.jsonl").read_bytes())},
        "corpus_builder": {"path": "scripts/build_drift_train_corpus.py",
                           "source_sha256": sha256((repo_root / "scripts/build_drift_train_corpus.py").read_bytes())},
        "train": train,
        "validation": validation,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    record["manifest_sha256"] = sha256(manifest_path.read_bytes())
    return record


def build_all(repo_root, repo_cache_dir, output_root):
    repo_root = Path(repo_root)
    sample, heldout = verify_frozen_inputs(repo_root)
    scorer_bytes = (repo_root / SCORER_REGISTRATION_PATH).read_bytes()
    scorer_registration_sha = sha256(scorer_bytes)
    runner_path = repo_root / "scripts" / "train_drift_adapters.py"
    if not runner_path.is_file():
        raise ValueError("training runner must exist before the plan is frozen")
    records = [build_snapshot(repo_root, repo_cache_dir, output_root, sample, heldout, repo, snapshot)
               for repo in sorted(PACKAGE_ROOTS) for snapshot in ("old", "new")]
    plan = {
        "schema": "tiny-fleet.drift-adapter-training-plan/v1",
        "status": "corpora-built-no-training-run-yet",
        "source_sample_manifest": {"path": SAMPLE_PATH.as_posix(), "sha256": SAMPLE_SHA256},
        "heldout_excerpt_ledger": {"path": HELDOUT_PATH.as_posix(), "sha256": HELDOUT_SHA256},
        "scorer_registration": {"path": SCORER_REGISTRATION_PATH.as_posix(), "sha256": scorer_registration_sha},
        "corpus_builder": {"path": "scripts/build_drift_train_corpus.py",
                           "source_sha256": sha256((repo_root / "scripts" / "build_drift_train_corpus.py").read_bytes())},
        "training_runner": {"path": "scripts/train_drift_adapters.py", "source_sha256": sha256(runner_path.read_bytes())},
        "base_model": {"id": BASE_MODEL, "revision": BASE_REVISION},
        "training": {
            "seed": 17,
            "epochs": 1,
            "max_sequence_length": 256,
            "train_token_budget_per_adapter": 16384,
            "validation_token_budget_per_adapter": 4096,
            "sequence_sampling": "tokenize per-file text, split to non-overlapping 256-token chunks, rank chunks by SHA256(repo + NUL + snapshot + NUL + source path + NUL + chunk index), then take the lowest ranks up to the registered budget",
            "batch_size": 1,
            "gradient_accumulation": 4,
            "learning_rate": 0.0002,
            "weight_decay": 0.01,
            "max_gradient_norm": 1.0,
            "lora": {"rank": 8, "alpha": 16, "dropout": 0.05, "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]},
            "validation": "token-weighted causal-language-model loss on the file-disjoint deterministic 10% split; reports adaptation validation only, not external semantic truth",
            "runtime": "local-only pinned Transformers/PyTorch/PEFT; CPU fallback is prohibited for this GPU-budgeted run",
            "parameter_rationale": {
                "seed": "use the first seed in the already frozen generation schedule for a reproducible per-snapshot adapter",
                "epochs_and_token_budget": "one pass over a deterministic maximum of 16384 train tokens bounds each of six adapters to at most 64 full 256-token sequences; source corpora contain substantially more data and selected excerpts are removed",
                "validation": "reserve deterministic whole source files (10% by path hash) before token selection; at most 4096 validation tokens per adapter, with smaller actual validation corpora left smaller",
                "sequence_and_batch": "256-token windows and batch size one bound RTX 3060 activation memory; four-step gradient accumulation yields effective batch size four",
                "learning_rate_and_rank": "2e-4 AdamW with rank 8 / alpha 16 LoRA is a low-rank bounded adaptation for the pinned 360M base and small repository-specific corpus",
                "gpu_and_ram_budget": "admit only with 8192 MiB free VRAM and an 8192 MiB mesh-heavy-run RAM ceiling; current baseline has less VRAM, so use mesh-gpu-lease preemption and restore the exact previously active managed services",
            },
        },
        "corpora": records,
    }
    plan_path = Path(output_root) / "training-plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": str(plan_path), "corpora": len(records), "sha256": sha256(plan_path.read_bytes()),
            "included_files": sum(row["inventory"]["included"] for row in records),
            "excluded_files": sum(row["inventory"]["excluded"] for row in records)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--repo-cache-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build_all(args.repo_root, args.repo_cache_dir, args.output_root), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
