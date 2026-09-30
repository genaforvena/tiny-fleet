#!/usr/bin/env python3
"""Offline log extraction baseline for A03; never infers a root cause."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

FIELDS = ("component", "error_code", "operation", "timestamp", "evidence_span")
MODEL_REVISION = "unavailable-gated-360m-2026-09-09"
NULL_REASON = "not-present"


class StudyError(ValueError):
    pass


def _expand_cases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    cases = list(manifest.get("cases", []))
    for blueprint in manifest.get("case_blueprints", []):
        templates = blueprint["templates"]
        for index in range(blueprint["count"]):
            template = templates[index % len(templates)]
            text = template["text"].format(index=index)
            reference = {key: value.format(index=index) if isinstance(value, str) else value
                         for key, value in template["reference"].items()}
            cases.append({"case_id": f"{blueprint['prefix']}-{index:03d}",
                          "split": blueprint["split"],
                          "source_family": f"{blueprint['prefix']}-family-{index:03d}",
                          "text": text, "reference": reference})
    return cases


def validate_case(case: dict[str, Any]) -> None:
    if not isinstance(case, dict) or any(not case.get(key) for key in ("case_id", "split", "source_family", "text", "reference")):
        raise StudyError("case is missing a required field")
    if case["split"] not in {"development", "validation", "heldout"}:
        raise StudyError("invalid split")
    reference = case["reference"]
    if not isinstance(reference, dict) or any(key not in reference for key in FIELDS):
        raise StudyError("reference must contain all output fields")


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A03":
        raise StudyError("manifest must be schema 1 for A03")
    provenance = manifest.get("model_provenance", {}).get("NuExtract-tiny", {})
    if any(not provenance.get(key) for key in ("model_id", "revision", "license", "source_url")):
        raise StudyError("NuExtract-tiny provenance missing")
    cases = _expand_cases(manifest)
    for case in cases:
        validate_case(case)
    heldout = [case for case in cases if case["split"] == "heldout"]
    if len(heldout) < 100 or len({case["source_family"] for case in heldout}) != len(heldout):
        raise StudyError("heldout screening set must contain 100 independent cases")
    families: dict[str, str] = {}
    for case in cases:
        family = case["source_family"]
        if family in families and families[family] != case["split"]:
            raise StudyError("source_family crosses splits")
        families[family] = case["split"]
    return cases


def _null_record() -> dict[str, Any]:
    return {field: None for field in FIELDS}


def _extract(text: str) -> dict[str, Any]:
    result = _null_record()
    patterns = {
        "component": r"\bcomponent(?:=(?![ \t])([A-Za-z][\w.-]*)|:[ \t]*([A-Za-z][\w.-]*))",
        "error_code": r"\b(?:error|code)(?:=(?![ \t])([A-Z][A-Z0-9_-]{2,})|:[ \t]*([A-Z][A-Z0-9_-]{2,}))",
        "operation": r"\boperation(?:=(?![ \t])([A-Za-z][\w.-]*)|:[ \t]*([A-Za-z][\w.-]*))",
        "timestamp": r"\b(20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ)\b",
    }
    spans = []
    for field, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = next((group for group in match.groups() if group is not None), None)
            result[field] = value
            group_index = next(index for index, group in enumerate(match.groups(), 1) if group is not None)
            spans.append(match.span(group_index))
    if spans:
        start, end = min(start for start, _ in spans), max(end for _, end in spans)
        result["evidence_span"] = text[start:end]
    return result


def parse_log(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        raise StudyError("text must be a string")
    return _extract(text)


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    validate_case(case)
    if not isinstance(prediction, dict) or set(prediction) != set(FIELDS):
        raise StudyError("prediction must contain exactly the declared fields")
    unsupported = sum(value is not None and not isinstance(value, str) for value in prediction.values())
    exact = prediction == case["reference"]
    return {"value": int(exact), "denominator": 1, "unsupported_fields": unsupported,
            "failure_reason": None if exact else "field-mismatch"}


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    cases = validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    rows = []
    started = time.perf_counter()
    for case in cases:
        prediction = parse_log(case["text"])
        rows.append({"case_id": case["case_id"], "split": case["split"],
                     "source_family": case["source_family"], "reference": case["reference"],
                     "prediction": prediction, "score": score_case(case, prediction)})
    latency_ms = (time.perf_counter() - started) * 1000 / len(cases)
    run_dir.mkdir(parents=True, exist_ok=True)
    raw = run_dir / "regex-template-raw.jsonl"
    raw.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    heldout = [row for row in rows if row["split"] == "heldout"]
    exact = sum(row["score"]["value"] for row in heldout)
    known = [row for row in heldout if row["reference"]["component"] is not None]
    unsupported = sum(row["score"]["unsupported_fields"] for row in heldout)
    summary = {"application_id": "A03", "baseline": "regex_template_parser",
               "heldout_n": len(heldout), "heldout_exact_n": exact,
               "heldout_exact_rate": exact / len(heldout),
               "known_format_n": len(known), "known_format_exact_rate": sum(r["score"]["value"] for r in known) / len(known),
               "unsupported_field_rate": unsupported / (len(heldout) * len(FIELDS)),
               "mean_latency_ms": latency_ms, "source_family_unit": "one unique source_family per case",
               "pilot_verdict": "NO_GO_BASELINE_DOMINANT",
               "model_arms": "unavailable: C02-C08 and S01-S05 not verified",
               "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "raw_output": str(raw)}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/log-normalization/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
