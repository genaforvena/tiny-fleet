#!/usr/bin/env python3
"""Offline protected-text correction baselines for application A08."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


class StudyError(ValueError):
    """Raised when a frozen A08 artifact violates its contract."""


def _protected(text: str, value: str, kind: str) -> dict[str, Any]:
    start = text.index(value)
    return {"start": start, "end": start + len(value), "text": value, "kind": kind}


def _expand(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    documents = []
    for blueprint in manifest.get("blueprints", []):
        for index in range(blueprint["count"]):
            identifier = f"ORD-2026-{index + 1:04d}"
            clean = blueprint["clean"].format(id=identifier)
            noisy = blueprint["noisy"].format(id=identifier)
            documents.append({
                "document_id": f"{blueprint['prefix']}-{index:03d}",
                "split": blueprint["split"],
                "source_family": f"{blueprint['source_family_prefix']}-{index:03d}",
                "language": blueprint["language"],
                "clean_text": clean,
                "noisy_text": noisy,
                "protected_spans": [_protected(clean, identifier, manifest["protected_kind"])],
            })
    return documents


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A08":
        raise StudyError("manifest must be schema 1 for A08")
    if manifest.get("license") != "CC0-1.0" or manifest.get("data_policy") != "synthetic-only":
        raise StudyError("manifest must declare synthetic CC0 data")
    documents = _expand(manifest)
    if not documents:
        raise StudyError("documents must be non-empty")
    seen: set[str] = set()
    families: dict[str, str] = {}
    for document in documents:
        required = {"document_id", "split", "source_family", "language", "clean_text", "noisy_text", "protected_spans"}
        if not required.issubset(document) or document["document_id"] in seen:
            raise StudyError("document schema mismatch or duplicate ID")
        seen.add(document["document_id"])
        if document["split"] not in {"development", "validation", "heldout"} or document["language"] not in {"en", "ru"}:
            raise StudyError("invalid split or language")
        family = document["source_family"]
        if family in families and families[family] != document["split"]:
            raise StudyError("source family crosses splits")
        families[family] = document["split"]
        for span in document["protected_spans"]:
            if document["clean_text"][span["start"]:span["end"]] != span["text"]:
                raise StudyError("protected span does not match clean text")
    heldout = [item for item in documents if item["split"] == "heldout"]
    validation = [item for item in documents if item["split"] == "validation"]
    if len(heldout) < 100 or len({item["source_family"] for item in heldout}) != len(heldout):
        raise StudyError("heldout screening set must contain 100 independent documents")
    if len(validation) == 0 or {item["source_family"] for item in heldout} & {item["source_family"] for item in validation}:
        raise StudyError("validation must be disjoint from heldout")
    if {item["language"] for item in heldout} != {"en", "ru"}:
        raise StudyError("heldout set must be multilingual")
    return documents


def correct_identity(text: str) -> str:
    if not isinstance(text, str) or not text:
        raise StudyError("text must be a non-empty string")
    return text


def correct_dictionary(text: str, dictionary: dict[str, str]) -> str:
    if not isinstance(text, str) or not text:
        raise StudyError("text must be a non-empty string")
    if not isinstance(dictionary, dict):
        raise StudyError("dictionary must be a mapping")
    result = text
    for source, target in sorted(dictionary.items(), key=lambda pair: (-len(pair[0]), pair[0])):
        result = result.replace(source, target)
    return result


def _distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, 1):
        current = [i]
        for j, right_char in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left_char != right_char)))
        previous = current
    return previous[-1]


def _span_values(text: str, spans: list[dict[str, Any]]) -> list[str]:
    return [text[span["start"]:span["end"]] for span in spans]


def score_document(document: dict[str, Any], prediction: str) -> dict[str, Any]:
    if not isinstance(prediction, str):
        raise StudyError("prediction must be a string")
    reference = document["clean_text"] if "clean_text" in document else document["reference"]
    protected = document["protected_spans"]
    reference_values = _span_values(reference, protected)
    prediction_values = _span_values(prediction, protected) if all(span["end"] <= len(prediction) for span in protected) else []
    unchanged = int(reference_values == prediction_values)
    return {
        "cer": _distance(prediction, reference) / max(1, len(reference)),
        "protected_unchanged": unchanged,
        "protected_violation_n": 0 if unchanged else 1,
        "exact": int(prediction == reference),
    }


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = validate_manifest(manifest)
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    started = time.perf_counter()
    for document in documents:
        for baseline, corrector in (("identity", correct_identity), ("dictionary_edit_distance", lambda text: correct_dictionary(text, manifest["dictionary"]))):
            prediction = corrector(document["noisy_text"])
            rows.append({"document_id": document["document_id"], "split": document["split"], "source_family": document["source_family"], "baseline": baseline, "prediction": prediction, "reference": document["clean_text"], "score": score_document(document, prediction)})
    raw = run_dir / "raw.jsonl"
    raw.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    heldout = [row for row in rows if row["split"] == "heldout"]
    metrics = {}
    for baseline in ("identity", "dictionary_edit_distance"):
        selected = [row for row in heldout if row["baseline"] == baseline]
        metrics[baseline] = {"cer_mean": sum(row["score"]["cer"] for row in selected) / len(selected), "exact_n": sum(row["score"]["exact"] for row in selected), "protected_field_unchanged_n": sum(row["score"]["protected_unchanged"] for row in selected), "protected_field_n": len(selected)}
    strongest = min(metrics, key=lambda key: metrics[key]["cer_mean"])
    reduction = (metrics["identity"]["cer_mean"] - metrics[strongest]["cer_mean"]) / max(metrics["identity"]["cer_mean"], 1e-12)
    summary = {
        "application_id": "A08", "heldout_n": len({row["document_id"] for row in heldout}), "validation_n": len([row for row in documents if row["split"] == "validation"]), "metrics": {"baselines": metrics, "strongest_baseline": strongest, "relative_cer_reduction_vs_identity": reduction, "protected_field": {"unchanged_n": metrics[strongest]["protected_field_unchanged_n"], "total_n": metrics[strongest]["protected_field_n"], "corruption_rate": 1 - metrics[strongest]["protected_field_unchanged_n"] / metrics[strongest]["protected_field_n"]}},
        "gate": {"relative_cer_reduction_minimum": 0.20, "clean_field_corruption_maximum": 0.005, "protected_fields_unchanged": True, "uncertainty": "source-family intervals are not estimable for synthetic singleton families; verdict remains INCONCLUSIVE"},
        "model_arms": {"ByT5-small": {"status": "unavailable", "reason": "dependency gates C02-C08 and S01-S05 not independently verified"}, "360m_lora": {"status": "unavailable", "reason": "dependency gates C02-C08 and S01-S05 not independently verified"}},
        "verdict": "INCONCLUSIVE", "pilot": {"status": "not-run", "reason": "model arms unavailable and baseline headroom is not sufficient for a justified pilot"}, "cost": {"gpu_minutes": 0, "paid_api_calls": 0}, "raw_output": str(raw), "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "mean_latency_ms": (time.perf_counter() - started) * 1000 / len(documents), "provenance": {"license": manifest["license"], "data_policy": manifest["data_policy"], "precedent": manifest["precedent"]}
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/noisy-text-correction/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
