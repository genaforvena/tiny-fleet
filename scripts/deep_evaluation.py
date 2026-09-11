#!/usr/bin/env python3
"""Dependency-free validator for a frozen tiny-fleet evaluation run."""

import argparse
import hashlib
import json
import re
import math
from collections import Counter
import unicodedata
from datetime import datetime
from pathlib import Path


REQUIRED = (
    "config.json", "environment.txt", "predictions.jsonl", "scores.json",
    "slices.tsv", "calibration.tsv", "routing.tsv", "adversarial.tsv",
    "cost.tsv", "decision.md",
)
SPLITS = ("train", "validation", "heldout", "adversarial")
ROW_FIELDS = (
    "case_id", "source_id", "created_at", "domain", "language", "split",
    "expected_route", "expected_action", "prompt", "reference", "source_family", "provenance",
)


class ValidationError(ValueError):
    """A stable, operator-facing contract rejection."""


def reject(category, detail):
    raise ValidationError(f"REJECT {category} {detail}".rstrip())


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path, category="manifest-mismatch"):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        reject(category, f"{path.name}: {exc}")


def load_rows(path, expected_split):
    rows = []
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        reject("missing-artifact", path.name)
    for line_no, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            reject("manifest-mismatch", f"{path.name}:{line_no}: {exc}")
        missing = [field for field in ROW_FIELDS if field not in row]
        if missing:
            reject("manifest-mismatch", f"{path.name}:{line_no}: missing {','.join(missing)}")
        if row["split"] != expected_split:
            reject("split-boundary", f"{row['case_id']} declares {row['split']} in {expected_split}")
        if not isinstance(row["case_id"], str) or not row["case_id"]:
            reject("manifest-mismatch", f"{path.name}:{line_no}: case_id")
        for field in ("source_id", "domain", "language", "prompt", "reference", "source_family"):
            if not isinstance(row[field], str) or not row[field].strip():
                reject("manifest-mismatch", f"{path.name}:{line_no}: {field}")
        rows.append(row)
    return rows


def parse_timestamp(value, label):
    if not isinstance(value, str) or not re.search(r"(?:Z|[+-]\d\d:\d\d)$", value):
        reject("split-boundary", f"{label} must be timezone-aware")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        reject("split-boundary", f"{label} invalid timestamp")


