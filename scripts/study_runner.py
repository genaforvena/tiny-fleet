#!/usr/bin/env python3
"""Run the controlled fleet-study matrix with auditable raw records.

The default backend is the real Transformers backend.  Tests inject the small
fake backend below; it is deliberately incapable of seeing corpus references.
Each invocation writes one JSONL record per requested case and arm, including
failures, so missing generations cannot become synthetic scores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("toy_passage_ppl", "executable_code", "rated_style", "adversarial_safety")
BASE_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
BASE_REVISION = "a10cc1512eabd3dde888204e902eca88bddb4951"
ARMS = ("base", "prompt-only", "pooled-lora", *(f"specialist:{d}" for d in DOMAINS))


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_json(value: Any) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_corpus(manifest_path: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent.parent.parent
    rows = {split: load_jsonl(root / path) for split, path in manifest["files"].items()}
    return manifest, rows


def validate_corpus(manifest: dict[str, Any], rows: dict[str, list[dict[str, Any]]]) -> None:
    expected = set(manifest["files"])
    if set(rows) != expected:
        raise ValueError("corpus split set does not match manifest")
    families: dict[str, str] = {}
    for split, items in rows.items():
        if len(items) != manifest["rows_per_file"][split]:
            raise ValueError(f"{split}: row count mismatch")
        for row in items:
            for key in ("case_id", "domain", "prompt", "reference", "source_family", "split"):
                if key not in row:
                    raise ValueError(f"{split}: missing {key}")
            if row["split"] != split:
                raise ValueError(f"{row['case_id']}: split mismatch")
            old = families.setdefault(row["source_family"], split)
            if old != split:
                raise ValueError(f"source family leakage: {row['source_family']}")
            if row["reference"] in row["prompt"]:
                raise ValueError(f"reference already in prompt: {row['case_id']}")


def _domain_train(rows: list[dict[str, Any]], domain: str) -> list[dict[str, Any]]:
    return [r for r in rows if r["domain"] == domain]


def render_input(case: dict[str, Any], arm: str, train_rows: list[dict[str, Any]]) -> str:
    if arm == "base" or arm.startswith("specialist:") or arm == "pooled-lora":
        return case["prompt"]
    if arm != "prompt-only":
        raise ValueError(f"unknown arm: {arm}")
    examples = _domain_train(train_rows, case["domain"])[:2]
    # The reference belongs to scoring only, including for prompt-only.  Use
    # the train prompts as context without smuggling target text into input.
    shots = "\n".join(f"Related task: {x['prompt']}" for x in examples)
    return f"{shots}\n\nTask: {case['prompt']}\nAnswer:"


class Backend:
    name = "abstract"

    def generate(self, rendered_input: str, *, seed: int, arm: str, timeout_s: float) -> str:
        raise NotImplementedError


class FakeBackend(Backend):
    name = "fake-v1"

    def generate(self, rendered_input: str, *, seed: int, arm: str, timeout_s: float) -> str:
        if "__TIMEOUT__" in rendered_input:
            raise TimeoutError("fake backend timeout")
        return f"fake answer seed={seed} arm={arm} input_sha={sha_bytes(rendered_input.encode())[:12]}"


class TransformersBackend(Backend):
    name = "transformers"

    def __init__(self, model_id: str, revision: str, adapter_dir: Path | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, local_files_only=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, local_files_only=True)
        if adapter_dir:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, str(adapter_dir))
        self.model.eval()

    def generate(self, rendered_input: str, *, seed: int, arm: str, timeout_s: float) -> str:
        torch = self.torch
        torch.manual_seed(seed)
        encoded = self.tokenizer(rendered_input, return_tensors="pt", truncation=True, max_length=256)
        started = time.monotonic()
        with torch.no_grad():
            output = self.model.generate(**encoded, max_new_tokens=16, do_sample=False, pad_token_id=self.tokenizer.pad_token_id)
        if time.monotonic() - started > timeout_s:
            raise TimeoutError(f"generation exceeded {timeout_s}s")
        return self.tokenizer.decode(output[0, encoded["input_ids"].shape[-1]:], skip_special_tokens=True).strip()


def run(manifest_path: Path, run_dir: Path, arm: str, seed: int, backend: Backend | None = None,
        limit: int | None = None, timeout_s: float = 120.0) -> dict[str, Any]:
    corpus_manifest, rows = load_corpus(manifest_path)
    validate_corpus(corpus_manifest, rows)
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}")
    cases = rows["heldout"] if limit is None else rows["heldout"][:limit]
    backend = backend or TransformersBackend(BASE_MODEL, BASE_REVISION)
    config = {
        "schema": "tiny-fleet.study-run-config/v1", "study_id": "fleet-study-v1", "arm": arm,
        "seed": seed, "base_model": {"id": BASE_MODEL, "revision": BASE_REVISION},
        "decoding": {"do_sample": False, "max_new_tokens": 16}, "timeout_s": timeout_s,
        "backend": backend.name, "corpus_manifest_sha256": sha_bytes(manifest_path.read_bytes()),
        "reference_policy": "reference is scorer-only and must not enter rendered_input",
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records_path = run_dir / f"predictions-{arm.replace(':', '__')}.jsonl"
    records: list[dict[str, Any]] = []
    with records_path.open("w", encoding="utf-8") as handle:
        for case in cases:
            rendered = render_input(case, arm, rows["train"])
            started = time.perf_counter()
            record: dict[str, Any] = {
                "schema": "tiny-fleet.study-prediction/v1", "case_id": case["case_id"], "domain": case["domain"],
                "split": case["split"], "arm": arm, "seed": seed,
                "case_prompt_sha256": sha_bytes(case["prompt"].encode()), "rendered_input": rendered,
                "rendered_input_sha256": sha_bytes(rendered.encode()), "reference_in_input": case["reference"] in rendered,
                "model_id": BASE_MODEL, "model_revision": BASE_REVISION, "config_sha256": sha_json(config),
            }
            try:
                if record["reference_in_input"]:
                    raise ValueError("reference leakage")
                record["output"] = backend.generate(rendered, seed=seed, arm=arm, timeout_s=timeout_s)
                record["runtime_status"] = "ok"
            except TimeoutError as exc:
                record["runtime_status"], record["error"] = "timeout", str(exc)
            except Exception as exc:  # retain the failed observation in the raw matrix
                record["runtime_status"], record["error"] = "error", f"{type(exc).__name__}: {exc}"
            record["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            records.append(record)
    summary = {"schema": "tiny-fleet.study-run-summary/v1", "arm": arm, "records": len(records),
               "ok": sum(r["runtime_status"] == "ok" for r in records),
               "failed": sum(r["runtime_status"] != "ok" for r in records),
               "predictions": str(records_path), "config": str(run_dir / "config.json"),
               "records_sha256": sha_bytes(records_path.read_bytes())}
    (run_dir / f"summary-{arm.replace(':', '__')}.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "corpus/study-v1/manifest.json")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout-s", type=float, default=120.0)
    parser.add_argument("--fake", action="store_true")
    args = parser.parse_args()
    backend = FakeBackend() if args.fake else None
    print(json.dumps(run(args.manifest, args.run_dir, args.arm, args.seed, backend, args.limit, args.timeout_s), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
