#!/usr/bin/env python3
"""Prospectively bound, local-only CPU terminology instrumentation experiment.

Prepare never loads model weights. Run is single-use, supervised, and never resumes.
Historical adapter receipts are checked as historical evidence, not amended runs.
"""
from __future__ import annotations

import argparse
import collections
import ctypes
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import resource
import signal
import subprocess
import sys
import tarfile
import time
import traceback

from train_drift_adapters import (BASE_MODEL, BASE_REVISION, tokenized_chunks,
                                  select_chunks, read_jsonl, evaluate_loss)
from drift_generate import adapter_tree_digest

ROOT = Path(__file__).resolve().parent.parent
HISTORICAL = Path("runs/drift-generative-v2")
STAGES = ["baseline", "repeat4", "repeat19"]
SCHEMA = "tiny-fleet.model-terminology-drift/v1"
TAPES = ("likelihood.jsonl", "generations.jsonl", "training.jsonl", "failures.jsonl")
GLOBAL_LOCK = Path("/tmp/tiny-fleet-terminology-model.lock")
PROMPTS = [
    {"prompt_id": "identifiers", "text": "List salient repository identifiers and concept names you learned. Give a concise list; do not invent names."},
    {"prompt_id": "interfaces", "text": "Describe the key concepts and interfaces you learned, using their characteristic terminology. Be concise."},
]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def json_sha256(value):
    return sha256(canonical(value))


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    pending = path.with_name(f".{path.name}.{os.getpid()}.pending")
    with pending.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    # Link is atomic and exclusive; a killed worker cannot leave a half receipt.
    os.link(pending, path)
    pending.unlink()


def append_row(path, row):
    path = Path(path)
    separator = ""
    if path.exists() and path.stat().st_size:
        with path.open("rb") as existing:
            existing.seek(-1, os.SEEK_END)
            if existing.read(1) != b"\n":
                separator = "\n"  # Retain, but separate, a deadline-interrupted row.
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(separator + json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def progress(message):
    print(message, flush=True)


def offline():
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      HF_DATASETS_OFFLINE="1", CUDA_VISIBLE_DEVICES="",
                      TOKENIZERS_PARALLELISM="false", OMP_NUM_THREADS="4",
                      MKL_NUM_THREADS="4")


def tokenizer_binding(tokenizer):
    return {"backend_sha256": sha256(tokenizer.backend_tokenizer.to_str().encode()),
            "vocab_size": len(tokenizer),
            "special_tokens_sha256": json_sha256(tokenizer.special_tokens_map),
            "chat_template_sha256": sha256((tokenizer.chat_template or "").encode())}


def cached_inputs():
    from huggingface_hub import snapshot_download
    directory = Path(snapshot_download(BASE_MODEL, revision=BASE_REVISION, local_files_only=True))
    names = ["config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
             "generation_config.json"]
    files = {name: file_sha256(directory / name) for name in names if (directory / name).is_file()}
    weights = sorted(directory.glob("*.safetensors"))
    if not weights:
        raise ValueError("pinned local cache has no safetensors model weights")
    for path in weights:
        files[path.name] = file_sha256(path)
    for path in directory.glob("*.safetensors.index.json"):
        files[path.name] = file_sha256(path)
    return {"path": str(directory), "files": files}


def load_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION,
                                         local_files_only=True, trust_remote_code=False)


def chat_input(tokenizer, text):
    return tokenizer.apply_chat_template([{ "role": "user", "content": text}],
                                         tokenize=True, add_generation_prompt=True)


def likelihood_input(model_case, target_case, arm, control):
    ids = list(target_case["heldout"]["input_ids"])
    if control == "token_shuffle":
        targets = ids[1:]
        random.Random(17).shuffle(targets)
        ids[1:] = targets
    elif control != "original":
        raise ValueError("unknown source control")
    return {"input_ids": ids,
            "prefix_ids": list(model_case["conditioning_ids"]) if arm == "prompt-only" else []}


def expected_likelihood_rows(protocol, cases):
    result = []
    conditions = cases["conditions"]
    for target in conditions:
        peers = [c for c in conditions if c["repo"] == target["repo"]]
        for control in ("original", "token_shuffle"):
            for arm in ("lora", "base", "prompt-only", "unigram"):
                models = [None] if arm == "base" else peers
                stages = protocol["stages"] if arm == "lora" else ["shared"]
                for model_case in models:
                    for stage in stages:
                        spec = likelihood_input(model_case, target, arm, control)
                        result.append({"repo": target["repo"], "stage": stage,
                                       "model_snapshot": model_case["snapshot"] if model_case else "shared",
                                       "target_snapshot": target["snapshot"], "control": control, "arm": arm,
                                       "source_path": target["heldout"]["source_path"],
                                       "input_sha256": json_sha256(spec),
                                       "target_tokens": len(spec["input_ids"]) - 1})
    return result


def expected_generation_rows(protocol, cases):
    result = []
    groups = [("shared", "shared", "shared", "base", cases["base_generation_inputs"])]
    for case in cases["conditions"]:
        groups.append((case["repo"], case["snapshot"], "shared", "prompt-only", case["generation_inputs"]))
        for stage in protocol["stages"]:
            groups.append((case["repo"], case["snapshot"], stage, "lora", cases["base_generation_inputs"]))
    for repo, snapshot, stage, arm, inputs in groups:
        for item in inputs:
            for decode_id in ("greedy", "sample17", "sample29", "sample43"):
                result.append({"repo": repo, "snapshot": snapshot, "stage": stage, "arm": arm,
                               "prompt_id": item["prompt_id"], "decode_id": decode_id,
                               "input_sha256": json_sha256(item["input_ids"])})
    identity = protocol["identity"]
    original = next(row for row in result if all(row.get(k) == v for k, v in identity.items()))
    result.append({**original, "decode_id": "identity"})
    return result


