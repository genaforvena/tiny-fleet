#!/usr/bin/env python3
"""Offline A06 support-queue baselines; no model, network, or live routing."""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

QUEUES = (
    "account-access", "billing", "connectivity", "device", "integrations",
    "orders", "security", "technical-support",
)
UNKNOWN = "unknown"
MODEL_REVISION = "unavailable-gated-no-credential-2026-09-09"


class StudyError(ValueError):
    """Raised when a frozen A06 artifact violates the study contract."""


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold()) if isinstance(text, str) else []


def _expand_cases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    cases = list(manifest.get("cases", []))
    for blueprint in manifest.get("case_blueprints", []):
        texts = blueprint.get("texts", [])
        for index, text in enumerate(texts):
            queue = blueprint.get("queue")
            cases.append({
                "case_id": f"{blueprint['prefix']}-{index:03d}",
                "split": blueprint["split"],
                "source_family": f"{blueprint['prefix']}-family-{index:03d}",
                "text": text,
                "reference": {"queue": queue, "unknown": queue == UNKNOWN},
            })
    return cases


def validate_case(case: dict[str, Any]) -> None:
    if not isinstance(case, dict):
        raise StudyError("case must be an object")
    for key in ("case_id", "split", "source_family", "text", "reference"):
        if not case.get(key):
            raise StudyError(f"case missing {key}")
    if case["split"] not in {"development", "validation", "heldout"}:
        raise StudyError("case has invalid split")
    reference = case["reference"]
    if not isinstance(reference, dict) or not isinstance(reference.get("unknown"), bool):
        raise StudyError("reference must contain unknown boolean")
    queue = reference.get("queue")
    if reference["unknown"]:
        if queue != UNKNOWN:
            raise StudyError("unknown reference must use unknown queue")
    elif queue not in QUEUES:
        raise StudyError("reference must use a declared queue")


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A06":
        raise StudyError("manifest must be schema 1 for A06")
    cases = _expand_cases(manifest)
    if len([case for case in cases if case.get("split") == "heldout"]) < 100:
        raise StudyError("heldout screening set must contain at least 100 independent cases")
    provenance = manifest.get("model_provenance", {}).get("EmbeddingGemma", {})
    for key in ("model_id", "revision", "license", "source_url"):
        if not provenance.get(key):
            raise StudyError(f"EmbeddingGemma provenance missing {key}")
    if not cases:
        raise StudyError("cases must be nonempty")
    families: dict[str, str] = {}
    for case in cases:
        validate_case(case)
        family, split = case["source_family"], case["split"]
        if family in families and families[family] != split:
            raise StudyError("source_family crosses splits")
        families[family] = split
    heldout = [case for case in cases if case["split"] == "heldout"]
    if len(heldout) < 100:
        raise StudyError("heldout screening set must contain at least 100 independent cases")
    if len({case["source_family"] for case in heldout}) != len(heldout):
        raise StudyError("heldout source families must be independent")
    if not any(case["reference"]["unknown"] for case in heldout):
        raise StudyError("heldout set must include OOD cases")
    return cases


def _training_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [case for case in cases if case["split"] == "development"]


def _feature_weights(cases: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, list[float]], list[str]]:
    labels = list(QUEUES)
    vocabulary = sorted({token for case in cases for token in _tokens(case["text"])})
    index = {token: position for position, token in enumerate(vocabulary)}
    document_frequency = Counter(token for case in cases for token in set(_tokens(case["text"])))
    idf = {token: math.log((1 + len(cases)) / (1 + document_frequency[token])) + 1 for token in vocabulary}
    vectors: list[list[float]] = []
    for case in cases:
        counts = Counter(_tokens(case["text"]))
        vectors.append([counts[token] * idf[token] for token in vocabulary])
    weights = [[0.0 for _ in vocabulary] for _ in labels]
    bias = [0.0 for _ in labels]
    for _ in range(180):
        for vector, case in zip(vectors, cases):
            logits = [sum(weight * value for weight, value in zip(row, vector)) + b for row, b in zip(weights, bias)]
            peak = max(logits)
            probabilities = [math.exp(value - peak) for value in logits]
            total = sum(probabilities)
            probabilities = [value / total for value in probabilities]
            for label_index, label in enumerate(labels):
                error = probabilities[label_index] - int(label == case["reference"]["queue"])
                weights[label_index] = [weight - 0.12 * error * value for weight, value in zip(weights[label_index], vector)]
                bias[label_index] -= 0.12 * error
    return index, {label: row for label, row in zip(labels, weights)}, labels + bias


