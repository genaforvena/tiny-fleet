#!/usr/bin/env python3
"""Dependency-free validator for the derived report bundle."""

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

from deep_evaluation import ValidationError, validate_run


REPORTS = (
    "scores.json", "slices.tsv", "calibration.tsv", "routing.tsv",
    "adversarial.tsv", "cost.tsv", "decision.md",
)
HEADERS = {
    "slices.tsv": ("slice", "value", "count", "scored", "correct", "accuracy"),
    "calibration.tsv": ("bin", "count", "confidence_sum", "correct", "ece", "brier"),
    "routing.tsv": ("case_id", "model", "seed", "repetition", "expected_route", "actual_route", "decision"),
    "adversarial.tsv": ("case_id", "model", "seed", "repetition", "expected_action", "actual_action", "forbidden_output", "reviewed"),
    "cost.tsv": ("metric", "value", "unit", "count"),
}


def reject(category, detail):
    raise ValidationError(f"REJECT {category} {detail}".rstrip())


def finite(value, label, nonnegative=True):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        reject("report-schema", f"{label} must be finite")
    if nonnegative and value < 0:
        reject("report-schema", f"{label} must be nonnegative")
    return value


def integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        reject("report-schema", f"{label} must be a nonnegative integer")
    return value


def parse_integer(value, label):
    try:
        return integer(int(value), label)
    except (TypeError, ValueError):
        reject("report-schema", f"{label} must be a nonnegative integer")


def parse_number(value, label):
    try:
        return finite(float(value), label)
    except (TypeError, ValueError):
        reject("report-schema", f"{label} must be finite")


def load_scores(path):
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        reject("report-schema", f"scores.json {exc}")
    if not isinstance(value, dict) or value.get("schema") != "tiny-fleet.deep-eval.scores/v1":
        reject("report-schema", "scores.json schema")
    if value.get("result_status") not in {"positive", "negative", "inconclusive", "failed"}:
        reject("report-schema", "scores.json result_status")
    for field in ("total_predictions", "scored_predictions", "correct_predictions", "false_accepts"):
        integer(value.get(field), f"scores.{field}")
    finite(value.get("accuracy"), "scores.accuracy")
    return value


def load_tsv(path, name):
    try:
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != HEADERS[name]:
                reject("report-schema", f"{name} headers")
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        reject("report-schema", f"{name} {exc}")
    if not rows:
        reject("report-schema", f"{name} empty")
    if any(any(value == "" for value in row.values()) for row in rows):
        reject("report-schema", f"{name} empty field")
    return rows


def parse_key(row, name):
    try:
        return (row["case_id"], row["model"], int(row["seed"]), int(row["repetition"]))
    except (KeyError, ValueError) as exc:
        reject("report-schema", f"{name} key {exc}")


def parse_decision(path):
    try:
        text = path.read_text()
    except OSError as exc:
        reject("report-schema", f"decision.md {exc}")
    result = re.search(r"^result_status:\s*(\w+)\s*$", text, re.MULTILINE)
    eligible = re.search(r"^routing_eligible:\s*(true|false)\s*$", text, re.MULTILINE)
    coverage = re.search(r"^coverage:\s*([0-9]+(?:\.[0-9]+)?)\s*$", text, re.MULTILINE)
    if not result or not eligible or not coverage:
        reject("report-schema", "decision.md required fields")
    return result.group(1), eligible.group(1) == "true", finite(float(coverage.group(1)), "decision.coverage")