def expected_training_rows(protocol, cases):
    result = []
    for case in cases["conditions"]:
        key = {"repo": case["repo"], "snapshot": case["snapshot"]}
        for stage, number in zip(protocol["stages"], (0, 4, 19)):
            result.append({**key, "stage": stage, "pass": number, "kind": "diagnostic"})
        for number in range(1, 20):
            result.append({**key, "stage": "repeat4" if number <= 4 else "repeat19",
                           "pass": number, "kind": "pass"})
    return result


def prepare(run_dir):
    run_dir.mkdir(parents=True, exist_ok=False)
    offline()
    try:
        files = {}
        def bind(relative, expected=None):
            relative = Path(relative).as_posix()
            digest = file_sha256(ROOT / relative)
            if expected is not None and digest != expected:
                raise ValueError(f"frozen historical hash mismatch: {relative}")
            files[relative] = digest
            return json.loads((ROOT / relative).read_text()) if relative.endswith(".json") else None

        plan_path = HISTORICAL / "training-corpora/training-plan.json"
        registration = bind(HISTORICAL / "adapter-registration.json")
        plan = bind(plan_path, registration["training_plan_sha256"])
        ledger_path = Path(plan["heldout_excerpt_ledger"]["path"])
        ledger = bind(ledger_path, plan["heldout_excerpt_ledger"]["sha256"])
        if plan["base_model"] != {"id": BASE_MODEL, "revision": BASE_REVISION} or registration["base_model"] != plan["base_model"]:
            raise ValueError("historical base model mismatch")
        for key in ("source_sample_manifest", "scorer_registration"):
            bind(plan[key]["path"], plan[key]["sha256"])
        sample = json.loads((ROOT / plan["source_sample_manifest"]["path"]).read_text())
        expected_pairs = {(repo, snapshot) for repo in ("flask", "requests", "pydantic") for snapshot in ("old", "new")}
        if {(c["repo"], c["snapshot"]) for c in plan["corpora"]} != expected_pairs or len(plan["corpora"]) != 6:
            raise ValueError("expected exactly six source snapshots")
        if {(c["repo"], c["snapshot"]) for c in registration["adapters"]} != expected_pairs or len(registration["adapters"]) != 6:
            raise ValueError("expected exactly six historical adapters")
        tokenizer = load_tokenizer()
        cache = cached_inputs()
        conditions, frozen_cases, source_records = [], [], {}
        for corpus in sorted(plan["corpora"], key=lambda c: (c["repo"], c["snapshot"])):
            repo, snapshot = corpus["repo"], corpus["snapshot"]
            progress(f"prepare {repo}/{snapshot}: checking receipt, source and adapter")
            manifest_path = HISTORICAL / f"training-corpora/{repo}-{snapshot}/manifest.json"
            manifest = bind(manifest_path, corpus["manifest_sha256"])
            if manifest != {key: value for key, value in corpus.items() if key != "manifest_sha256"}:
                raise ValueError("historical plan/manifest disagreement")
            adapter = next(a for a in registration["adapters"] if (a["repo"], a["snapshot"]) == (repo, snapshot))
            receipt_path = HISTORICAL / f"training-runs/{repo}-{snapshot}/run.json"
            receipt = bind(receipt_path, adapter["training_run_sha256"])
            for key, wanted in (("status", "complete"), ("repo", repo), ("snapshot", snapshot),
                                ("source_commit", corpus["source_commit"]), ("seed", 17),
                                ("training_plan_sha256", files[plan_path.as_posix()]),
                                ("corpus_manifest_sha256", corpus["manifest_sha256"]),
                                ("train_corpus_sha256", corpus["train"]["sha256"]),
                                ("validation_corpus_sha256", corpus["validation"]["sha256"]),
                                ("base_model", plan["base_model"]), ("hyperparameters", {k: plan["training"][k] for k in receipt["hyperparameters"]})):
                if receipt.get(key) != wanted:
                    raise ValueError(f"historical receipt binding mismatch: {repo}/{snapshot}/{key}")
            if receipt["hyperparameters"]["epochs"] != 1 or receipt["token_budget"]["train_selected_tokens"] != 16384:
                raise ValueError("historical adapter is not the registered one-pass 16k adaptation")
            adapter_path = HISTORICAL / adapter["adapter_path"]
            digest = adapter_tree_digest(ROOT / adapter_path)
            if digest != adapter["adapter_digest"] or digest != receipt["adapter_digest"]:
                raise ValueError("historical adapter tree mismatch")
            actual_adapter_files = {p.relative_to(ROOT / adapter_path).as_posix(): file_sha256(p)
                                    for p in (ROOT / adapter_path).rglob("*") if p.is_file()}
            if actual_adapter_files != receipt["adapter_files"]:
                raise ValueError("historical adapter files mismatch")
            for name, digest in actual_adapter_files.items():
                bind(adapter_path / name, digest)
            config = json.loads((ROOT / adapter_path / "adapter_config.json").read_text())
            if config["base_model_name_or_path"] != BASE_MODEL:
                raise ValueError("adapter base tokenizer/model binding mismatch")
            for split in ("train", "validation"):
                bind(corpus[split]["path"], corpus[split]["sha256"])
            inventory = corpus["inventory"]
            bind(inventory["path"], inventory["sha256"])
            bind(corpus["license"]["saved_path"], corpus["license"]["saved_sha256"])
            included = {r["path"]: r["sha256"] for r in read_jsonl(ROOT / inventory["path"]) if r["status"] == "included"}
            train, validation = read_jsonl(ROOT / corpus["train"]["path"]), read_jsonl(ROOT / corpus["validation"]["path"])
            source_records[(repo, snapshot)] = train + validation
            for record in train + validation:
                prefix = f"### {record['source_path']}\n"
                if not record["text"].startswith(prefix) or sha256(record["text"][len(prefix):].encode()) != record["source_file_sha256"]:
                    raise ValueError("training source content/hash mismatch")
                if included.get(record["source_path"]) != record["source_file_sha256"]:
                    raise ValueError("source inventory mismatch")
            heldout_matches = [h for h in ledger["prompts"] if (h["repo"], h["snapshot"]) == (repo, snapshot)]
            if len(heldout_matches) != 1:
                raise ValueError("expected one prospectively selected heldout module per snapshot")
            heldout = heldout_matches[0]
            archive_path = Path("runs/behavioral-preflight-v3-python311/source-archives") / f"{repo}-{snapshot}.tar"
            sample_repo = next(r for r in sample["repositories"] if r["repo_id"] == repo)
            sample_snapshot = next(s for s in sample_repo["snapshots"] if s["label"] == snapshot)
            if sample_snapshot["commit"] != corpus["source_commit"]:
                raise ValueError("source archive commit binding mismatch")
            bind(archive_path, sample_snapshot["archive"]["sha256"])
            with tarfile.open(ROOT / archive_path, "r:*") as archive:
                comment = archive.pax_headers.get("comment")
                if comment is not None and comment != corpus["source_commit"]:
                    raise ValueError("source archive commit comment mismatch")
                members = [m for m in archive.getmembers() if m.isfile() and
                           (m.name == heldout["source_path"] or m.name.endswith("/" + heldout["source_path"]))]
                if len(members) != 1:
                    raise ValueError("heldout full source member must be unique and regular")
                source_member = members[0].name
                with archive.extractfile(members[0]) as stream:
                    full_source = stream.read()
            if sha256(full_source) != heldout["source_file_sha256"]:
                raise ValueError("heldout full-module source hash mismatch")
            full_source_text = full_source.decode("utf-8")
            if "\n".join(full_source_text.splitlines()[:80]) != heldout["snapshot_excerpt"]:
                raise ValueError("heldout excerpt differs from canonical first80 full-source lines")
            excerpt_path = ledger_path.parent / heldout["excerpt_path"]
            bind(excerpt_path, heldout["snapshot_excerpt_sha256"])
            if (ROOT / excerpt_path).read_text() != heldout["snapshot_excerpt"] or heldout["source_commit"] != corpus["source_commit"]:
                raise ValueError("heldout source binding mismatch")
            if heldout["source_path"] != corpus["selection"]["heldout_source_excluded"]:
                raise ValueError("heldout exclusion selection mismatch")
            license_entry = next(r for r in ledger["licenses"] if (r["repo"], r["snapshot"]) == (repo, snapshot))
            bind(ledger_path.parent / license_entry["saved_path"], license_entry["source_sha256"])
            train_chunks = select_chunks(repo, snapshot, tokenized_chunks(train, tokenizer, 256), token_budget=4096, max_length=256)
            validation_chunks = select_chunks(repo, snapshot, tokenized_chunks(validation, tokenizer, 256), token_budget=4096, max_length=256)
            selected = [token for chunk in train_chunks for token in chunk["input_ids"]]
            if len(selected) != 4096:
                raise ValueError("insufficient training tokens for the fixed 4096-token subset")
            context_ids = selected[:512]
            context_text = tokenizer.decode(context_ids, skip_special_tokens=False)
            context = "Training source context:\n" + context_text + "\n\n"
            generation_inputs = [{"prompt_id": p["prompt_id"], "text": context + p["text"],
                                  "input_ids": chat_input(tokenizer, context + p["text"])} for p in PROMPTS]
            ids = tokenizer(heldout["snapshot_excerpt"], add_special_tokens=True, truncation=False, verbose=False)["input_ids"]
            if len(ids) < 2:
                raise ValueError("heldout excerpt has no causal target tokens")
            condition = {"repo": repo, "snapshot": snapshot, "source_commit": corpus["source_commit"],
                         "adapter_path": adapter_path.as_posix(), "adapter_digest": adapter["adapter_digest"],
                         "receipt_path": receipt_path.as_posix(), "manifest_path": manifest_path.as_posix(),
                         "source_archive_path": archive_path.as_posix(), "source_archive_member": source_member,
                         "train_path": corpus["train"]["path"], "validation_path": corpus["validation"]["path"],
                         "heldout_path": excerpt_path.as_posix(), "source_path": heldout["source_path"],
                         "source_file_sha256": heldout["source_file_sha256"]}
            conditions.append(condition)
            frozen_cases.append({"repo": repo, "snapshot": snapshot, "train_chunks": train_chunks,
                                 "validation_chunks": validation_chunks,
                                 "heldout": {"input_ids": ids, "text": heldout["snapshot_excerpt"], "source_path": heldout["source_path"],
                                             "full_source_text": full_source_text, "full_source_sha256": heldout["source_file_sha256"]},
                                 "unigram_counts": dict(collections.Counter(selected)),
                                 "context_input_ids": context_ids, "context_text": context_text,
                                 "context_sha256": json_sha256(context_ids),
                                 "conditioning_ids": chat_input(tokenizer, context + "Continue the source text."),
                                 "generation_inputs": generation_inputs})
        for case in frozen_cases:
            paths = {case["heldout"]["source_path"]}
            # Package root moved for Requests; exclude the corresponding module in BOTH snapshots.
            paths |= {c["heldout"]["source_path"] for c in frozen_cases if c["repo"] == case["repo"]}
            for snapshot in ("old", "new"):
                if any(r["source_path"] in paths for r in source_records[(case["repo"], snapshot)]):
                    raise ValueError("heldout source leaks into old/new train or validation corpus")
        for name in ("model_terminology_drift.py", "analyze_model_terminology_drift.py", "train_drift_adapters.py", "build_drift_train_corpus.py", "drift_generate.py", "drift_lexical.py"):
            bind(Path("scripts") / name)
        cases = {"schema": SCHEMA + "/cases", "conditions": frozen_cases,
                 "base_generation_inputs": [{"prompt_id": p["prompt_id"], "text": p["text"],
                                             "input_ids": chat_input(tokenizer, p["text"])} for p in PROMPTS]}
        write_json(run_dir / "cases.json", cases)
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
        pair_controls = []
        for repo in ("flask", "pydantic", "requests"):
            old = next(c for c in frozen_cases if (c["repo"], c["snapshot"]) == (repo, "old"))
            new = next(c for c in frozen_cases if (c["repo"], c["snapshot"]) == (repo, "new"))
            unchanged = old["heldout"]["text"] == new["heldout"]["text"]
            pair_controls.append({"repo": repo, "heldout_byte_identical": unchanged,
                                  "role": "unchanged-heldout-source negative control" if unchanged else "changed heldout source pair"})
        if [p["repo"] for p in pair_controls if p["heldout_byte_identical"]] != ["requests"]:
            raise ValueError("heldout identity status changed from prospective source inspection")
        protocol = {"schema": SCHEMA + "/protocol", "source_revision": revision, "input_root": str(ROOT),
                    "files": files, "base_model": plan["base_model"], "cached_model": cache,
                    "tokenizer": tokenizer_binding(tokenizer), "cases_sha256": file_sha256(run_dir / "cases.json"),
                    "stages": STAGES, "conditions": conditions, "prompts": PROMPTS,
                    "source_pair_controls": pair_controls,
                    "generation": {"seeds": [17, 29, 43], "max_new_tokens": 96, "temperature": 0.7, "top_p": 0.9},
                    "identity": {"repo": "flask", "snapshot": "old", "stage": "baseline", "arm": "lora", "prompt_id": "identifiers", "decode_id": "greedy"},
                    "training": {"seed": 17, "additional_passes": 19, "checkpoint_passes": [4, 19],
                                 "train_token_budget": 4096, "validation_token_budget": 4096,
                                 "max_sequence_length": 256, "batch_size": 1, "gradient_accumulation": 4,
                                 "pass_seed_schedule": "seed17 + additional_pass - 1; reset dropout/order independently of probes",
                                 "learning_rate": 0.0002, "weight_decay": 0.01, "max_gradient_norm": 1.0,
                                 "optimizer": "fresh AdamW; historical optimizer unavailable"},
                    "budget": {"model_wall_seconds": 21600, "minimum_available_memory_gib": 6},
                    "runtime": {"device": "cpu", "dtype": "float32", "threads": 4, "global_lock": str(GLOBAL_LOCK), "local_files_only": True,
                                "packages": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "tokenizers", "safetensors", "numpy")}},
                    "controls": {"shuffle_seed": 17, "unigram_alpha": 1.0, "prompt_context_tokens": 512,
                                 "prompt_only": "base model conditioned on first512 selected training tokens; no heldout context",
                                 "shared_reuse": "base/prompt-only/unigram evaluated once, reused explicitly at all LoRA stages",
                                 "likelihood_context_tokens": 2048, "likelihood_target_block_tokens": 1024,
                                 "likelihood_window": "2048-token rolling causal context; every target token once, first source token excluded"},
                    "limitations": ["unknown pretraining contamination", "one training seed", "three correlated repository source pairs",
                                    "repeated4k-subset fitting after historical16k adaptation, NOT5/20 full-corpus epochs",
                                    "Requests heldout source unchanged; only Flask/Pydantic are changed-source pairs; sign-flip actual attainable tail may be1/4",
                                    "source discrimination is not semantic truth or pure terminology causality"]}
        write_json(run_dir / "protocol.json", protocol)
        write_json(run_dir / "prepared.json", {"schema": SCHEMA + "/prepared",
                                              "protocol_sha256": file_sha256(run_dir / "protocol.json"),
                                              "cases_sha256": file_sha256(run_dir / "cases.json")})
        progress(f"prepared {run_dir}: protocol={file_sha256(run_dir / 'protocol.json')}")
    except BaseException as exc:
        write_json(run_dir / "prepare_failure.json", {"status": "failed", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()})
        raise