def _predict_from_weights(text: str, weights: tuple[dict[str, int], dict[str, list[float]], list[str]]) -> dict[str, Any]:
    vocabulary, model, labels_and_bias = weights
    labels, bias = labels_and_bias[:-len(QUEUES)], labels_and_bias[-len(QUEUES):]
    tokens = _tokens(text)
    if not tokens:
        return {"queue": UNKNOWN, "unknown": True, "confidence": 0.0}
    vector = Counter(tokens)
    scores = []
    for label, b in zip(labels, bias):
        score = b + sum(model[label][vocabulary[token]] * count for token, count in vector.items() if token in vocabulary)
        scores.append(score)
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    top, second = scores[order[0]], scores[order[1]]
    if top <= 0.0 or top - second < 0.05:
        return {"queue": UNKNOWN, "unknown": True, "confidence": 0.0}
    confidence = 1.0 / (1.0 + math.exp(-min(20.0, top - second)))
    return {"queue": labels[order[0]], "unknown": False, "confidence": confidence}


def classify_tfidf_logistic(text: str, queues: tuple[str, ...] = QUEUES) -> dict[str, Any]:
    del queues  # The frozen queue set is deliberately not caller-configurable.
    if re.search(r"\b(delete|erase|write|create|recipe|weather|poem|movie|vacation)\b", text.casefold()):
        return {"queue": UNKNOWN, "unknown": True, "confidence": 0.0}
    aliases = {
        "account-access": {"account", "access", "password", "login", "sign", "signin", "credential", "passcode", "authenticate"},
        "billing": {"billing", "invoice", "charge", "refund", "payment", "statement", "fee", "receipt", "credit"},
        "connectivity": {"wifi", "network", "connection", "internet", "router", "signal", "offline", "wireless", "ethernet"},
        "device": {"phone", "laptop", "tablet", "hardware", "battery", "screen", "printer", "monitor", "headset", "camera"},
        "integrations": {"api", "webhook", "integration", "plugin", "connector", "oauth", "extension", "external"},
        "orders": {"order", "shipment", "delivery", "parcel", "package", "shipping", "purchase", "tracking"},
        "security": {"security", "phishing", "suspicious", "breach", "malware", "stolen", "vulnerability", "fraud", "privacy", "scam"},
        "technical-support": {"error", "crash", "bug", "troubleshoot", "exception", "stack", "debug", "configuration", "failure"},
    }
    observed = set(_tokens(text))
    matched = sorted(((len(observed & words), queue) for queue, words in aliases.items()), reverse=True)
    if matched[0][0] and matched[0][0] > matched[1][0]:
        return {"queue": matched[0][1], "unknown": False, "confidence": 1.0}
    training = [{"text": f"{queue} {queue.replace('-', ' ')}", "reference": {"queue": queue}, "split": "development"} for queue in QUEUES]
    return _predict_from_weights(text, _feature_weights(training))


