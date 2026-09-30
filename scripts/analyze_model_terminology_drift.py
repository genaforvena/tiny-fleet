#!/usr/bin/env python3
"""Strict source-bound descriptive analysis; never treats decoding draws as replicas."""
import argparse
import hashlib
import itertools
import json
import math
import tarfile
from collections import Counter
from pathlib import Path

from drift_lexical import tokenize

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("baseline", "repeat4", "repeat19")
SNAPSHOTS = ("old", "new")
SOURCE_CONTROLS = ("original", "token_shuffle")
ARMS = ("lora", "base", "prompt-only", "unigram")
DECODES = ("greedy", "sample17", "sample29", "sample43")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def exact_sign_flips(values):
    """The source unit is the repository: exactly 2**3 sign assignments."""
    if len(values) != 3 or not all(finite(value) for value in values):
        raise ValueError("exact inference requires three finite repository-level values")
    observed = math.fsum(values) / 3
    permutations = [
        {"signs": list(signs), "mean": math.fsum(sign * value for sign, value in zip(signs, values)) / 3}
        for signs in itertools.product((-1, 1), repeat=3)
    ]
    tail = sum(row["mean"] >= observed for row in permutations)
    largest = max(row["mean"] for row in permutations)
    actual_floor = sum(row["mean"] == largest for row in permutations) / 8
    return {"observed_mean": observed, "repository_values": values,
            "permutations": permutations, "one_sided_p": tail / 8,
            "nominal_eight_assignment_p_floor": 1 / 8,
            "attainable_one_sided_p_floor": actual_floor, "source_units": 3,
            "upper_tail_assignments": tail, "maximum_statistic_tie_assignments": int(actual_floor * 8),
            "nonzero_repository_units": sum(value != 0 for value in values),
            "null_distribution": [{"mean": value, "assignments": count}
                                  for value, count in sorted(Counter(row["mean"] for row in permutations).items())],
            "interpretation": "Exploratory label sign-flip reference, not evidence of statistical superiority; repository exchangeability is unproven."}


def preference(matrix):
    """Rows are conditioning snapshot, columns target snapshot; smaller NLL wins."""
    old_margin = matrix[("new", "old")] - matrix[("old", "old")]
    new_margin = matrix[("old", "new")] - matrix[("new", "new")]
    correct = lambda margin: 1.0 if margin > 0 else (0.0 if margin < 0 else 0.5)
    return {"diagonal_self_preference": (old_margin + new_margin) / 2,
            "old_target_margin": old_margin, "new_target_margin": new_margin,
            "balanced_snapshot_accuracy": (correct(old_margin) + correct(new_margin)) / 2,
            "matrix_mean_token_nll": {f"{model}->{target}": value for (model, target), value in matrix.items()}}


def lexical_profile(text):
    counts = Counter(tokenize(text))
    total = sum(counts.values())
    return counts, total, {term: count / total for term, count in counts.items()} if total else {}


def lexical_shift(old_text, new_text):
    old_counts, old_total, old_rates = lexical_profile(old_text)
    new_counts, new_total, new_rates = lexical_profile(new_text)
    vocabulary = sorted(old_counts.keys() | new_counts.keys())
    delta = {term: new_rates.get(term, 0.0) - old_rates.get(term, 0.0) for term in vocabulary}
    return {"old_lexical_tokens": old_total, "new_lexical_tokens": new_total,
            "zero_vocabulary": old_total == 0 or new_total == 0,
            "terms": [{"term": term, "old_count": old_counts[term], "new_count": new_counts[term],
                       "old_rate": old_rates.get(term, 0.0), "new_rate": new_rates.get(term, 0.0),
                       "delta_rate": delta[term]} for term in vocabulary],
            "delta": delta}


def delta_alignment(source_shift, output_shift):
    source, generated = source_shift["delta"], output_shift["delta"]
    vocabulary = source.keys() | generated.keys()
    source_norm = math.sqrt(math.fsum(value * value for value in source.values()))
    generated_norm = math.sqrt(math.fsum(value * value for value in generated.values()))
    dot = math.fsum(source.get(term, 0.0) * generated.get(term, 0.0) for term in vocabulary)
    changed = {term for term, value in source.items() if value != 0}
    present = {row["term"] for row in output_shift["terms"]}
    weight = math.fsum(abs(source[term]) for term in changed)
    covered = changed & present
    defined = not source_shift["zero_vocabulary"] and not output_shift["zero_vocabulary"]
    return {"cosine_delta_alignment": dot / (source_norm * generated_norm) if defined and source_norm and generated_norm else None,
            "source_changed_terms": len(changed), "source_changed_terms_present_in_output": len(covered),
            "source_delta_term_coverage": len(covered) / len(changed) if changed else None,
            "source_delta_mass_coverage": math.fsum(abs(source[term]) for term in covered) / weight if weight else None,
            "signed_source_delta_mass_agreement": math.fsum(abs(source[term]) for term in changed
                if source[term] * generated.get(term, 0.0) > 0) / weight if weight else None,
            "source_delta_l2": source_norm, "output_delta_l2": generated_norm,
            "zero_vocabulary": source_shift["zero_vocabulary"] or output_shift["zero_vocabulary"],
            "zero_source_delta": source_norm == 0, "zero_output_delta": generated_norm == 0}


def read_jsonl(path, errors, invalid_lines=None):
    rows = []
    if not path.is_file():
        errors.append(f"missing tape: {path.name}")
        return rows
    try:
        with path.open("rb") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line, parse_constant=reject_constant)
                    if not isinstance(row, dict):
                        raise ValueError("record must be an object")
                    rows.append(row)
                except (ValueError, TypeError) as exc:
                    errors.append(f"{path.name}:{line_number}: {exc}")
                    if invalid_lines is not None:
                        invalid_lines.append(line_number)
    except OSError as exc:
        errors.append(f"{path.name}: {exc}")
    return rows


def index_rows(rows, fields, label, errors):
    result = {}
    for number, row in enumerate(rows, 1):
        try:
            key = tuple(row[field] for field in fields)
            if key in result:
                errors.append(f"duplicate {label} key: {key}")
            else:
                result[key] = row
        except (KeyError, TypeError) as exc:
            errors.append(f"invalid {label} key at record {number}: {exc}")
    return result


def validate_cost(row, label, errors):
    if not finite(row.get("elapsed_s")) or row["elapsed_s"] < 0:
        errors.append(f"{label}: invalid elapsed_s")


def validate_nll(row, expected_tokens, label, errors):
    if row.get("status") != "ok":
        errors.append(f"{label}: status={row.get('status')}; {row.get('error', 'no error detail')}")
        return False
    valid = positive_int(row.get("target_tokens")) and row["target_tokens"] == expected_tokens
    valid = valid and finite(row.get("nll_sum")) and row["nll_sum"] >= 0
    valid = valid and finite(row.get("mean_token_nll")) and row["mean_token_nll"] >= 0
    if valid:
        valid = math.isclose(row["mean_token_nll"], row["nll_sum"] / row["target_tokens"], rel_tol=1e-9, abs_tol=1e-9)
    if not valid:
        errors.append(f"{label}: invalid NLL sum, exact denominator, or mean")
    return valid