def validate_reports(run_dir):
    run_dir = Path(run_dir)
    for name in REPORTS:
        if not (run_dir / name).is_file():
            reject("report-missing", name)
    scores = load_scores(run_dir / "scores.json")
    tables = {name: load_tsv(run_dir / name, name) for name in HEADERS}
    decision_status, decision_eligible, decision_coverage = parse_decision(run_dir / "decision.md")
    if decision_status != scores["result_status"]:
        reject("report-reconciliation", "decision result_status")

    if validate_run(run_dir) != "ACCEPT":
        reject("raw-validation", "deep evaluation rejected raw artifacts")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    models = manifest["prediction_matrix"]["models"]
    seeds = manifest["prediction_matrix"]["seeds"]
    repetitions = manifest["prediction_matrix"]["repetitions"]
    expected_keys = set()
    expected_routes = {}
    expected_actions = {}
    references = {}
    adversarial_cases = set()
    for split in ("heldout", "adversarial"):
        path = run_dir / manifest["datasets"][split]["path"]
        for line in path.read_text().splitlines():
            row = json.loads(line)
            case = row["case_id"]
            if split == "adversarial":
                adversarial_cases.add(case)
            expected_routes[case] = row["expected_route"]
            expected_actions[case] = row["expected_action"]
            references[case] = row["reference"]
            expected_keys.update((case, model, seed, repetition)
                                 for model in models for seed in seeds for repetition in repetitions)

    predictions = {}
    for line in (run_dir / "predictions.jsonl").read_text().splitlines():
        prediction = json.loads(line)
        predictions[parse_key(prediction, "predictions.jsonl")] = prediction
    scored = [p for p in predictions.values() if p["status"] == "ok"]
    correct = sum(p["output"] == references[p["case_id"]] for p in scored)
    false_accepts = sum(p["case_id"] in adversarial_cases and p["action"] != expected_actions[p["case_id"]]
                        for p in scored)
    actual_keys = set(predictions)
    if actual_keys != expected_keys:
        reject("report-cardinality", "raw prediction keys")
    expected_count = len(expected_keys)
    for field, observed in (("total_predictions", expected_count),
                            ("scored_predictions", len(scored)),
                            ("correct_predictions", correct),
                            ("false_accepts", false_accepts)):
        if scores[field] != observed:
            reject("report-reconciliation", f"{field} expected={observed} observed={scores[field]}")
    expected_accuracy = correct / len(scored) if scored else 0.0
    if not math.isclose(scores["accuracy"], expected_accuracy, rel_tol=0, abs_tol=1e-12):
        reject("report-reconciliation", "accuracy")
    expected_coverage = len(scored) / expected_count
    if not math.isclose(decision_coverage, expected_coverage, rel_tol=0, abs_tol=1e-12):
        reject("report-reconciliation", "decision coverage")
    if not scored and decision_eligible:
        reject("report-quality", "all predictions abstain but routing is eligible")

    expected_routing = actual_keys
    routing = {parse_key(row, "routing.tsv"): row for row in tables["routing.tsv"]}
    if set(routing) != expected_routing or len(routing) != len(tables["routing.tsv"]):
        reject("report-cardinality", "routing.tsv")
    for key, row in routing.items():
        prediction = predictions[key]
        case = key[0]
        if (row["expected_route"], row["actual_route"], row["decision"]) != (
                expected_routes[case], prediction["route"], prediction["action"]):
            reject("report-reconciliation", f"routing {key}")

    expected_adversarial = {key for key in expected_keys if key[0] in adversarial_cases}
    adversarial = {parse_key(row, "adversarial.tsv"): row for row in tables["adversarial.tsv"]}
    if set(adversarial) != expected_adversarial or len(adversarial) != len(tables["adversarial.tsv"]):
        reject("report-cardinality", "adversarial.tsv")
    for key, row in adversarial.items():
        prediction = predictions[key]
        if row["expected_action"] != expected_actions[key[0]] or row["actual_action"] != prediction["action"]:
            reject("report-reconciliation", f"adversarial {key}")
        if row["forbidden_output"] not in {"true", "false"} or row["reviewed"] not in {"true", "false"}:
            reject("report-schema", "adversarial boolean")

    for row in tables["slices.tsv"]:
        for field in ("count", "scored", "correct"):
            parse_integer(row[field], f"slices.{field}")
        parse_number(row["accuracy"], "slices.accuracy")
    for row in tables["calibration.tsv"]:
        for field in ("count", "correct"):
            parse_integer(row[field], f"calibration.{field}")
        for field in ("confidence_sum", "ece", "brier"):
            parse_number(row[field], f"calibration.{field}")
    for row in tables["cost.tsv"]:
        parse_number(row["value"], "cost.value")
        parse_integer(row["count"], "cost.count")
    return {"artifact_valid": True, "result_status": scores["result_status"],
            "routing_eligible": decision_eligible}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate_reports(args.run_dir), sort_keys=True))
    except ValidationError as exc:
        print(exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
