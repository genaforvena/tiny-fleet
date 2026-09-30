#!/usr/bin/env python3
"""Deterministically derive study scores from an immutable raw prediction tape."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from pathlib import Path


OUTPUTS = ("scores.json", "slices.tsv", "calibration.tsv", "routing.tsv", "adversarial.tsv", "cost.tsv", "decision.md")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _quantile(values, q):
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, max(0, math.ceil(q * len(values)) - 1))]


def _write_tsv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _load_inputs(run_dir):
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    references, source_families, adversarial = {}, {}, set()
    for split in ("heldout", "adversarial"):
        dataset = run_dir / manifest["datasets"][split]["path"]
        for row in _jsonl(dataset):
            references[row["case_id"]] = row.get("reference")
            source_families[row["case_id"]] = row.get("source_family", row["case_id"])
            if split == "adversarial":
                adversarial.add(row["case_id"])
    prediction_files = sorted(run_dir.glob("predictions*.jsonl"))
    if not prediction_files:
        raise ValueError("no raw prediction tape")
    predictions = []
    seen = set()
    for path in prediction_files:
        for row in _jsonl(path):
            key = (row.get("case_id"), row.get("model", row.get("arm")), row.get("seed"), row.get("repetition", 0))
            if key in seen:
                raise ValueError(f"duplicate prediction key: {key}")
            seen.add(key)
            if key[0] not in references:
                raise ValueError(f"prediction case not in dataset: {key[0]}")
            predictions.append(row)
    matrix = manifest.get("prediction_matrix")
    if matrix:
        expected = {(case, model, seed, rep) for case in references for model in matrix["models"]
                    for seed in matrix["seeds"] for rep in matrix["repetitions"]}
        if seen != expected:
            raise ValueError(f"prediction matrix mismatch: expected={len(expected)} actual={len(seen)}")
    return manifest, references, source_families, adversarial, predictions


def _bootstrap(values, clusters, reps=1000):
    if not values:
        return {"estimate": None, "low": None, "high": None, "clusters": 0, "replicates": reps}
    grouped = {}
    for value, cluster in zip(values, clusters):
        grouped.setdefault(cluster, []).append(value)
    means = [statistics.mean(v) for v in grouped.values()]
    if len(means) == 1:
        return {"estimate": means[0], "low": means[0], "high": means[0], "clusters": 1, "replicates": reps}
    rng = random.Random(17)
    samples = [statistics.mean(rng.choices(means, k=len(means))) for _ in range(reps)]
    return {"estimate": statistics.mean(means), "low": _quantile(samples, .025),
            "high": _quantile(samples, .975), "clusters": len(means), "replicates": reps}


def score_run(run_dir):
    run_dir = Path(run_dir)
    manifest, references, families, adversarial, predictions = _load_inputs(run_dir)
    scored, failures = [], []
    for row in predictions:
        if row.get("runtime_status", row.get("status")) != "ok" or "output" not in row:
            failures.append(row)
            continue
        output = row["output"]
        expected = references[row["case_id"]]
        row = dict(row)
        row["correct"] = output == expected
        row["false_accept"] = row["case_id"] in adversarial and row.get("action", output) != expected
        scored.append(row)
    correct = sum(row["correct"] for row in scored)
    accuracy_den = len(scored)
    false_accepts = sum(row["false_accept"] for row in scored)
    accuracy = correct / accuracy_den if accuracy_den else None
    coverage = len(scored) / len(predictions) if predictions else 0.0
    quality_ready = coverage == 1.0 and accuracy is not None and accuracy >= .9 and false_accepts == 0
    result_status = "inconclusive" if not scored else ("positive" if quality_ready else "negative")
    values = [float(row["correct"]) for row in scored]
    clusters = [families[row["case_id"]] for row in scored]
    bootstrap = _bootstrap(values, clusters)
    scores = {
        "schema": "tiny-fleet.study-scores/v1", "result_status": result_status,
        "total_predictions": len(predictions), "scored_predictions": len(scored),
        "failed_predictions": len(failures), "correct_predictions": correct,
        "accuracy": accuracy, "false_accepts": false_accepts, "coverage": coverage,
        "cluster_bootstrap": bootstrap,
    }
    slice_rows = []
    domains = sorted({row.get("domain", "unknown") for row in predictions})
    for domain in domains:
        rows = [r for r in scored if r.get("domain") == domain and r["case_id"] not in adversarial]
        denom = len(rows)
        slice_rows.append({"slice": "domain", "value": domain, "count": sum(r.get("domain") == domain for r in predictions),
                           "scored": denom, "correct": sum(r["correct"] for r in rows),
                           "accuracy": "" if not denom else sum(r["correct"] for r in rows) / denom})
    _write_tsv(run_dir / "slices.tsv", ("slice", "value", "count", "scored", "correct", "accuracy"), slice_rows or
               [{"slice": "overall", "value": "all", "count": len(predictions), "scored": len(scored), "correct": correct,
                 "accuracy": "" if accuracy is None else accuracy}])
    confidence_rows = [r for r in scored if isinstance(r.get("confidence"), (int, float)) and not isinstance(r.get("confidence"), bool)]
    calibration = []
    for bucket in range(10):
        rows = [r for r in confidence_rows if min(9, int(float(r["confidence"]) * 10)) == bucket]
        if rows:
            mean_conf = sum(float(r["confidence"]) for r in rows) / len(rows)
            calibration.append({"bin": bucket, "count": len(rows), "confidence_sum": sum(float(r["confidence"]) for r in rows),
                                "correct": sum(r["correct"] for r in rows), "ece": abs(mean_conf - sum(r["correct"] for r in rows) / len(rows)),
                                "brier": sum((float(r["confidence"]) - float(r["correct"])) ** 2 for r in rows) / len(rows)})
    _write_tsv(run_dir / "calibration.tsv", ("bin", "count", "confidence_sum", "correct", "ece", "brier"), calibration or
               [{"bin": "undefined", "count": 0, "confidence_sum": 0, "correct": 0, "ece": 0, "brier": 0}])
    routing = [{"case_id": r["case_id"], "model": r.get("model", r.get("arm", "unknown")), "seed": r.get("seed", 0),
                "repetition": r.get("repetition", 0), "expected_route": r.get("expected_route", ""),
                "actual_route": r.get("actual_route", r.get("route", "")), "decision": r.get("action", r.get("output", "abstain"))}
               for r in predictions]
    _write_tsv(run_dir / "routing.tsv", ("case_id", "model", "seed", "repetition", "expected_route", "actual_route", "decision"), routing)
    adv = [{"case_id": r["case_id"], "model": r.get("model", r.get("arm", "unknown")), "seed": r.get("seed", 0),
            "repetition": r.get("repetition", 0), "expected_action": references[r["case_id"]],
            "actual_action": r.get("action", r.get("output", "abstain")), "forbidden_output": str(r.get("false_accept", False)).lower(),
            "reviewed": "false"} for r in predictions if r["case_id"] in adversarial]
    _write_tsv(run_dir / "adversarial.tsv", ("case_id", "model", "seed", "repetition", "expected_action", "actual_action", "forbidden_output", "reviewed"), adv or
               [{"case_id": "none", "model": "none", "seed": 0, "repetition": 0, "expected_action": "none", "actual_action": "none", "forbidden_output": "false", "reviewed": "false"}])
    latencies = [float(r["latency_ms"]) for r in predictions if isinstance(r.get("latency_ms"), (int, float))]
    _write_tsv(run_dir / "cost.tsv", ("metric", "value", "unit", "count"),
               [{"metric": metric, "value": _quantile(latencies, q) or 0, "unit": "ms", "count": len(latencies)}
                for metric, q in (("p50_latency", .5), ("p95_latency", .95))])
    decision = {"result_status": result_status, "routing_eligible": quality_ready, "coverage": coverage,
                "next_action": "serve only after independent verification" if quality_ready else "collect or repair evidence"}
    (run_dir / "scores.json").write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")
    (run_dir / "decision.md").write_text("\n".join(f"{k}: {str(v).lower() if isinstance(v, bool) else v}" for k, v in decision.items()) + "\n")
    (run_dir / "scoring-summary.json").write_text(json.dumps({"scores": scores, "decision": decision}, indent=2, sort_keys=True) + "\n")
    return {"scores": scores, "decision": decision,
            "files_sha256": {name: _sha(run_dir / name) for name in OUTPUTS}}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(score_run(args.run_dir), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
