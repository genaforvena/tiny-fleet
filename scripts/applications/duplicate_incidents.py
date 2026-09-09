#!/usr/bin/env python3
"""Offline duplicate-incident screening baselines; no model or network."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

MODEL_REVISION = "57c266a740f537b4dc058e1b0cda161fd15afa75"
MODEL_ID = "google/embeddinggemma-300m"
UNKNOWN = None
TOKEN_RE = re.compile(r"[a-z0-9]+")


class StudyError(ValueError):
    """Raised when a frozen A05 artifact or prediction violates its contract."""


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold()) if isinstance(text, str) else []


def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(_tokens(text))


def _expand_manifest(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    incidents = list(manifest.get("incidents", []))
    cases = list(manifest.get("cases", []))
    for blueprint in manifest.get("incident_blueprints", []):
        for index in range(blueprint["count"]):
            incident_id = f"{blueprint['prefix']}-{index:03d}"
            incidents.append({
                "incident_id": incident_id,
                "source_family": incident_id,
                "split": blueprint["split"],
                "time_period": blueprint["time_period"],
                "text": f"{blueprint['symptom']} {index}: {blueprint['detail']}",
            })
    by_id = {item["incident_id"]: item for item in incidents}
    for blueprint in manifest.get("case_blueprints", []):
        prefix = blueprint["incident_prefix"]
        for index in range(blueprint["count"]):
            incident_id = f"{prefix}-{index:03d}"
            incident = by_id[incident_id]
            hard_negative = f"{prefix}-{(index + 1) % blueprint['incident_count']:03d}"
            ticket = incident["text"]
            if blueprint.get("paraphrase_every") and index % blueprint["paraphrase_every"] == 0:
                ticket = ticket.replace("service", "component").replace("error", "failure")
            if blueprint.get("negative"):
                ticket = f"{incident['text'].split(':', 1)[0]} unrelated resolution note"
                reference = None
            else:
                reference = incident_id
            candidates = [hard_negative, incident_id] if reference else [hard_negative]
            cases.append({
                "case_id": f"{blueprint['prefix']}-{index:03d}",
                "split": blueprint["split"],
                "source_family": f"{blueprint['source_family_prefix']}-{index:03d}",
                "time_period": blueprint["time_period"],
                "ticket": ticket,
                "candidate_incident_ids": candidates,
                "reference": {"incident_id": reference, "abstain": reference is None},
            })
    return incidents, cases


def validate_case(case: dict[str, Any], incident_ids: set[str]) -> None:
    if not isinstance(case, dict):
        raise StudyError("case must be an object")
    required = ("case_id", "split", "source_family", "time_period", "ticket", "candidate_incident_ids", "reference")
    if any(key not in case for key in required):
        raise StudyError("case missing required field")
    if case["split"] not in {"development", "validation", "heldout"}:
        raise StudyError("invalid split")
    if not isinstance(case["ticket"], str) or not case["ticket"].strip():
        raise StudyError("ticket must be nonempty text")
    candidates = case["candidate_incident_ids"]
    if not isinstance(candidates, list) or not candidates or len(set(candidates)) != len(candidates):
        raise StudyError("candidate incident IDs must be unique and nonempty")
    if not all(isinstance(item, str) and item in incident_ids for item in candidates):
        raise StudyError("candidate incident is unknown")
    reference = case["reference"]
    if not isinstance(reference, dict) or set(reference) != {"incident_id", "abstain"}:
        raise StudyError("reference must contain incident_id and abstain")
    if not isinstance(reference["abstain"], bool):
        raise StudyError("reference abstain must be boolean")
    if reference["abstain"] != (reference["incident_id"] is None):
        raise StudyError("abstain must agree with reference incident")
    if reference["incident_id"] is not None and reference["incident_id"] not in candidates:
        raise StudyError("reference incident must be a candidate")


def validate_manifest(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A05":
        raise StudyError("manifest must be schema 1 for A05")
    provenance = manifest.get("model_provenance", {}).get("EmbeddingGemma", {})
    for key in ("model_id", "revision", "license", "source_url"):
        if not provenance.get(key):
            raise StudyError(f"EmbeddingGemma provenance missing {key}")
    if provenance["model_id"] != MODEL_ID or provenance["revision"] != MODEL_REVISION:
        raise StudyError("EmbeddingGemma revision is not pinned")
    incidents, cases = _expand_manifest(manifest)
    if not incidents or not cases:
        raise StudyError("incidents and cases must be nonempty")
    incident_ids = {item.get("incident_id") for item in incidents}
    if None in incident_ids or len(incident_ids) != len(incidents):
        raise StudyError("incident IDs must be unique")
    incident_splits = {item["incident_id"]: item["split"] for item in incidents}
    families: dict[str, str] = {}
    for case in cases:
        validate_case(case, incident_ids)
        if case["source_family"] in families and families[case["source_family"]] != case["split"]:
            raise StudyError("source family crosses splits")
        families[case["source_family"]] = case["split"]
        if any(incident_splits[item] != case["split"] for item in case["candidate_incident_ids"]):
            raise StudyError("candidate incident crosses split")
    heldout = [case for case in cases if case["split"] == "heldout"]
    if len(heldout) < 100:
        raise StudyError("heldout screening set must contain at least 100 independent cases")
    if len({case["source_family"] for case in heldout}) != len(heldout):
        raise StudyError("heldout source families must be independent")
    if not any(case["reference"]["abstain"] for case in heldout):
        raise StudyError("heldout set must include no-match cases")
    return incidents, cases


def _ngrams(text: str, width: int = 3) -> Counter[str]:
    value = f"  {normalize(text)}  "
    return Counter(value[index:index + width] for index in range(max(0, len(value) - width + 1)))


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    norm = math.sqrt(sum(value * value for value in left.values()) * sum(value * value for value in right.values()))
    return dot / norm if norm else 0.0


def _ranked_candidates(ticket: str, candidates: list[dict[str, Any]], scorer) -> list[tuple[float, int, str]]:
    ranked = [(scorer(ticket, item["text"]), index, item["incident_id"]) for index, item in enumerate(candidates)]
    return sorted(ranked, key=lambda item: (-item[0], item[1]))


def predict_normalized_hash(case: dict[str, Any], incidents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    query = normalize(case["ticket"])
    matches = [incident_id for incident_id in case["candidate_incident_ids"] if normalize(incidents[incident_id]["text"]) == query]
    if len(matches) != 1:
        return {"incident_id": None, "abstain": True, "candidate_scores": []}
    return {"incident_id": matches[0], "abstain": False, "candidate_scores": [{"incident_id": matches[0], "score": 1.0}]}


def predict_character_ngram(case: dict[str, Any], incidents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = _ranked_candidates(case["ticket"], [incidents[item] for item in case["candidate_incident_ids"]], lambda a, b: _cosine(_ngrams(a), _ngrams(b)))
    if not rows or rows[0][0] < 0.35:
        return {"incident_id": None, "abstain": True, "candidate_scores": []}
    return {"incident_id": rows[0][2], "abstain": False, "candidate_scores": [{"incident_id": item[2], "score": round(item[0], 6)} for item in rows]}


def _bm25_score(query: str, document: str, documents: list[str]) -> float:
    qtokens, tokens = _tokens(query), _tokens(document)
    if not qtokens or not tokens:
        return 0.0
    df = Counter(token for text in documents for token in set(_tokens(text)))
    average = sum(len(_tokens(text)) for text in documents) / len(documents)
    counts = Counter(tokens)
    score = 0.0
    for token in qtokens:
        if token not in counts:
            continue
        idf = math.log(1 + (len(documents) - df[token] + 0.5) / (df[token] + 0.5))
        norm = 1 - 0.75 + 0.75 * len(tokens) / average if average else 1
        score += idf * counts[token] * 2.2 / (counts[token] + 1.2 * norm)
    return score


def predict_bm25(case: dict[str, Any], incidents: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate_rows = [incidents[item] for item in case["candidate_incident_ids"]]
    rows = _ranked_candidates(case["ticket"], candidate_rows, lambda a, b: _bm25_score(a, b, [item["text"] for item in candidate_rows]))
    if not rows or rows[0][0] <= 0:
        return {"incident_id": None, "abstain": True, "candidate_scores": []}
    return {"incident_id": rows[0][2], "abstain": False, "candidate_scores": [{"incident_id": item[2], "score": round(item[0], 6)} for item in rows]}


def score_case(case: dict[str, Any], prediction: dict[str, Any], incident_ids: set[str] | None = None) -> dict[str, Any]:
    if incident_ids is None:
        incident_ids = set(case["candidate_incident_ids"])
    validate_case(case, incident_ids)
    if not isinstance(prediction, dict) or not isinstance(prediction.get("abstain"), bool):
        raise StudyError("prediction must contain abstain boolean")
    predicted = prediction.get("incident_id")
    if predicted is not None and predicted not in case["candidate_incident_ids"]:
        raise StudyError("prediction incident is not a candidate")
    if prediction["abstain"] != (predicted is None):
        raise StudyError("prediction abstain must agree with incident")
    target = case["reference"]["incident_id"]
    correct = predicted == target
    return {"case_id": case["case_id"], "source_family": case["source_family"],
            "pair_correct": int(correct), "pair_denominator": 1,
            "candidate_retrieval": int(target is None or target in case["candidate_incident_ids"]),
            "candidate_retrieval_denominator": int(target is not None),
            "failure_reason": None if correct else "wrong-match-or-abstention"}


def _metrics(rows: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [case for case in cases if case["reference"]["incident_id"] is not None]
    negative_ids = {case["case_id"] for case in cases if case["reference"]["incident_id"] is None}
    correct = sum(row["score"]["pair_correct"] for row in rows)
    false_accept = sum(row["prediction"]["incident_id"] is not None for row in rows if row["case_id"] in negative_ids)
    positive_rows = [row for row in rows if row["case_id"] not in negative_ids]
    retrieval = sum(row["score"]["candidate_retrieval"] for row in positive_rows)
    predicted_matches = sum(row["prediction"]["incident_id"] is not None for row in rows)
    true_matches = sum(row["prediction"]["incident_id"] == row["reference"]["incident_id"] for row in rows if row["reference"]["incident_id"] is not None)
    return {"n": len(rows), "positive_n": len(positives), "negative_n": len(negative_ids),
            "pair_correct_n": correct, "pair_accuracy": correct / len(rows) if rows else None,
            "pair_precision": true_matches / predicted_matches if predicted_matches else None,
            "pair_recall": true_matches / len(positives) if positives else None,
            "abstention_n": len(rows) - predicted_matches,
            "abstention_rate": (len(rows) - predicted_matches) / len(rows) if rows else None,
            "false_accept_n": false_accept, "false_accept_rate": false_accept / len(negative_ids) if negative_ids else None,
            "candidate_retrieval_recall": retrieval / len(positive_rows) if positive_rows else None,
            "source_family_unit": "one independently authored incident-family/time-period ticket per case"}


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    incidents, cases = validate_manifest(manifest)
    by_id = {item["incident_id"]: item for item in incidents}
    predictors = {"normalized-hash": predict_normalized_hash, "character-ngram": predict_character_ngram, "bm25": predict_bm25}
    run_dir.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, Any] = {}
    for name, predictor in predictors.items():
        started = time.perf_counter()
        rows = []
        for case in cases:
            prediction = predictor(case, by_id)
            rows.append({"case_id": case["case_id"], "split": case["split"], "source_family": case["source_family"],
                         "reference": case["reference"], "prediction": prediction,
                         "score": score_case(case, prediction, set(case["candidate_incident_ids"]))})
        raw = run_dir / f"{name}-raw.jsonl"
        raw.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        heldout = [row for row in rows if row["split"] == "heldout"]
        metrics = _metrics(heldout, [case for case in cases if case["split"] == "heldout"])
        metrics.update({"baseline": name, "mean_latency_ms": (time.perf_counter() - started) * 1000 / len(cases),
                        "raw_output": str(raw), "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest()})
        summaries[name] = metrics
    summary = {"application_id": "A05", "baselines": summaries,
               "all_MiniLM": {"status": "unavailable", "reason": "model scoring gated until C02-C08 and S01-S05 verification"},
               "pilot_verdict": "NO_GO_BASELINE_DOMINANT" if any(item["pair_precision"] >= 0.95 and item["pair_recall"] >= 0.95 and item["false_accept_rate"] <= 0.05 for item in summaries.values()) else "INCONCLUSIVE",
               "model_arms": "unavailable: C02-C08 and S01-S05 not verified",
               "provenance": {"model_id": MODEL_ID, "revision": MODEL_REVISION, "license": "Gemma Terms of Use; candidate only, not scored"}}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/duplicate-incidents/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