def likelihood_summary(rows, repositories, cases):
    index = {(row["repo"], row["stage"], row["model_snapshot"], row["target_snapshot"],
              row["control"], row["arm"]): row for row in rows}
    conditions = {(case["repo"], case["snapshot"]): case for case in cases["conditions"]}
    changed = [repo for repo in repositories if conditions[(repo, "old")]["heldout"]["text"]
               != conditions[(repo, "new")]["heldout"]["text"]]
    results = []
    for stage in STAGES:
        for control in SOURCE_CONTROLS:
            by_arm = {}
            for arm in ARMS:
                repository_results = {}
                for repo in repositories:
                    matrix = {}
                    for model, target in itertools.product(SNAPSHOTS, repeat=2):
                        row = index.get((repo, stage if arm == "lora" else "shared", model, target, control, arm))
                        if arm == "base":
                            row = index.get((repo, "shared", "shared", target, control, arm))
                        if row is None or row.get("status") != "ok":
                            matrix = {}
                            break
                        matrix[(model, target)] = row["mean_token_nll"]
                    repository_results[repo] = preference(matrix) if len(matrix) == 4 else None
                successful = [value for value in repository_results.values() if value is not None]
                by_arm[arm] = {
                    "repositories": repository_results,
                    "mean_balanced_snapshot_accuracy": math.fsum(value["balanced_snapshot_accuracy"] for value in successful) / 3
                        if len(successful) == 3 else None,
                    "diagonal_sign_flips": exact_sign_flips([repository_results[repo]["diagonal_self_preference"] for repo in repositories])
                        if len(successful) == 3 else None,
                    "changed_source_pair_mean_accuracy": math.fsum(repository_results[repo]["balanced_snapshot_accuracy"]
                        for repo in changed) / len(changed) if changed and all(repository_results[repo] is not None for repo in changed) else None,
                    "changed_source_pair_mean_diagonal_preference": math.fsum(repository_results[repo]["diagonal_self_preference"]
                        for repo in changed) / len(changed) if changed and all(repository_results[repo] is not None for repo in changed) else None,
                }
            differences = {}
            for arm in ("base", "unigram", "prompt-only"):
                values = [
                    by_arm["lora"]["repositories"][repo]["diagonal_self_preference"]
                    - by_arm[arm]["repositories"][repo]["diagonal_self_preference"]
                    for repo in repositories
                    if by_arm["lora"]["repositories"][repo] is not None and by_arm[arm]["repositories"][repo] is not None
                ]
                differences[arm] = exact_sign_flips(values) if len(values) == 3 else None
            results.append({"stage": stage, "source_control": control, "arms": by_arm,
                            "lora_minus_control_diagonal_preference": differences})
    shuffle_contrasts = []
    for stage in STAGES:
        original = next(row for row in results if row["stage"] == stage and row["source_control"] == "original")
        shuffled = next(row for row in results if row["stage"] == stage and row["source_control"] == "token_shuffle")
        values = [
            original["arms"]["lora"]["repositories"][repo]["diagonal_self_preference"]
            - shuffled["arms"]["lora"]["repositories"][repo]["diagonal_self_preference"]
            for repo in repositories
            if original["arms"]["lora"]["repositories"][repo] is not None and shuffled["arms"]["lora"]["repositories"][repo] is not None
        ]
        shuffle_contrasts.append({"stage": stage, "original_minus_token_shuffle_diagonal_preference":
                                 exact_sign_flips(values) if len(values) == 3 else None})
    return {"cells": results, "shuffle_contrasts": shuffle_contrasts,
            "repository_order_for_sign_flips": repositories,
            "snapshot_classification_decisions": 2 * len(repositories),
            "changed_pair_snapshot_classification_decisions": 2 * len(changed),
            "changed_heldout_source_repositories": changed,
            "unchanged_heldout_source_repositories": [repo for repo in repositories if repo not in changed],
            "identity_source_limit": "Identical heldout inputs force diagonal preference=0 and balanced classification=0.5. This is an unchanged-excerpt negative control, not evidence that the whole repository is unchanged or that global generated drift is a false positive.",
            "formula": "D=((NLL(new->old)-NLL(old->old))+(NLL(old->new)-NLL(new->new)))/2; accuracy is mean of two correct-model choices, ties=0.5.",
            "units": "Mean causal NLL per target token; equal-weight repository aggregation, not chunk-level or draw-level inference.",
            "control_reuse": "Stage-independent base, token-unigram and training-context prompt-only rows are reused explicitly across stages. Base is snapshot-agnostic, hence classification=0.5 and diagonal preference=0."}


def generation_summary(rows, cases, protocol, repositories):
    index = {(row["repo"], row["snapshot"], row["stage"], row["arm"], row["prompt_id"], row["decode_id"]): row for row in rows}
    conditions = {(case["repo"], case["snapshot"]): case for case in cases["conditions"]}
    source = {repo: lexical_shift(conditions[(repo, "old")]["heldout"]["text"],
                                 conditions[(repo, "new")]["heldout"]["text"]) for repo in repositories}
    pairs = []
    for repo, stage, arm, prompt, decode in itertools.product(repositories, STAGES,
             ("lora", "base", "prompt-only"), protocol["prompts"], DECODES):
        matching = []
        for snapshot in SNAPSHOTS:
            key = ("shared", "shared", "shared", "base", prompt["prompt_id"], decode) if arm == "base" else (
                repo, snapshot, stage if arm == "lora" else "shared", arm, prompt["prompt_id"], decode)
            matching.append(index.get(key))
        record = {"repo": repo, "stage": stage, "arm": arm, "prompt_id": prompt["prompt_id"], "decode_id": decode,
                  "reuse": arm != "lora", "status": "ok" if all(row and row.get("status") == "ok" for row in matching) else "error"}
        record["outcomes"] = [{key: row.get(key) for key in ("status", "error", "output_sha256", "generated_tokens", "cap_hit", "empty_output", "elapsed_s")}
                              if row else {"status": "missing"} for row in matching]
        if record["status"] == "ok":
            shift = lexical_shift(matching[0]["output"], matching[1]["output"])
            record.update(output_shift=shift, alignment=delta_alignment(source[repo], shift))
        else:
            record.update(output_shift=None, alignment=None)
        pairs.append(record)
    variability = []
    for repo, stage, arm, prompt in itertools.product(repositories, STAGES, ("lora", "base", "prompt-only"), protocol["prompts"]):
        selected = [row for row in pairs if row["repo"] == repo and row["stage"] == stage and row["arm"] == arm
                    and row["prompt_id"] == prompt["prompt_id"] and row["decode_id"].startswith("sample")]
        values = [row["alignment"]["cosine_delta_alignment"] for row in selected
                  if row["alignment"] and row["alignment"]["cosine_delta_alignment"] is not None]
        mean = math.fsum(values) / len(values) if values else None
        variability.append({"repo": repo, "stage": stage, "arm": arm, "prompt_id": prompt["prompt_id"],
                            "successful_sample_draws": sum(row["status"] == "ok" for row in selected),
                            "defined_alignment_draws": len(values), "mean_cosine_alignment": mean,
                            "population_sd_cosine_alignment": math.sqrt(math.fsum((value - mean) ** 2 for value in values) / len(values))
                                if values else None})
    identities = []
    for row in rows:
        if row.get("decode_id") != "identity":
            continue
        key = (row["repo"], row["snapshot"], row["stage"], row["arm"], row["prompt_id"], "greedy")
        original = index.get(key)
        identities.append({"repo": row["repo"], "snapshot": row["snapshot"], "stage": row["stage"], "prompt_id": row["prompt_id"],
                           "both_successful": bool(original and original.get("status") == row.get("status") == "ok"),
                           "same_input": bool(original and original.get("input_sha256") == row.get("input_sha256")),
                           "same_raw_output": bool(original and original.get("status") == row.get("status") == "ok"
                               and original.get("output") == row.get("output")
                               and original.get("generated_tokens") == row.get("generated_tokens")
                               and original.get("cap_hit") == row.get("cap_hit"))})
    return {"source_lexical_shifts": source, "paired_outputs": pairs, "sample_variability": variability,
            "identity_repeats": identities,
            "measurement": "drift_lexical.tokenize on all raw outputs and heldout source excerpts; relative-frequency new-minus-old vectors over the full union vocabulary. Cosine includes output-only terms in its norm. Coverage counts changed source terms appearing in either output; no term selection or output cleaning.",
            "limits": "Undefined cosine and coverage remain null for zero vectors/vocabularies; failed outputs remain error records. Sampled decodes are variability probes, not independent training seeds or source units. Lexical alignment is not human semantic validity."}


