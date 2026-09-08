#!/usr/bin/env python3
"""Offline contract validator for the application exploration registry.

This module deliberately does not import a model, access a network, or execute
an application.  It validates the frozen study contract that later pilots use.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


class RegistryError(ValueError):
    """Raised when a registry or screening case violates the frozen contract."""


def zero_failure_upper_bound(n: int, confidence: float = 0.95) -> float:
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("n must be a positive integer")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    return 1.0 - (1.0 - confidence) ** (1.0 / n)


def minimum_zero_failure_sample(target_rate: float, confidence: float = 0.95) -> int:
    if not 0 < target_rate < 1:
        raise ValueError("target_rate must be between 0 and 1")
    n = 1
    while zero_failure_upper_bound(n, confidence) > target_rate:
        n += 1
    return n


def load_registry(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read registry: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryError("registry must be an object")
    return value


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise RegistryError(f"{where}: missing field {key}")
    return mapping[key]


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise RegistryError("registry: schema_version must be 1")
    applications = _require(registry, "applications", "registry")
    if not isinstance(applications, list) or len(applications) != 10:
        raise RegistryError("registry: applications must contain exactly ten entries")
    if registry.get("sample_size_contract", {}).get("zero_failure_upper_95") != "1-0.05**(1/n)":
        raise RegistryError("registry: missing exact zero-failure sample contract")

    ids: set[str] = set()
    for item in applications:
        if not isinstance(item, dict):
            raise RegistryError("application entry must be an object")
        app_id = _require(item, "application_id", "application")
        if app_id in ids:
            raise RegistryError(f"duplicate application_id: {app_id}")
        ids.add(app_id)
        for key in ("task_kind", "source", "baseline", "metric", "gate", "cost_cap", "input_schema", "output_schema", "state", "run_hashes"):
            _require(item, key, app_id)
        if not isinstance(item["source"], dict) or not str(item["source"].get("url", "")).startswith("https://"):
            raise RegistryError(f"{app_id}: source URL must be HTTPS")
        if not item["source"].get("license"):
            raise RegistryError(f"{app_id}: source license is required")
        baselines = item["baseline"]
        if not isinstance(baselines, list) or not baselines or not all(isinstance(x, dict) for x in baselines):
            raise RegistryError(f"{app_id}: baseline must be a non-empty list of objects")
        if not any(not bool(x.get("llm", False)) for x in baselines):
            raise RegistryError(f"{app_id}: explicit non-LLM competitor required")
        if not isinstance(item["gate"], str) or not item["gate"].strip():
            raise RegistryError(f"{app_id}: preregistered gate is required")
        cap = item["cost_cap"]
        if not isinstance(cap, dict) or cap.get("gpu_minutes") != 30 or cap.get("gpu_jobs") != 1 or cap.get("paid_api") is not False:
            raise RegistryError(f"{app_id}: cost cap must be 30 GPU minutes, one job, no paid API")
        if not isinstance(item["input_schema"], dict) or not item["input_schema"].get("required"):
            raise RegistryError(f"{app_id}: input schema required fields missing")
        if not isinstance(item["output_schema"], dict) or not item["output_schema"].get("fields"):
            raise RegistryError(f"{app_id}: output schema fields missing")
        if item["state"] not in {"registered", "no-go", "inconclusive", "shortlisted"}:
            raise RegistryError(f"{app_id}: invalid state")
        if not isinstance(item["run_hashes"], list) or not all(isinstance(x, str) for x in item["run_hashes"]):
            raise RegistryError(f"{app_id}: run_hashes must be a list of strings")
    if ids != {f"A{i:02d}" for i in range(1, 11)}:
        raise RegistryError("registry: application IDs must be A01 through A10")


def validate_case(case: dict[str, Any], seen_source_families: set[str] | None = None) -> None:
    if not isinstance(case, dict):
        raise RegistryError("case must be an object")
    for key in ("case_id", "split", "source_family", "input", "reference", "score"):
        _require(case, key, "case")
    family = case["source_family"]
    if not isinstance(family, str) or not family.strip():
        raise RegistryError("case: source_family is required")
    if seen_source_families is not None and family in seen_source_families:
        raise RegistryError("case: source_family duplicated; cannot count as independent")
    if case["split"] not in {"development", "validation", "heldout"}:
        raise RegistryError("case: invalid split")
    if not isinstance(case["input"], dict) or not isinstance(case["reference"], dict):
        raise RegistryError("case: input and reference must be objects")
    for name, value in case["reference"].items():
        if value is None and not (isinstance(case.get("missing"), dict) and name in case["missing"]):
            raise RegistryError(f"case: missing field {name} requires a reason")
    score = case["score"]
    if not isinstance(score, dict) or "value" not in score or "denominator" not in score:
        raise RegistryError("case: score fields missing")
    if score.get("value") is None:
        if not score.get("reason"):
            raise RegistryError("case: unavailable score requires a reason")
    elif score.get("is_probability") and score.get("calibrated") is not True:
        raise RegistryError("case: probability score must be calibrated")
    elif not isinstance(score["value"], (int, float)) or isinstance(score["value"], bool) or not math.isfinite(score["value"]):
        raise RegistryError("case: score value must be finite")
    if not isinstance(score["denominator"], int) or isinstance(score["denominator"], bool) or score["denominator"] < 0:
        raise RegistryError("case: denominator must be a non-negative integer")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if not args.validate:
        parser.error("--validate is required")
    try:
        registry = load_registry(args.registry)
        validate_registry(registry)
    except RegistryError as exc:
        print(f"INVALID: {exc}")
        return 1
    print(json.dumps({"status": "valid", "applications": len(registry["applications"]), "registry": str(args.registry)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
