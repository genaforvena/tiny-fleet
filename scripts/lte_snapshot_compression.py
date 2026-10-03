#!/usr/bin/env python3
"""Measure whether same-seed LoRA adapters compress two repository snapshots differently.

Raw source, inventories, checkpoints, and likelihood tapes belong in an ignored local run
folder. The script reads Git objects without checking out or changing the source repository.
"""
from __future__ import annotations

import argparse
import collections
import fcntl
import importlib.metadata
import hashlib
import json
import math
import os
from pathlib import Path
import random
import resource
import signal
import subprocess
import sys
import time
import traceback

from model_terminology_drift import (
    BASE_MODEL, BASE_REVISION, cached_inputs, cross_score, diagnostic_loss,
    file_sha256, load_base, load_tokenizer, offline, progress, train_pass,
    tokenizer_binding, tokenized_chunks, write_json,
)
from train_drift_adapters import select_chunks

SCHEMA = "tiny-fleet.lte-snapshot-compression/v1"
SEEDS = (17, 29, 43)
STAGES = (0, 4, 19)
TRAIN_TOKENS = 4096
VALIDATION_TOKENS = 4096
MAX_LENGTH = 256
TEST_TOKENS_PER_FILE = 512
MAX_FILE_BYTES = 262144
ALLOW_SUFFIXES = {
    ".md", ".py", ".sh", ".c", ".h", ".ts", ".swift", ".tal", ".m",
    ".yaml", ".yml", ".json", ".toml", ".txt", ".tsv", ".service",
    ".timer", ".example", ".gitignore", ".mailmap", ".gitattributes",
    ".list", ".cfg", ".conf", ".ini", ".patch",
}
PRIVATE_ROOTS = {"charter", "job", "artifacts", "captures", "seed", ".mesh"}
PRIVATE_NAMES = {".sops.yaml", "nodes.example"}
GLOBAL_LOCK = Path("/tmp/tiny-fleet-terminology-model.lock")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_sha256(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def git(repo: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    return result.stdout


def tracked_files(repo: Path, revision: str):
    entries = []
    for raw in git(repo, "ls-tree", "-r", "-l", "-z", revision).split(b"\0"):
        if not raw:
            continue
        metadata, raw_path = raw.split(b"\t", 1)
        mode, kind, oid, size = metadata.decode("ascii").split(" ", 3)
        path = raw_path.decode("utf-8", "strict")
        size = None if size == "-" else int(size)
        reason = None
        top = path.split("/", 1)[0]
        suffix = Path(path).suffix.lower()
        if kind != "blob" or mode not in {"100644", "100755"}:
            reason = "non-regular Git object"
        elif top in PRIVATE_ROOTS or Path(path).name in PRIVATE_NAMES:
            reason = "private/local data exclusion"
        elif suffix not in ALLOW_SUFFIXES:
            reason = "non-text or unregistered file type"
        elif size is None or size > MAX_FILE_BYTES:
            reason = "missing size or file exceeds 256 KiB cap"
        if reason:
            entries.append({"path": path, "git_blob": oid, "size_bytes": size,
                            "status": "excluded", "reason": reason})
            continue
        content = git(repo, "cat-file", "blob", oid)
        try:
            text = content.decode("utf-8", "strict")
        except UnicodeDecodeError:
            entries.append({"path": path, "git_blob": oid, "size_bytes": size,
                            "status": "excluded", "reason": "invalid UTF-8"})
            continue
        if b"\0" in content:
            entries.append({"path": path, "git_blob": oid, "size_bytes": size,
                            "status": "excluded", "reason": "NUL byte"})
            continue
        entries.append({"path": path, "git_blob": oid, "size_bytes": size,
                        "content_sha256": sha256(content), "status": "included", "text": text})
    return entries


def _write_jsonl(path: Path, rows):
    if path.exists():
        raise FileExistsError(path)
    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _replace_json(path: Path, value):
    pending = path.with_name(f".{path.name}.{os.getpid()}.pending")
    with pending.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


def _deadline(_signum, _frame):
    raise TimeoutError("registered 6-hour model wall cap exceeded")


def _effective_cgroup_memory_bytes(root=Path("/sys/fs/cgroup"), membership=Path("/proc/self/cgroup")):
    try:
        rows = membership.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for row in rows:
        try:
            _, controllers, relative = row.split(":", 2)
        except ValueError:
            continue
        if not controllers:
            filename = "memory.max"
            directory = root / relative.lstrip("/")
        elif "memory" in controllers.split(","):
            filename = "memory.limit_in_bytes"
            directory = root / "memory" / relative.lstrip("/")
        else:
            continue
        limits = []
        while directory == root or root in directory.parents:
            try:
                raw = (directory / filename).read_text(encoding="ascii").strip()
                if raw != "max":
                    limit = int(raw)
                    if 0 < limit < 1 << 60:
                        limits.append(limit)
            except (OSError, ValueError):
                pass
            if directory == root:
                break
            directory = directory.parent
        return min(limits) if limits else None
    return None


def _require_cgroup_memory_limit(ceiling_mb, limit_bytes=None):
    if limit_bytes is None:
        limit_bytes = _effective_cgroup_memory_bytes()
    ceiling_bytes = ceiling_mb * 1024 * 1024
    if limit_bytes is None or limit_bytes > ceiling_bytes:
        raise RuntimeError(f"process cgroup must enforce a memory limit of at most {ceiling_mb} MB")


def _private_run_dir(source_repo, run_dir):
    source_repo = Path(source_repo).resolve()
    run_dir = Path(run_dir).expanduser().resolve()
    if run_dir == source_repo or source_repo in run_dir.parents:
        raise ValueError("private run directory must not be inside the source repository")
    parent = run_dir.parent
    while not parent.exists():
        parent = parent.parent
    probe = subprocess.run(["git", "-C", str(parent), "rev-parse", "--show-toplevel"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if probe.returncode:
        return run_dir
    root = Path(probe.stdout.decode("utf-8", "strict").strip()).resolve()
    try:
        relative = run_dir.relative_to(root)
    except ValueError:
        return run_dir
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "--quiet",
                              "--no-index", "--", relative.as_posix()],
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    if ignored.returncode:
        raise ValueError("run directory inside a Git worktree must be ignored or placed outside it")
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--",
                              relative.as_posix()],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if tracked.returncode == 0:
        raise ValueError("private run directory is tracked by Git")
    return run_dir


def _require_token_budget(chunks, expected, snapshot, split):
    actual = sum(len(row["input_ids"]) for row in chunks)
    if actual != expected:
        raise ValueError(f"{snapshot} {split} token budget mismatch: expected {expected}, got {actual}")


def _read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _component_splits(entries):
    """Keep every version of a path and every exact duplicate blob in one split."""
    rows = [(snapshot, entry) for snapshot in ("old", "new") for entry in entries[snapshot]
            if entry["status"] == "included"]
    parent = list(range(len(rows)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left, right):
        a, b = find(left), find(right)
        if a != b:
            parent[max(a, b)] = min(a, b)

    by_path, by_digest = {}, {}
    for index, (snapshot, entry) in enumerate(rows):
        if entry["path"] in by_path:
            union(index, by_path[entry["path"]])
        by_path[entry["path"]] = index
        digest = entry["content_sha256"]
        if digest in by_digest:
            union(index, by_digest[digest])
        by_digest[digest] = index
    members = collections.defaultdict(list)
    for index, (snapshot, entry) in enumerate(rows):
        members[find(index)].append((snapshot, entry))
    split_for = {}
    for root, group in members.items():
        key = "\n".join(sorted({item[1]["path"] for item in group})).encode()
        value = int(hashlib.sha256(key).hexdigest()[:8], 16) / 0x100000000
        split_for[root] = "test" if value < 0.20 else "validation" if value < 0.30 else "train"
    assignments = {}
    for index, (snapshot, entry) in enumerate(rows):
        assignments[(snapshot, entry["path"])] = split_for[find(index)]
    return assignments


def _heldout_prefix(text, tokenizer):
    encoded = tokenizer(text, add_special_tokens=True, truncation=False,
                        return_offsets_mapping=True, verbose=False)
    input_ids = encoded["input_ids"][:TEST_TOKENS_PER_FILE]
    offsets = encoded["offset_mapping"][:len(input_ids)]
    targets = [(left, right) for left, right in offsets[1:] if right > left]
    if len(input_ids) < 2 or not targets:
        return input_ids, 0
    return input_ids, len(text[targets[0][0]:targets[-1][1]].encode("utf-8"))

def prepare(repo: Path, old_revision: str, new_revision: str, run_dir: Path):
    repo = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    run_dir = _private_run_dir(repo, run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    old = git(repo, "rev-parse", "--verify", f"{old_revision}^{{commit}}").decode().strip()
    new = git(repo, "rev-parse", "--verify", f"{new_revision}^{{commit}}").decode().strip()
    entries = {"old": tracked_files(repo, old), "new": tracked_files(repo, new)}
    assignments = _component_splits(entries)
    eligible = {snapshot: {entry["path"]: entry for entry in entries[snapshot]
                           if entry["status"] == "included"} for snapshot in ("old", "new")}
    common = set(eligible["old"]) & set(eligible["new"])
    unchanged = [path for path in common if eligible["old"][path]["content_sha256"] ==
                 eligible["new"][path]["content_sha256"]]
    unchanged_test = [path for path in unchanged if assignments[("old", path)] == "test"]
    forced_identity = None
    digest_counts = collections.Counter(entry["content_sha256"] for snapshot in ("old", "new")
                                        for entry in entries[snapshot] if entry["status"] == "included")
    if not unchanged_test:
        candidates = [path for path in unchanged
                      if digest_counts[eligible["old"][path]["content_sha256"]] == 2]
        if not candidates:
            raise ValueError("no unique byte-identical path can supply the unchanged-source control")
        selected = min(candidates, key=lambda path: sha256(path.encode()))
        assignments[("old", selected)] = assignments[("new", selected)] = "test"
        forced_identity = selected
    inventories, records = [], {"old": [], "new": []}
    for snapshot in ("old", "new"):
        for entry in entries[snapshot]:
            row = {k: v for k, v in entry.items() if k != "text"}
            row.update(snapshot=snapshot, split=assignments.get((snapshot, entry["path"])))
            inventories.append(row)
            if entry["status"] == "included":
                records[snapshot].append({"source_path": entry["path"], "text": entry["text"],
                                          "source_file_sha256": entry["content_sha256"],
                                          "split": assignments[(snapshot, entry["path"])]})
    _write_jsonl(run_dir / "inventory.jsonl", inventories)
    for snapshot in ("old", "new"):
        _write_jsonl(run_dir / f"source-{snapshot}.jsonl", records[snapshot])
    offline()
    tokenizer = load_tokenizer()
    cases = {"schema": SCHEMA + "/cases", "base_model": {"id": BASE_MODEL, "revision": BASE_REVISION},
             "tokenizer": tokenizer_binding(tokenizer), "snapshots": {}}
    common_paths = set(r["source_path"] for r in records["old"]) & set(r["source_path"] for r in records["new"])
    for snapshot in ("old", "new"):
        train = [r for r in records[snapshot] if r["split"] == "train"]
        validation = [r for r in records[snapshot] if r["split"] == "validation"]
        train_chunks = select_chunks("lte-workstation", snapshot,
                                     tokenized_chunks(train, tokenizer, MAX_LENGTH),
                                     token_budget=TRAIN_TOKENS, max_length=MAX_LENGTH)
        validation_chunks = select_chunks("lte-workstation", snapshot,
                                          tokenized_chunks(validation, tokenizer, MAX_LENGTH),
                                          token_budget=VALIDATION_TOKENS, max_length=MAX_LENGTH)
        _require_token_budget(train_chunks, TRAIN_TOKENS, snapshot, "train")
        _require_token_budget(validation_chunks, VALIDATION_TOKENS, snapshot, "validation")
        cases["snapshots"][snapshot] = {
            "train_chunks": [{"source_path": r["source_path"], "chunk_index": r["chunk_index"],
                              "input_ids": list(r["input_ids"])} for r in train_chunks],
            "validation_chunks": [{"source_path": r["source_path"], "chunk_index": r["chunk_index"],
                                   "input_ids": list(r["input_ids"])} for r in validation_chunks],
            "unigram_counts": dict(collections.Counter(token for r in train_chunks for token in r["input_ids"])),
            "included_train_paths": sorted({r["source_path"] for r in train}),
            "included_validation_paths": sorted({r["source_path"] for r in validation}),
        }
    heldout = []
    by_snapshot = {s: {r["source_path"]: r for r in records[s]} for s in ("old", "new")}
    for path in sorted(common_paths):
        old_row, new_row = by_snapshot["old"][path], by_snapshot["new"][path]
        if old_row["split"] != "test" or new_row["split"] != "test":
            continue
        old_ids, old_bytes = _heldout_prefix(old_row["text"], tokenizer)
        new_ids, new_bytes = _heldout_prefix(new_row["text"], tokenizer)
        if len(old_ids) < 2 or len(new_ids) < 2 or old_bytes <= 0 or new_bytes <= 0:
            continue
        heldout.append({"source_path": path, "changed": old_row["source_file_sha256"] != new_row["source_file_sha256"],
                        "content_sha256": {"old": old_row["source_file_sha256"], "new": new_row["source_file_sha256"]},
                        "score_bytes": {"old": old_bytes, "new": new_bytes},
                        "input_ids": {"old": old_ids, "new": new_ids}})


    changed = [r for r in heldout if r["changed"]]
    unchanged = [r for r in heldout if not r["changed"]]
    if len(changed) < 3 or len(unchanged) < 1:
        raise ValueError(f"split too small for paired test: changed={len(changed)} unchanged={len(unchanged)}")
    cases["heldout_pairs"] = heldout
    write_json(run_dir / "cases.json", cases)
    files = {}
    for name in ("lte_snapshot_compression.py", "model_terminology_drift.py", "train_drift_adapters.py"):
        path = Path(__file__).resolve().parent / name
        files[str(path)] = file_sha256(path)
    protocol = {
        "schema": SCHEMA + "/protocol", "source_repository": str(repo),
        "snapshots": {"old": old, "new": new},
        "source_tree": {"old": git(repo, "rev-parse", f"{old}^{{tree}}").decode().strip(),
                        "new": git(repo, "rev-parse", f"{new}^{{tree}}").decode().strip()},
        "model": {"id": BASE_MODEL, "revision": BASE_REVISION, "cache": cached_inputs(),
                  "tokenizer": cases["tokenizer"]},
        "runtime": {"python": sys.version, "packages": {name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "peft", "tokenizers", "safetensors", "numpy")}},
        "source_filter": {"allow_suffixes": sorted(ALLOW_SUFFIXES), "private_roots_excluded": sorted(PRIVATE_ROOTS),
                          "private_names_excluded": sorted(PRIVATE_NAMES), "max_file_bytes": MAX_FILE_BYTES,
                          "partition": "union path/exact-blob component; hash test<20% and validation<30%; if no unchanged common test path, force the unique byte-identical common path with lowest SHA256(path) into test"},
        "training": {"seeds": list(SEEDS), "tokens": TRAIN_TOKENS, "validation_tokens": VALIDATION_TOKENS,
                     "max_sequence_length": MAX_LENGTH, "additional_passes": 19, "checkpoints": list(STAGES),
                     "optimizer": "fresh AdamW per seed/snapshot", "learning_rate": 0.0002,
                     "weight_decay": 0.01, "max_gradient_norm": 1.0, "gradient_accumulation": 4,
                     "gradient_checkpointing": {"enabled": True, "use_reentrant": False,
                                                 "purpose": "recompute activations under the 3072 MB process ceiling"},
                     "lora": {"rank": 8, "alpha": 16, "dropout": 0.05,
                              "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]},
                     "device": "cpu", "dtype": "float32", "threads": 1, "offline": True},
        "test": {"common_test_paths": len(heldout), "changed_paths": len(changed), "unchanged_paths": len(unchanged),
                 "forced_identity_control_path": forced_identity,
                 "tokens_per_file_cap": TEST_TOKENS_PER_FILE,
                 "primary": "crossed heldout negative log likelihood on paired changed paths",
                 "controls": ["same-path byte-identical files", "shared base model", "training unigram"]},
        "budget": {"model_wall_seconds": 21600, "memory_ceiling_mb": 3072,
                   "global_lock": str(GLOBAL_LOCK)},
        "source_files": files,
        "cases_sha256": file_sha256(run_dir / "cases.json"),
        "inventory_sha256": file_sha256(run_dir / "inventory.jsonl"),
        "corpus_sha256": {s: file_sha256(run_dir / f"source-{s}.jsonl") for s in ("old", "new")},
        "limitations": ["one repository and two historical snapshots", "few paired changed files",
                        "only three training seeds and one pinned base", "pretraining contamination unknown",
                        "heldout predictive compression is not semantic correctness", "model/adapter size excluded from predictive bits/token"]
    }
    write_json(run_dir / "protocol.json", protocol)
    write_json(run_dir / "prepared.json", {"schema": SCHEMA + "/prepared",
              "protocol_sha256": file_sha256(run_dir / "protocol.json"),
              "cases_sha256": file_sha256(run_dir / "cases.json")})
    progress(f"prepared {run_dir}: old={old} new={new} changed-test-paths={len(changed)} unchanged-test-paths={len(unchanged)}")


def validate_prepared(run_dir: Path):
    protocol_path, cases_path, prepared_path = run_dir / "protocol.json", run_dir / "cases.json", run_dir / "prepared.json"
    protocol, cases, prepared = json.loads(protocol_path.read_text()), json.loads(cases_path.read_text()), json.loads(prepared_path.read_text())
    if prepared["protocol_sha256"] != file_sha256(protocol_path) or prepared["cases_sha256"] != file_sha256(cases_path):
        raise ValueError("prepared protocol or cases changed")
    if protocol["cases_sha256"] != file_sha256(cases_path) or protocol["inventory_sha256"] != file_sha256(run_dir / "inventory.jsonl"):
        raise ValueError("prepared source binding changed")
    for snapshot in ("old", "new"):
        path = run_dir / f"source-{snapshot}.jsonl"
        if protocol["corpus_sha256"][snapshot] != file_sha256(path):
            raise ValueError(f"prepared {snapshot} corpus changed")
        spec = cases["snapshots"][snapshot]
        _require_token_budget(spec["train_chunks"], protocol["training"]["tokens"], snapshot, "train")
        _require_token_budget(spec["validation_chunks"], protocol["training"]["validation_tokens"], snapshot, "validation")
    for raw, expected in protocol["source_files"].items():
        if file_sha256(raw) != expected:
            raise ValueError(f"runner dependency changed: {raw}")
    for raw, expected in protocol["model"]["cache"]["files"].items():
        if file_sha256(Path(protocol["model"]["cache"]["path"]) / raw) != expected:
            raise ValueError(f"pinned model cache changed: {raw}")
    return protocol, cases


def _lora_model(torch, seed):
    from peft import LoraConfig, TaskType, get_peft_model
    torch.manual_seed(seed)
    random.seed(seed)
    model = load_base(torch)
    model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
        lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], bias="none"))
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    return model


def _score_model(model, snapshot, seed, stage, cases, torch, tape):
    model.eval()
    for target in cases["heldout_pairs"]:
        for target_snapshot in ("old", "new"):
            result = cross_score(model, {"input_ids": target["input_ids"][target_snapshot], "prefix_ids": []}, torch)
            row = {"model_snapshot": snapshot, "seed": seed, "stage": stage,
                   "target_snapshot": target_snapshot, "source_path": target["source_path"],
                   "changed": target["changed"], "status": "ok", **result}
            tape.write(json.dumps(row, sort_keys=True) + "\n")
            tape.flush()
            os.fsync(tape.fileno())


def execute(run_dir: Path):
    protocol, cases = validate_prepared(run_dir)
    _require_cgroup_memory_limit(protocol["budget"]["memory_ceiling_mb"])
    lock = GLOBAL_LOCK.open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError("another terminology-model run owns the global lock") from exc
    started = time.monotonic()
    receipt_path = run_dir / "receipt.json"
    write_json(receipt_path, {"schema": SCHEMA + "/receipt", "status": "running",
                              "protocol_sha256": file_sha256(run_dir / "protocol.json"),
                              "source_sha256": protocol["source_tree"], "started_unix": time.time()})
    signal.signal(signal.SIGALRM, _deadline)
    signal.setitimer(signal.ITIMER_REAL, protocol["budget"]["model_wall_seconds"])
    try:
        offline()
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(True)
        tokenizer = load_tokenizer()
        training_tape = run_dir / "training.jsonl"
        likelihood_tape = run_dir / "likelihood.jsonl"
        for path in (training_tape, likelihood_tape):
            if path.exists():
                raise FileExistsError(path)
        settings = {"gradient_accumulation": protocol["training"]["gradient_accumulation"],
                    "max_gradient_norm": protocol["training"]["max_gradient_norm"]}
        with training_tape.open("x", encoding="utf-8") as train_out, likelihood_tape.open("x", encoding="utf-8") as score_out:
            for snapshot in ("old", "new"):
                spec = cases["snapshots"][snapshot]
                for seed in SEEDS:
                    progress(f"fit {snapshot} seed={seed}")
                    torch.manual_seed(seed)
                    model = _lora_model(torch, seed)
                    params = [p for p in model.parameters() if p.requires_grad]
                    optimizer = torch.optim.AdamW(params, lr=protocol["training"]["learning_rate"],
                                                  weight_decay=protocol["training"]["weight_decay"])
                    train_out.write(json.dumps({"snapshot": snapshot, "seed": seed, "pass": 0,
                        "kind": "diagnostic", "status": "ok",
                        "train_diagnostic": diagnostic_loss(model, spec["train_chunks"], torch),
                        "validation": diagnostic_loss(model, spec["validation_chunks"], torch)}) + "\n")
                    train_out.flush()
                    os.fsync(train_out.fileno())
                    _score_model(model, snapshot, seed, 0, cases, torch, score_out)
                    for number in range(1, 20):
                        settings["seed"] = seed
                        result = train_pass(model, spec["train_chunks"], optimizer, number, settings, torch)
                        train_out.write(json.dumps({"snapshot": snapshot, "seed": seed, "pass": number,
                                                    "status": "ok", **result}) + "\n")
                        train_out.flush()
                        os.fsync(train_out.fileno())
                        if number in STAGES:
                            diagnostic = diagnostic_loss(model, spec["train_chunks"], torch)
                            validation = diagnostic_loss(model, spec["validation_chunks"], torch)
                            train_out.write(json.dumps({"snapshot": snapshot, "seed": seed, "pass": number,
                                "kind": "diagnostic", "status": "ok", "train_diagnostic": diagnostic,
                                "validation": validation}) + "\n")
                            train_out.flush()
                            os.fsync(train_out.fileno())
                            _score_model(model, snapshot, seed, number, cases, torch, score_out)
                            destination = run_dir / "checkpoints" / f"{snapshot}-seed{seed}-pass{number}"
                            destination.mkdir(parents=True, exist_ok=False)
                            model.save_pretrained(destination, safe_serialization=True)
                    del optimizer, params, model
                    import gc
                    gc.collect()
        # Shared base and each snapshot's training unigram are scored on exactly the same test rows.
        progress("score shared base and training-unigram controls")
        base = load_base(torch)
        with likelihood_tape.open("a", encoding="utf-8") as score_out:
            for target in cases["heldout_pairs"]:
                for target_snapshot in ("old", "new"):
                    spec = {"input_ids": target["input_ids"][target_snapshot], "prefix_ids": []}
                    base_result = cross_score(base, spec, torch)
                    base_row = {"model_snapshot": "shared", "seed": None, "stage": 0,
                                "target_snapshot": target_snapshot, "source_path": target["source_path"],
                                "changed": target["changed"], "arm": "base", "status": "ok", **base_result}
                    score_out.write(json.dumps(base_row, sort_keys=True) + "\n")
                    for unigram_snapshot in ("old", "new"):
                        case = cases["snapshots"][unigram_snapshot]
                        from model_terminology_drift import unigram_score
                        unigram = unigram_score(case, spec, len(tokenizer), 1.0)
                        row = {"model_snapshot": unigram_snapshot, "seed": None, "stage": 0,
                               "target_snapshot": target_snapshot, "source_path": target["source_path"],
                               "changed": target["changed"], "arm": "unigram", "status": "ok", **unigram}
                        score_out.write(json.dumps(row, sort_keys=True) + "\n")
                    score_out.flush()
                    os.fsync(score_out.fileno())
        receipt = {"schema": SCHEMA + "/receipt", "status": "complete", "protocol_sha256": file_sha256(run_dir / "protocol.json"),
                   "source_sha256": protocol["source_tree"], "likelihood_rows": sum(1 for _ in likelihood_tape.open()),
                   "training_rows": sum(1 for _ in training_tape.open()), "elapsed_s": time.monotonic() - started,
                   "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2,
                   "likelihood_sha256": file_sha256(likelihood_tape), "training_sha256": file_sha256(training_tape)}
        _replace_json(receipt_path, receipt)
        progress(f"complete {run_dir / 'receipt.json'}")
        return 0
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        failed = {"schema": SCHEMA + "/receipt", "status": "failed", "error": error,
                  "traceback": traceback.format_exc(), "protocol_sha256": file_sha256(run_dir / "protocol.json"),
                  "elapsed_s": time.monotonic() - started,
                  "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2}
        pending = run_dir / ".receipt-failed.json.pending"
        pending.write_text(json.dumps(failed, indent=2, sort_keys=True) + "\n")
        os.replace(pending, receipt_path)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def _validated_rows(likelihood, cases):
    paths = cases["heldout_pairs"]
    for item in paths:
        for snapshot in ("old", "new"):
            count = item.get("score_bytes", {}).get(snapshot)
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                raise ValueError("invalid heldout UTF-8 byte denominator")
    expected = {
        "lora": {(model, seed, stage, target, item["source_path"])
                 for model in ("old", "new") for seed in SEEDS for stage in STAGES
                 for target in ("old", "new") for item in paths},
        "base": {(target, item["source_path"])
                 for target in ("old", "new") for item in paths},
        "unigram": {(model, target, item["source_path"])
                    for model in ("old", "new") for target in ("old", "new") for item in paths},
    }
    rows = {arm: {} for arm in expected}
    errors = []
    for row in likelihood:
        if not isinstance(row, dict):
            errors.append("non-object likelihood row")
            continue
        nll, tokens, mean = row.get("nll_sum"), row.get("target_tokens"), row.get("mean_token_nll")
        if (row.get("status") != "ok" or not isinstance(tokens, int) or isinstance(tokens, bool)
                or tokens <= 0 or not isinstance(nll, (int, float)) or isinstance(nll, bool)
                or not math.isfinite(nll) or nll < 0 or not isinstance(mean, (int, float))
                or isinstance(mean, bool) or not math.isfinite(mean)
                or not math.isclose(mean, nll / tokens, rel_tol=1e-9, abs_tol=1e-12)):
            errors.append("invalid likelihood row")
        arm = row.get("arm", "lora")
        try:
            if arm == "lora":
                key = (row["model_snapshot"], row["seed"], row["stage"],
                       row["target_snapshot"], row["source_path"])
            elif arm == "base":
                if row["model_snapshot"] != "shared" or row["seed"] is not None or row["stage"] != 0:
                    errors.append("invalid base-model identity")
                key = (row["target_snapshot"], row["source_path"])
            elif arm == "unigram":
                if row["seed"] is not None or row["stage"] != 0:
                    errors.append("invalid unigram identity")
                key = (row["model_snapshot"], row["target_snapshot"], row["source_path"])
            else:
                errors.append(f"unknown likelihood arm: {arm}")
                continue
        except (KeyError, TypeError):
            errors.append("likelihood row missing identity fields")
            continue
        if key in rows[arm]:
            errors.append(f"duplicate {arm} likelihood row: {key}")
        rows[arm][key] = row
    for arm, keys in expected.items():
        actual = set(rows[arm])
        if actual != keys:
            errors.append(f"{arm} denominator mismatch: expected {len(keys)} rows, got {len(actual)}")
    if errors:
        raise ValueError("; ".join(errors))
    return rows


def _validate_training_rows(training, expected_tokens):
    expected = {(snapshot, seed, number, "update")
                for snapshot in ("old", "new") for seed in SEEDS for number in range(1, 20)}
    expected.update((snapshot, seed, number, "diagnostic")
                    for snapshot in ("old", "new") for seed in SEEDS for number in STAGES)
    actual = set()
    for row in training:
        if not isinstance(row, dict) or row.get("status") != "ok":
            raise ValueError("invalid training row")
        key = (row.get("snapshot"), row.get("seed"), row.get("pass"),
               row.get("kind", "update"))
        if key in actual:
            raise ValueError(f"duplicate training row: {key}")
        if key[3] == "update" and row.get("selected_tokens") != expected_tokens:
            raise ValueError("training token budget mismatch")
        actual.add(key)
    if actual != expected:
        raise ValueError(f"training denominator mismatch: expected {len(expected)} rows, got {len(actual)}")


def _check_receipt_tapes(run_dir, receipt, protocol):
    likelihood_path = run_dir / "likelihood.jsonl"
    training_path = run_dir / "training.jsonl"
    likelihood = _read_jsonl(likelihood_path)
    training = _read_jsonl(training_path)
    if (receipt.get("likelihood_sha256") != file_sha256(likelihood_path)
            or receipt.get("likelihood_rows") != len(likelihood)):
        raise ValueError("likelihood tape does not match complete receipt")
    if (receipt.get("training_sha256") != file_sha256(training_path)
            or receipt.get("training_rows") != len(training)):
        raise ValueError("training tape does not match complete receipt")
    _validate_training_rows(training, protocol["training"]["tokens"])
    return likelihood


def _mean_loss(rows):
    tokens = sum(row["target_tokens"] for row in rows)
    if not tokens:
        raise ValueError("cannot aggregate an empty likelihood denominator")
    return math.fsum(row["nll_sum"] for row in rows) / tokens

def _bits_per_source_byte(rows, byte_denominators):
    byte_count = sum(byte_denominators[(row["source_path"], row["target_snapshot"])] for row in rows)
    if not byte_count:
        raise ValueError("cannot aggregate an empty UTF-8 byte denominator")
    return math.fsum(row["nll_sum"] for row in rows) / (math.log(2) * byte_count)



def analyze(run_dir: Path):
    protocol, cases = validate_prepared(run_dir)
    receipt = json.loads((run_dir / "receipt.json").read_text())
    if (receipt.get("schema") != SCHEMA + "/receipt" or receipt.get("status") != "complete"
            or receipt.get("protocol_sha256") != file_sha256(run_dir / "protocol.json")):
        raise ValueError("complete source-bound run receipt required")
    if receipt.get("source_sha256") != protocol["source_tree"]:
        raise ValueError("receipt source-tree binding mismatch")
    likelihood = _check_receipt_tapes(run_dir, receipt, protocol)
    rows = _validated_rows(likelihood, cases)
    byte_denominators = {(item["source_path"], snapshot): item["score_bytes"][snapshot]
                         for item in cases["heldout_pairs"] for snapshot in ("old", "new")}
    changed = {item["source_path"] for item in cases["heldout_pairs"] if item["changed"]}
    unchanged = {item["source_path"] for item in cases["heldout_pairs"] if not item["changed"]}
    output = {"schema": SCHEMA + "/analysis", "complete": True, "protocol_sha256": file_sha256(run_dir / "protocol.json"),
              "receipt_sha256": file_sha256(run_dir / "receipt.json"), "errors": [],
              "denominators": {"changed_paths": len(changed), "unchanged_paths": len(unchanged),
                               "paired_paths": len(cases["heldout_pairs"]),
                               "expected_lora_rows": len(rows["lora"]),
                               "expected_base_rows": len(rows["base"]),
                               "expected_unigram_rows": len(rows["unigram"])}, "stages": {}}
    for stage in STAGES:
        populations, byte_populations = {}, {}
        for name, selected in (("changed", changed), ("unchanged", unchanged)):
            scores, byte_scores = {}, {}
            for model in ("old", "new"):
                for seed in SEEDS:
                    for target in ("old", "new"):
                        sample = [row for (m, s, step, t, path), row in rows["lora"].items()
                                  if m == model and s == seed and step == stage and t == target and path in selected]
                        key = f"lora_{model}_seed{seed}_on_{target}"
                        scores[key] = _mean_loss(sample)
                        byte_scores[key] = _bits_per_source_byte(sample, byte_denominators)
            for target in ("old", "new"):
                sample = [row for (target_snapshot, path), row in rows["base"].items()
                          if target_snapshot == target and path in selected]
                key = "base_on_" + target
                scores[key] = _mean_loss(sample)
                byte_scores[key] = _bits_per_source_byte(sample, byte_denominators)
                for unigram_model in ("old", "new"):
                    sample = [row for (model_snapshot, target_snapshot, path), row in rows["unigram"].items()
                              if model_snapshot == unigram_model and target_snapshot == target and path in selected]
                    key = f"unigram_{unigram_model}_on_{target}"
                    scores[key] = _mean_loss(sample)
                    byte_scores[key] = _bits_per_source_byte(sample, byte_denominators)
            populations[name] = scores
            byte_populations[name] = byte_scores
        summary = populations["changed"]
        crossovers = []
        for seed in SEEDS:
            old_old = summary[f"lora_old_seed{seed}_on_old"]
            new_old = summary[f"lora_new_seed{seed}_on_old"]
            old_new = summary[f"lora_old_seed{seed}_on_new"]
            new_new = summary[f"lora_new_seed{seed}_on_new"]
            crossovers.append({"seed": seed, "old_advantage_nats_per_token": new_old - old_old,
                               "new_advantage_nats_per_token": old_new - new_new,
                               "both_timepoints_preferred": new_old > old_old and old_new > new_new})
        output["stages"][str(stage)] = {
            "nats_per_token": populations,
            "bits_per_source_byte": byte_populations,
            "seed_crossovers": crossovers,
            "seeds_with_both_preferences": sum(row["both_timepoints_preferred"] for row in crossovers),
        }
    destination = run_dir / "analysis.json"
    write_json(destination, output)
    progress(f"analyzed {destination}: changed-paths={len(changed)}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--analyze", action="store_true")
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--old-revision")
    parser.add_argument("--new-revision")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.prepare:
            if not args.repository or not args.old_revision or not args.new_revision:
                parser.error("--prepare requires --repository, --old-revision and --new-revision")
            prepare(args.repository, args.old_revision, args.new_revision, args.run_dir)
        elif args.run:
            execute(args.run_dir)
        else:
            analyze(args.run_dir)
    except BaseException as exc:
        progress(f"failed: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
