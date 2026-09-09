#!/usr/bin/env python3
"""Offline PII span-highlighting baseline; suggestions require human review."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PII_TYPES = ("name", "email", "phone", "account_id")
MODEL_STATUS = {"status": "unavailable", "reason": "model scoring gated until dependency verification"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![\w-])\+?\d[\d ()-]{7,}\d(?!\w)")
ACCOUNT_RE = re.compile(r"(?<!\w)(?:ACCT|СЧЕТ)-\d{4}-\d{4}(?!\w)", re.IGNORECASE)
NAME_RE = re.compile(
    r"(?:Name|Имя):\s*("
    r"[A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)+|"
    r"[А-ЯЁ][а-яё]+(?:[ \t]+[А-ЯЁ][а-яё]+)+"
    r")"
)


class StudyError(ValueError):
    """Raised when a frozen A07 artifact violates its contract."""


def _entity(text: str, entity_type: str, start: int, end: int) -> dict[str, Any]:
    return {"type": entity_type, "start": start, "end": end, "text": text[start:end]}


def _expand_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    documents = list(manifest.get("documents", []))
    for blueprint in manifest.get("document_blueprints", []):
        for index in range(blueprint["count"]):
            value = blueprint["values"][index % len(blueprint["values"])]
            label = blueprint["label"]
            text = blueprint["template"].format(label=label, value=value, index=index)
            start = text.index(value)
            documents.append({
                "document_id": f"{blueprint['prefix']}-{index:03d}",
                "split": blueprint["split"],
                "source_family": f"{blueprint['source_family_prefix']}-{index:03d}",
                "format_family": blueprint["format_family"],
                "language": blueprint["language"],
                "text": text,
                "entities": [_entity(text, blueprint["entity_type"], start, start + len(value))],
            })
    return documents


def _check_entity(document: dict[str, Any], entity: dict[str, Any]) -> None:
    if not isinstance(entity, dict) or set(entity) != {"type", "start", "end", "text"}:
        raise StudyError("entity schema mismatch")
    if entity["type"] not in PII_TYPES:
        raise StudyError("unknown PII type")
    if not isinstance(entity["start"], int) or not isinstance(entity["end"], int):
        raise StudyError("entity offsets must be integers")
    if entity["start"] < 0 or entity["end"] > len(document["text"]) or entity["start"] >= entity["end"]:
        raise StudyError("entity offsets out of bounds")
    if document["text"][entity["start"] : entity["end"]] != entity["text"]:
        raise StudyError("entity text does not match offsets")


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A07":
        raise StudyError("manifest must be schema 1 for A07")
    if manifest.get("license") != "CC0-1.0" or manifest.get("data_policy") != "synthetic-only":
        raise StudyError("manifest must declare synthetic CC0 data")
    documents = _expand_manifest(manifest)
    if not documents:
        raise StudyError("documents must be nonempty")
    ids: set[str] = set()
    families: dict[str, str] = {}
    for document in documents:
        required = {"document_id", "split", "source_family", "format_family", "language", "text", "entities"}
        if not isinstance(document, dict) or not required.issubset(document):
            raise StudyError("document schema mismatch")
        if document["document_id"] in ids:
            raise StudyError("document IDs must be unique")
        ids.add(document["document_id"])
        if document["split"] not in {"development", "validation", "heldout"}:
            raise StudyError("invalid split")
        if document["language"] not in {"en", "ru"} or not isinstance(document["text"], str) or not document["text"].strip():
            raise StudyError("document language/text invalid")
        if not isinstance(document["entities"], list) or not document["entities"]:
            raise StudyError("document must have gold entities")
        if document["source_family"] in families and families[document["source_family"]] != document["split"]:
            raise StudyError("source family crosses splits")
        families[document["source_family"]] = document["split"]
        for entity in document["entities"]:
            _check_entity(document, entity)
    heldout = [document for document in documents if document["split"] == "heldout"]
    if len(heldout) < 100:
        raise StudyError("heldout screening set must contain at least 100 independent documents")
    if len({document["source_family"] for document in heldout}) != len(heldout):
        raise StudyError("heldout source families must be independent")
    if {document["language"] for document in heldout} != {"en", "ru"}:
        raise StudyError("heldout set must be multilingual")
    return documents


def detect_regex(text: str) -> list[dict[str, Any]]:
    """Return review suggestions with exact character offsets."""
    if not isinstance(text, str):
        raise StudyError("text must be a string")
    found: list[dict[str, Any]] = []
    for entity_type, pattern, group in (
        ("name", NAME_RE, 1),
        ("email", EMAIL_RE, 0),
        ("phone", PHONE_RE, 0),
        ("account_id", ACCOUNT_RE, 0),
    ):
        for match in pattern.finditer(text):
            start, end = match.span(group)
            found.append({"type": entity_type, "start": start, "end": end, "text": match.group(group), "confidence": 1.0})
    return sorted(found, key=lambda row: (row["start"], row["end"], row["type"]))


def score_document(document: dict[str, Any], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    gold = {(row["type"], row["start"], row["end"], row["text"]) for row in document["entities"]}
    checked: list[tuple[str, int, int, str]] = []
    for prediction in predictions:
        if not isinstance(prediction, dict) or not {"type", "start", "end", "text"}.issubset(prediction):
            raise StudyError("prediction schema mismatch")
        if prediction["type"] not in PII_TYPES or not isinstance(prediction["start"], int) or not isinstance(prediction["end"], int):
            raise StudyError("prediction type/offset invalid")
        if prediction["start"] < 0 or prediction["end"] > len(document["text"]) or prediction["start"] >= prediction["end"]:
            raise StudyError("prediction offsets out of bounds")
        if document["text"][prediction["start"] : prediction["end"]] != prediction["text"]:
            raise StudyError("prediction text does not match offsets")
        checked.append((prediction["type"], prediction["start"], prediction["end"], prediction["text"]))
    predicted = set(checked)
    return {
        "true_positive": len(gold & predicted),
        "false_positive": len(predicted - gold),
        "false_negative": len(gold - predicted),
        "exact_match": gold == predicted,
    }


def _wilson(successes: int, total: int) -> dict[str, float] | None:
    if total == 0:
        return None
    z = 1.96
    point = successes / total
    denominator = 1 + z * z / total
    centre = (point + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(point * (1 - point) / total + z * z / (4 * total * total)) / denominator
    return {"estimate": round(point, 6), "lower_95": round(max(0.0, centre - margin), 6), "upper_95": round(min(1.0, centre + margin), 6)}


def _metrics(rows: list[dict[str, Any]], documents: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, Counter[str]] = defaultdict(Counter)
    for row, document in zip(rows, documents):
        for entity in document["entities"]:
            key = entity["type"]
            by_type[key]["gold"] += 1
            by_type[key]["tp"] += row["score"]["true_positive"] if row["score"]["true_positive"] and key in {item["type"] for item in document["entities"]} else 0
            by_type[key]["fn"] += row["score"]["false_negative"]
        for prediction in row["prediction"]:
            by_type[prediction["type"]]["predicted"] += 1
            if (prediction["type"], prediction["start"], prediction["end"], prediction["text"]) in {
                (item["type"], item["start"], item["end"], item["text"]) for item in document["entities"]
            }:
                by_type[prediction["type"]]["tp_prediction"] += 1
    per_type = {}
    for entity_type in PII_TYPES:
        counts = by_type[entity_type]
        tp = counts["tp_prediction"]
        gold = counts["gold"]
        predicted = counts["predicted"]
        per_type[entity_type] = {
            "gold_n": gold,
            "predicted_n": predicted,
            "true_positive_n": tp,
            "false_negative_n": gold - tp,
            "recall": _wilson(tp, gold),
            "precision": _wilson(tp, predicted),
            "exact_offsets": (gold == tp),
        }
    return per_type


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = validate_manifest(manifest)
    heldout = [document for document in documents if document["split"] == "heldout"]
    run_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    rows = []
    for document in heldout:
        prediction = detect_regex(document["text"])
        rows.append({
            "document_id": document["document_id"],
            "split": document["split"],
            "source_family": document["source_family"],
            "prediction": prediction,
            "score": score_document(document, prediction),
        })
    raw = run_dir / "regex-raw.jsonl"
    raw.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    per_type = _metrics(rows, heldout)
    gate = all(
        item["recall"] is not None
        and item["recall"]["lower_95"] >= 0.99
        and item["precision"] is not None
        and item["precision"]["lower_95"] >= 0.90
        and item["exact_offsets"]
        for item in per_type.values()
    )
    summary = {
        "application_id": "A07",
        "split": {"heldout_n": len(heldout), "source_family_n": len({item["source_family"] for item in heldout}), "languages": sorted({item["language"] for item in heldout})},
        "baseline": "regex",
        "per_type": per_type,
        "gate": {"critical_types": list(PII_TYPES), "precision_minimum": 0.90, "recall_minimum": 0.99, "confidence": "Wilson 95%", "passed": gate},
        "verdict": "NO_GO_BASELINE_DOMINANT" if gate else "INCONCLUSIVE",
        "residual_risks": [
            "Suggestions are not automatic redaction and require human review.",
            "Regex can miss unseen spellings, obfuscation, OCR noise, and entity types outside the declared taxonomy.",
            "Synthetic CC0 documents do not establish performance on private or production records.",
            "False negatives remain possible even when the finite screening gate passes; no complete anonymization claim is made.",
        ],
        "model_arm": MODEL_STATUS,
        "raw_output": str(raw),
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "mean_latency_ms": round((time.perf_counter() - started) * 1000 / len(heldout), 6),
        "provenance": {"dataset_license": "CC0-1.0", "dataset_policy": "synthetic-only", "precedent": "https://arxiv.org/abs/2605.09973"},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/redaction-assistance/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
