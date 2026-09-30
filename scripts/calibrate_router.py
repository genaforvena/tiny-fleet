#!/usr/bin/env python3
"""Freeze a validation-only selective router calibration."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


class CalibrationError(ValueError):
    pass


def _norm(vector):
    values = [float(x) for x in vector]
    if not values or not all(math.isfinite(x) for x in values):
        raise CalibrationError("invalid embedding")
    length = math.sqrt(sum(x * x for x in values))
    if length == 0:
        raise CalibrationError("zero embedding")
    return [x / length for x in values]


def _cos(a, b):
    return sum(x * y for x, y in zip(a, b))


def _scores(vector, centroids):
    query = _norm(vector)
    scores = {domain: _cos(query, centroid) for domain, centroid in centroids.items()}
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    margin = ranked[0][1] - ranked[1][1] if len(ranked) > 1 else ranked[0][1]
    return scores, ranked[0][0], ranked[0][1], margin


def _validate_inputs(cases, embeddings):
    validation = []
    for case in cases:
        split = case.get("split")
        if split != "validation":
            raise CalibrationError(f"calibration labels must be validation-only, got {split}")
        case_id = case.get("case_id")
        if not case_id or case_id not in embeddings:
            raise CalibrationError("missing validation embedding")
        validation.append(case)
    if not validation:
        raise CalibrationError("empty validation population")
    domains = sorted({case["domain"] for case in validation if not case.get("ood") and case.get("domain")})
    if not domains:
        raise CalibrationError("no labeled in-domain validation cases")
    vectors = {case["case_id"]: _norm(embeddings[case["case_id"]]) for case in validation}
    return validation, domains, vectors


def _centroids(cases, domains, vectors):
    result = {}
    for domain in domains:
        rows = [vectors[c["case_id"]] for c in cases if c.get("domain") == domain and not c.get("ood")]
        if not rows:
            raise CalibrationError(f"no centroid examples for {domain}")
        result[domain] = _norm([sum(row[i] for row in rows) / len(rows) for i in range(len(rows[0]))])
    return result


def _decision(case, scores, best, similarity, margin, similarity_min, margin_min):
    if similarity < similarity_min:
        return "abstain", "absolute_similarity"
    if margin < margin_min:
        return "abstain", "low_margin"
    return f"specialist:{best}", "routed"


def _score_rows(cases, vectors, centroids, similarity_min=None, margin_min=None):
    rows = []
    for case in cases:
        scores, best, similarity, margin = _scores(vectors[case["case_id"]], centroids)
        if similarity_min is None:
            route, reason = f"specialist:{best}", "nearest_centroid"
        else:
            route, reason = _decision(case, scores, best, similarity, margin, similarity_min, margin_min)
        expected = None if case.get("ood") else (f"specialist:{case.get('domain')}" if case.get("domain") else None)
        rows.append({"case_id": case["case_id"], "route": route, "reason": reason, "scores": scores,
                     "best_similarity": similarity, "margin": margin, "expected": expected,
                     "model_refusal": bool(case.get("model_refusal", False)),
                     "correct": expected is not None and route == expected,
                     "false_accept": bool(case.get("ood")) and route != "abstain"})
    return rows


def _metrics(rows):
    routed = [row for row in rows if row["route"] != "abstain"]
    return {"n": len(rows), "routed": len(routed), "coverage": len(routed) / len(rows) if rows else None,
            "correct": sum(row["correct"] for row in routed),
            "false_accepts": sum(row["false_accept"] for row in routed),
            "risk": (sum(not row["correct"] for row in routed) / len(routed)) if routed else None}


def compare_methods(cases, embeddings):
    validation, domains, vectors = _validate_inputs(cases, embeddings)
    centroids = _centroids(validation, domains, vectors)
    lexical = []
    for case in validation:
        text = str(case.get("text", "")).casefold()
        hits = [(text.count(domain), domain) for domain in domains]
        best = max(hits)[1] if max(hits)[0] else None
        route = f"specialist:{best}" if best else "abstain"
        expected = None if case.get("ood") else f"specialist:{case.get('domain')}"
        lexical.append({"case_id": case["case_id"], "route": route, "reason": "lexical_rule",
                        "correct": expected is not None and route == expected, "false_accept": bool(case.get("ood")) and route != "abstain"})
    nearest = _score_rows(validation, vectors, centroids)
    gated_artifact = calibrate(validation, embeddings, embedding_digest="comparison", corpus_hash="comparison")
    gated = _score_rows(validation, vectors, {k: _norm(v) for k, v in gated_artifact["centroids"].items()},
                        gated_artifact["similarity_min"], gated_artifact["margin_min"])
    oracle = [{"case_id": c["case_id"], "route": "abstain" if c.get("ood") else f"specialist:{c['domain']}",
               "reason": "oracle", "correct": not c.get("ood"), "false_accept": False} for c in validation]
    abstain = [{"case_id": c["case_id"], "route": "abstain", "reason": "abstain_all", "correct": False, "false_accept": False} for c in validation]
    return {"lexical": lexical, "nearest_centroid": nearest, "gated": gated, "oracle": oracle, "abstain_all": abstain,
            "metrics": {name: _metrics(rows) for name, rows in {"lexical": lexical, "nearest_centroid": nearest,
                      "gated": gated, "oracle": oracle, "abstain_all": abstain}.items()}}


def calibrate(cases, embeddings, *, embedding_digest, corpus_hash, out_path=None, false_accept_bound=0.05):
    try:
        validation, domains, vectors = _validate_inputs(cases, embeddings)
    except CalibrationError as exc:
        if str(exc) != "no labeled in-domain validation cases":
            raise
        validation = list(cases)
        if not validation or any(case.get("split") != "validation" for case in validation):
            raise
        domains, vectors = [], {case["case_id"]: _norm(embeddings[case["case_id"]]) for case in validation}
        artifact = {"schema": "tiny-fleet.router-calibration/v1", "embedding_digest": embedding_digest,
                    "corpus_hash": corpus_hash, "centroids": {}, "similarity_min": 1.0, "margin_min": 1.0,
                    "calibration_method": "validation_grid_abs_margin", "false_accept_bound": false_accept_bound,
                    "verdict": "no-eligible-router", "cases": {"validation_n": len(validation),
                    "validation_ids": [case["case_id"] for case in validation]}, "metrics": {"n": len(validation),
                    "routed": 0, "coverage": 0.0, "correct": 0, "false_accepts": 0, "risk": None},
                    "score_grid": [], "validation_routes": [], "artifact_sha256": None}
        if out_path is not None:
            path = Path(out_path); path.parent.mkdir(parents=True, exist_ok=True)
            unsigned = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
            artifact["artifact_sha256"] = hashlib.sha256(unsigned.encode()).hexdigest()
            path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return artifact
    centroids = _centroids(validation, domains, vectors)
    grid = [(-1.0, 0.0), (-0.5, 0.0), (0.0, 0.0), (0.2, 0.05), (0.4, 0.1), (0.6, 0.1), (0.8, 0.2), (0.9, 0.4)]
    candidates = []
    for similarity_min, margin_min in grid:
        rows = _score_rows(validation, vectors, centroids, similarity_min, margin_min)
        metrics = _metrics(rows)
        if metrics["false_accepts"] / len(validation) <= false_accept_bound:
            candidates.append((metrics["coverage"] or 0.0, similarity_min, margin_min, metrics))
    chosen = max(candidates, key=lambda row: (row[0], -row[1], -row[2])) if candidates else None
    if chosen is None or chosen[0] == 0:
        similarity_min, margin_min, verdict = 1.0, 1.0, "no-eligible-router"
        metrics = _metrics(_score_rows(validation, vectors, centroids, similarity_min, margin_min))
    else:
        _, similarity_min, margin_min, metrics = chosen
        verdict = "eligible-router"
    artifact = {"schema": "tiny-fleet.router-calibration/v1", "embedding_digest": embedding_digest,
                "corpus_hash": corpus_hash, "centroids": centroids, "similarity_min": similarity_min,
                "margin_min": margin_min, "calibration_method": "validation_grid_abs_margin",
                "false_accept_bound": false_accept_bound, "verdict": verdict,
                "cases": {"validation_n": len(validation), "validation_ids": [c["case_id"] for c in validation]},
                "metrics": metrics, "score_grid": grid,
                "validation_routes": _score_rows(validation, vectors, centroids, similarity_min, margin_min),
                "artifact_sha256": None}
    if out_path is not None:
        path = Path(out_path); path.parent.mkdir(parents=True, exist_ok=True)
        unsigned = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
        artifact["artifact_sha256"] = hashlib.sha256(unsigned.encode()).hexdigest()
        path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def route_with_calibration(vector, calibration):
    try:
        scores, best, similarity, margin = _scores(vector, {k: _norm(v) for k, v in calibration["centroids"].items()})
    except CalibrationError as exc:
        return {"route": "abstain", "reason": "zero_query_embedding" if "zero" in str(exc) else str(exc), "scores": {}}
    route, reason = _decision({}, scores, best, similarity, margin, calibration["similarity_min"], calibration["margin_min"])
    return {"route": route, "reason": reason, "scores": scores, "best_similarity": similarity, "margin": margin,
            "model_refusal": False}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--embedding-digest", required=True)
    parser.add_argument("--corpus-hash", required=True)
    args = parser.parse_args(argv)
    cases = [json.loads(line) for line in args.cases.read_text().splitlines()]
    result = calibrate(cases, json.loads(args.embeddings.read_text()), embedding_digest=args.embedding_digest,
                       corpus_hash=args.corpus_hash, out_path=args.out)
    print(json.dumps({"out": str(args.out), "verdict": result["verdict"], "coverage": result["metrics"]["coverage"]}, sort_keys=True))


if __name__ == "__main__":
    main()