def normalize_prompt(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def require_text(value, label):
    if not isinstance(value, str) or not value:
        reject("prediction-schema", f"{label} must be a nonempty string")


def require_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        reject("prediction-schema", f"{label} must be an integer")


def require_digest(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        reject("prediction-schema", f"{label} must be a SHA-256 digest")


def validate_prediction(prediction, row_by_case, models, seeds, repetitions):
    required = ("case_id", "model", "seed", "repetition", "case_prompt_sha256",
                "rendered_input", "rendered_input_sha256", "output", "route", "action",
                "confidence", "confidence_kind", "latency_ms", "status")
    missing = [field for field in required if field not in prediction]
    if missing:
        reject("prediction-schema", f"missing {','.join(missing)}")
    case_id = prediction["case_id"]
    model = prediction["model"]
    require_text(case_id, "case_id")
    require_text(model, "model")
    if case_id not in row_by_case:
        reject("prediction-cardinality", f"unknown case_id={case_id}")
    if model not in models:
        reject("prediction-cardinality", f"unknown model={model}")
    require_int(prediction["seed"], "seed")
    require_int(prediction["repetition"], "repetition")
    if prediction["seed"] not in seeds or prediction["repetition"] not in repetitions:
        reject("prediction-cardinality", f"extra key ({case_id},{model},{prediction['seed']},{prediction['repetition']})")
    require_digest(prediction["case_prompt_sha256"], "case_prompt_sha256")
    require_text(prediction["rendered_input"], "rendered_input")
    require_digest(prediction["rendered_input_sha256"], "rendered_input_sha256")
    row = row_by_case[case_id]
    expected_prompt_hash = hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest()
    if prediction["case_prompt_sha256"] != expected_prompt_hash:
        reject("prediction-input", f"case_prompt_sha256 for {case_id}")
    rendered_hash = hashlib.sha256(prediction["rendered_input"].encode("utf-8")).hexdigest()
    if prediction["rendered_input_sha256"] != rendered_hash:
        reject("prediction-input", f"rendered_input_sha256 for {case_id}/{model}")
    if row["reference"] and row["reference"] in prediction["rendered_input"] and not prediction.get("reference_overlap_justification"):
        reject("prediction-input", f"reference leaked into rendered_input for {case_id}/{model}")
    status = prediction["status"]
    if status not in {"ok", "timeout", "error"}:
        reject("prediction-schema", f"status {status!r}")
    if status == "ok" and prediction["output"] is None:
        reject("prediction-schema", "output required for status=ok")
    if status != "ok" and prediction["output"] is not None and not isinstance(prediction["output"], str):
        reject("prediction-schema", "output must be string or null")
    if status != "ok" and not isinstance(prediction.get("unavailable_reason"), str):
        reject("prediction-schema", "unavailable_reason required for failed status")
    if prediction["confidence"] is not None:
        if isinstance(prediction["confidence"], bool) or not isinstance(prediction["confidence"], (int, float)) or not math.isfinite(prediction["confidence"]):
            reject("prediction-schema", "confidence must be finite or null")
        if not 0 <= prediction["confidence"] <= 1:
            reject("prediction-schema", "confidence must be between 0 and 1")
        require_text(prediction["confidence_kind"], "confidence_kind")
    elif not isinstance(prediction.get("unavailable_reason"), str):
        reject("prediction-schema", "confidence null requires unavailable_reason")
    if prediction["latency_ms"] is not None:
        if isinstance(prediction["latency_ms"], bool) or not isinstance(prediction["latency_ms"], (int, float)) or not math.isfinite(prediction["latency_ms"]):
            reject("prediction-schema", "latency must be finite or null")
        if prediction["latency_ms"] < 0:
            reject("prediction-schema", "latency must be nonnegative")
    elif not isinstance(prediction.get("unavailable_reason"), str):
        reject("prediction-schema", "latency null requires unavailable_reason")
    require_text(prediction["route"], "route")
    require_text(prediction["action"], "action")


def validate_run(run_dir):
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        reject("missing-artifact", "manifest.json")
    manifest = load_json(manifest_path)
    if manifest.get("schema") not in {"tiny-fleet.deep-eval.manifest/v1", "tiny-fleet.deep-eval.manifest/v2"}:
        reject("manifest-mismatch", "schema")
    if manifest.get("schema") != "tiny-fleet.deep-eval.manifest/v2":
        reject("manifest-mismatch", "legacy v1 is archival-only")
    for name in REQUIRED:
        if not (run_dir / name).is_file():
            reject("missing-artifact", name)
    config_hash = sha256(run_dir / "config.json")
    if manifest.get("config_sha256") != config_hash:
        reject("manifest-mismatch", f"config.json sha256 expected={manifest.get('config_sha256')} observed={config_hash}")
    if isinstance(manifest.get("seed"), bool) or not isinstance(manifest.get("seed"), int):
        reject("manifest-mismatch", "seed must be an integer")
    datasets = manifest.get("datasets", {})
    candidate = manifest.get("candidate")
    base_model = manifest.get("base_model")
    if not isinstance(base_model, dict) or not base_model.get("id") or not base_model.get("revision"):
        reject("manifest-mismatch", "base_model")
    if not isinstance(candidate, dict) or not candidate.get("id") or not candidate.get("revision"):
        reject("manifest-mismatch", "candidate")
    require_digest(candidate["revision"], "candidate.revision")
    controls = manifest.get("controls")
    if not isinstance(controls, list) or any(not isinstance(model, str) or not model for model in controls):
        reject("manifest-mismatch", "controls")
    if len(set(controls)) != len(controls):
        reject("manifest-mismatch", "duplicate model in controls")
    models = controls + [candidate["id"]]
    if len(set(models)) != len(models):
        reject("manifest-mismatch", "duplicate model id")
    matrix = manifest.get("prediction_matrix")
    if not isinstance(matrix, dict):
        reject("manifest-mismatch", "prediction_matrix")
    matrix_models = matrix.get("models")
    seeds = matrix.get("seeds")
    repetitions = matrix.get("repetitions")
    if isinstance(matrix_models, list) and len(set(matrix_models)) != len(matrix_models):
        reject("manifest-mismatch", "duplicate model in prediction_matrix")
    if matrix_models != models or not isinstance(seeds, list) or not isinstance(repetitions, list) or not seeds or not repetitions:
        reject("manifest-mismatch", "prediction_matrix does not match declared models")
    if any(isinstance(x, bool) or not isinstance(x, int) for x in seeds + repetitions):
        reject("manifest-mismatch", "prediction_matrix types or duplicates")
    raw_schema = manifest.get("raw_output_schema")
    if not isinstance(raw_schema, str) or not raw_schema:
        reject("manifest-mismatch", "raw_output_schema")
    migration = manifest.get("migration_report")
    if not isinstance(migration, dict) or not isinstance(migration.get("status"), str):
        reject("manifest-mismatch", "migration_report")
    rendering = manifest.get("rendering")
    if not isinstance(rendering, dict):
        reject("manifest-mismatch", "rendering")
    require_digest(rendering.get("template_sha256"), "rendering.template_sha256")
    if rendering.get("config_sha256") != config_hash:
        reject("manifest-mismatch", "rendering.config_sha256")
    for artifact in manifest.get("model_artifacts", []):
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            reject("manifest-mismatch", "model_artifacts")
        require_digest(artifact.get("sha256"), "model_artifacts.sha256")
        artifact_path = (run_dir / artifact["path"]).resolve()
        try:
            artifact_path.relative_to(run_dir.resolve())
        except ValueError:
            reject("manifest-mismatch", f"model artifact outside run: {artifact['path']}")
        if not artifact_path.is_file() or sha256(artifact_path) != artifact["sha256"]:
            reject("manifest-mismatch", f"model artifact hash: {artifact['path']}")
    all_rows = []
    cutoff = manifest.get("cutoff")
    cutoff_dt = parse_timestamp(cutoff, "cutoff")
    temporal = manifest.get("temporal")
    if not isinstance(temporal, dict):
        reject("manifest-mismatch", "temporal")
    train_end = parse_timestamp(temporal.get("train_end"), "train_end")
    heldout_start = parse_timestamp(temporal.get("heldout_start"), "heldout_start")
    if train_end > heldout_start:
        reject("split-boundary", "contradictory temporal windows")
    for split in SPLITS:
        spec = datasets.get(split)
        if not isinstance(spec, dict) or not spec.get("path"):
            reject("manifest-mismatch", f"datasets.{split}")
        if not isinstance(spec["path"], str) or Path(spec["path"]).is_absolute():
            reject("manifest-mismatch", f"dataset outside run: {spec.get('path')}")
        path = (run_dir / spec["path"]).resolve()
        try:
            path.relative_to(run_dir.resolve())
        except ValueError:
            reject("manifest-mismatch", f"dataset outside run: {spec['path']}")
        if not path.is_file():
            reject("missing-artifact", spec["path"])
        rows = load_rows(path, split)
        if not rows:
            reject("manifest-mismatch", f"empty {split}")
        observed_hash = sha256(path)
        if spec.get("sha256") != observed_hash:
            reject("manifest-mismatch", f"{spec['path']} sha256 expected={spec.get('sha256')} observed={observed_hash}")
        if spec.get("rows") != len(rows):
            reject("manifest-mismatch", f"{spec['path']} rows expected={spec.get('rows')} observed={len(rows)}")
        for row in rows:
            created = parse_timestamp(row["created_at"], row["case_id"])
            if created > cutoff_dt:
                reject("split-boundary", f"{row['case_id']} after cutoff {cutoff}")
            if split == "train" and created > train_end:
                reject("split-boundary", f"{row['case_id']} after train_end")
            if split == "heldout" and created < heldout_start:
                reject("split-boundary", f"{row['case_id']} before heldout_start")
            if split in ("heldout", "adversarial") and created > cutoff_dt:
                reject("split-boundary", f"{row['case_id']} after cutoff {cutoff}")
            row["_split_file"] = split
        all_rows.extend(rows)
    by_case = {}
    by_source = {}
    by_family = {}
    seen_ids = set()
    for row in all_rows:
        case = row["case_id"]
        split = row["_split_file"]
        if (split, case) in seen_ids:
            reject("manifest-mismatch", f"duplicate case_id={case} in {split}")
        seen_ids.add((split, case))
        if case in by_case and by_case[case]["_split_file"] != row["_split_file"]:
            reject("leakage", f"case_id={case} crosses {by_case[case]['_split_file']}/{row['_split_file']}")
        by_case[case] = row
        by_source.setdefault(row["source_id"], set()).add(row["_split_file"])
        by_family.setdefault(row["source_family"], set()).add(split)
    for family, splits in by_family.items():
        if ("train" in splits and "validation" in splits) or ("validation" in splits and "heldout" in splits):
            reject("split-boundary", f"source_family={family} crosses {'/'.join(sorted(splits))}")
    for source, splits in by_source.items():
        if "train" in splits and any(split in splits for split in ("heldout", "adversarial")):
            reject("split-boundary", f"source_id={source} crosses {'/'.join(sorted(splits))}")
    texts = {}
    for row in all_rows:
        text = normalize_prompt(row["prompt"])
        if text in texts and texts[text]["_split_file"] != row["_split_file"]:
            reject("leakage", f"normalized prompt crosses {texts[text]['_split_file']}/{row['_split_file']}")
        texts[text] = row
    evaluation_rows = [row for row in all_rows if row["_split_file"] in ("heldout", "adversarial")]
    row_by_case = {row["case_id"]: row for row in evaluation_rows}
    expected = [(row["case_id"], model, seed, repetition) for row in evaluation_rows
                for model in models for seed in seeds for repetition in repetitions]
    observed = []
    for line in (run_dir / "predictions.jsonl").read_text().splitlines():
        try:
            prediction = json.loads(line)
        except json.JSONDecodeError as exc:
            reject("prediction-schema", str(exc))
        validate_prediction(prediction, row_by_case, models, seeds, repetitions)
        observed.append((prediction["case_id"], prediction["model"], prediction["seed"], prediction["repetition"]))
    counts = Counter(observed)
    duplicates = [key for key, count in counts.items() if count > 1]
    if duplicates:
        reject("prediction-cardinality", f"duplicate {duplicates[0]}")
    if Counter(observed) != Counter(expected):
        reject("prediction-cardinality", f"expected={len(expected)} observed={len(observed)}")
    return "ACCEPT"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    try:
        print(validate_run(args.run_dir))
    except ValidationError as exc:
        print(exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