def training_summary(rows, likelihood_rows):
    diagnostics = {(row["repo"], row["snapshot"], row["stage"]): row for row in rows if row["kind"] == "diagnostic"}
    likelihood = {(row["repo"], row["stage"], row["model_snapshot"], row["target_snapshot"], row["control"], row["arm"]): row
                  for row in likelihood_rows}
    comparisons = []
    for (repo, snapshot, stage), row in sorted(diagnostics.items()):
        baseline = diagnostics[(repo, snapshot, "baseline")]
        self_row = likelihood[(repo, stage, snapshot, snapshot, "original", "lora")]
        baseline_self = likelihood[(repo, "baseline", snapshot, snapshot, "original", "lora")]
        train = row["train"]["mean_token_nll"]
        validation = row["validation"]["mean_token_nll"]
        heldout = self_row["mean_token_nll"]
        train_change = train - baseline["train"]["mean_token_nll"]
        heldout_change = heldout - baseline_self["mean_token_nll"]
        validation_change = validation - baseline["validation"]["mean_token_nll"]
        comparisons.append({"repo": repo, "snapshot": snapshot, "stage": stage,
                            "additional_selected_subset_passes": row["pass"],
                            "train_mean_token_nll": train, "validation_mean_token_nll": validation,
                            "heldout_self_mean_token_nll": heldout,
                            "validation_minus_train_gap": validation - train, "heldout_minus_train_gap": heldout - train,
                            "train_change_from_baseline": train_change, "validation_change_from_baseline": validation_change,
                            "heldout_change_from_baseline": heldout_change,
                            "heldout_train_gap_change_from_baseline": heldout_change - train_change,
                            "train_improved": train_change < 0, "heldout_improved": heldout_change < 0,
                            "observed_overfit_to_selected_subset": stage != "baseline" and train_change < 0 and heldout_change > 0})
    return {"diagnostic_comparisons": comparisons,
            "pass_records": [row for row in rows if row["kind"] == "pass"],
            "interpretation": "Repeated fitting is 4/19 ADDITIONAL passes over one selected4096-token subset after original one-epoch16384-token adaptation, not5/20 full-corpus epochs. Train decrease alone is learning, not a drift instrument. Overfit-to-subset flag requires train decrease and heldout increase from baseline; train/heldout gaps are descriptive and distributions differ. Validation is original corpus validation, not the independent heldout module."}


def reject_constant(value):
    raise ValueError(f"non-finite JSON constant {value}")


def load_json(path, errors):
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
        if not isinstance(value, dict):
            raise ValueError("expected JSON object")
        return value
    except (OSError, ValueError) as exc:
        errors.append(f"{path.name}: {exc}")
        return None


def check_digest(path, expected, label, errors):
    try:
        with path.open("rb") as stream:
            observed = hashlib.file_digest(stream, "sha256").hexdigest()
        if not isinstance(expected, str) or observed != expected:
            errors.append(f"{label}: SHA256 mismatch (expected {expected}, observed {observed})")
        return observed
    except OSError as exc:
        errors.append(f"{label}: {exc}")
        return None


def observed_tapes(tapes):
    result = {}
    for name, rows in tapes.items():
        successful = [row for row in rows if row.get("status") == "ok"]
        result[name] = {"rows": len(rows), "status_counts": dict(sorted(Counter(str(row.get("status", "absent")) for row in rows).items())),
                        "finite_record_elapsed_s": math.fsum(row["elapsed_s"] for row in rows if finite(row.get("elapsed_s")) and row["elapsed_s"] >= 0),
                        "failures": [row for row in rows if row.get("status") != "ok"]}
        if name == "likelihood.jsonl":
            result[name]["recorded_successful_target_tokens"] = sum(row["target_tokens"] for row in successful if positive_int(row.get("target_tokens")))
        elif name == "generations.jsonl":
            result[name]["recorded_generated_tokens"] = sum(row["generated_tokens"] for row in successful
                if isinstance(row.get("generated_tokens"), int) and not isinstance(row["generated_tokens"], bool) and row["generated_tokens"] >= 0)
            result[name]["cap_hits"] = sum(row.get("cap_hit") is True for row in successful)
            result[name]["empty_outputs"] = sum(row.get("empty_output") is True for row in successful)
        elif name == "training.jsonl":
            result[name]["successful_additional_passes"] = sum(row.get("kind") == "pass" for row in successful)
            result[name]["recorded_pass_target_tokens"] = sum(row["train"]["target_tokens"] for row in successful
                if row.get("kind") == "pass" and isinstance(row.get("train"), dict) and positive_int(row["train"].get("target_tokens")))
        result[name]["verification"] = "Raw finite recorded observations; see report complete/errors before using as validated evidence."
    return result


def validate_matrix(rows, expected, fields, label, protocol_digest, errors):
    actual = index_rows(rows, fields, label, errors)
    planned = index_rows(expected, fields, f"expected {label}", errors)
    for key in sorted(planned.keys() - actual.keys()):
        errors.append(f"missing {label} row: {key}")
    for key in sorted(actual.keys() - planned.keys()):
        errors.append(f"unexpected {label} row: {key}")
    for key, row in actual.items():
        name = f"{label} {key}"
        if row.get("protocol_sha256") != protocol_digest:
            errors.append(f"{name}: protocol binding mismatch")
        validate_cost(row, name, errors)
        if key not in planned:
            continue
        for field in ("input_sha256", "source_path", "target_tokens"):
            if field in planned[key] and row.get(field) != planned[key][field]:
                errors.append(f"{name}: {field} binding mismatch")
        if label == "likelihood":
            validate_nll(row, planned[key]["target_tokens"], name, errors)
        elif label == "generation":
            if row.get("status") != "ok":
                errors.append(f"{name}: status={row.get('status')}; {row.get('error', 'no error detail')}")
            if not isinstance(row.get("output"), str) or row.get("output_sha256") != sha256(row.get("output", "").encode("utf-8")):
                errors.append(f"{name}: raw output SHA256 mismatch")
            if not isinstance(row.get("generated_tokens"), int) or isinstance(row.get("generated_tokens"), bool) or row["generated_tokens"] < 0:
                errors.append(f"{name}: invalid generated_tokens")
            if not isinstance(row.get("cap_hit"), bool):
                errors.append(f"{name}: invalid cap_hit")
    return actual