def validate_prepared(run_dir):
    protocol = json.loads((run_dir / "protocol.json").read_text())
    cases = json.loads((run_dir / "cases.json").read_text())
    prepared = json.loads((run_dir / "prepared.json").read_text())
    if prepared["protocol_sha256"] != file_sha256(run_dir / "protocol.json") or prepared["cases_sha256"] != file_sha256(run_dir / "cases.json"):
        raise ValueError("prospectively prepared protocol/cases changed")
    if protocol["schema"] != SCHEMA + "/protocol" or cases["schema"] != SCHEMA + "/cases":
        raise ValueError("unsupported protocol/cases schema")
    if file_sha256(run_dir / "cases.json") != protocol["cases_sha256"]:
        raise ValueError("prepared cases changed")
    input_root = Path(protocol["input_root"])
    for name, digest in protocol["files"].items():
        if file_sha256(input_root / name) != digest:
            raise ValueError(f"prepared input changed: {name}")
    for condition in protocol["conditions"]:
        if adapter_tree_digest(input_root / condition["adapter_path"]) != condition["adapter_digest"]:
            raise ValueError("prepared adapter tree changed")
    for name, digest in protocol["cached_model"]["files"].items():
        if file_sha256(Path(protocol["cached_model"]["path"]) / name) != digest:
            raise ValueError(f"cached base model changed: {name}")
    return protocol, cases


