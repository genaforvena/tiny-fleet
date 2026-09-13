#!/usr/bin/env python3
"""Train six bounded, snapshot-specific LoRA adapters from frozen source corpora."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import random
import re
import subprocess
import sys
from pathlib import Path


BASE_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
BASE_REVISION = "a10cc1512eabd3dde888204e902eca88bddb4951"
REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATION_RUNNER = REPO_ROOT / "scripts" / "drift_generate.py"
LEASE_SERVICES = ("mesh-voice-clone.service", "mesh-room-gigaam.service", "ollama.service")
HEAVY_RUN = os.environ.get("MESH_HEAVY_RUN_CMD", "mesh-heavy-run")
GPU_BUDGET_MB = 8192
LEASE_TTL = 1800
LOG = logging.getLogger("drift-adapter-training")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def chunk_tokens(input_ids, *, max_length, minimum_tokens=32):
    if max_length <= 1 or minimum_tokens <= 0 or minimum_tokens > max_length:
        raise ValueError("invalid token chunk limits")
    result = []
    for start in range(0, len(input_ids), max_length):
        chunk = tuple(input_ids[start:start + max_length])
        if len(chunk) >= minimum_tokens:
            result.append(chunk)
    return result


def select_chunks(repo, snapshot, chunks, *, token_budget, max_length):
    if not isinstance(token_budget, int) or token_budget <= 0:
        raise ValueError("positive token budget required")
    ranked = sorted(
        chunks,
        key=lambda row: (
            hashlib.sha256(f"{repo}\0{snapshot}\0{row['source_path']}\0{row['chunk_index']}".encode()).hexdigest(),
            row["source_path"], row["chunk_index"],
        ),
    )
    chosen = []
    remaining = token_budget
    for row in ranked:
        if remaining <= 0:
            break
        tokens = tuple(row["input_ids"][:min(max_length, remaining)])
        if len(tokens) < 2:
            break
        chosen.append({**row, "input_ids": tokens})
        remaining -= len(tokens)
    if not chosen:
        raise ValueError("no eligible token chunks within the registered budget")
    return chosen


def read_jsonl(path):
    rows = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}") from exc
    return rows


def run_command(args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def system_resources():
    resource = {"gpu_name": None, "gpu_free_mib": None, "gpu_total_mib": None,
                "gpu_lease": None, "services": {}, "memory_available_mib": None, "swap_free_mib": None,
                "resource_guard_summary": None}
    try:
        meminfo = {}
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            key, raw = line.split(":", 1)
            if key in {"MemAvailable", "SwapFree"}:
                meminfo[key] = int(raw.split()[0]) // 1024
        resource["memory_available_mib"] = meminfo.get("MemAvailable")
        resource["swap_free_mib"] = meminfo.get("SwapFree")
    except (OSError, ValueError, IndexError):
        pass
    guard = run_command(["mesh-resource-guard", "--status"])
    if guard.returncode == 0:
        resource["resource_guard_summary"] = next((line.strip() for line in guard.stdout.splitlines() if line.startswith("node:")), None)
    smi = run_command(["nvidia-smi", "--query-gpu=name,memory.free,memory.total", "--format=csv,noheader,nounits"])
    if smi.returncode == 0 and smi.stdout.strip():
        fields = [item.strip() for item in smi.stdout.splitlines()[0].split(",")]
        if len(fields) == 3:
            resource.update(gpu_name=fields[0], gpu_free_mib=int(fields[1]), gpu_total_mib=int(fields[2]))
    lease = run_command(["mesh-gpu-lease", "--status"])
    if lease.returncode == 0 and lease.stdout.startswith("GPU_LEASE="):
        raw = lease.stdout.strip().split("=", 1)[1]
        state = json.loads(raw) if raw.startswith("{") else None
        if state:
            state.pop("token", None)
        resource["gpu_lease"] = state
    for service in LEASE_SERVICES:
        result = run_command(["systemctl", "--user", "is-active", service])
        resource["services"][service] = result.stdout.strip() if result.returncode in (0, 3, 4) else "unknown"
    return resource


def load_corpus(plan_path, repo, snapshot):
    plan_path = Path(plan_path)
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    if plan.get("schema") != "tiny-fleet.drift-adapter-training-plan/v1":
        raise ValueError("training plan schema mismatch")
    if plan.get("base_model") != {"id": BASE_MODEL, "revision": BASE_REVISION}:
        raise ValueError("training plan base-model mismatch")
    runner = plan.get("training_runner", {})
    if runner.get("path") != "scripts/train_drift_adapters.py" or runner.get("source_sha256") != sha256(Path(__file__).read_bytes()):
        raise ValueError("training runner hash does not match the frozen plan")
    corpus = next((row for row in plan["corpora"] if row["repo"] == repo and row["snapshot"] == snapshot), None)
    if corpus is None:
        raise ValueError("no corpus row for requested snapshot")
    corpus_manifest_path = REPO_ROOT / "runs" / "drift-generative-v2" / "training-corpora" / f"{repo}-{snapshot}" / "manifest.json"
    manifest_bytes = corpus_manifest_path.read_bytes()
    if sha256(manifest_bytes) != corpus["manifest_sha256"]:
        raise ValueError("snapshot corpus manifest hash mismatch")
    manifest = json.loads(manifest_bytes)
    if manifest.get("repo") != repo or manifest.get("snapshot") != snapshot:
        raise ValueError("corpus source commit mismatch")
    train_path = REPO_ROOT / corpus["train"]["path"]
    validation_path = REPO_ROOT / corpus["validation"]["path"]
    train_bytes, validation_bytes = train_path.read_bytes(), validation_path.read_bytes()
    if sha256(train_bytes) != corpus["train"]["sha256"] or sha256(validation_bytes) != corpus["validation"]["sha256"]:
        raise ValueError("corpus split hash mismatch")
    train_records, validation_records = read_jsonl(train_path), read_jsonl(validation_path)
    heldout = manifest["selection"]["heldout_source_excluded"]
    for row in train_records + validation_records:
        if row["source_path"] == heldout:
            raise ValueError("held-out module leaked into training corpus")
    inventory_path = REPO_ROOT / manifest["inventory"]["path"]
    if sha256(inventory_path.read_bytes()) != manifest["inventory"]["sha256"]:
        raise ValueError("corpus file inventory hash mismatch")
    included = {row["path"]: row["sha256"] for row in read_jsonl(inventory_path) if row["status"] == "included"}
    for row in train_records + validation_records:
        if included.get(row["source_path"]) != row["source_file_sha256"]:
            raise ValueError("training row source-file hash disagrees with inventory")
    return plan, sha256(plan_bytes), corpus, manifest, train_records, validation_records


def tokenized_chunks(records, tokenizer, max_length):
    chunks = []
    for row in records:
        ids = tokenizer(row["text"], add_special_tokens=True, truncation=False, verbose=False)["input_ids"]
        for chunk_index, input_ids in enumerate(chunk_tokens(ids, max_length=max_length)):
            chunks.append({"source_path": row["source_path"], "chunk_index": chunk_index,
                           "input_ids": input_ids})
    return chunks


def evaluate_loss(model, chunks, device, torch):
    model.eval()
    total_nll, total_targets = 0.0, 0
    with torch.inference_mode():
        for row in chunks:
            ids = torch.tensor(row["input_ids"], dtype=torch.long, device=device).unsqueeze(0)
            result = model(input_ids=ids, attention_mask=torch.ones_like(ids), labels=ids)
            count = max(0, ids.shape[1] - 1)
            total_nll += float(result.loss.detach().float().cpu()) * count
            total_targets += count
    if total_targets <= 0 or not math.isfinite(total_nll):
        raise ValueError("validation loss has no finite token targets")
    mean_loss = total_nll / total_targets
    return {"mean_token_nll": mean_loss, "perplexity": math.exp(min(mean_loss, 80.0)),
            "target_tokens": total_targets, "chunks": len(chunks)}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def train_one(plan_path, repo, snapshot):
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    plan, plan_sha, corpus, corpus_manifest, train_records, validation_records = load_corpus(plan_path, repo, snapshot)
    config = plan["training"]
    seed = int(config["seed"])
    run_key = hashlib.sha256(f"{plan_sha}\0{repo}\0{snapshot}\0{seed}".encode()).hexdigest()[:20]
    run_dir = REPO_ROOT / "runs" / "drift-generative-v2" / "training-runs" / f"{repo}-{snapshot}"
    adapter_dir = REPO_ROOT / "runs" / "drift-generative-v2" / "adapters" / f"{repo}-{snapshot}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "training.log"
    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)
    resource = system_resources()
    result = {
        "schema": "tiny-fleet.drift-adapter-training-run/v1", "run_id": run_key,
        "status": "running", "repo": repo, "snapshot": snapshot,
        "source_commit": corpus_manifest["source_commit"], "corpus_manifest_sha256": corpus["manifest_sha256"],
        "training_plan_sha256": plan_sha, "train_corpus_sha256": corpus["train"]["sha256"],
        "validation_corpus_sha256": corpus["validation"]["sha256"],
        "base_model": plan["base_model"], "seed": seed,
        "hyperparameters": {key: config[key] for key in ("epochs", "max_sequence_length", "train_token_budget_per_adapter",
            "validation_token_budget_per_adapter", "batch_size", "gradient_accumulation", "learning_rate", "weight_decay",
            "max_gradient_norm", "lora")},
        "adapter_path": adapter_dir.relative_to(REPO_ROOT / "runs" / "drift-generative-v2").as_posix(),
        "resource_at_start": resource,
    }
    write_json(run_dir / "run.json", result)
    LOG.info("starting run=%s repo=%s snapshot=%s gpu=%s free_mib=%s", run_key, repo, snapshot,
             resource["gpu_name"], resource["gpu_free_mib"])
    try:
        import torch
        import transformers
        import peft
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable inside GPU-admitted training run")
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        random.seed(seed)
        device = torch.device("cuda")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION, local_files_only=True,
                                                  trust_remote_code=False)
        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, revision=BASE_REVISION, local_files_only=True,
                                                     trust_remote_code=False, dtype=torch.float16)
        model.config.use_cache = False
        model = model.to(device)
        target_modules = config["lora"]["target_modules"]
        available = {name.rsplit(".", 1)[-1] for name, _module in model.named_modules()}
        missing_targets = sorted(set(target_modules) - available)
        if missing_targets:
            raise ValueError(f"base model lacks registered LoRA target modules: {missing_targets}")
        lora = config["lora"]
        model = get_peft_model(model, LoraConfig(
            task_type=TaskType.CAUSAL_LM, r=lora["rank"], lora_alpha=lora["alpha"],
            lora_dropout=lora["dropout"], target_modules=target_modules, bias="none",
        ))
        model.train()
        train_candidates = tokenized_chunks(train_records, tokenizer, config["max_sequence_length"])
        validation_candidates = tokenized_chunks(validation_records, tokenizer, config["max_sequence_length"])
        train_chunks = select_chunks(repo, snapshot, train_candidates,
                                     token_budget=config["train_token_budget_per_adapter"],
                                     max_length=config["max_sequence_length"])
        validation_chunks = select_chunks(repo, snapshot, validation_candidates,
                                          token_budget=config["validation_token_budget_per_adapter"],
                                          max_length=config["max_sequence_length"])
        result["token_budget"] = {"train_candidates": len(train_candidates), "validation_candidates": len(validation_candidates),
                                  "train_selected_chunks": len(train_chunks), "validation_selected_chunks": len(validation_chunks),
                                  "train_selected_tokens": sum(len(row["input_ids"]) for row in train_chunks),
                                  "validation_selected_tokens": sum(len(row["input_ids"]) for row in validation_chunks)}
        result["validation_before"] = evaluate_loss(model, validation_chunks, device, torch)
        model.train()
        optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad),
                                      lr=float(config["learning_rate"]), weight_decay=float(config["weight_decay"]))
        order = list(train_chunks)
        random.Random(seed).shuffle(order)
        accumulation = int(config["gradient_accumulation"])
        losses, optimizer_steps, pending = [], 0, 0
        optimizer.zero_grad(set_to_none=True)
        for index, row in enumerate(order):
            ids = torch.tensor(row["input_ids"], dtype=torch.long, device=device).unsqueeze(0)
            output = model(input_ids=ids, attention_mask=torch.ones_like(ids), labels=ids)
            loss = output.loss
            if not torch.isfinite(loss):
                raise ValueError(f"non-finite training loss at chunk {index}")
            (loss / accumulation).backward()
            losses.append(float(loss.detach().float().cpu()))
            pending += 1
            if pending == accumulation or index + 1 == len(order):
                if pending < accumulation:
                    scale = accumulation / pending
                    for parameter in model.parameters():
                        if parameter.grad is not None:
                            parameter.grad.mul_(scale)
                torch.nn.utils.clip_grad_norm_((p for p in model.parameters() if p.requires_grad),
                                               float(config["max_gradient_norm"]))
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_steps += 1
                pending = 0
            if (index + 1) % 16 == 0 or index + 1 == len(order):
                LOG.info("progress chunks=%s/%s mean_loss=%.5f", index + 1, len(order), sum(losses) / len(losses))
        result["train"] = {"epochs": int(config["epochs"]), "chunks_seen": len(order),
                            "optimizer_steps": optimizer_steps, "mean_chunk_loss": sum(losses) / len(losses)}
        result["validation_after"] = evaluate_loss(model, validation_chunks, device, torch)
        adapter_dir.mkdir(parents=True, exist_ok=False)
        model.save_pretrained(adapter_dir, safe_serialization=True)
        from drift_generate import adapter_tree_digest
        adapter_digest = adapter_tree_digest(adapter_dir)
        result.update(status="complete", adapter_digest=adapter_digest,
                      adapter_files={path.relative_to(adapter_dir).as_posix(): sha256(path.read_bytes())
                                     for path in sorted(adapter_dir.rglob("*")) if path.is_file()},
                      runtime={"python": sys.version.split()[0], "torch": torch.__version__,
                               "transformers": transformers.__version__, "peft": peft.__version__,
                               "cuda": torch.version.cuda, "device": torch.cuda.get_device_name(0)},
                      resource_during_run=system_resources())
        LOG.info("complete adapter_sha256=%s train_loss=%.5f validation_before=%.5f validation_after=%.5f",
                 adapter_digest, result["train"]["mean_chunk_loss"], result["validation_before"]["mean_token_nll"],
                 result["validation_after"]["mean_token_nll"])
    except Exception as exc:
        result.update(status="failed", failure_type=type(exc).__name__, failure=str(exc))
        LOG.exception("training failed")
        write_json(run_dir / "run.json", result)
        raise
    finally:
        LOG.removeHandler(handler)
        handler.close()
    write_json(run_dir / "run.json", result)
    return result


def _redact_lease_token(value):
    return re.sub(r"token=[0-9a-f]{32}", "token=<redacted>", value)


def run_all(plan_path):
    plan_path = Path(plan_path)
    baseline = system_resources()
    if any(state not in {"active", "inactive"} for state in baseline["services"].values()):
        raise RuntimeError("cannot establish exact managed GPU-service state before training")
    if baseline["gpu_lease"] is not None or baseline["gpu_name"] is None or baseline["gpu_free_mib"] is None:
        raise RuntimeError("cannot start: an existing GPU lease or unreadable GPU state is present")
    training_rows = []
    adapter_root = REPO_ROOT / "runs" / "drift-generative-v2" / "adapters"
    training_root = REPO_ROOT / "runs" / "drift-generative-v2" / "training-runs"
    training_root.mkdir(parents=True, exist_ok=True)
    for corpus in json.loads(plan_path.read_text(encoding="utf-8"))["corpora"]:
        repo, snapshot = corpus["repo"], corpus["snapshot"]
        run_dir = training_root / f"{repo}-{snapshot}"
        log_stdout, log_stderr = run_dir / "mesh-heavy-run.stdout.log", run_dir / "mesh-heavy-run.stderr.log"
        child_path = run_dir / "run.json"
        if child_path.is_file():
            previous = json.loads(child_path.read_text(encoding="utf-8"))
            if previous.get("status") == "running":
                raise RuntimeError(f"prior {repo}/{snapshot} run is still queued or unfinished; inspect its durable run/queue artifact before retry")
            if previous.get("status") == "complete":
                if previous.get("training_plan_sha256") != sha256(plan_path.read_bytes()):
                    raise RuntimeError(f"completed run plan changed for {repo}/{snapshot}")
                from drift_generate import adapter_tree_digest
                adapter_dir = REPO_ROOT / "runs" / "drift-generative-v2" / previous["adapter_path"]
                if adapter_tree_digest(adapter_dir) != previous.get("adapter_digest"):
                    raise RuntimeError(f"completed adapter digest changed for {repo}/{snapshot}")
                post = system_resources()
                previous["resource_after_run"] = post
                previous["restoration_check"] = {"lease_released": post["gpu_lease"] is None,
                    "service_states_before": baseline["services"], "service_states_after": post["services"],
                    "service_states_match_baseline": post["services"] == baseline["services"],
                    "passed": post["gpu_lease"] is None and post["services"] == baseline["services"],
                    "recovered_from_prior_wrapper_completion": True}
                if not previous["restoration_check"]["passed"]:
                    raise RuntimeError(f"service restoration mismatch while resuming after {repo}/{snapshot}")
                write_json(child_path, previous)
                training_rows.append({"repo": repo, "snapshot": snapshot, "status": "complete", "returncode": 0,
                    "run_path": child_path.relative_to(REPO_ROOT).as_posix(), "adapter_digest": previous["adapter_digest"],
                    "restoration_check": previous["restoration_check"], "reused": True})
                write_json(training_root / "training-progress.json", {"schema": "tiny-fleet.drift-adapter-training-progress/v1",
                    "status": "in-progress" if len(training_rows) < 6 else "complete", "baseline_resources": baseline,
                    "runs": training_rows})
                continue
        env = dict(os.environ)
        env.update({"MESH_HEAVY_GPU_MIN_FREE_MB": str(GPU_BUDGET_MB), "MESH_HEAVY_GPU_PREEMPT": "1",
                    "MESH_HEAVY_GPU_LEASE_TTL": str(LEASE_TTL), "MESH_HEAVY_SWAPMAX_MB": "0"})
        command = [HEAVY_RUN, "8192", "--", sys.executable, str(Path(__file__).resolve()),
                   "--one", "--plan", str(plan_path), "--repo", repo, "--snapshot", snapshot]
        execution = subprocess.run(command, cwd=REPO_ROOT, env=env, text=True, capture_output=True, check=False)
        run_dir.mkdir(parents=True, exist_ok=True)
        log_stdout.write_text(_redact_lease_token(execution.stdout), encoding="utf-8")
        log_stderr.write_text(_redact_lease_token(execution.stderr), encoding="utf-8")
        post = system_resources()
        child = json.loads(child_path.read_text(encoding="utf-8")) if child_path.is_file() else {"status": "not-started"}
        child["resource_after_run"] = post
        child["heavy_run"] = {"command": ["mesh-heavy-run", "8192", "--", "train_drift_adapters.py", "--one", repo, snapshot],
                              "returncode": execution.returncode, "gpu_min_free_mib": GPU_BUDGET_MB,
                              "gpu_preempt": True, "gpu_lease_ttl_seconds": LEASE_TTL,
                              "stdout_path": log_stdout.relative_to(REPO_ROOT).as_posix(),
                              "stderr_path": log_stderr.relative_to(REPO_ROOT).as_posix(),
                              "lease_stdout_sha256": sha256(log_stdout.read_bytes()),
                              "lease_stderr_sha256": sha256(log_stderr.read_bytes())}
        child["restoration_check"] = {
            "lease_released": post["gpu_lease"] is None,
            "service_states_before": baseline["services"],
            "service_states_after": post["services"],
            "service_states_match_baseline": post["services"] == baseline["services"],
            "passed": post["gpu_lease"] is None and post["services"] == baseline["services"],
        }
        write_json(child_path, child)
        training_rows.append({"repo": repo, "snapshot": snapshot, "status": child.get("status"),
                              "returncode": execution.returncode, "run_path": child_path.relative_to(REPO_ROOT).as_posix(),
                              "adapter_digest": child.get("adapter_digest"),
                              "restoration_check": child["restoration_check"]})
        write_json(training_root / "training-progress.json", {"schema": "tiny-fleet.drift-adapter-training-progress/v1",
                   "status": "in-progress" if len(training_rows) < 6 else "complete", "baseline_resources": baseline,
                   "runs": training_rows})
        if execution.returncode != 0 or child.get("status") != "complete" or not child["restoration_check"]["passed"]:
            print(json.dumps({"status": "incomplete", "failed_snapshot": f"{repo}/{snapshot}",
                              "returncode": execution.returncode, "child_status": child.get("status"),
                              "resource_after_run": post}, sort_keys=True))
            return execution.returncode or 1
    registration = {
        "schema": "tiny-fleet.drift-adapter-registration/v1", "status": "six-adapters-trained",
        "training_plan_sha256": sha256(plan_path.read_bytes()), "base_model": {"id": BASE_MODEL, "revision": BASE_REVISION},
        "seed": 17, "adapters": [], "temporal_limit": "inherits the strict blind-order limitation in execution-scorer.json",
    }
    for row in training_rows:
        run = json.loads((REPO_ROOT / row["run_path"]).read_text(encoding="utf-8"))
        adapter_path = REPO_ROOT / "runs" / "drift-generative-v2" / run["adapter_path"]
        registration["adapters"].append({"repo": row["repo"], "snapshot": row["snapshot"],
                                         "source_commit": run["source_commit"],
                                         "adapter_path": adapter_path.relative_to(REPO_ROOT / "runs" / "drift-generative-v2").as_posix(),
                                         "adapter_digest": run["adapter_digest"],
                                         "training_run_sha256": sha256((REPO_ROOT / row["run_path"]).read_bytes()),
                                         "corpus_manifest_sha256": run["corpus_manifest_sha256"]})
    registration_path = REPO_ROOT / "runs" / "drift-generative-v2" / "adapter-registration.json"
    write_json(registration_path, registration)
    progress = {"schema": "tiny-fleet.drift-adapter-training-progress/v1", "status": "complete",
                "baseline_resources": baseline, "runs": training_rows,
                "adapter_registration": registration_path.relative_to(REPO_ROOT).as_posix(),
                "adapter_registration_sha256": sha256(registration_path.read_bytes())}
    write_json(training_root / "training-progress.json", progress)
    print(json.dumps({"status": "complete", "runs": len(training_rows),
                      "adapter_registration": str(registration_path),
                      "adapter_registration_sha256": progress["adapter_registration_sha256"]}, sort_keys=True))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="train all six registered snapshots, sequentially through mesh-heavy-run")
    mode.add_argument("--one", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--repo", choices=("flask", "requests", "pydantic"))
    parser.add_argument("--snapshot", choices=("old", "new"))
    args = parser.parse_args(argv)
    if args.all:
        return run_all(args.plan)
    if not args.repo or not args.snapshot:
        parser.error("--one requires --repo and --snapshot")
    train_one(args.plan, args.repo, args.snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
