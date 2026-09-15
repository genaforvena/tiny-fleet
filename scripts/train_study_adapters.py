#!/usr/bin/env python3
"""Train the five frozen fleet-study LoRA adapters with explicit provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import sys
from pathlib import Path

from study_runner import load_corpus, validate_corpus


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "runs/fleet-study-v1/registration.json"
MANIFEST = ROOT / "corpus/study-v1/manifest.json"
ADAPTERS = ROOT / "adapters"
DOMAINS = ("toy_passage_ppl", "executable_code", "rated_style", "adversarial_safety")
BASE_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
BASE_REVISION = "a10cc1512eabd3dde888204e902eca88bddb4951"
PROVENANCE_FILE = "study-adapter.json"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_json(value: object) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def adapter_tree_digest(path: Path) -> str:
    """Digest adapter payload/config files, excluding the self-describing receipt."""
    entries = []
    for item in sorted(Path(path).rglob("*")):
        if item.is_file() and item.name != PROVENANCE_FILE:
            entries.append(item.relative_to(path).as_posix().encode() + b"\0" + item.read_bytes())
    if not entries:
        raise ValueError(f"adapter has no payload files: {path}")
    return sha_bytes(b"".join(entries))


def training_specs(registration: dict, manifest_bytes: bytes, train_bytes: bytes) -> dict[str, dict]:
    if registration.get("study_id") != "fleet-study-v1":
        raise ValueError("unexpected study registration")
    model = registration.get("model", {})
    if {model.get("base_id"), model.get("base_revision")} != {BASE_MODEL, BASE_REVISION}:
        raise ValueError("study base model is not the pinned local model")
    adapter_config = model.get("adapter")
    if not isinstance(adapter_config, dict):
        raise ValueError("study adapter configuration is missing")
    frozen = {"model": {"base_id": BASE_MODEL, "base_revision": BASE_REVISION}, "adapter": adapter_config,
              "seed": 17, "source": "corpus/study-v1/train.jsonl"}
    common = {"study_id": registration["study_id"], "base_model": {"id": BASE_MODEL, "revision": BASE_REVISION},
              "corpus_manifest_sha256": sha_bytes(manifest_bytes), "train_corpus_sha256": sha_bytes(train_bytes),
              "config": frozen, "config_sha256": sha_json(frozen)}
    return {"pooled": {**common, "adapter_id": "study-pooled", "role": "pooled", "domains": list(DOMAINS)},
            **{domain: {**common, "adapter_id": f"study-{domain}", "role": "specialist", "domains": [domain]}
               for domain in DOMAINS}}


def derive_rows(rows: list[dict], role: str, domain: str | None = None) -> list[str]:
    selected = rows if role == "pooled" else [row for row in rows if row.get("domain") == domain]
    if not selected:
        raise ValueError(f"no frozen training rows for {role}:{domain or 'all'}")
    families = [row.get("source_family") for row in selected]
    if any(not isinstance(family, str) or not family for family in families):
        raise ValueError("every training row must carry source-family provenance")
    return [row["prompt"] + "\nAnswer: " + row["reference"] for row in selected]


def train_one(spec: dict, texts: list[str], destination: Path) -> dict:
    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if destination.exists():
        raise FileExistsError(f"refusing to overwrite adapter: {destination}")
    torch.use_deterministic_algorithms(True)
    seed = spec["config"]["seed"]
    random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, revision=BASE_REVISION, local_files_only=True,
                                                 torch_dtype=torch.float16).to("cuda")
    model.config.use_cache = False
    cfg = spec["config"]["adapter"]
    model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, r=cfg["r"], lora_alpha=cfg["alpha"],
                                             lora_dropout=cfg["dropout"], target_modules=cfg["target_modules"], bias="none"))
    model.train()
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=cfg["learning_rate"])
    epochs, max_length = cfg["epochs"], cfg["max_length"]
    losses = []
    for _epoch in range(epochs):
        for text in texts:
            encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
            ids = encoded["input_ids"].to("cuda")
            loss = model(input_ids=ids, attention_mask=torch.ones_like(ids), labels=ids).loss
            if not torch.isfinite(loss):
                raise ValueError("non-finite training loss")
            loss.backward(); optimizer.step(); optimizer.zero_grad(set_to_none=True)
            losses.append(float(loss.detach().cpu()))
    destination.mkdir(parents=True)
    model.save_pretrained(destination, safe_serialization=True)
    receipt = {**spec, "status": "complete", "train_rows": len(texts), "epochs": epochs,
               "mean_loss": sum(losses) / len(losses), "adapter_tree_digest": adapter_tree_digest(destination)}
    (destination / PROVENANCE_FILE).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def run_all() -> int:
    registration_bytes = REGISTRATION.read_bytes()
    registration = json.loads(registration_bytes)
    manifest_bytes = MANIFEST.read_bytes()
    manifest, rows = load_corpus(MANIFEST)
    validate_corpus(manifest, rows)
    specs = training_specs(registration, manifest_bytes, (ROOT / "corpus/study-v1/train.jsonl").read_bytes())
    results = []
    for key, spec in specs.items():
        texts = derive_rows(rows["train"], spec["role"], key if spec["role"] == "specialist" else None)
        results.append(train_one(spec, texts, ADAPTERS / spec["adapter_id"]))
    receipt = {"schema": "tiny-fleet.study-adapter-training/v1", "study_id": registration["study_id"],
               "registration_sha256": sha_bytes(registration_bytes), "manifest_sha256": sha_bytes(manifest_bytes),
               "adapters": results}
    (ROOT / "runs/fleet-study-v1/adapter-training.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "complete", "adapters": len(results), "receipt": "runs/fleet-study-v1/adapter-training.json"}))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", required=True)
    args = parser.parse_args()
    raise SystemExit(run_all())