def memory_available_gib():
    mem = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        mem[key] = int(value.strip().split()[0]) * 1024
    available = mem["MemAvailable"]
    # Respect local cgroup constraints as well as host RAM; no eviction or swap assumptions.
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            group = Path("/sys/fs/cgroup") / line.split("::", 1)[1].lstrip("/")
            for parent in [group, *group.parents]:
                if not str(parent).startswith("/sys/fs/cgroup"):
                    break
                maximum, current = parent / "memory.max", parent / "memory.current"
                if maximum.is_file() and current.is_file():
                    limit = maximum.read_text().strip()
                    if limit != "max":
                        available = min(available, int(limit) - int(current.read_text()))
    return max(available, 0) / 1024 ** 3


def runtime():
    offline()
    import torch
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(17)
    random.seed(17)
    return torch


def load_base(torch):
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, revision=BASE_REVISION,
                                                local_files_only=True, trust_remote_code=False,
                                                dtype=torch.float32, attn_implementation="eager")
    model.to("cpu")
    model.config.use_cache = False
    return model

def diagnostic_loss(model, chunks, torch):
    value = evaluate_loss(model, chunks, "cpu", torch)
    return {**value, "nll_sum": value["mean_token_nll"] * value["target_tokens"]}



def cross_score(model, spec, torch):
    """Bounded rolling causal NLL, scoring positions1..end exactly once.

    Each forward scores up to1024 new targets in a2048-token causal window.
    Training-context prefixes never contribute target tokens.
    """
    target = spec["input_ids"]
    prefix = spec["prefix_ids"]
    combined = prefix + target
    offset = len(prefix)
    nll, count = 0.0, 0
    model.eval()
    if int(model.config.max_position_embeddings) < 2048:
        raise ValueError("base model cannot supply the prospectively bound2048-token scoring context")
    with torch.inference_mode():
        for start in range(1, len(target), 1024):
            end = min(start + 1024, len(target))
            absolute_start, absolute_end = offset + start, offset + end
            window_start = max(0, absolute_end - 2048)
            ids = torch.tensor(combined[window_start:absolute_end], dtype=torch.long).unsqueeze(0)
            labels = ids.clone()
            labels[:, :absolute_start - window_start] = -100
            output = model(input_ids=ids, attention_mask=torch.ones_like(ids), labels=labels)
            targets = end - start
            loss = float(output.loss)
            if not math.isfinite(loss):
                raise ValueError("non-finite cross likelihood")
            nll += loss * targets
            count += targets
    if count != len(target) - 1 or not math.isfinite(nll):
        raise ValueError("invalid causal target denominator")
    return {"nll_sum": nll, "target_tokens": count, "mean_token_nll": nll / count}


