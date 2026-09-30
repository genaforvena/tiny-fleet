#!/usr/bin/env python3
"""Offline cited-runbook retrieval baseline; no model, network, or generation."""

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

MODEL_REVISION = "unavailable-gated-embeddinggemma-2026-09-09"
TOKEN_RE = re.compile(r"[a-z0-9]+")


class StudyError(ValueError):
    pass


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold()) if isinstance(text, str) else []


def _expand_manifest(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manuals = list(manifest.get("manuals", []))
    for blueprint in manifest.get("manual_blueprints", []):
        for index in range(blueprint["count"]):
            family = f"{blueprint['prefix']}-{index:03d}"
            manuals.append({
                "manual_id": family,
                "source_family": family,
                "license": "CC0-1.0",
                "paragraphs": [
                    {"paragraph_id": f"{family}-p0", "text": f"{blueprint['topic']} restart service safely"},
                    {"paragraph_id": f"{family}-p1", "text": f"{blueprint['topic']} verify health after restart"},
                    {"paragraph_id": f"{family}-p2", "text": f"{blueprint['topic']} collect logs before escalation"},
                ],
            })
    cases = list(manifest.get("cases", []))
    for blueprint in manifest.get("case_blueprints", []):
        for index in range(blueprint["count"]):
            family = f"{blueprint['manual_prefix']}-{index + blueprint.get('start', 0):03d}"
            if blueprint["answerable"]:
                paragraph_id = f"{family}-p0"
                query = f"{blueprint['topic']} restart service"
                gold = [paragraph_id]
                available = [f"{family}-p{i}" for i in range(3)]
            else:
                query = f"zzqmissing{index} zzqabsent{index}"
                gold, available = [], [f"{family}-p{i}" for i in range(3)]
            cases.append({
                "case_id": f"{blueprint['prefix']}-{index:03d}",
                "split": blueprint["split"],
                "source_family": family,
                "manual_id": family,
                "query": query,
                "gold_paragraph_ids": gold,
                "available_paragraph_ids": available,
                "answerable": blueprint["answerable"],
            })
    return manuals, cases


def validate_case(case: dict[str, Any]) -> None:
    required = ("case_id", "split", "source_family", "manual_id", "query", "gold_paragraph_ids", "available_paragraph_ids", "answerable")
    if not isinstance(case, dict) or any(
        (key not in case or case[key] is None or case[key] == "" or case[key] == [])
        and key not in {"gold_paragraph_ids"}
        for key in required
    ):
        raise StudyError("case missing required field")
    if case["split"] not in {"development", "validation", "heldout"}:
        raise StudyError("invalid split")
    if not isinstance(case["answerable"], bool) or not isinstance(case["gold_paragraph_ids"], list):
        raise StudyError("case answerability or gold IDs malformed")
    if case["answerable"] != bool(case["gold_paragraph_ids"]):
        raise StudyError("answerable must agree with gold paragraph IDs")
    if not set(case["gold_paragraph_ids"]).issubset(case["available_paragraph_ids"]):
        raise StudyError("gold paragraph is absent from manual")


def validate_manifest(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A04":
        raise StudyError("manifest must be schema 1 for A04")
    provenance = manifest.get("model_provenance", {}).get("EmbeddingGemma", {})
    if any(not provenance.get(key) for key in ("model_id", "revision", "license", "source_url")):
        raise StudyError("EmbeddingGemma provenance missing")
    manuals, cases = _expand_manifest(manifest)
    if not manuals or not cases:
        raise StudyError("manuals and cases must be nonempty")
    manual_families = {manual.get("source_family") for manual in manuals}
    if len(manual_families) != len(manuals):
        raise StudyError("manual source families must be unique")
    split_families: dict[str, str] = {}
    for case in cases:
        validate_case(case)
        if case["manual_id"] not in {manual["manual_id"] for manual in manuals}:
            raise StudyError("case references unknown manual")
        family = case["source_family"]
        if family in split_families and split_families[family] != case["split"]:
            raise StudyError("source family crosses splits")
        split_families[family] = case["split"]
    heldout = [case for case in cases if case["split"] == "heldout"]
    if len(heldout) < 100:
        raise StudyError("heldout screening set must contain at least 100 independent cases")
    if not any(not case["answerable"] for case in heldout):
        raise StudyError("heldout set must include unanswerable near matches")
    return manuals, cases


def bm25_retrieve(query: str, paragraphs: list[dict[str, str]], limit: int = 5) -> list[str]:
    if not isinstance(query, str) or not isinstance(paragraphs, list):
        raise StudyError("query and paragraphs malformed")
    qtokens = _tokens(query)
    if not qtokens or not paragraphs:
        return []
    docs = [_tokens(item.get("text", "")) for item in paragraphs]
    document_frequency = Counter(token for doc in docs for token in set(doc))
    average_length = sum(len(doc) for doc in docs) / len(docs)
    scored: list[tuple[float, int, str]] = []
    for index, (paragraph, doc) in enumerate(zip(paragraphs, docs)):
        counts = Counter(doc)
        score = 0.0
        for token in qtokens:
            if token not in counts:
                continue
            idf = math.log(1 + (len(docs) - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5))
            length_norm = 1 - 0.75 + 0.75 * len(doc) / average_length if average_length else 1
            score += idf * counts[token] * 2.2 / (counts[token] + 1.2 * length_norm)
        if score > 0:
            scored.append((score, index, paragraph["paragraph_id"]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [paragraph_id for _, _, paragraph_id in scored[:limit]]


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    validate_case(case)
    if not isinstance(prediction, dict) or not isinstance(prediction.get("paragraph_ids"), list):
        raise StudyError("prediction must contain paragraph_ids")
    ids = prediction["paragraph_ids"]
    if len(ids) > 5 or any(not isinstance(item, str) for item in ids):
        raise StudyError("paragraph_ids must contain at most five strings")
    if len(set(ids)) != len(ids) or not set(ids).issubset(case["available_paragraph_ids"]):
        raise StudyError("prediction cites paragraph outside the manual")
    supported = bool(set(ids) & set(case["gold_paragraph_ids"]))
    false_accept = int(not case["answerable"] and bool(ids))
    return {"case_id": case["case_id"], "source_family": case["source_family"],
            "recall_at_5": int(supported) if case["answerable"] else None,
            "no_answer_false_accept": false_accept if not case["answerable"] else None,
            "denominator": 1, "failure_reason": None if (supported or not case["answerable"] and not ids) else "gold-not-retrieved"}


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manuals, cases = validate_manifest(manifest)
    by_id = {manual["manual_id"]: manual for manual in manuals}
    rows = []
    started = time.perf_counter()
    for case in cases:
        paragraphs = by_id[case["manual_id"]]["paragraphs"]
        prediction = {"paragraph_ids": bm25_retrieve(case["query"], paragraphs)}
        rows.append({"case_id": case["case_id"], "split": case["split"], "source_family": case["source_family"],
                     "reference": {"gold_paragraph_ids": case["gold_paragraph_ids"], "answerable": case["answerable"]},
                     "prediction": prediction, "score": score_case(case, prediction)})
    latency_ms = (time.perf_counter() - started) * 1000 / len(cases)
    run_dir.mkdir(parents=True, exist_ok=True)
    raw = run_dir / "bm25-raw.jsonl"
    raw.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    heldout = [row for row in rows if row["split"] == "heldout"]
    answerable = [row for row in heldout if row["reference"]["answerable"]]
    unanswerable = [row for row in heldout if not row["reference"]["answerable"]]
    recall = sum(row["score"]["recall_at_5"] for row in answerable) / len(answerable)
    false_accepts = sum(row["score"]["no_answer_false_accept"] for row in unanswerable)
    upper = 1 - 0.05 ** (1 / len(unanswerable)) if false_accepts == 0 and unanswerable else None
    summary = {"application_id": "A04", "baseline": "bm25", "heldout_n": len(heldout),
               "answerable_n": len(answerable), "no_answer_n": len(unanswerable),
               "recall_at_5": recall, "no_answer_false_accept_n": false_accepts,
               "no_answer_false_accept_rate": false_accepts / len(unanswerable),
               "no_answer_false_accept_upper_95": upper, "mean_latency_ms": latency_ms,
               "peak_ram_mb": None, "source_family_unit": "one frozen manual/source family per case",
               "pilot_verdict": "NO_GO_BASELINE_DOMINANT" if recall >= 0.95 and upper is not None and upper <= 0.05 else "INCONCLUSIVE",
               "model_arms": "unavailable: C02-C08 and S01-S05 not verified",
               "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "raw_output": str(raw)}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/runbook-retrieval/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
