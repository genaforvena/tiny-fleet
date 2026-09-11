#!/usr/bin/env python3
"""Prepare immutable, independently identifiable training runs.

This module is dependency-free by design: input validation and run allocation happen before
optional torch/transformers imports or model loading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
from pathlib import Path
from typing import Callable


class ManifestError(ValueError):
    """A frozen input, run identity, or resume contract is invalid."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def step_count(examples: int, epochs: int, batch: int, accumulation: int) -> int:
    if min(examples, epochs, batch, accumulation) <= 0:
        raise ManifestError("training counts must be positive")
    microbatches = math.ceil(examples / batch)
    return epochs * math.ceil(microbatches / accumulation)


def _input_specs(manifest: dict) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                found.append((value["path"], value["sha256"]))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(manifest.get("domains", manifest.get("datasets", {})))
    if not found:
        raise ManifestError("manifest has no hashed input files")
    return list(dict.fromkeys(found))


def verify_inputs(manifest: dict, manifest_path: Path) -> dict[str, str]:
    root = manifest_path.parent.resolve()
    hashes: dict[str, str] = {}
    for relative, expected in _input_specs(manifest):
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ManifestError(f"input escapes manifest root: {relative}") from exc
        if not path.is_file():
            raise ManifestError(f"input missing: {relative}")
        actual = sha256(path)
        hashes[relative] = actual
        if actual != expected:
            raise ManifestError(f"input hash mismatch: {relative}")
    return hashes


def _train_examples(manifest: dict, manifest_path: Path) -> int:
    total = 0
    domains = manifest.get("domains", {})
    for domain in domains.values():
        spec = domain.get("train") if isinstance(domain, dict) else None
        if not isinstance(spec, dict):
            continue
        if isinstance(spec.get("rows"), int):
            total += spec["rows"]
        else:
            total += len(((manifest_path.parent / spec["path"]).read_bytes()).splitlines())
    if total <= 0:
        raise ManifestError("manifest has no training examples")
    return total


def _resolved_config(manifest: dict, manifest_path: Path, seed: int, device: str, dtype: str) -> dict:
    base = manifest.get("base_model", {})
    revision = base.get("revision")
    if not isinstance(revision, str) or not revision or revision.startswith("UNPINNED"):
        raise ManifestError("base model revision is not pinned")
    tokenizer = manifest.get("tokenizer", {"id": base.get("id"), "revision": revision})
    tok_revision = tokenizer.get("revision")
    if not isinstance(tok_revision, str) or not tok_revision or tok_revision.startswith("UNPINNED"):
        raise ManifestError("tokenizer revision is not pinned")
    training = dict(manifest.get("training", {}))
    batch = int(training.get("batch", training.get("batch_size", 1)))
    accumulation = int(training.get("gradient_accumulation", 1))
    epochs = int(training.get("epochs", 1))
    examples_per_epoch = _train_examples(manifest, manifest_path)
    return {
        "schema": "tiny-fleet.run-config/v1",
        "base_model": {"id": base.get("id"), "revision": revision},
        "tokenizer": {"id": tokenizer.get("id", base.get("id")), "revision": tok_revision},
        "seeds": {"python": seed, "numpy": seed, "torch": seed},
        "runtime": {"device": device, "dtype": dtype},
        "training": {
            **training, "batch": batch, "gradient_accumulation": accumulation,
            "max_length": int(training.get("max_length", 256)), "epochs": epochs,
            "examples_per_epoch": examples_per_epoch, "examples": examples_per_epoch * epochs,
            "expected_optimizer_steps": step_count(examples_per_epoch, epochs, batch, accumulation),
        },
        "evaluation": dict(manifest.get("evaluation", {"max_length": int(training.get("max_length", 256))})),
        "data_hashes": verify_inputs(manifest, manifest_path),
    }


def seed_everything(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def prepare_run(manifest_path: Path, run_dir: Path, seed: int, *, arm: str = "persona-code",
                device: str = "cpu", dtype: str = "float32", checkpoint: Path | None = None,
                model_loader: Callable[[], object] | None = None) -> dict:
    manifest_path = manifest_path.resolve()
    config = _resolved_config(json.loads(manifest_path.read_text()), manifest_path, seed, device, dtype)
    run_dir = run_dir.resolve()
    marker = run_dir / "COMPLETE.json"
    config_path = run_dir / "config.json"
    if marker.exists():
        raise ManifestError(f"completed run exists: {run_dir}")
    if run_dir.exists() and any(run_dir.iterdir()):
        if not checkpoint or not config_path.is_file():
            raise ManifestError("existing run requires explicit checkpoint resume")
        old = json.loads(config_path.read_text())
        if old.get("data_hashes") != config["data_hashes"] or old.get("base_model") != config["base_model"]:
            raise ManifestError("resume config/data hashes do not match")
    run_dir.mkdir(parents=True, exist_ok=True)
    adapter_dir = run_dir / "adapters" / f"{arm}-seed-{seed}"
    if adapter_dir.exists():
        raise ManifestError(f"adapter already exists for seed: {adapter_dir}")
    adapter_dir.parent.mkdir(parents=True, exist_ok=True)
    config["run"] = {"seed": seed, "arm": arm, "adapter_dir": str(adapter_dir),
                     "manifest_sha256": sha256(manifest_path), "checkpoint": str(checkpoint) if checkpoint else None}
    tmp = config_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, config_path)
    seed_everything(seed)
    if model_loader is not None:
        model_loader()
    return {**config, "adapter_dir": str(adapter_dir)}


def record_completion(run_dir: Path, result: dict) -> None:
    marker = run_dir / "COMPLETE.json"
    if marker.exists():
        raise ManifestError("run is already complete")
    marker.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--arm", default="persona-code")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--dtype", default="float32")
    args = parser.parse_args()
    config = prepare_run(args.manifest, args.run_dir, args.seed, arm=args.arm, device=args.device, dtype=args.dtype)
    print(json.dumps(config, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