def unigram_score(case, spec, vocab_size, alpha):
    counts = case["unigram_counts"]
    denominator = sum(counts.values()) + alpha * vocab_size
    nll = math.fsum(-math.log((counts.get(str(token), counts.get(token, 0)) + alpha) / denominator)
              for token in spec["input_ids"][1:])
    count = len(spec["input_ids"]) - 1
    return {"nll_sum": nll, "target_tokens": count, "mean_token_nll": nll / count}


def generate(model, tokenizer, item, decode_id, settings, torch):
    model.eval()
    seed = int(decode_id.removeprefix("sample")) if decode_id.startswith("sample") else 17
    torch.manual_seed(seed)
    random.seed(seed)
    ids = torch.tensor(item["input_ids"], dtype=torch.long).unsqueeze(0)
    options = {"max_new_tokens": settings["max_new_tokens"], "do_sample": decode_id.startswith("sample"),
               "pad_token_id": tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id,
               "eos_token_id": tokenizer.eos_token_id, "use_cache": True}
    if options["do_sample"]:
        options.update(temperature=settings["temperature"], top_p=settings["top_p"])
    with torch.inference_mode():
        result = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), **options)
    generated = result[0, ids.shape[1]:]
    output = tokenizer.decode(generated, skip_special_tokens=True)
    return {"output": output, "output_sha256": sha256(output.encode()),
            "generated_tokens": generated.numel(), "cap_hit": generated.numel() >= settings["max_new_tokens"],
            "empty_output": not bool(output.strip())}