def validate_training(rows, cases, protocol_digest, errors):
    fields = ("repo", "snapshot", "kind", "pass")
    actual = index_rows(rows, fields, "training", errors)
    expected = {}
    for case in cases["conditions"]:
        for stage, number in zip(STAGES, (0, 4, 19)):
            expected[(case["repo"], case["snapshot"], "diagnostic", number)] = (case, stage)
        for number in range(1, 20):
            expected[(case["repo"], case["snapshot"], "pass", number)] = (case, None)
    for key in sorted(expected.keys() - actual.keys()):
        errors.append(f"missing training row: {key}")
    for key in sorted(actual.keys() - expected.keys()):
        errors.append(f"unexpected training row: {key}")
    for key, row in actual.items():
        name = f"training {key}"
        if row.get("protocol_sha256") != protocol_digest:
            errors.append(f"{name}: protocol binding mismatch")
        validate_cost(row, name, errors)
        if row.get("status") != "ok":
            errors.append(f"{name}: status={row.get('status')}; {row.get('error', 'no error detail')}")
        if key not in expected:
            continue
        case, stage = expected[key]
        expected_stage = stage if stage else ("repeat4" if row["pass"] <= 4 else "repeat19")
        if row.get("stage") != expected_stage:
            errors.append(f"{name}: stage/pass mismatch")
        for split in ("train", "validation") if stage else ("train",):
            losses = row.get(split)
            tokens = sum(len(chunk["input_ids"]) - 1 for chunk in case[f"{split}_chunks"])
            if not isinstance(losses, dict):
                errors.append(f"{name}: missing {split} losses")
                continue
            validate_nll({**losses, "status": row.get("status")}, tokens, f"{name}/{split}", errors)
        if not stage:
            if row.get("optimizer_steps") != math.ceil(len(case["train_chunks"]) / 4) or isinstance(row.get("optimizer_steps"), bool):
                errors.append(f"{name}: optimizer step denominator mismatch")
            if row.get("selected_tokens") != 4096:
                errors.append(f"{name}: per-pass selected token count mismatch")
    return actual


