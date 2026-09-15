#!/usr/bin/env python3
"""Orchestrate the preregistered Tiny Fleet study matrix."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from study_runner import FakeBackend, TransformersBackend, load_corpus, run as run_arm


ROOT = Path(__file__).resolve().parents[1]


def gpu_free_mb(smi: str = "nvidia-smi") -> int:
    """Read live free VRAM, failing loudly when telemetry is unavailable."""
    result = subprocess.run(
        [smi, "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, check=False,
    )
    value = result.stdout.strip().splitlines()[0].strip() if result.stdout.strip() else ""
    if result.returncode != 0 or not value.isdigit():
        detail = result.stderr.strip() or "no numeric memory.free reading"
        raise RuntimeError(f"GPU telemetry unavailable: {detail}")
    return int(value)


def wait_for_gpu(min_free_mb: int, smi: str = "nvidia-smi", *, poll_s: float = 30.0,
                 timeout_s: float = 86400.0) -> dict:
    """Wait for capacity without operator input; return the live admission evidence."""
    if min_free_mb < 1 or poll_s < 0 or timeout_s < 0:
        raise ValueError("GPU wait parameters must be non-negative and min_free_mb must be positive")
    started = time.monotonic()
    samples = 0
    while True:
        free_mb = gpu_free_mb(smi)
        samples += 1
        waited_s = round(time.monotonic() - started, 3)
        if free_mb >= min_free_mb:
            return {"status": "admitted", "probe": smi, "min_free_mb": min_free_mb,
                    "free_mb": free_mb, "waited_s": waited_s, "samples": samples}
        if waited_s >= timeout_s:
            raise TimeoutError(
                f"GPU remained below {min_free_mb} MiB after {waited_s}s (free={free_mb} MiB)"
            )
        time.sleep(min(poll_s, max(0.0, timeout_s - waited_s)))


REGISTERED_TO_EXECUTION = {
    "base": ("base",),
    "prompt_only": ("prompt-only",),
    "pooled_adapter": ("pooled-lora",),
    # Router arms are evaluated by running the frozen specialist for each
    # held-out domain and concatenating those raw records.  This keeps routing
    # explicit in the matrix instead of silently treating a router as base.
    "simple_router": tuple(f"specialist:{domain}" for domain in (
        "toy_passage_ppl", "executable_code", "rated_style", "adversarial_safety")),
    "routed_specialists": tuple(f"specialist:{domain}" for domain in (
        "toy_passage_ppl", "executable_code", "rated_style", "adversarial_safety")),
}


def build_matrix(registration: dict) -> list[dict]:
    arms = registration.get("arms")
    seeds = registration.get("statistics", {}).get("seeds")
    if not isinstance(arms, list) or not arms:
        raise ValueError("registration arms must be a non-empty list")
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("registration seeds must be a non-empty list")

    arm_ids = []
    matrix = []
    for arm in arms:
        if not isinstance(arm, dict) or not isinstance(arm.get("id"), str) or not arm["id"]:
            raise ValueError("each registered arm must have a non-empty id")
        if arm["id"] in arm_ids:
            raise ValueError(f"duplicate registered arm id: {arm['id']}")
        arm_ids.append(arm["id"])
    for seed in seeds:
        for arm in arms:
            matrix.append({"arm": arm["id"], "seed": seed})
    return matrix


def execution_arms(registered_arm: str) -> tuple[str, ...]:
    try:
        return REGISTERED_TO_EXECUTION[registered_arm]
    except KeyError as exc:
        raise ValueError(f"no execution mapping for registered arm: {registered_arm}") from exc


def selected_matrix_rows(registration: dict, seeds: list[int] | None = None) -> list[dict]:
    """Return each registered arm×seed row once, preserving registration order."""
    matrix = build_matrix(registration)
    if seeds is None:
        return matrix
    wanted = set(seeds)
    unknown = wanted - set(registration["statistics"]["seeds"])
    if unknown:
        raise ValueError(f"unregistered seed selection: {sorted(unknown)}")
    return [row for row in matrix if row["seed"] in wanted]


def require_adapters(run_root: Path, registered_arm: str) -> dict[str, Path]:
    """Resolve and validate required frozen adapter artifacts; never substitute another arm."""
    study_root = run_root.parents[1]
    if registered_arm == "pooled_adapter":
        required = {"pooled-lora": study_root / "adapters/study-pooled"}
    elif registered_arm in {"simple_router", "routed_specialists"}:
        required = {
            arm: study_root / "adapters" / f"study-{arm.split(':', 1)[1]}"
            for arm in execution_arms(registered_arm)
        }
    else:
        return {}
    missing = [str(path) for path in required.values() if not path.is_dir()]
    if missing:
        raise RuntimeError(
            f"missing trained adapter artifacts for {registered_arm}: {', '.join(missing)}"
        )
    from train_study_adapters import adapter_tree_digest, training_specs
    registration = json.loads((run_root / "registration.json").read_text(encoding="utf-8"))
    manifest_path = study_root / "corpus/study-v1/manifest.json"
    train_path = study_root / "corpus/study-v1/train.jsonl"
    specs = training_specs(registration, manifest_path.read_bytes(), train_path.read_bytes())
    for execution_arm, path in required.items():
        key = "pooled" if execution_arm == "pooled-lora" else execution_arm.split(":", 1)[1]
        receipt_path = path / "study-adapter.json"
        if not receipt_path.is_file():
            raise RuntimeError(f"adapter provenance receipt missing: {path}")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        expected = specs[key]
        for field in ("study_id", "adapter_id", "role", "base_model", "corpus_manifest_sha256", "train_corpus_sha256", "config_sha256"):
            if receipt.get(field) != expected.get(field):
                raise RuntimeError(f"adapter provenance mismatch for {path}: {field}")
        if receipt.get("adapter_tree_digest") != adapter_tree_digest(path):
            raise RuntimeError(f"adapter tree digest mismatch: {path}")
    return required


def run_registered_arm(manifest: Path, run_root: Path, registered_arm: str, seed: int,
                       backend: object, limit: int | None) -> dict:
    adapter_paths = require_adapters(run_root, registered_arm)
    summaries = []
    for execution_arm in execution_arms(registered_arm):
        adapter_dir = adapter_paths.get(execution_arm)
        arm_backend = backend
        if adapter_dir is not None:
            arm_backend = TransformersBackend(
                backend.model_id, backend.revision, adapter_dir=adapter_dir,
            )
        arm_dir = run_root / f"seed-{seed}" / registered_arm / execution_arm.replace(':', '__')
        summaries.append(run_arm(manifest, arm_dir, execution_arm, seed,
                                 backend=arm_backend, limit=limit))
    return {"registered_arm": registered_arm, "seed": seed, "execution": summaries}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the immutable fleet-study matrix.")
    parser.add_argument("--registration", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--plan-only", action="store_true", help="validate and print the frozen matrix without running it")
    parser.add_argument("--manifest", type=Path, default=Path("corpus/study-v1/manifest.json"))
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--max-train-steps", type=int, help="accepted for bounded smoke compatibility; no training is performed")
    parser.add_argument("--verification-only", action="store_true", help="run a labeled fake-backend smoke in the supplied run root")
    parser.add_argument("--gpu-min-free-mb", type=int,
                        help="minimum free VRAM before real execution (default: 2048 MiB or MESH_STUDY_GPU_MIN_FREE_MB)")
    parser.add_argument("--gpu-poll-s", type=float, default=30.0,
                        help="seconds between GPU capacity checks")
    parser.add_argument("--gpu-wait-s", type=float,
                        help="maximum GPU wait (default: registered max_wall_hours)")
    args = parser.parse_args(argv)
    default_manifest = Path("corpus/study-v1/manifest.json")
    if not args.verification_only and (
        args.seeds is not None or args.max_cases is not None or args.manifest != default_manifest
    ):
        raise ValueError(
            "real execution is autonomous: --manifest, --seeds, and --max-cases are verification-only overrides"
        )
    registration = json.loads(args.registration.read_text(encoding="utf-8"))
    matrix = build_matrix(registration)
    if args.plan_only:
        print(json.dumps({"study_id": registration.get("study_id"), "rows": matrix}, sort_keys=True))
        return 0
    if args.run_root.exists() and any(args.run_root.iterdir()):
        allowed_inputs = {"registration.json", "config.json", "datasets.json", "router.json", "resource-preflight.json", "autonomy-decision.json", "adapter-training.json"}
        existing = {entry.name for entry in args.run_root.iterdir()}
        if not existing.issubset(allowed_inputs):
            raise RuntimeError(f"refusing to overwrite non-empty run root: {args.run_root}")
    if args.max_cases is not None and args.max_cases < 1:
        raise ValueError("--max-cases must be positive")
    if args.max_train_steps not in (None, 0, 1, 2):
        raise ValueError("verification-only supports --max-train-steps 2 or less")

    seeds = args.seeds or registration["statistics"]["seeds"]
    selected = selected_matrix_rows(registration, args.seeds)
    args.run_root.mkdir(parents=True, exist_ok=True)
    manifest, rows = load_corpus(args.manifest)
    limit = args.max_cases
    if args.verification_only:
        backend = FakeBackend()
        resource_receipt = {"status": "not-required", "reason": "verification-only fake backend"}
    else:
        min_free_mb = args.gpu_min_free_mb
        if min_free_mb is None:
            min_free_mb = int(os.environ.get("MESH_STUDY_GPU_MIN_FREE_MB", "2048"))
        wait_s = args.gpu_wait_s
        if wait_s is None:
            wait_s = float(registration.get("resource_cap", {}).get("max_wall_hours", 24)) * 3600
        try:
            resource_receipt = wait_for_gpu(min_free_mb, os.environ.get("MESH_STUDY_GPU_SMI", "nvidia-smi"),
                                            poll_s=args.gpu_poll_s, timeout_s=wait_s)
        except (RuntimeError, TimeoutError) as exc:
            resource_receipt = {"status": "deferred", "reason": str(exc), "min_free_mb": min_free_mb,
                                "wait_s": wait_s}
            (args.run_root / "resource-preflight.json").write_text(
                json.dumps(resource_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(resource_receipt, sort_keys=True), file=sys.stderr)
            return 75
        (args.run_root / "resource-preflight.json").write_text(
            json.dumps(resource_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for registered_arm in [row["arm"] for row in matrix if (args.seeds is None or row["seed"] in args.seeds)]:
            require_adapters(args.run_root, registered_arm)
        backend = TransformersBackend(
            registration["model"]["base_id"], registration["model"]["base_revision"]
        )
    arm_map = {
        "base": "base", "prompt_only": "prompt-only", "pooled_adapter": "pooled-lora",
        "simple_router": "base", "routed_specialists": "base",
    }
    summaries = []
    for item in selected:
        registered_arm = item["arm"]
        if args.verification_only:
            summary = run_arm(args.manifest, args.run_root / f"seed-{item['seed']}" / registered_arm,
                              arm_map[registered_arm], item["seed"], backend=backend, limit=limit)
            summary["registered_arm"] = registered_arm
            summary["verification_only"] = True
        else:
            summary = run_registered_arm(args.manifest, args.run_root, registered_arm,
                                         item["seed"], backend, limit)
            summary["verification_only"] = False
        summaries.append(summary)
    result = {
        "schema": "tiny-fleet.study-matrix-smoke/v1", "study_id": registration.get("study_id"),
        "verification_only": args.verification_only, "training_executed": not args.verification_only, "max_cases": limit,
        "seeds": seeds, "arms": [a["id"] for a in registration["arms"]],
        "rows": len(summaries), "summaries": summaries,
        "resource_preflight": resource_receipt,
    }
    (args.run_root / "smoke-summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
