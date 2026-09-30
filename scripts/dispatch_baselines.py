#!/usr/bin/env python3
"""Deterministic, offline baselines for the advisory dispatch study.

The functions in this module only rank already-authoritative eligible owners.
They never read or mutate mesh state.  ``None`` means abstain, including when
the case is not admissible for an advisory suggestion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import resource
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable


TOKEN = re.compile(r"[a-z0-9]+")


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _tokens(text: str) -> list[str]:
    return TOKEN.findall(text.casefold())


def _valid_case(case: dict[str, Any]) -> bool:
    eligible = case.get("eligible_owner_ids")
    return (
        isinstance(eligible, list)
        and bool(eligible)
        and all(isinstance(owner, str) and owner for owner in eligible)
        and len(set(eligible)) == len(eligible)
    )


def authoritative_guard(case: dict[str, Any], ranked: Iterable[str] | None) -> list[str] | None:
    """Intersect a suggestion with authoritative state, or abstain fail-closed."""
    if not _valid_case(case):
        return None
    eligible = set(case["eligible_owner_ids"])
    explicit = case.get("explicit_owner")
    if explicit is not None:
        return [explicit] if explicit in eligible else None
    if case.get("dependency_state") != "ready" or case.get("lease_state") != "none":
        return None
    if not isinstance(case.get("retry_budget"), int) or isinstance(case["retry_budget"], bool) or case["retry_budget"] <= 0:
        return None
    if ranked is None:
        return None
    result = []
    for owner in ranked:
        if owner in eligible and owner not in result:
            result.append(owner)
    return result or None


def rank_explicit(case: dict[str, Any]) -> list[str] | None:
    """Current-rule replay: preserve explicit owner and never replace it."""
    if case.get("explicit_owner") is not None:
        return authoritative_guard(case, [case["explicit_owner"]])
    return authoritative_guard(case, None)


def rank_role_keyword(case: dict[str, Any]) -> list[str] | None:
    if not _valid_case(case) or case.get("explicit_owner") is not None:
        return authoritative_guard(case, None)
    text = set(_tokens(str(case.get("sanitized_text", ""))))
    scored = []
    for owner in case["eligible_owner_ids"]:
        role = case.get("role_descriptions", {}).get(owner, "")
        overlap = len(text & set(_tokens(str(role))))
        if overlap:
            scored.append((overlap, owner))
    return authoritative_guard(case, [owner for _, owner in sorted(scored, key=lambda x: (-x[0], x[1]))])


class TfidfOwnerRanker:
    """A dependency-free TF-IDF nearest-centroid linear baseline."""

    def __init__(self, cases: Iterable[dict[str, Any]]):
        rows = [c for c in cases if c.get("split") == "train" and c.get("label", {}).get("allowed_owner_set")]
        self.document_frequency = Counter()
        self.centroids: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for case in rows:
            terms = set(_tokens(case["sanitized_text"]))
            self.document_frequency.update(terms)
        n = max(1, len(rows))
        for case in rows:
            terms = Counter(_tokens(case["sanitized_text"]))
            for owner in case["label"]["allowed_owner_set"]:
                for term, count in terms.items():
                    self.centroids[owner][term] += (count / max(1, sum(terms.values()))) * math.log((1 + n) / (1 + self.document_frequency[term]))

    def rank(self, case: dict[str, Any]) -> list[str] | None:
        if not _valid_case(case) or case.get("explicit_owner") is not None:
            return authoritative_guard(case, None)
        terms = Counter(_tokens(str(case.get("sanitized_text", ""))))
        scores = []
        for owner in case["eligible_owner_ids"]:
            centroid = self.centroids.get(owner, {})
            score = sum(count * centroid.get(term, 0.0) for term, count in terms.items())
            if score > 0:
                scores.append((score, owner))
        return authoritative_guard(case, [owner for _, owner in sorted(scores, key=lambda x: (-x[0], x[1]))])


def rank_minilm(case: dict[str, Any], embeddings: dict[str, list[float]] | None = None, centroids: dict[str, list[float]] | None = None) -> list[str] | None:
    """Optional pinned all-MiniLM replay; missing vectors are explicitly unavailable."""
    if embeddings is None or centroids is None or case.get("case_id") not in embeddings:
        return authoritative_guard(case, None)
    vector = embeddings[case["case_id"]]
    scored = []
    for owner in case.get("eligible_owner_ids", []):
        centroid = centroids.get(owner)
        if not centroid or len(centroid) != len(vector):
            continue
        dot = sum(a * b for a, b in zip(vector, centroid))
        norm = math.sqrt(sum(a * a for a in vector) * sum(b * b for b in centroid))
        if norm and math.isfinite(dot / norm):
            scored.append((dot / norm, owner))
    return authoritative_guard(case, [owner for _, owner in sorted(scored, key=lambda x: (-x[0], x[1]))])


def score_predictions(cases: list[dict[str, Any]], predictions: dict[str, list[str] | None], name: str) -> dict[str, Any]:
    eligible = [c for c in cases if c.get("split") == "heldout" and c.get("explicit_owner") is None]
    scored = [c for c in eligible if c.get("label", {}).get("allowed_owner_set") and not c["label"].get("needs_clarification")]
    correct = sum(bool(predictions.get(c["case_id"])) and predictions[c["case_id"]][0] in c["label"]["allowed_owner_set"] for c in scored)
    coverage = sum(predictions.get(c["case_id"]) is not None for c in eligible)
    violations = sum(bool(predictions.get(c["case_id"])) and not set(predictions[c["case_id"]]).issubset(c.get("eligible_owner_ids", [])) for c in cases)
    confusion = Counter()
    for case in scored:
        gold = case["label"]["allowed_owner_set"][0]
        predicted = (predictions.get(case["case_id"]) or ["abstain"])[0]
        confusion[f"{gold}->{predicted}"] += 1
    return {"baseline": name, "heldout_unowned": len(eligible), "quality_units": len(scored), "correct": correct, "suitable_owner_accuracy": correct / len(scored) if scored else None, "coverage": coverage / len(eligible) if eligible else None, "severe_constraint_violations": violations, "role_confusion": dict(sorted(confusion.items()))}


def run(cases: list[dict[str, Any]], corpus_sha256: str | None = None) -> dict[str, Any]:
    ranker = TfidfOwnerRanker(cases)
    methods: dict[str, Callable[[dict[str, Any]], list[str] | None]] = {
        "explicit-rule": rank_explicit,
        "role-keyword": rank_role_keyword,
        "tfidf-linear": ranker.rank,
        "all-minilm-centroid": lambda case: rank_minilm(case),
        "abstain-all": lambda case: authoritative_guard(case, None),
    }
    output: dict[str, Any] = {"schema": "tiny-fleet.board-dispatch.baselines/v1", "corpus_sha256": corpus_sha256 or hashlib.sha256(json.dumps(cases, separators=(",", ":")).encode()).hexdigest(), "predictions": {}, "metrics": [], "resource": {"max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
    for name, method in methods.items():
        predictions = {}
        durations = []
        for case in cases:
            started = time.perf_counter_ns()
            predictions[case["case_id"]] = method(case)
            durations.append((time.perf_counter_ns() - started) / 1_000_000)
        result = score_predictions(cases, predictions, name)
        result.update({"latency_ms_p50": sorted(durations)[len(durations) // 2], "latency_ms_p95": sorted(durations)[max(0, math.ceil(len(durations) * .95) - 1)], "cost": {"paid_api": False, "gpu_minutes": 0}})
        output["predictions"][name] = predictions
        output["metrics"].append(result)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("corpus/board-dispatch-v1/cases.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("runs/board-dispatch-v1/baselines/results.json"))
    args = parser.parse_args()
    cases = load_cases(args.corpus)
    result = run(cases, hashlib.sha256(args.corpus.read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "cases": len(cases), "baselines": len(result["metrics"]), "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