def validate_inputs(protocol, cases, run_dir, root, model_cache, errors):
    from drift_generate import adapter_tree_digest
    from model_terminology_drift import (HISTORICAL, SCHEMA, json_sha256, tokenizer_binding, chat_input)
    from train_drift_adapters import tokenized_chunks, select_chunks
    if protocol.get("schema") != SCHEMA + "/protocol" or cases.get("schema") != SCHEMA + "/cases":
        errors.append("unsupported protocol/cases schema")
    if protocol.get("stages") != list(STAGES):
        errors.append("frozen stage contract mismatch")
    required_pairs = set(itertools.product(("flask", "pydantic", "requests"), SNAPSHOTS))
    conditions = index_rows(protocol["conditions"], ("repo", "snapshot"), "protocol condition", errors)
    selected = index_rows(cases["conditions"], ("repo", "snapshot"), "case condition", errors)
    if set(conditions) != required_pairs or set(selected) != required_pairs:
        errors.append("expected exactly six Flask/Requests/Pydantic old/new conditions")
    files = protocol["files"]
    for name, digest in sorted(files.items()):
        check_digest(root / name, digest, f"frozen input {name}", errors)
    for name in ("model_terminology_drift.py", "analyze_model_terminology_drift.py", "train_drift_adapters.py", "drift_generate.py", "drift_lexical.py"):
        key = "scripts/" + name
        if key not in files:
            errors.append(f"unbound implementing source: {key}")
        else:
            check_digest(ROOT / key, files[key], f"executing source {key}", errors)
    check_digest(run_dir / "cases.json", protocol.get("cases_sha256"), "protocol cases binding", errors)
    prepared = load_json(run_dir / "prepared.json", errors)
    expected_prepared = {"schema": SCHEMA + "/prepared",
                         "protocol_sha256": sha256((run_dir / "protocol.json").read_bytes()),
                         "cases_sha256": protocol["cases_sha256"]}
    if prepared != expected_prepared:
        errors.append("prospective prepared protocol/cases marker mismatch")
    cache = protocol["cached_model"]
    if not cache.get("files") or not any(name.endswith(".safetensors") for name in cache["files"]):
        errors.append("missing frozen base-model weights")
    tokenizer = None
    if model_cache is not None:
        for name, digest in sorted(cache["files"].items()):
            check_digest(model_cache / name, digest, f"cached model {name}", errors)
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(model_cache), local_files_only=True, trust_remote_code=False)
        if tokenizer_binding(tokenizer) != protocol["tokenizer"]:
            errors.append("cached tokenizer fingerprint differs from prospective binding")
    vocab_size = protocol["tokenizer"]["vocab_size"]
    if not positive_int(vocab_size):
        raise ValueError("invalid tokenizer vocabulary size")
    plan_path = (HISTORICAL / "training-corpora/training-plan.json").as_posix()
    plan = load_json(root / plan_path, errors)
    if plan is None:
        raise ValueError("missing frozen historical training plan")
    ledger_path = Path(plan["heldout_excerpt_ledger"]["path"])
    ledger = load_json(root / ledger_path, errors)
    sample_path = plan["source_sample_manifest"]["path"]
    sample = load_json(root / sample_path, errors)
    if ledger is None or sample is None:
        raise ValueError("missing frozen source/excerpt provenance")
    for field in ("heldout_excerpt_ledger", "source_sample_manifest"):
        if files.get(plan[field]["path"]) != plan[field]["sha256"]:
            errors.append(f"historical {field} hash binding mismatch")
    if plan_path not in files:
        errors.append("historical training plan not prospectively bound")
    ledger_conditions = index_rows(ledger["prompts"], ("repo", "snapshot"), "historical heldout", errors)
    sample_repos = {row["repo_id"]: row for row in sample["repositories"]}
    source_paths = {repo: {row["source_path"] for key, row in conditions.items() if key[0] == repo}
                    for repo in ("flask", "pydantic", "requests")}
    source_bindings = []
    for key, condition in sorted(conditions.items()):
        repo, snapshot = key
        if key not in selected:
            continue
        case = selected[key]
        heldout_ledger = ledger_conditions[key]
        for field in ("source_commit", "source_path", "source_file_sha256"):
            if condition[field] != heldout_ledger[field]:
                errors.append(f"{key}: historical heldout {field} mismatch")
        if case["heldout"]["text"] != heldout_ledger["snapshot_excerpt"] or condition["heldout_path"] != (
                ledger_path.parent / heldout_ledger["excerpt_path"]).as_posix():
            errors.append(f"{key}: prospectively selected heldout excerpt binding mismatch")
        snapshot_source = next(row for row in sample_repos[repo]["snapshots"] if row["label"] == snapshot)
        if snapshot_source["commit"] != condition["source_commit"] or files.get(condition["source_archive_path"]) != snapshot_source["archive"]["sha256"]:
            errors.append(f"{key}: frozen source archive/commit binding mismatch")
        if (root / condition["source_archive_path"]).stat().st_size != snapshot_source["archive"]["bytes"]:
            errors.append(f"{key}: frozen source archive byte count mismatch")
        for field in ("train_path", "validation_path", "heldout_path", "manifest_path", "receipt_path"):
            if condition[field] not in files:
                errors.append(f"{key}: unbound {field}")
        try:
            observed_adapter = adapter_tree_digest(root / condition["adapter_path"])
            if observed_adapter != condition["adapter_digest"]:
                errors.append(f"{key}: original adapter tree digest mismatch")
        except (OSError, ValueError) as exc:
            errors.append(f"{key}: original adapter {exc}")
        manifest = load_json(root / condition["manifest_path"], errors)
        original = load_json(root / condition["receipt_path"], errors)
        if manifest:
            if (manifest.get("repo"), manifest.get("snapshot"), manifest.get("source_commit")) != (repo, snapshot, condition["source_commit"]):
                errors.append(f"{key}: corpus source/commit mismatch")
            for split in ("train", "validation"):
                if manifest[split]["path"] != condition[f"{split}_path"] or files.get(manifest[split]["path"]) != manifest[split]["sha256"]:
                    errors.append(f"{key}: {split} manifest hash mismatch")
            inventory_path = manifest["inventory"]["path"]
            if files.get(inventory_path) != manifest["inventory"]["sha256"]:
                errors.append(f"{key}: inventory binding mismatch")
            inventory = read_jsonl(root / inventory_path, errors)
            included = {row["path"]: row["sha256"] for row in inventory if row.get("status") == "included"}
            if len(inventory) != manifest["inventory"]["rows"] or len(included) != manifest["inventory"]["included"]:
                errors.append(f"{key}: source inventory recorded counts mismatch")
            if sum(row.get("status") == "excluded" for row in inventory) != manifest["inventory"]["excluded"]:
                errors.append(f"{key}: source inventory excluded count mismatch")
            if manifest["selection"]["heldout_source_excluded"] != condition["source_path"]:
                errors.append(f"{key}: manifest heldout exclusion mismatch")
            license_path = manifest["license"]["saved_path"]
            if files.get(license_path) != manifest["license"]["saved_sha256"] or manifest["license"]["source_sha256"] != manifest["license"]["saved_sha256"]:
                errors.append(f"{key}: license binding mismatch")
        else:
            included = {}
        if original:
            for field, wanted in (("status", "complete"), ("repo", repo), ("snapshot", snapshot),
                                   ("source_commit", condition["source_commit"]), ("seed", 17),
                                   ("adapter_digest", condition["adapter_digest"]), ("base_model", protocol["base_model"])):
                if original.get(field) != wanted:
                    errors.append(f"{key}: original receipt {field} mismatch")
            if original["hyperparameters"].get("epochs") != 1 or original["token_budget"].get("train_selected_tokens") != 16384:
                errors.append(f"{key}: original one-epoch16384-token training receipt mismatch")
        for split in ("train", "validation"):
            corpus = read_jsonl(root / condition[f"{split}_path"], errors)
            if manifest and len(corpus) != manifest[split]["rows"]:
                errors.append(f"{key}/{split}: full corpus record count mismatch")
            available = {row.get("source_path") for row in corpus}
            if available & source_paths[repo]:
                errors.append(f"{key}/{split}: heldout module leaked into either snapshot corpus")
            for record in corpus:
                prefix = f"### {record['source_path']}\n"
                text = record.get("text", "")
                if not text.startswith(prefix) or sha256(text[len(prefix):].encode("utf-8")) != record.get("source_file_sha256"):
                    errors.append(f"{key}/{split}: source content digest mismatch: {record.get('source_path')}")
                if included.get(record["source_path"]) != record.get("source_file_sha256"):
                    errors.append(f"{key}/{split}: inventory source digest mismatch: {record['source_path']}")
            chunks = case[f"{split}_chunks"]
            if not chunks:
                errors.append(f"{key}/{split}: empty selected chunks")
            if tokenizer is not None:
                recomputed = select_chunks(repo, snapshot, tokenized_chunks(corpus, tokenizer, 256), token_budget=4096, max_length=256)
                recomputed = [{**chunk, "input_ids": list(chunk["input_ids"])} for chunk in recomputed]
                if recomputed != chunks:
                    errors.append(f"{key}/{split}: deterministic selected token windows mismatch")
            for chunk in chunks:
                ids = chunk["input_ids"]
                if chunk["source_path"] not in available or chunk["source_path"] in source_paths[repo]:
                    errors.append(f"{key}/{split}: invalid selected source path")
                if not isinstance(ids, list) or not 2 <= len(ids) <= 256 or not all(
                        isinstance(token, int) and not isinstance(token, bool) and 0 <= token < vocab_size for token in ids):
                    errors.append(f"{key}/{split}: invalid selected token window")
        flattened = [token for chunk in case["train_chunks"] for token in chunk["input_ids"]]
        if len(flattened) != 4096:
            errors.append(f"{key}: selected training subset is not4096 tokens")
        expected_counts = {str(token): count for token, count in Counter(flattened).items()}
        if case["unigram_counts"] != expected_counts:
            errors.append(f"{key}: unigram counts differ from identical selected training tokens")
        if case["context_input_ids"] != flattened[:512] or case["context_sha256"] != json_sha256(flattened[:512]):
            errors.append(f"{key}: prompt-only training context prefix/hash mismatch")
        if not isinstance(case["conditioning_ids"], list) or not case["conditioning_ids"] or not all(
                isinstance(token, int) and not isinstance(token, bool) and 0 <= token < vocab_size for token in case["conditioning_ids"]):
            errors.append(f"{key}: invalid prompt-only causal conditioning token IDs")
        if tokenizer is not None:
            if case["context_text"] != tokenizer.decode(flattened[:512], skip_special_tokens=False):
                errors.append(f"{key}: training context token/text mismatch")
            conditioning_text = "Training source context:\n" + case["context_text"] + "\n\nContinue the source text."
            if case["conditioning_ids"] != chat_input(tokenizer, conditioning_text):
                errors.append(f"{key}: likelihood training-context prefix mismatch")
        heldout = case["heldout"]
        if heldout["source_path"] != condition["source_path"]:
            errors.append(f"{key}: heldout source path mismatch")
        if (root / condition["heldout_path"]).read_text(encoding="utf-8") != heldout["text"]:
            errors.append(f"{key}: frozen heldout text mismatch")
        heldout_ids = heldout["input_ids"]
        if len(heldout_ids) < 2 or not all(isinstance(token, int) and not isinstance(token, bool) and 0 <= token < vocab_size for token in heldout_ids):
            errors.append(f"{key}: invalid heldout token IDs")
        if tokenizer is not None and heldout_ids != tokenizer(heldout["text"], add_special_tokens=True, truncation=False, verbose=False)["input_ids"]:
            errors.append(f"{key}: heldout text/token-ID mismatch")
        archive_path = condition["source_archive_path"]
        if archive_path not in files:
            errors.append(f"{key}: source archive not prospectively bound")
        with tarfile.open(root / archive_path, "r:*") as archive:
            members = [member for member in archive.getmembers() if member.isfile() and
                       (member.name == condition["source_path"] or member.name.endswith("/" + condition["source_path"]))]
            if len(members) != 1 or members[0].name != condition["source_archive_member"]:
                raise ValueError(f"{key}: heldout source archive member is not unique/bound")
            if archive.pax_headers.get("comment", condition["source_commit"]) != condition["source_commit"]:
                errors.append(f"{key}: source archive commit comment mismatch")
            with archive.extractfile(members[0]) as source:
                source_bytes = source.read()
        full_digest = sha256(source_bytes)
        full_text = source_bytes.decode("utf-8")
        if full_digest != condition["source_file_sha256"]:
            errors.append(f"{key}: full heldout source digest mismatch")
        if heldout.get("full_source_sha256") != full_digest or heldout.get("full_source_text") != full_text:
            errors.append(f"{key}: frozen cases full-source text/hash mismatch")
        if "\n".join(full_text.splitlines()[:80]) != heldout["text"]:
            errors.append(f"{key}: heldout excerpt is not first80 lines of source module")
        source_bindings.append({"repo": repo, "snapshot": snapshot, "source_commit": condition["source_commit"],
                                "source_path": heldout["source_path"], "excerpt_sha256": sha256(heldout["text"].encode("utf-8")),
                                "source_file_sha256": condition["source_file_sha256"], "verified_full_source_sha256": full_digest,
                                "source_archive_path": archive_path, "source_archive_member": condition["source_archive_member"],
                                "heldout_target_tokens": len(heldout_ids) - 1,
                                "selected_training_tokens": len(flattened),
                                "original_adapter_digest": condition["adapter_digest"]})
    prompts = protocol["prompts"]
    if len(prompts) != 2 or len({row["prompt_id"] for row in prompts}) != 2:
        errors.append("expected two distinct frozen source-free prompts")
    expected_prompts = {prompt["prompt_id"]: prompt["text"] for prompt in prompts}
    base_inputs = {item["prompt_id"]: item for item in cases["base_generation_inputs"]}
    for group in [cases["base_generation_inputs"], *(case["generation_inputs"] for case in cases["conditions"])]:
        for item in group:
            if not isinstance(item["input_ids"], list) or not item["input_ids"] or not all(
                    isinstance(token, int) and not isinstance(token, bool) and 0 <= token < vocab_size for token in item["input_ids"]):
                errors.append(f"{item.get('prompt_id')}: invalid generation input token IDs")
    if set(base_inputs) != set(expected_prompts):
        errors.append("base generation prompt matrix mismatch")
    for prompt_id, text in expected_prompts.items():
        if prompt_id in base_inputs and base_inputs[prompt_id]["text"] != text:
            errors.append(f"{prompt_id}: source-free generation input text mismatch")
        if tokenizer is not None and prompt_id in base_inputs and base_inputs[prompt_id]["input_ids"] != chat_input(tokenizer, text):
            errors.append(f"{prompt_id}: source-free generation text/token-ID mismatch")
    for key, case in selected.items():
        inputs = {item["prompt_id"]: item for item in case["generation_inputs"]}
        if set(inputs) != set(expected_prompts):
            errors.append(f"{key}: training-context generation prompt matrix mismatch")
        for prompt_id, text in expected_prompts.items():
            if prompt_id in inputs and inputs[prompt_id]["text"] != "Training source context:\n" + case["context_text"] + "\n\n" + text:
                errors.append(f"{key}/{prompt_id}: prompt-only input text mismatch")
            if tokenizer is not None and prompt_id in inputs and inputs[prompt_id]["input_ids"] != chat_input(tokenizer, inputs[prompt_id]["text"]):
                errors.append(f"{key}/{prompt_id}: training-context generation text/token-ID mismatch")
    return source_bindings