def train_pass(model, chunks, optimizer, number, settings, torch):
    model.train()
    torch.manual_seed(settings["seed"] + number - 1)
    order = list(chunks)
    random.Random(settings["seed"] + number - 1).shuffle(order)
    accumulation = settings["gradient_accumulation"]
    optimizer.zero_grad(set_to_none=True)
    nll, targets, steps = 0.0, 0, 0
    parameters = [p for p in model.parameters() if p.requires_grad]
    for index, row in enumerate(order):
        ids = torch.tensor(row["input_ids"], dtype=torch.long).unsqueeze(0)
        result = model(input_ids=ids, attention_mask=torch.ones_like(ids), labels=ids)
        loss = result.loss
        if not torch.isfinite(loss):
            raise ValueError(f"non-finite training loss at pass{number} chunk{index}")
        pending = min(accumulation, len(order) - (index // accumulation) * accumulation)
        (loss / pending).backward()
        count = ids.shape[1] - 1
        nll += float(loss.detach()) * count
        targets += count
        if (index + 1) % accumulation == 0 or index + 1 == len(order):
            norm = torch.nn.utils.clip_grad_norm_(parameters, settings["max_gradient_norm"], error_if_nonfinite=True)
            if not torch.isfinite(norm):
                raise ValueError("non-finite LoRA gradients")
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            steps += 1
            progress(f"pass{number}: chunks{index + 1}/{len(order)} loss={nll / targets:.6f}")
    return {"train": {"nll_sum": nll, "target_tokens": targets, "mean_token_nll": nll / targets},
            "optimizer_steps": steps, "selected_tokens": sum(len(r["input_ids"]) for r in chunks)}


def row_key(row, tape):
    keys = {"likelihood.jsonl": ("repo", "stage", "model_snapshot", "target_snapshot", "control", "arm"),
            "generations.jsonl": ("repo", "snapshot", "stage", "arm", "prompt_id", "decode_id"),
            "training.jsonl": ("repo", "snapshot", "stage", "pass", "kind")}
    return tuple(row[k] for k in keys[tape])


def retained_rows(path):
    """Read finalization evidence, retaining malformed deadline rows as failures."""
    rows, invalid_lines = [], []
    if not Path(path).exists():
        return rows, invalid_lines
    with Path(path).open("rb") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("tape row is not an object")
                rows.append(value)
            except (ValueError, UnicodeDecodeError):
                invalid_lines.append(number)
    return rows, invalid_lines


def finish_receipt(run_dir, protocol, cases, started, error=None, child_rss=None):
    binding = file_sha256(run_dir / "protocol.json")
    failures, interrupted_failure_lines = retained_rows(run_dir / "failures.jsonl")
    if interrupted_failure_lines:
        error = (error or "execution interrupted") + f"; malformed retained failure lines{interrupted_failure_lines}"
    if error:
        failure = {"status": "error", "error": error, "protocol_sha256": binding}
        append_row(run_dir / "failures.jsonl", failure)
        failures.append(failure)
    expected = {"likelihood.jsonl": expected_likelihood_rows(protocol, cases),
                "generations.jsonl": expected_generation_rows(protocol, cases),
                "training.jsonl": expected_training_rows(protocol, cases)}
    counts = {}
    for tape in TAPES:
        path = run_dir / tape
        if not path.exists():
            path.touch(exist_ok=False)
        rows, invalid_lines = retained_rows(path)
        if invalid_lines and tape != "failures.jsonl":
            failure = {"status": "error", "error": f"malformed retained tape lines{invalid_lines}",
                       "tape": tape, "protocol_sha256": binding}
            append_row(run_dir / "failures.jsonl", failure)
            failures.append(failure)
        if tape in expected:
            present = {row_key(r, tape) for r in rows}
            for spec in expected[tape]:
                if row_key(spec, tape) not in present:
                    row = {**spec, "status": "error", "error": error or "execution stopped before this cell",
                           "elapsed_s": 0.0, "protocol_sha256": binding}
                    append_row(path, row)
                    rows.append(row)
        counts[tape] = {"rows": len(rows), "ok": sum(r.get("status") == "ok" for r in rows),
                        "error": sum(r.get("status") == "error" for r in rows),
                        "invalid_json_lines": invalid_lines}
    checkpoints = {}
    checkpoint_root = run_dir / "checkpoints"
    if checkpoint_root.exists():
        for condition_dir in sorted(checkpoint_root.iterdir()):
            for stage_dir in sorted(condition_dir.iterdir()):
                if stage_dir.is_dir() and any(p.is_file() for p in stage_dir.rglob("*")):
                    checkpoints[f"{condition_dir.name}/{stage_dir.name}"] = adapter_tree_digest(stage_dir)
    failed = bool(error or failures or any(v["error"] for v in counts.values()))
    receipt = {"schema": SCHEMA + "/receipt", "status": "failed" if failed else "complete",
               "protocol_sha256": binding, "cases_sha256": file_sha256(run_dir / "cases.json"),
               "tape_sha256": {name: file_sha256(run_dir / name) for name in TAPES},
               "counts": counts, "total_model_wall_s": time.monotonic() - started,
               "peak_rss_gib": child_rss if child_rss is not None else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2,
               "failures": failures, "checkpoints": checkpoints}
    write_json(run_dir / "receipt.json", receipt)
    return receipt


def execute(run_dir, protocol, cases):
    started = time.monotonic()
    binding = file_sha256(run_dir / "protocol.json")
    error = None
    try:
        torch = runtime()
        tokenizer = load_tokenizer()
        if tokenizer_binding(tokenizer) != protocol["tokenizer"]:
            raise ValueError("tokenizer runtime differs from prospective binding")
        import peft
        import transformers
        if {name: importlib.metadata.version(name) for name in protocol["runtime"]["packages"]} != protocol["runtime"]["packages"]:
            raise ValueError("runtime packages changed after prospective preparation")
        write_json(run_dir / "runtime.json", {"python": sys.version, "torch": torch.__version__,
                                              "peft": peft.__version__, "transformers": transformers.__version__,
                                              "numpy": importlib.metadata.version("numpy"),
                                              "device": "cpu", "dtype": "float32", "threads": torch.get_num_threads()})
        lookup = {(c["repo"], c["snapshot"]): c for c in cases["conditions"]}
        likelihood_rows = expected_likelihood_rows(protocol, cases)
        generation_rows = expected_generation_rows(protocol, cases)
        def record(tape, spec, callback):
            before = time.monotonic()
            progress(f"{tape}: {row_key(spec, tape)}")
            try:
                row = {**spec, **callback(), "status": "ok"}
            except Exception as exc:
                row = {**spec, "status": "error", "error_type": type(exc).__name__, "error": str(exc)}
                append_row(run_dir / "failures.jsonl", {**row, "tape": tape, "protocol_sha256": binding})
            row.update(elapsed_s=time.monotonic() - before, protocol_sha256=binding)
            append_row(run_dir / tape, row)

        def probe(model, arm, stage, repo=None, snapshot=None):
            for spec in likelihood_rows:
                if spec["arm"] != arm or spec["stage"] != stage:
                    continue
                if repo is not None and (spec["repo"], spec["model_snapshot"]) != (repo, snapshot):
                    continue
                target = lookup[(spec["repo"], spec["target_snapshot"])]
                condition = lookup.get((spec["repo"], spec["model_snapshot"]))
                inputs = likelihood_input(condition, target, arm, spec["control"])
                if arm == "unigram":
                    record("likelihood.jsonl", spec, lambda: unigram_score(condition, inputs, protocol["tokenizer"]["vocab_size"], protocol["controls"]["unigram_alpha"]))
                else:
                    record("likelihood.jsonl", spec, lambda: cross_score(model, inputs, torch))
            for spec in generation_rows:
                if spec["arm"] != arm or spec["stage"] != stage:
                    continue
                if repo is not None and (spec["repo"], spec["snapshot"]) != (repo, snapshot):
                    continue
                group = lookup[(spec["repo"], spec["snapshot"])]["generation_inputs"] if arm == "prompt-only" else cases["base_generation_inputs"]
                item = next(p for p in group if p["prompt_id"] == spec["prompt_id"])
                record("generations.jsonl", spec, lambda: generate(model, tokenizer, item, spec["decode_id"], protocol["generation"], torch))

        for case in cases["conditions"]:
            probe(None, "unigram", "shared", case["repo"], case["snapshot"])
        progress("loading cached fp32 CPU base for shared controls")
        base = load_base(torch)
        probe(base, "base", "shared")
        for case in cases["conditions"]:
            probe(base, "prompt-only", "shared", case["repo"], case["snapshot"])
        del base
        import gc
        gc.collect()
        from peft import PeftModel
        for condition in protocol["conditions"]:
            repo, snapshot = condition["repo"], condition["snapshot"]
            case = lookup[(repo, snapshot)]
            torch.manual_seed(17)
            random.seed(17)
            progress(f"loading original adapter {repo}/{snapshot} for fresh-optimizer continuation")
            model = PeftModel.from_pretrained(load_base(torch), str(Path(protocol["input_root"]) / condition["adapter_path"]),
                                             is_trainable=True, local_files_only=True)
            model.config.use_cache = False
            params = [p for p in model.parameters() if p.requires_grad]
            if not params or any(p.device.type != "cpu" or p.dtype != torch.float32 for p in params):
                raise ValueError("continuation requires real trainable CPU fp32 LoRA parameters")
            optimizer = torch.optim.AdamW(params, lr=protocol["training"]["learning_rate"], weight_decay=protocol["training"]["weight_decay"])
            def diagnostics(stage, number):
                spec = {"repo": repo, "snapshot": snapshot, "stage": stage, "pass": number, "kind": "diagnostic"}
                record("training.jsonl", spec, lambda: {"train": diagnostic_loss(model, case["train_chunks"], torch),
                                                        "validation": diagnostic_loss(model, case["validation_chunks"], torch)})
                probe(model, "lora", stage, repo, snapshot)
            diagnostics("baseline", 0)
            for number in range(1, 20):
                before = time.monotonic()
                values = train_pass(model, case["train_chunks"], optimizer, number, protocol["training"], torch)
                append_row(run_dir / "training.jsonl", {"repo": repo, "snapshot": snapshot,
                           "stage": "repeat4" if number <= 4 else "repeat19", "pass": number, "kind": "pass",
                           "status": "ok", **values, "elapsed_s": time.monotonic() - before, "protocol_sha256": binding})
                if number in (4, 19):
                    stage = f"repeat{number}"
                    destination = run_dir / "checkpoints" / f"{repo}-{snapshot}" / stage
                    destination.mkdir(parents=True, exist_ok=False)
                    model.save_pretrained(destination, safe_serialization=True)
                    write_json(destination / "continuation.json", {"protocol_sha256": binding, "original_adapter_digest": condition["adapter_digest"],
                                                                  "additional_passes": number, "selected_tokens": 4096})
                    diagnostics(stage, number)
            del optimizer, params, model
            gc.collect()
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        append_row(run_dir / "failures.jsonl", {"status": "error", "error": error,
                                               "traceback": traceback.format_exc(), "protocol_sha256": binding})
    receipt = finish_receipt(run_dir, protocol, cases, started, error)
    progress(f"experiment {receipt['status']}: {run_dir / 'receipt.json'}")
    return 1 if receipt["status"] == "failed" else 0


def smoke_execute(run_dir):
    """Separate throwaway actual256-token one-step continuation, no scientific rows."""
    started = time.monotonic()
    try:
        torch = runtime()
        tokenizer = load_tokenizer()
        from peft import PeftModel
        plan = json.loads((ROOT / HISTORICAL / "training-corpora/training-plan.json").read_text())
        corpus = next(c for c in plan["corpora"] if (c["repo"], c["snapshot"]) == ("flask", "old"))
        train = read_jsonl(ROOT / corpus["train"]["path"])
        if file_sha256(ROOT / corpus["train"]["path"]) != corpus["train"]["sha256"]:
            raise ValueError("smoke corpus hash mismatch")
        chunks = select_chunks("flask", "old", tokenized_chunks(train, tokenizer, 256), token_budget=256, max_length=256)
        adapter = ROOT / HISTORICAL / "adapters/flask-old"
        registration = json.loads((ROOT / HISTORICAL / "adapter-registration.json").read_text())
        expected_digest = next(a["adapter_digest"] for a in registration["adapters"] if (a["repo"], a["snapshot"]) == ("flask", "old"))
        if adapter_tree_digest(adapter) != expected_digest:
            raise ValueError("smoke original adapter digest mismatch")
        model = PeftModel.from_pretrained(load_base(torch), str(adapter), is_trainable=True, local_files_only=True)
        params = [p for p in model.parameters() if p.requires_grad]
        # Hash small LoRA parameters, not a second copy of the360M frozen base.
        def parameter_digest():
            digest = hashlib.sha256()
            for name, p in model.named_parameters():
                if p.requires_grad:
                    digest.update(name.encode() + b"\0")
                    digest.update(p.detach().cpu().contiguous().numpy().tobytes())
            return digest.hexdigest()
        before_digest = parameter_digest()
        before_loss = evaluate_loss(model, chunks, "cpu", torch)
        optimizer = torch.optim.AdamW(params, lr=0.0002, weight_decay=0.01)
        settings = {"seed": 17, "gradient_accumulation": len(chunks), "max_gradient_norm": 1.0}
        progress("smoke: real256-token continuation, one optimizer step")
        training = train_pass(model, chunks, optimizer, 1, settings, torch)
        after_digest = parameter_digest()
        if before_digest == after_digest or training["optimizer_steps"] != 1:
            raise ValueError("smoke did not update real LoRA parameters in exactly one step")
        after_loss = evaluate_loss(model, chunks, "cpu", torch)
        heldout = json.loads((ROOT / HISTORICAL / "heldout-excerpts/heldout-excerpts.json").read_text())
        examples = [h for h in heldout["prompts"] if h["repo"] == "flask"]
        scores = {}
        for example in examples:
            ids = tokenizer(example["snapshot_excerpt"], add_special_tokens=True)["input_ids"][:256]
            scores[example["snapshot"]] = cross_score(model, {"input_ids": ids, "prefix_ids": []}, torch)
        item = {"input_ids": chat_input(tokenizer, PROMPTS[0]["text"])}
        generation = generate(model, tokenizer, item, "greedy", {"max_new_tokens": 16}, torch)
        destination = run_dir / "checkpoint"
        destination.mkdir(exist_ok=False)
        model.save_pretrained(destination, safe_serialization=True)
        receipt = {"schema": SCHEMA + "/smoke", "status": "complete", "scientific_run": False,
                   "parameter_sha256_before": before_digest, "parameter_sha256_after": after_digest,
                   "loss_before": before_loss, "loss_after": after_loss, "training": training,
                   "cross_likelihood": scores, "generation": generation, "checkpoint_digest": adapter_tree_digest(destination),
                   "elapsed_s": time.monotonic() - started, "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2}
        write_json(run_dir / "smoke_receipt.json", receipt)
        progress(f"smoke complete: {run_dir / 'smoke_receipt.json'}")
        return 0
    except BaseException as exc:
        write_json(run_dir / "smoke_receipt.json", {"status": "failed", "scientific_run": False,
                   "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(),
                   "elapsed_s": time.monotonic() - started, "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2})
        return 1


def child_parent_death(expected_parent):
    # Linux: hard-kill worker if its supervisor dies, even while inside native training.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "cannot establish parent-death signal")
    if expected_parent is None or os.getppid() != expected_parent:
        raise RuntimeError("worker must be launched by its live lock-holding supervisor")


def supervise(run_dir, smoke=False):
    offline()
    run_dir = run_dir.resolve()
    protocol = cases = None
    if smoke:
        run_dir.mkdir(parents=True, exist_ok=False)
        budget, minimum_memory = 1800, 6
    else:
        protocol = json.loads((run_dir / "protocol.json").read_text())
        cases = json.loads((run_dir / "cases.json").read_text())
        budget = protocol["budget"]["model_wall_seconds"]
        minimum_memory = protocol["budget"]["minimum_available_memory_gib"]
    # Permanent started marker disallows restart even after interrupted or failed attempts.
    write_json(run_dir / "started.json", {"started_unix": time.time(), "mode": "smoke" if smoke else "run", "budget_seconds": budget})
    started, worker, error, lock = time.monotonic(), None, None, None
    def interrupt(signum, frame):
        raise KeyboardInterrupt(f"supervisor received signal{signum}")
    previous = {sig: signal.signal(sig, interrupt) for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    try:
        lock = GLOBAL_LOCK.open("a+")
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not smoke:
            protocol, cases = validate_prepared(run_dir)
        available = memory_available_gib()
        if available < minimum_memory:
            raise RuntimeError(f"CPU memory admission denied: {available:.3f}GiB available, {minimum_memory}GiB required; no eviction")
        progress(f"CPU admitted: {available:.3f}GiB available; global lock held; hard deadline{budget}s")
        remaining = budget - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError("model deadline elapsed before worker launch")
        worker = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                   "--_worker-smoke" if smoke else "--_worker-run", "--run-dir", str(run_dir),
                                   "--_parent-pid", str(os.getpid())],
                                  start_new_session=True)
        result = worker.wait(timeout=remaining)
        if result:
            error = f"worker exited{result}"
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if worker is not None and worker.poll() is None:
            # SIGKILL cannot be delayed by a native model call or an ignored signal.
            try:
                os.killpg(worker.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Worker finished between poll and kill; still reap it.
            worker.wait()
        if lock is not None:
            lock.close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    if smoke:
        receipt_path = run_dir / "smoke_receipt.json"
        if not receipt_path.exists():
            write_json(receipt_path, {"status": "failed", "scientific_run": False, "error": error or "missing worker receipt",
                                      "elapsed_s": time.monotonic() - started,
                                      "peak_rss_gib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024 ** 2})
    else:
        receipt_path = run_dir / "receipt.json"
        if not receipt_path.exists():
            finish_receipt(run_dir, protocol, cases, started, error or "missing worker receipt",
                           resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024 ** 2)
    receipt = json.loads(receipt_path.read_text())
    progress(f"{receipt['status']}: {receipt_path}")
    return 0 if receipt["status"] == "complete" and error is None else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--smoke", action="store_true")
    modes.add_argument("--_worker-run", action="store_true", help=argparse.SUPPRESS)
    modes.add_argument("--_worker-smoke", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--_parent-pid", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.prepare:
            prepare(args.run_dir)
            return 0
        if args._worker_run or args._worker_smoke:
            child_parent_death(args._parent_pid)
            return smoke_execute(args.run_dir) if args._worker_smoke else execute(args.run_dir, *validate_prepared(args.run_dir))
        return supervise(args.run_dir, smoke=args.smoke)
    except BaseException as exc:
        progress(f"failed: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
