#!/usr/bin/env python3
"""Offline, provenance-preserving generative drift matrix runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
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


def _is_hex(value, size):
    return isinstance(value, str) and len(value) == size and all(char in "0123456789abcdef" for char in value)


def _effective_seed(seed, repetition, prompt):
    return int(sha(f"{seed}:{repetition}:{prompt}")[:8], 16) % (2**31)


def validate_v2_manifest(manifest):
    if manifest.get("schema") != "tiny-fleet.drift-generative-manifest/v2":
        raise ValueError("v2 manifest schema")
    arms = manifest.get("arms", [])
    if not isinstance(arms, list) or len(arms) != 3 or set(arms) != {"base", "prompt-only", "lora"}:
        raise ValueError("v2 manifest must declare base, prompt-only, and lora arms")
    if not _is_hex(manifest.get("sample_manifest_sha256"), 64):
        raise ValueError("frozen source sample manifest hash required")
    snapshots = manifest.get("snapshots", [])
    snapshot_map = {}
    for snapshot in snapshots:
        repo = snapshot.get("repo")
        if not repo or repo in snapshot_map or not _is_hex(snapshot.get("old"), 40) or not _is_hex(snapshot.get("new"), 40):
            raise ValueError("v2 snapshots require unique repos and immutable old/new commits")
        snapshot_map[repo] = {"old": snapshot["old"], "new": snapshot["new"]}
    if len(snapshot_map) != 3:
        raise ValueError("v2 requires three registered source repositories")
    base = manifest.get("base_model", {})
    if not base.get("model_id") or not _is_hex(base.get("revision"), 40):
        raise ValueError("base model id and immutable revision required")
    scorer = manifest.get("scorer", {})
    if not scorer.get("id") or not _is_hex(scorer.get("revision"), 40) or not _is_hex(scorer.get("digest"), 64):
        raise ValueError("scorer id, immutable revision, and digest required")
    template = manifest.get("prompt_template")
    if not isinstance(template, str) or not template or manifest.get("prompt_template_sha256") != sha(template):
        raise ValueError("prompt template hash mismatch")
    generation = manifest.get("generation", {})
    if generation.get("do_sample") is not True or not isinstance(generation.get("temperature"), (int, float)) or generation["temperature"] <= 0:
        raise ValueError("v2 generation settings must use positive-temperature sampling")
    if not isinstance(generation.get("top_p"), (int, float)) or not 0 < generation["top_p"] <= 1:
        raise ValueError("invalid top_p")
    if not isinstance(generation.get("max_new_tokens"), int) or generation["max_new_tokens"] <= 0:
        raise ValueError("invalid max_new_tokens")
    seeds = manifest.get("seeds", [])
    repetitions = manifest.get("repetitions", [])
    if (not seeds or len(set(seeds)) != len(seeds) or any(not isinstance(seed, int) for seed in seeds)
            or not repetitions or len(set(repetitions)) != len(repetitions)
            or any(not isinstance(rep, int) or rep < 0 for rep in repetitions)):
        raise ValueError("seeds and nonnegative repetitions are required")
    prompts = manifest.get("prompts", [])
    prompt_keys = set()
    snapshots = {}
    for row in prompts:
        key = (row.get("repo"), row.get("snapshot"), row.get("prompt_id"))
        if key in prompt_keys:
            raise ValueError(f"duplicate v2 prompt key: {key}")
        prompt_keys.add(key)
        if not row.get("repo") or not row.get("source_family") or not row.get("prompt_id"):
            raise ValueError("missing v2 prompt provenance")
        if row.get("snapshot") not in {"old", "new"}:
            raise ValueError("invalid v2 snapshot")
        if row["repo"] not in snapshot_map or row.get("source_commit") != snapshot_map[row["repo"]][row["snapshot"]]:
            raise ValueError(f"prompt source commit mismatch: {key}")
        source_path = Path(row.get("source_path", ""))
        if not source_path.as_posix() or source_path.is_absolute() or ".." in source_path.parts or not _is_hex(row.get("source_file_sha256"), 64):
            raise ValueError(f"prompt source path or file hash invalid: {key}")
        snapshots.setdefault(row["repo"], set()).add(row["snapshot"])
        excerpt = row.get("snapshot_excerpt")
        if not isinstance(excerpt, str) or not excerpt or row.get("snapshot_excerpt_sha256") != sha(excerpt):
            raise ValueError(f"snapshot excerpt hash mismatch: {key}")
        adapter = row.get("lora_adapter", {})
        if not isinstance(adapter.get("path"), str) or not adapter["path"] or not _is_hex(adapter.get("digest"), 64):
            raise ValueError(f"LoRA adapter digest and path required: {key}")
        adapter_path = Path(adapter["path"])
        if adapter_path.is_absolute() or ".." in adapter_path.parts:
            raise ValueError(f"LoRA adapter path must stay inside the manifest tree: {key}")
    if len(prompts) != 6 or len(snapshots) != 3 or set(snapshots) != set(snapshot_map) or any(labels != {"old", "new"} for labels in snapshots.values()):
        raise ValueError("v2 requires old/new prompt rows for exactly three repositories")
    return len(prompts)


def build_effective_input(manifest, prompt, arm):
    if arm == "prompt-only":
        return f"{manifest['prompt_template']}\n\nSnapshot excerpt:\n{prompt['snapshot_excerpt']}"
    if arm in {"base", "lora"}:
        return manifest["prompt_template"]
    raise ValueError(f"unknown arm: {arm}")


def validate_v2_records(manifest, records):
    validate_v2_manifest(manifest)
    expected = {
        (p["repo"], p["snapshot"], arm, p["prompt_id"], seed, repetition)
        for p in manifest["prompts"] for arm in manifest["arms"]
        for seed in manifest["seeds"] for repetition in manifest["repetitions"]
    }
    actual = set()
    prompts = {(p["repo"], p["snapshot"], p["prompt_id"]): p for p in manifest["prompts"]}
    base = manifest["base_model"]
    for row in records:
        key = tuple(row.get(field) for field in KEYS)
        if key in actual:
            raise ValueError(f"duplicate v2 record key: {key}")
        actual.add(key)
        prompt = prompts.get((row.get("repo"), row.get("snapshot"), row.get("prompt_id")))
        if prompt is None or row.get("schema") != "tiny-fleet.drift-generative/v2":
            raise ValueError(f"unknown v2 prompt or record schema: {key}")
        for field in ("source_commit", "source_path", "source_file_sha256", "snapshot_excerpt_sha256"):
            if row.get(field) != prompt.get(field):
                raise ValueError(f"snapshot source provenance mismatch: {key}")
        arm = row["arm"]
        effective = build_effective_input(manifest, prompt, arm)
        if row.get("effective_input") != effective or row.get("effective_input_sha256") != sha(effective):
            raise ValueError(f"effective input mismatch: {key}")
        if row.get("base_model_id") != base["model_id"] or row.get("base_model_revision") != base["revision"]:
            raise ValueError(f"base model provenance mismatch: {key}")
        if row.get("effective_seed") != _effective_seed(row["seed"], row["repetition"], effective):
            raise ValueError(f"effective seed mismatch: {key}")
        expected_adapter = prompt["lora_adapter"]["digest"] if arm == "lora" else None
        if row.get("adapter_digest") != expected_adapter:
            raise ValueError(f"adapter digest mismatch: {key}")
        scorer = manifest["scorer"]
        if row.get("scorer_id") != scorer["id"] or row.get("scorer_revision") != scorer["revision"]:
            raise ValueError(f"scorer provenance mismatch: {key}")
        if row.get("scorer_digest") != scorer["digest"]:
            raise ValueError(f"scorer digest mismatch: {key}")
        if not row.get("backend") or row["backend"].startswith("fake"):
            raise ValueError("fixture backends cannot emit v2 records")
        runtime = row.get("runtime", {})
        if not all(isinstance(runtime.get(field), str) and runtime[field] for field in ("python", "torch", "transformers", "device")):
            raise ValueError(f"v2 runtime provenance missing: {key}")
        if row.get("status") == "ok":
            if not isinstance(row.get("output"), str) or not row["output"]:
                raise ValueError(f"successful v2 record has no output: {key}")
        elif row.get("status") == "error":
            if not isinstance(row.get("error"), str) or not row["error"]:
                raise ValueError(f"failed v2 record has no error detail: {key}")
        else:
            raise ValueError(f"invalid v2 status: {key}")
    missing = expected - actual
    if missing:
        raise ValueError(f"missing v2 arm: {sorted(missing)[0][2]}")
    if actual != expected:
        raise ValueError("v2 record matrix mismatch")
    return "ACCEPT"


def adapter_tree_digest(adapter_dir):
    adapter_dir = Path(adapter_dir)
    if not adapter_dir.is_dir():
        raise ValueError(f"adapter directory missing: {adapter_dir}")
    files = sorted(path for path in adapter_dir.rglob("*") if path.is_file())
    if not files:
        raise ValueError("adapter directory is empty")
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(adapter_dir).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


class TransformersBackend(Backend):
    """Local-only Transformers/PEFT backend pinned to immutable source revisions."""
    name = "transformers-pinned-v2"

    def __init__(self, model_id, revision, *, device="cpu", adapter_path=None, adapter_digest=None, generation=None):
        if not model_id or not _is_hex(revision, 40):
            raise ValueError("Transformers backend requires an immutable 40-hex model revision")
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.adapter_digest = None
        try:
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("install the pinned torch and transformers runtime") from exc
        self.torch = torch
        self.transformers_version = transformers.__version__
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, local_files_only=True, trust_remote_code=False)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, revision=revision, local_files_only=True, trust_remote_code=False, dtype=torch.float32
        )
        if adapter_path is not None:
            observed = adapter_tree_digest(adapter_path)
            if not _is_hex(adapter_digest, 64) or observed != adapter_digest:
                raise ValueError("LoRA adapter tree digest mismatch")
            try:
                from peft import PeftModel
            except ImportError as exc:
                raise RuntimeError("install pinned peft to load LoRA adapters") from exc
            model = PeftModel.from_pretrained(model, adapter_path, is_trainable=False, local_files_only=True)
            self.adapter_digest = observed
        elif adapter_digest is not None:
            raise ValueError("adapter digest is only valid with an adapter path")
        self.model = model.to(device).eval()
        self.generation = generation or {"do_sample": True, "temperature": 0.7, "top_p": 0.9, "max_new_tokens": 128}

    def generate(self, prompt, *, arm, seed, repetition):
        effective_seed = _effective_seed(seed, repetition, prompt)
        self.torch.manual_seed(effective_seed)
        if self.device.startswith("cuda") and self.torch.cuda.is_available():
            self.torch.cuda.manual_seed_all(effective_seed)
        if getattr(self.tokenizer, "chat_template", None):
            encoded = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt",
            )
        else:
            encoded = self.tokenizer(prompt, return_tensors="pt")
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        input_ids = encoded["input_ids"]
        options = dict(self.generation)
        with self.torch.inference_mode():
            result = self.model.generate(**encoded, **options)
        return self.tokenizer.decode(result[0][input_ids.shape[1]:], skip_special_tokens=True).strip()


def generate_v2(manifest_path, run_dir, backend=None, *, device="cpu"):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_v2_manifest(manifest)
    if backend is not None and (isinstance(backend, FakeBackend) or backend.name.startswith("fake")):
        raise ValueError("fixture backends cannot emit v2 records")
    run_dir = Path(run_dir)
    records = []
    backends = {}
    base = manifest["base_model"]
    for prompt in manifest["prompts"]:
        for arm in manifest["arms"]:
            adapter = prompt["lora_adapter"] if arm == "lora" else None
            adapter_digest = adapter["digest"] if adapter else None
            backend_key = adapter_digest or "base-model"
            if backend is not None:
                selected_backend = backend
            else:
                if backend_key not in backends:
                    adapter_path = manifest_path.parent / adapter["path"] if adapter else None
                    backends[backend_key] = TransformersBackend(
                        base["model_id"], base["revision"], device=device, adapter_path=adapter_path,
                        adapter_digest=adapter_digest, generation=manifest["generation"],
                    )
                selected_backend = backends[backend_key]
            for seed in manifest["seeds"]:
                for repetition in manifest["repetitions"]:
                    effective_input = build_effective_input(manifest, prompt, arm)
                    row = {
                        "schema": "tiny-fleet.drift-generative/v2",
                        **{key: prompt[key] for key in ("repo", "snapshot", "prompt_id", "source_family")},
                        **{key: prompt[key] for key in ("source_commit", "source_path", "source_file_sha256", "snapshot_excerpt_sha256")},
                        "arm": arm, "seed": seed, "repetition": repetition,
                        "effective_input": effective_input,
                        "effective_input_sha256": sha(effective_input),
                        "effective_seed": _effective_seed(seed, repetition, effective_input),
                        "base_model_id": base["model_id"], "base_model_revision": base["revision"],
                        "adapter_digest": adapter_digest,
                        "scorer_id": manifest["scorer"]["id"], "scorer_revision": manifest["scorer"]["revision"],
                        "scorer_digest": manifest["scorer"]["digest"], "backend": selected_backend.name,
                    }
                    started = time.perf_counter()
                    try:
                        output = selected_backend.generate(effective_input, arm=arm, seed=seed, repetition=repetition)
                        if not output:
                            raise ValueError("empty model output")
                        row.update(status="ok", output=output)
                    except Exception as exc:
                        row.update(status="error", error=f"{type(exc).__name__}: {exc}")
                    row["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
                    row["runtime"] = {
                        "python": platform.python_version(),
                        "torch": getattr(getattr(selected_backend, "torch", None), "__version__", None),
                        "transformers": getattr(selected_backend, "transformers_version", None),
                        "device": device,
                    }
                    records.append(row)
    validate_v2_records(manifest, records)
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "generative-v2.jsonl"
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    frozen = dict(manifest)
    frozen["records_sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    (run_dir / "manifest-v2.json").write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"schema": "tiny-fleet.drift-generative-run/v2", "records": len(records), "arms": manifest["arms"], "generative": str(output_path), "records_sha256": frozen["records_sha256"]}


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
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)
    schema = json.loads(args.manifest.read_text(encoding="utf-8")).get("schema")
    if schema == "tiny-fleet.drift-generative-manifest/v2":
        result = generate_v2(args.manifest, args.run_dir, FakeBackend() if args.fake else None, device=args.device)
    elif schema == "tiny-fleet.drift-generative-manifest/v1":
        result = generate(args.manifest, args.run_dir, FakeBackend() if args.fake else None)
    else:
        raise ValueError("unsupported generative manifest schema")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