def validate_receipt(receipt, protocol, cases, tapes, invalid_lines, run_dir, protocol_digest, errors):
    from drift_generate import adapter_tree_digest
    from model_terminology_drift import SCHEMA
    if receipt.get("schema") != SCHEMA + "/receipt":
        errors.append("unsupported receipt schema")
    if receipt.get("status") != "complete":
        errors.append(f"execution receipt status: {receipt.get('status')}")
    if receipt.get("protocol_sha256") != protocol_digest:
        errors.append("receipt protocol hash mismatch")
    check_digest(run_dir / "cases.json", receipt.get("cases_sha256"), "receipt cases binding", errors)
    if set(receipt.get("tape_sha256", {})) != set(tapes):
        errors.append("receipt tape hash matrix mismatch")
    if set(receipt.get("counts", {})) != set(tapes):
        errors.append("receipt tape count matrix mismatch")
    for name, rows in tapes.items():
        check_digest(run_dir / name, receipt.get("tape_sha256", {}).get(name), f"receipt tape {name}", errors)
        expected_counts = {"rows": len(rows), "ok": sum(row.get("status") == "ok" for row in rows),
                           "error": sum(row.get("status") == "error" for row in rows),
                           "invalid_json_lines": invalid_lines[name]}
        if receipt.get("counts", {}).get(name) != expected_counts:
            errors.append(f"{name}: receipt observed counts mismatch")
    if receipt.get("failures") != tapes["failures.jsonl"]:
        errors.append("receipt failure ledger mismatch")
    for row in tapes["failures.jsonl"]:
        if row.get("protocol_sha256") != protocol_digest:
            errors.append("failure record protocol binding mismatch")
    if receipt.get("failures"):
        errors.append("execution failures retained: positive completeness conclusion refused")
    for field in ("total_model_wall_s", "peak_rss_gib"):
        if not finite(receipt.get(field)) or receipt[field] <= 0:
            errors.append(f"receipt invalid {field}")
    if finite(receipt.get("total_model_wall_s")) and receipt["total_model_wall_s"] > protocol["budget"]["model_wall_seconds"]:
        errors.append("prospective six-hour model wall budget exceeded")
    expected_checkpoints = {f"{case['repo']}-{case['snapshot']}/{stage}" for case in cases["conditions"] for stage in STAGES[1:]}
    if set(receipt.get("checkpoints", {})) != expected_checkpoints:
        errors.append("receipt must bind all twelve continued adapter checkpoints")
    conditions = {(row["repo"], row["snapshot"]): row for row in protocol["conditions"]}
    for case in cases["conditions"]:
        condition = conditions[(case["repo"], case["snapshot"])]
        for stage, number in (("repeat4", 4), ("repeat19", 19)):
            key = f"{case['repo']}-{case['snapshot']}/{stage}"
            directory = run_dir / "checkpoints" / key
            try:
                digest = adapter_tree_digest(directory)
                if digest != receipt.get("checkpoints", {}).get(key):
                    errors.append(f"{key}: continued checkpoint digest mismatch")
            except (OSError, ValueError) as exc:
                errors.append(f"{key}: {exc}")
            continuation = load_json(directory / "continuation.json", errors)
            wanted = {"protocol_sha256": protocol_digest, "original_adapter_digest": condition["adapter_digest"],
                      "additional_passes": number, "selected_tokens": 4096}
            if continuation != wanted:
                errors.append(f"{key}: checkpoint continuation receipt mismatch")


def validate_fixed_settings(protocol, errors):
    from train_drift_adapters import BASE_MODEL, BASE_REVISION
    from model_terminology_drift import PROMPTS
    if protocol["base_model"] != {"id": BASE_MODEL, "revision": BASE_REVISION}:
        errors.append("pinned360M base model/revision mismatch")
    revision = protocol.get("source_revision", "")
    if not isinstance(revision, str) or len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        errors.append("invalid frozen source revision")
    expected_training = {"seed": 17, "additional_passes": 19, "checkpoint_passes": [4, 19],
                         "train_token_budget": 4096, "validation_token_budget": 4096,
                         "max_sequence_length": 256, "batch_size": 1, "gradient_accumulation": 4,
                         "learning_rate": 0.0002, "weight_decay": 0.01, "max_gradient_norm": 1.0}
    for field, expected in expected_training.items():
        if protocol["training"].get(field) != expected:
            errors.append(f"frozen training setting mismatch: {field}")
    for field, expected in {"seeds": [17, 29, 43], "max_new_tokens": 96, "temperature": 0.7, "top_p": 0.9}.items():
        if protocol["generation"].get(field) != expected:
            errors.append(f"frozen generation setting mismatch: {field}")
    for field, expected in {"shuffle_seed": 17, "unigram_alpha": 1.0, "prompt_context_tokens": 512,
                            "likelihood_context_tokens": 2048, "likelihood_target_block_tokens": 1024}.items():
        if protocol["controls"].get(field) != expected:
            errors.append(f"frozen control setting mismatch: {field}")
    for field, expected in {"device": "cpu", "dtype": "float32", "threads": 4, "local_files_only": True}.items():
        if protocol["runtime"].get(field) != expected:
            errors.append(f"frozen runtime setting mismatch: {field}")
    if protocol["budget"].get("model_wall_seconds") != 21600:
        errors.append("prospective model budget must be21600s")
    if protocol["prompts"] != PROMPTS:
        errors.append("source-free prompt text differs from frozen runner definition")