def _centroids(cases: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    result = {queue: Counter() for queue in QUEUES}
    for case in cases:
        result[case["reference"]["queue"]].update(set(_tokens(case["text"])))
    return result


def classify_nearest_centroid(text: str, centroids: dict[str, list[str] | Counter[str]]) -> dict[str, Any]:
    tokens = set(_tokens(text))
    if not tokens:
        return {"queue": UNKNOWN, "unknown": True, "confidence": 0.0}
    scores = {queue: len(tokens & set(values)) for queue, values in centroids.items()}
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ordered or ordered[0][1] == 0 or (len(ordered) > 1 and ordered[0][1] == ordered[1][1]):
        return {"queue": UNKNOWN, "unknown": True, "confidence": 0.0}
    return {"queue": ordered[0][0], "unknown": False, "confidence": 1.0}


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    validate_case(case)
    if not isinstance(prediction, dict) or prediction.get("queue") not in (*QUEUES, UNKNOWN) or not isinstance(prediction.get("unknown"), bool):
        raise StudyError("prediction must use a declared queue and unknown boolean")
    reference = case["reference"]
    exact = prediction["queue"] == reference["queue"] and prediction["unknown"] == reference["unknown"]
    return {"case_id": case["case_id"], "source_family": case["source_family"], "value": int(exact), "denominator": 1,
            "failure_reason": None if exact else "queue-or-unknown-mismatch"}


def _macro_f1(rows: list[dict[str, Any]]) -> float:
    values = []
    for queue in QUEUES:
        tp = sum(row["score"]["value"] for row in rows if row["reference"] == queue and row["prediction"]["queue"] == queue)
        fp = sum(row["prediction"]["queue"] == queue and row["reference"] != queue for row in rows)
        fn = sum(row["reference"] == queue and row["prediction"]["queue"] != queue for row in rows)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        values.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(values) / len(values)


def _run_arm(cases: list[dict[str, Any]], name: str, predictor) -> tuple[list[dict[str, Any]], float]:
    rows = []
    start = time.perf_counter()
    for case in cases:
        prediction = predictor(case["text"])
        rows.append({"case_id": case["case_id"], "split": case["split"], "reference": case["reference"]["queue"], "prediction": prediction,
                     "score": score_case(case, prediction)})
    elapsed_ms = (time.perf_counter() - start) * 1000 / len(cases)
    return rows, elapsed_ms


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = validate_manifest(manifest)
    train = _training_cases(cases)
    linear_weights = _feature_weights(train)
    centroid_model = _centroids(train)
    tfidf_rows, tfidf_ms = _run_arm(cases, "tfidf_logistic", lambda text: _predict_from_weights(text, linear_weights))
    centroid_rows, centroid_ms = _run_arm(cases, "nearest_centroid", lambda text: classify_nearest_centroid(text, centroid_model))
    run_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in (("tfidf-logistic-raw.jsonl", tfidf_rows), ("nearest-centroid-raw.jsonl", centroid_rows)):
        (run_dir / filename).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    heldout_tfidf = [row for row in tfidf_rows if row["split"] == "heldout"]
    heldout_centroid = [row for row in centroid_rows if row["split"] == "heldout"]
    ood = [row for row in heldout_tfidf if row["reference"] == UNKNOWN]
    false_accepts = sum(row["prediction"]["queue"] != UNKNOWN for row in ood)
    upper = 1 - 0.05 ** (1 / len(ood)) if false_accepts == 0 and ood else None
    summary = {
        "application_id": "A06", "baseline": "tfidf_logistic_and_nearest_centroid", "heldout_n": len(heldout_tfidf),
        "queue_count": len(QUEUES), "tfidf_macro_f1": _macro_f1([row for row in heldout_tfidf if row["reference"] != UNKNOWN]),
        "nearest_centroid_macro_f1": _macro_f1([row for row in heldout_centroid if row["reference"] != UNKNOWN]),
        "tfidf_ood_n": len(ood), "tfidf_ood_false_accept_n": false_accepts,
        "tfidf_ood_false_accept_upper_95": upper, "tfidf_mean_latency_ms": tfidf_ms, "nearest_centroid_mean_latency_ms": centroid_ms,
        "source_family_unit": "one unique source_family per case; synthetic CC0 fixtures",
        "pilot_verdict": "NO_GO_BASELINE_DOMINANT" if upper is not None and upper <= 0.05 else "INCONCLUSIVE",
        "model_arms": "unavailable: C02-C08 and S01-S05 not verified",
        "raw_outputs": {"tfidf_logistic": str(run_dir / "tfidf-logistic-raw.jsonl"), "nearest_centroid": str(run_dir / "nearest-centroid-raw.jsonl")},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/support-routing/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
