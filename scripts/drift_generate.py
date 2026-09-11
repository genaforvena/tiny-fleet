#!/usr/bin/env python3
"""Offline, provenance-preserving generative drift matrix runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


KEYS = ("repo", "snapshot", "arm", "prompt_id", "seed", "repetition")


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Backend:
    name = "abstract"

    def generate(self, prompt, *, arm, seed, repetition):
        raise NotImplementedError


class FakeBackend(Backend):
    name = "fake-drift-v1"

    def generate(self, prompt, *, arm, seed, repetition):
        return f"fake:{arm}:{seed}:{repetition}:{sha(prompt)[:12]}"


def validate_manifest(manifest):
    if manifest.get("schema") != "tiny-fleet.drift-generative-manifest/v1":
        raise ValueError("manifest schema")
    arms = manifest.get("arms", [])
    if set(arms) != {"base", "prompt-only", "lora"}:
        raise ValueError("manifest must declare base, prompt-only, and lora arms")
    seen = set()
    prompts = manifest.get("prompts", [])
    for row in prompts:
        key = (row.get("repo"), row.get("snapshot"), row.get("prompt_id"))
        if key in seen:
            raise ValueError(f"duplicate prompt key: {key}")
        seen.add(key)
        if row.get("snapshot") not in {"old", "new"} or not row.get("prompt"):
            raise ValueError("invalid prompt provenance")
        if row["snapshot"] == "old" and "new prompt" in row["prompt"]:
            raise ValueError("contaminated old prompt")
        if row["snapshot"] == "new" and "old prompt" in row["prompt"]:
            raise ValueError("contaminated new prompt")
        for field in ("repo", "source_family"):
            if not row.get(field):
                raise ValueError(f"missing prompt provenance: {field}")
    if not prompts:
        raise ValueError("manifest has no prompts")


def validate_records(manifest, records):
    validate_manifest(manifest)
    expected = {(p["repo"], p["snapshot"], arm, p["prompt_id"], seed, repetition)
                for p in manifest["prompts"] for arm in manifest["arms"]
                for seed in manifest["seeds"] for repetition in manifest["repetitions"]}
    actual = set()
    prompt_map = {(p["repo"], p["snapshot"], p["prompt_id"]): p for p in manifest["prompts"]}
    for row in records:
        key = tuple(row.get(k) for k in KEYS)
        if key in actual:
            raise ValueError(f"duplicate record key: {key}")
        actual.add(key)
        p = prompt_map.get((row.get("repo"), row.get("snapshot"), row.get("prompt_id")))
        if p is None or row.get("prompt") != p["prompt"]:
            raise ValueError(f"snapshot label or prompt mismatch: {key}")
        if row.get("input_sha256") != sha(row["prompt"]):
            raise ValueError(f"input hash mismatch: {key}")
        if row.get("model_digest") != manifest["model_digest"] or row.get("scorer_digest") != manifest["scorer_digest"]:
            raise ValueError(f"provenance digest mismatch: {key}")
    missing = expected - actual
    if missing:
        arms = sorted({key[2] for key in missing})
        raise ValueError(f"missing arm: {arms[0]}")
    if actual != expected:
        raise ValueError("record matrix mismatch")
    return "ACCEPT"


def generate(manifest_path, run_dir, backend=None):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    validate_manifest(manifest)
    backend = backend or FakeBackend()
    run_dir = Path(run_dir); run_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for prompt in manifest["prompts"]:
        for arm in manifest["arms"]:
            for seed in manifest["seeds"]:
                for repetition in manifest["repetitions"]:
                    started = time.perf_counter()
                    row = {"schema": "tiny-fleet.drift-generative/v1", **{key: prompt[key] for key in ("repo", "snapshot", "prompt_id", "prompt", "source_family")},
                           "arm": arm, "seed": seed, "repetition": repetition,
                           "input_sha256": sha(prompt["prompt"]), "model_digest": manifest["model_digest"],
                           "scorer_digest": manifest["scorer_digest"], "backend": backend.name}
                    try:
                        row["output"] = backend.generate(prompt["prompt"], arm=arm, seed=seed, repetition=repetition)
                        row["status"] = "ok"
                    except Exception as exc:
                        row["status"] = "error"; row["error"] = f"{type(exc).__name__}: {exc}"
                    row["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
                    records.append(row)
    validate_records(manifest, records)
    path = run_dir / "generative.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    frozen = dict(manifest); frozen["records_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (run_dir / "manifest.json").write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"schema": "tiny-fleet.drift-generative-run/v1", "records": len(records), "arms": manifest["arms"],
            "generative": str(path), "records_sha256": frozen["records_sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--fake", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(generate(args.manifest, args.run_dir, FakeBackend() if args.fake else None), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