def validate_control_consistency(rows, cases, protocol, errors):
    from model_terminology_drift import likelihood_input
    conditions = {(case["repo"], case["snapshot"]): case for case in cases["conditions"]}
    index = {(row["repo"], row["stage"], row["model_snapshot"], row["target_snapshot"], row["control"], row["arm"]): row for row in rows}
    for case in cases["conditions"]:
        original = likelihood_input(None, case, "base", "original")["input_ids"]
        shuffled = likelihood_input(None, case, "base", "token_shuffle")["input_ids"]
        if original[0] != shuffled[0] or Counter(original[1:]) != Counter(shuffled[1:]):
            errors.append(f"{case['repo']}/{case['snapshot']}: shuffle changed the exact scored causal-token multiset")
    for row in rows:
        if row.get("status") != "ok":
            continue
        target = conditions[(row["repo"], row["target_snapshot"])]
        if row["arm"] == "unigram":
            model = conditions[(row["repo"], row["model_snapshot"])]
            ids = likelihood_input(model, target, "unigram", row["control"])["input_ids"]
            counts = model["unigram_counts"]
            alpha = protocol["controls"]["unigram_alpha"]
            denominator = sum(counts.values()) + alpha * protocol["tokenizer"]["vocab_size"]
            expected = math.fsum(-math.log((counts.get(str(token), 0) + alpha) / denominator) for token in ids[1:])
            if not math.isclose(row["nll_sum"], expected, rel_tol=1e-9, abs_tol=1e-9):
                errors.append(f"unigram {row['repo']}/{row['model_snapshot']}/{row['target_snapshot']}/{row['control']}: independently recomputed NLL mismatch")
            counterpart = index.get((row["repo"], "shared", row["model_snapshot"], row["target_snapshot"],
                                     "token_shuffle" if row["control"] == "original" else "original", "unigram"))
            if counterpart and counterpart.get("status") == "ok" and not math.isclose(
                    row["nll_sum"], counterpart["nll_sum"], rel_tol=1e-9, abs_tol=1e-9):
                errors.append(f"{row['repo']}/{row['model_snapshot']}/{row['target_snapshot']}: token-shuffled unigram NLL is not order-invariant")
    for repo in ("flask", "pydantic", "requests"):
        old, new = conditions[(repo, "old")], conditions[(repo, "new")]
        identical = old["heldout"]["text"] == new["heldout"]["text"]
        if (repo == "requests") != identical:
            errors.append(f"{repo}: pre-output changed/unchanged heldout source classification mismatch")
        if not identical:
            continue
        if old["heldout"]["input_ids"] != new["heldout"]["input_ids"]:
            errors.append(f"{repo}: identical heldout source has different frozen input IDs")
        for stage, model, control, arm in itertools.product(("shared", *STAGES), ("shared", *SNAPSHOTS), SOURCE_CONTROLS, ARMS):
            a = index.get((repo, stage, model, "old", control, arm))
            b = index.get((repo, stage, model, "new", control, arm))
            if a and b and a.get("status") == b.get("status") == "ok" and a["nll_sum"] != b["nll_sum"]:
                errors.append(f"{repo}/{stage}/{model}/{control}/{arm}: identical target inputs have unequal causal NLL")


