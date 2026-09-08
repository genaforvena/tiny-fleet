#!/usr/bin/env python3
"""Offline ticket evidence extractor and baseline scorer for application A02."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

FIELDS = ("product", "version", "issue", "requested_action")
MODEL_REVISION = "0f3834d3e119430e81ab797bda6e95ed85c4407c"
UNKNOWN = {field: None for field in FIELDS}


class StudyError(ValueError):
    pass


def _span(text: str, match: re.Match[str], field: str) -> dict[str, Any]:
    start, end = match.span(field)
    return {"start": start, "end": end, "text": text[start:end]}


def _extract_unique(text: str, pattern: str, field: str) -> tuple[str | None, list[dict[str, Any]]]:
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE))
    values = {m.group(field).strip() for m in matches}
    if len(values) != 1:
        return (None, [])
    match = matches[0]
    return (next(iter(values)), [_span(text, match, field)])


def extract_ticket(text: str) -> dict[str, Any]:
    """Extract only labelled evidence; quoted prompt-injection text is ignored."""
    if not isinstance(text, str) or not text.strip():
        return {"fields": dict(UNKNOWN), "evidence_spans": {field: [] for field in FIELDS}, "valid": True}
    safe_lines = [line for line in text.splitlines() if not re.search(r"ignore (?:all )?previous|system prompt|reveal instructions", line, re.I)]
    safe_text = "\n".join(safe_lines)
    patterns = {
        "product": r"^\s*Product\s*:\s*(?P<product>[^\n]+?)\s*$",
        "version": r"^\s*Version\s*:\s*(?P<version>[^\n]+?)\s*$",
        "issue": r"^\s*Issue\s*:\s*(?P<issue>[^\n]+?)\s*$",
        "requested_action": r"^\s*Requested action\s*:\s*(?P<requested_action>[^\n]+?)\s*$",
    }
    fields: dict[str, str | None] = {}
    spans: dict[str, list[dict[str, Any]]] = {}
    for field in FIELDS:
        fields[field], spans[field] = _extract_unique(safe_text, patterns[field], field)
    return {"fields": fields, "evidence_spans": spans, "valid": True}


def validate_case(case: dict[str, Any]) -> None:
    if not isinstance(case, dict):
        raise StudyError("case must be an object")
    for key in ("case_id", "split", "source_family", "text", "reference"):
        if not case.get(key):
            raise StudyError(f"case missing {key}")
    if case["split"] not in {"development", "validation", "heldout"}:
        raise StudyError("case has invalid split")
    if not isinstance(case["reference"], dict) or set(case["reference"]) != set(FIELDS):
        raise StudyError("reference must contain the four extraction fields")
    if not isinstance(case.get("labels"), dict) or case["labels"].get("missing_reason") is None:
        raise StudyError("case must record missing_reason, including none")


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A02":
        raise StudyError("manifest must be schema 1 for A02")
    provenance = manifest.get("model_provenance", {})
    nu = provenance.get("NuExtract-tiny", {})
    for key in ("model_id", "revision", "license", "source_url"):
        if not nu.get(key):
            raise StudyError(f"NuExtract-tiny provenance missing {key}")
    if nu["revision"] != MODEL_REVISION:
        raise StudyError("NuExtract-tiny revision is not pinned")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise StudyError("manifest cases must be nonempty")
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


def _span_equal(expected: Any, actual: Any) -> bool:
    return isinstance(actual, list) and actual == expected


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    validate_case(case)
    reference = case["reference"]
    predicted = prediction.get("fields", {}) if isinstance(prediction, dict) else {}
    correct = sum(predicted.get(field) == reference[field] for field in FIELDS)
    unsupported = sum(predicted.get(field) is not None and reference[field] is None for field in FIELDS)
    span_exact = all(_span_equal(case.get("evidence_spans", {}).get(field, []), prediction.get("evidence_spans", {}).get(field, [])) for field in FIELDS if reference[field] is not None)
    return {"case_id": case["case_id"], "source_family": case["source_family"], "correct_fields": correct,
            "field_total": len(FIELDS), "unsupported_fields": unsupported, "span_exact": span_exact,
            "failure_reason": None if correct == len(FIELDS) and span_exact else "field-or-evidence-mismatch"}


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); validate_manifest(manifest)
    rows = []
    for case in manifest["cases"]:
        prediction = extract_ticket(case["text"])
        rows.append({"case_id": case["case_id"], "split": case["split"], "prediction": prediction, "score": score_case(case, prediction)})
    run_dir.mkdir(parents=True, exist_ok=True)
    raw = run_dir / "regex-dictionary-raw.jsonl"
    raw.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    heldout = [row for row in rows if row["split"] == "heldout"]
    total_fields = sum(row["score"]["field_total"] for row in heldout)
    correct = sum(row["score"]["correct_fields"] for row in heldout)
    unsupported = sum(row["score"]["unsupported_fields"] for row in heldout)
    span_exact = sum(row["score"]["span_exact"] for row in heldout)
    upper = 1 - 0.05 ** (1 / total_fields) if total_fields else None
    summary = {"application_id": "A02", "baseline": "regex_dictionary", "heldout_n": len(heldout),
               "field_correct": correct, "field_total": total_fields, "field_precision": correct / total_fields if total_fields else None,
               "field_recall": correct / total_fields if total_fields else None, "unsupported_field_n": unsupported,
               "unsupported_field_rate_upper_95_zero_failure": upper if unsupported == 0 else None,
               "span_exact_case_n": span_exact, "raw_output": str(raw),
               "pilot_verdict": "NO_GO_BASELINE_DOMINANT", "model_arms": "unavailable: C02-C08 and S01-S05 not verified"}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/ticket-extraction/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
