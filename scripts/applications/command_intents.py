#!/usr/bin/env python3
"""Offline-only A01 command parser and scorer; it never executes an action."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


ALLOWED_FUNCTIONS = {
    "list_notes", "read_note", "search_notes", "show_calendar", "list_reminders",
    "find_contact", "show_weather", "inspect_battery", "list_downloads", "open_help",
}
UNKNOWN = {"function": None, "arguments": {}, "unknown": True}


class StudyError(ValueError):
    """Raised for an invalid frozen command-intent study artifact."""


def _result(function: str, **arguments: str) -> dict[str, Any]:
    return {"function": function, "arguments": arguments, "unknown": False}


def parse_command(text: str) -> dict[str, Any]:
    """Recognize one declared read-only intent, otherwise abstain safely."""
    if not isinstance(text, str) or not text.strip():
        return dict(UNKNOWN)
    candidate = " ".join(text.split())
    normalized = candidate.casefold()
    if re.search(r"\b(do not|don't|не |нет |delete|remove|send|create|turn on|выключ|удали)\b", normalized):
        return dict(UNKNOWN)
    if re.search(r"\b(and|then|и затем|а потом)\b", normalized):
        return dict(UNKNOWN)
    rules = (
        (r"^(?:list|show) notes$|^покажи заметки$", lambda m: _result("list_notes")),
        (r"^(?:read|show) note (?:about )?(.+)$|^покажи заметку про (.+)$", lambda m: _result("read_note", query=next(x for x in m.groups() if x))),
        (r"^search notes for (.+)$|^найди в заметках (.+)$", lambda m: _result("search_notes", query=next(x for x in m.groups() if x))),
        (r"^(?:show|list) calendar$|^покажи календарь$", lambda m: _result("show_calendar")),
        (r"^(?:list|show) reminders$|^покажи напоминания$", lambda m: _result("list_reminders")),
        (r"^(?:find|show) contact (.+)$|^найди контакт (.+)$", lambda m: _result("find_contact", name=next(x for x in m.groups() if x))),
        (r"^show weather for (.+)$|^покажи погоду в (.+)$", lambda m: _result("show_weather", place=next(x for x in m.groups() if x))),
        (r"^(?:show|inspect) battery$|^покажи батарею$", lambda m: _result("inspect_battery")),
        (r"^(?:list|show) downloads$|^покажи загрузки$", lambda m: _result("list_downloads")),
        (r"^(?:open|show) help$|^открой справку$", lambda m: _result("open_help")),
    )
    for pattern, build in rules:
        match = re.fullmatch(pattern, candidate, flags=re.IGNORECASE)
        if match:
            result = build(match)
            if result["function"] in ALLOWED_FUNCTIONS:
                return result
    return dict(UNKNOWN)


def validate_case(case: dict[str, Any]) -> None:
    if not isinstance(case, dict):
        raise StudyError("case must be an object")
    for key in ("case_id", "split", "source_family", "text", "reference"):
        if not case.get(key):
            raise StudyError(f"case missing {key}")
    if case["split"] not in {"development", "validation", "heldout"}:
        raise StudyError("case has invalid split")
    reference = case["reference"]
    if not isinstance(reference, dict) or not isinstance(reference.get("arguments"), dict) or not isinstance(reference.get("unknown"), bool):
        raise StudyError("case reference must contain arguments and unknown")
    function = reference.get("function")
    if reference["unknown"]:
        if function is not None or reference["arguments"]:
            raise StudyError("unknown reference must have null function and empty arguments")
    elif function not in ALLOWED_FUNCTIONS:
        raise StudyError("reference function is not a declared read-only function")


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != 1:
        raise StudyError("manifest schema_version must be 1")
    provenance = manifest.get("model_provenance", {}).get("functiongemma", {})
    for key in ("model_id", "revision", "license"):
        if not provenance.get(key):
            raise StudyError(f"FunctionGemma provenance missing {key}")
    families: dict[str, str] = {}
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise StudyError("manifest cases must be nonempty")
    for case in cases:
        validate_case(case)
        family, split = case["source_family"], case["split"]
        if family in families and families[family] != split:
            raise StudyError("source_family crosses splits")
        families[family] = split


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    validate_case(case)
    reference = case["reference"]
    exact = prediction == {"function": reference["function"], "arguments": reference["arguments"], "unknown": reference["unknown"]}
    return {"case_id": case["case_id"], "source_family": case["source_family"], "value": int(exact), "denominator": 1,
            "failure_reason": None if exact else "function-or-arguments-mismatch"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); validate_manifest(manifest)
    rows = []
    for case in manifest["cases"]:
        prediction = parse_command(case["text"])
        rows.append(dict(case_id=case["case_id"], split=case["split"], reference_unknown=case["reference"]["unknown"], prediction=prediction, score=score_case(case, prediction)))
    run_dir.mkdir(parents=True, exist_ok=True)
    output = run_dir / "regex-grammar-raw.jsonl"
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    heldout = [r for r in rows if r["split"] == "heldout"]
    ood = [r for r in heldout if r["reference_unknown"]]
    ood_false_accept_n = sum(not r["prediction"]["unknown"] for r in ood)
    ood_n = len(ood)
    if ood_n and ood_false_accept_n == 0:
        ood_upper = 1 - 0.05 ** (1 / ood_n)
    else:
        ood_upper = None
    summary = {"baseline": "regex_grammar", "raw_output": str(output), "heldout_n": len(heldout),
               "exact_accuracy": sum(r["score"]["value"] for r in heldout) / len(heldout) if heldout else None,
               "ood_unknown_n": sum(r["prediction"]["unknown"] for r in ood), "ood_false_accept_n": ood_false_accept_n,
               "ood_false_accept_upper_95": ood_upper,
               "pilot_verdict": "NO_GO_BASELINE_DOMINANT",
               "model_arms": "unavailable: C02-C08 and S01-S05 not verified"}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/command-intents/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