def analyze(run_dir, input_root=None, model_cache=None):
    run_dir = Path(run_dir).resolve()
    input_root = Path(input_root).resolve() if input_root is not None else ROOT
    model_cache = Path(model_cache).resolve() if model_cache is not None else None
    errors = []
    protocol = load_json(run_dir / "protocol.json", errors)
    cases = load_json(run_dir / "cases.json", errors)
    receipt = load_json(run_dir / "receipt.json", errors)
    tape_names = ("likelihood.jsonl", "generations.jsonl", "training.jsonl", "failures.jsonl")
    invalid_lines = {name: [] for name in tape_names}
    tapes = {name: read_jsonl(run_dir / name, errors, invalid_lines[name]) for name in tape_names}
    protocol_digest = check_digest(run_dir / "protocol.json", receipt.get("protocol_sha256") if receipt else None, "protocol execution binding", errors)
    report = {
        "schema": "tiny-fleet.model-terminology-drift-analysis/v1",
        "run_dir": str(run_dir), "protocol_sha256": protocol_digest,
        "resolved_input_root": str(input_root),
        "completeness_scope": "Frozen repository inputs, source archives/full modules, prepared cases and all scientific tapes/training/checkpoints. Optional cache-byte/tokenizer re-verification is separately reported; no model is loaded or called.",
        "model_cache_verification": {
            "requested": model_cache is not None, "resolved_cache": str(model_cache) if model_cache is not None else None,
            "status": "PENDING" if model_cache is not None else "NOT_CHECKED",
            "frozen_file_hashes": protocol.get("cached_model", {}).get("files", {}) if protocol else {},
            "limitation": "Tape-only analysis verifies the frozen token-ID/hash bindings, not physical base-model/tokenizer bytes or text-to-ID re-encoding. Use --model-cache PATH to verify all cached hashes, tokenizer fingerprint and deterministic source/token mappings without a model call."},
        "cases_sha256": sha256((run_dir / "cases.json").read_bytes()) if (run_dir / "cases.json").is_file() else None,
        "receipt_sha256": sha256((run_dir / "receipt.json").read_bytes()) if (run_dir / "receipt.json").is_file() else None,
        "analysis_source_sha256": sha256(Path(__file__).read_bytes()),
        "observed_tapes": observed_tapes(tapes), "source_bindings": [],
        "likelihood": None, "generation_lexical": None, "repeated_fitting": None,
        "token_shuffle_definition": "Keep the first unscored source token fixed and seed17-shuffle only causal target IDs[1:]; exact scored-token multiset is preserved, so unigram NLL is an order-invariant control.",
        "limits": [
            "Three purposively chosen repositories, one heldout module per snapshot, one training seed17; no population or training-seed generalization.",
            "Requests is a byte-identical heldout-excerpt negative control, not a third changed source pair; Flask/Pydantic changed-pair discrimination is reported separately.",
            "All eight repository-level old/new label sign flips are enumerated. The nominal floor1/8 is not attainable with a zero unit: actual floor1/4 with two nonzero effects, or higher when effects are zero/tied.",
            "Heldout source NLL can reflect syntax/style, code-vs-docstring/English composition and formatting, not terminology alone.",
            "All-token lexical delta alignment/coverage is descriptive source alignment, not precision/recall of true concepts, human semantic validity or causal terminology drift.",
            "No semantic/domain labels or human adjudication exist; semantic terminology precision is unmeasured.",
            "Unknown base-model pretraining contamination; corpus holdout does not imply pretraining holdout.",
            "Training-context prompt-only uses the first512 selected training tokens, never the heldout target; its shared controls and global base generation are explicitly reused.",
            "Correlated chunks and sampled decode seeds17/29/43 are not independent source units or training replications.",
            "Fresh AdamW optimizer; original16k adaptation plus4/19 repeated passes on an identical selected4k subset, not5/20 full-corpus epochs.",
            "Errors, unexecuted cells, empty outputs, caps and zero-vocabulary/zero-delta outcomes are retained. No imputation, output cleaning, stopword removal or selected terms.",
            "Hashes establish internal frozen-file/tape consistency, not authenticated provenance or proof that a receipt attests actual execution.",
            "Default relocation-safe tape analysis does not re-open the original private absolute model cache. Missing optional cache bytes are not represented as verified; --model-cache requests strict re-verification and fails closed.",
        ],
        "semantic_terminology_precision": None, "statistical_superiority_claim": False,
        "positive_usefulness_claim": False,
    }
    if protocol and cases and receipt:
        try:
            from model_terminology_drift import expected_likelihood_rows, expected_generation_rows
            validate_fixed_settings(protocol, errors)
            report["source_bindings"] = validate_inputs(protocol, cases, run_dir, input_root, model_cache, errors)
            if model_cache is not None:
                report["model_cache_verification"]["status"] = "verified" if not errors else "failed"
            expected_likelihood = expected_likelihood_rows(protocol, cases)
            expected_generation = expected_generation_rows(protocol, cases)
            report["expected_counts"] = {"likelihood.jsonl": len(expected_likelihood), "generations.jsonl": len(expected_generation),
                                         "training.jsonl": len(cases["conditions"]) * 22, "continued_checkpoints": len(cases["conditions"]) * 2}
            validate_matrix(tapes["likelihood.jsonl"], expected_likelihood,
                            ("repo", "stage", "model_snapshot", "target_snapshot", "control", "arm"), "likelihood", protocol_digest, errors)
            validate_matrix(tapes["generations.jsonl"], expected_generation,
                            ("repo", "snapshot", "stage", "arm", "prompt_id", "decode_id"), "generation", protocol_digest, errors)
            validate_training(tapes["training.jsonl"], cases, protocol_digest, errors)
            validate_receipt(receipt, protocol, cases, tapes, invalid_lines, run_dir, protocol_digest, errors)
            for row in tapes["generations.jsonl"]:
                if row.get("status") != "ok":
                    continue
                maximum = protocol["generation"]["max_new_tokens"]
                if row["generated_tokens"] > maximum or row["cap_hit"] != (row["generated_tokens"] >= maximum):
                    errors.append(f"generation {row.get('repo')}/{row.get('decode_id')}: token cap/count mismatch")
                if row.get("empty_output") != (not bool(row["output"].strip())):
                    errors.append(f"generation {row.get('repo')}/{row.get('decode_id')}: empty-output flag mismatch")
            if not errors:
                validate_control_consistency(tapes["likelihood.jsonl"], cases, protocol, errors)
            report["execution_costs"] = {field: receipt.get(field) for field in ("total_model_wall_s", "peak_rss_gib")}
            report["execution_costs"]["observation_limit"] = "Receipt wall time and summed finite row elapsed times are reported, not hypothetical GPU/savings claims. Error placeholders for unexecuted cells have zero elapsed time and are not model calls."
            report["source_revision"] = protocol["source_revision"]
            if not errors:
                repositories = ["flask", "pydantic", "requests"]
                report["likelihood"] = likelihood_summary(tapes["likelihood.jsonl"], repositories, cases)
                report["generation_lexical"] = generation_summary(tapes["generations.jsonl"], cases, protocol, repositories)
                report["repeated_fitting"] = training_summary(tapes["training.jsonl"], tapes["likelihood.jsonl"])
        except (OSError, ValueError, KeyError, TypeError, ImportError, ArithmeticError, tarfile.TarError) as exc:
            errors.append(f"analysis refused: {type(exc).__name__}: {exc}")
    report["errors"] = errors
    if model_cache is not None and report["model_cache_verification"]["status"] == "PENDING":
        report["model_cache_verification"]["status"] = "FAILED"
    report["complete"] = not errors
    report["status"] = "complete" if report["complete"] else "incomplete"
    report["direct_answer"] = "No positive instrument result is admissible: required source/hash, denominator, tape, training or checkpoint completeness validation failed. Failures and observed counts/costs remain visible; performance metrics are withheld rather than imputing success."
    if report["complete"]:
        stages = [cell for cell in report["likelihood"]["cells"] if cell["source_control"] == "original"]
        report["descriptive_findings"] = [
            {"stage": cell["stage"], "changed_pair_accuracy": {arm: values["changed_source_pair_mean_accuracy"] for arm, values in cell["arms"].items()},
             "all_repository_accuracy": {arm: values["mean_balanced_snapshot_accuracy"] for arm, values in cell["arms"].items()},
             "all_repository_mean_diagonal_preference": cell["arms"]["lora"]["diagonal_sign_flips"]["observed_mean"],
             "sign_flip_one_sided_p": cell["arms"]["lora"]["diagonal_sign_flips"]["one_sided_p"],
             "actual_attainable_p_floor": cell["arms"]["lora"]["diagonal_sign_flips"]["attainable_one_sided_p_floor"]}
            for cell in stages]
        final = next(cell for cell in stages if cell["stage"] == "repeat19")
        accuracies = final["arms"]
        final_training = [row for row in report["repeated_fitting"]["diagnostic_comparisons"] if row["stage"] == "repeat19"]
        report["direct_answer"] = (
            f"Usefulness and semantic terminology precision are not established. After19 additional selected-subset passes, changed-pair balanced snapshot accuracy was {accuracies['lora']['changed_source_pair_mean_accuracy']:.3f}, versus base {accuracies['base']['changed_source_pair_mean_accuracy']:.3f}, training-context prompt-only {accuracies['prompt-only']['changed_source_pair_mean_accuracy']:.3f} and unigram {accuracies['unigram']['changed_source_pair_mean_accuracy']:.3f}. "
            f"Selected-train loss improved in {sum(row['train_improved'] for row in final_training)}/6 adapters; {sum(row['observed_overfit_to_selected_subset'] for row in final_training)}/6 showed train decrease with heldout increase. "
            "These are descriptive source-discrimination and fitting outcomes, not human semantic precision or causal terminology effects. Requests is an unchanged-excerpt control; two changed pairs cannot establish statistical superiority. All-token lexical alignment and shuffle/control contrasts are reported without term selection."
        )
    if errors:
        report["likelihood"] = report["generation_lexical"] = report["repeated_fitting"] = None
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--input-root", type=Path, default=ROOT, help="Repository containing frozen repo-relative inputs; defaults to this script's repository, never the original absolute site path.")
    parser.add_argument("--model-cache", type=Path, help="Optional local pinned HF snapshot directory: strictly re-verify all cache bytes/tokenizer mappings, without loading or calling a model.")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"refusing to overwrite existing output: {args.output}")
    report = analyze(args.run_dir, args.input_root, args.model_cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    except FileExistsError:
        parser.error(f"refusing to overwrite existing output: {args.output}")
    print(json.dumps({"status": report["status"], "complete": report["complete"], "errors": len(report["errors"]),
                      "output": str(args.output)}, sort_keys=True), flush=True)
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
