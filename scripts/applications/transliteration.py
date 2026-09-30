#!/usr/bin/env python3
"""Offline Russian transliteration and diacritic-restoration baselines for A09."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"\b[\w-]+\b", re.UNICODE)
ID_RE = re.compile(r"^ORD-\d{4}-\d{4}$")


class StudyError(ValueError):
    """Raised when a frozen A09 artifact violates its contract."""


def _expand(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    documents = []
    for blueprint in manifest.get("blueprints", []):
        for index in range(blueprint["count"]):
            noisy = blueprint["noisy"].format(index=index)
            clean = blueprint["clean"].format(index=index)
            documents.append({"document_id": f"{blueprint['prefix']}-{index:03d}", "split": blueprint["split"], "source_family": f"{blueprint['source_family_prefix']}-{index:03d}", "language": blueprint["language"], "noisy_text": noisy, "clean_text": clean, "protected_tokens": [token for token in TOKEN_RE.findall(clean) if ID_RE.fullmatch(token)], "ambiguous": blueprint["ambiguous"]})
    return documents


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if manifest.get("schema_version") != 1 or manifest.get("application_id") != "A09":
        raise StudyError("manifest must be schema 1 for A09")
    if manifest.get("license") != "CC0-1.0" or manifest.get("data_policy") != "synthetic-only":
        raise StudyError("manifest must declare synthetic CC0 data")
    documents = _expand(manifest)
    seen: set[str] = set()
    families: dict[str, str] = {}
    for document in documents:
        required = {"document_id", "split", "source_family", "language", "noisy_text", "clean_text", "protected_tokens", "ambiguous"}
        if not required.issubset(document) or document["document_id"] in seen:
            raise StudyError("document schema mismatch or duplicate ID")
        seen.add(document["document_id"])
        if document["split"] not in {"development", "validation", "heldout"} or document["language"] not in {"ru-latn", "ru-cyrl"}:
            raise StudyError("invalid split or language")
        family = document["source_family"]
        if family in families and families[family] != document["split"]:
            raise StudyError("source family crosses splits")
        families[family] = document["split"]
        for token in document["protected_tokens"]:
            if token not in document["clean_text"] or not ID_RE.fullmatch(token):
                raise StudyError("protected token is invalid")
    heldout = [item for item in documents if item["split"] == "heldout"]
    validation = [item for item in documents if item["split"] == "validation"]
    if len(heldout) < 100 or len({item["source_family"] for item in heldout}) != len(heldout):
        raise StudyError("heldout screening set must contain 100 independent documents")
    if len(validation) == 0 or {item["source_family"] for item in heldout} & {item["source_family"] for item in validation}:
        raise StudyError("validation must be disjoint from heldout")
    if {item["language"] for item in heldout} != {"ru-latn", "ru-cyrl"}:
        raise StudyError("heldout set must cover both frozen language directions")
    return documents


def transliterate(text: str, lexicon: dict[str, str]) -> str:
    if not isinstance(text, str) or not text:
        raise StudyError("text must be a non-empty string")
    if not isinstance(lexicon, dict):
        raise StudyError("lexicon must be a mapping")
    protected = {token for token in TOKEN_RE.findall(text) if ID_RE.fullmatch(token)}
    pieces: list[str] = []
    cursor = 0
    for match in TOKEN_RE.finditer(text):
        pieces.append(text[cursor:match.start()])
        token = match.group(0)
        pieces.append(token if token in protected else lexicon.get(token, token))
        cursor = match.end()
    pieces.append(text[cursor:])
    return "".join(pieces)


def score_document(document: dict[str, Any], prediction: str) -> dict[str, Any]:
    if not isinstance(prediction, str):
        raise StudyError("prediction must be a string")
    reference_tokens = TOKEN_RE.findall(document["clean_text"])
    prediction_tokens = TOKEN_RE.findall(prediction)
    protected = set(document["protected_tokens"])
    if len(reference_tokens) != len(prediction_tokens):
        return {"exact_word_n": 0, "scored_word_n": len([x for x in reference_tokens if x not in protected]), "protected_unchanged": 0, "protected_violation_n": 1, "ambiguous": int(document.get("ambiguous", False))}
    scored = [(expected, actual) for expected, actual in zip(reference_tokens, prediction_tokens) if expected not in protected]
    protected_unchanged = all(expected == actual for expected, actual in zip(reference_tokens, prediction_tokens) if expected in protected)
    return {"exact_word_n": sum(expected == actual for expected, actual in scored), "scored_word_n": len(scored), "protected_unchanged": int(protected_unchanged), "protected_violation_n": int(not protected_unchanged), "ambiguous": int(document.get("ambiguous", False))}


def run_baseline(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = validate_manifest(manifest)
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    started = time.perf_counter()
    for document in documents:
        for baseline, corrector in (("identity", lambda text: text), ("deterministic_transliterator_lexicon", lambda text: transliterate(text, manifest["lexicon"]))):
            prediction = corrector(document["noisy_text"])
            rows.append({"document_id": document["document_id"], "split": document["split"], "source_family": document["source_family"], "baseline": baseline, "prediction": prediction, "reference": document["clean_text"], "score": score_document(document, prediction)})
    raw = run_dir / "raw.jsonl"
    raw.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    heldout = [row for row in rows if row["split"] == "heldout"]
    metrics = {}
    for baseline in ("identity", "deterministic_transliterator_lexicon"):
        selected = [row for row in heldout if row["baseline"] == baseline]
        scored = sum(row["score"]["scored_word_n"] for row in selected)
        exact = sum(row["score"]["exact_word_n"] for row in selected)
        metrics[baseline] = {"exact_word_n": exact, "scored_word_n": scored, "exact_word_rate": exact / scored, "protected_unchanged_n": sum(row["score"]["protected_unchanged"] for row in selected), "protected_total_n": len(selected)}
    gain = metrics["deterministic_transliterator_lexicon"]["exact_word_rate"] - metrics["identity"]["exact_word_rate"]
    summary = {"application_id": "A09", "heldout_n": len({row["document_id"] for row in heldout}), "validation_n": len([item for item in documents if item["split"] == "validation"]), "metrics": metrics, "exact_word_gain_vs_identity": gain, "ambiguous_n": sum(1 for item in documents if item["split"] == "heldout" and item["ambiguous"]), "gate": {"exact_word_gain_minimum": 0.05, "protected_spans_unchanged": True, "uncertainty": "source-family intervals are not estimable for synthetic singleton families; verdict remains INCONCLUSIVE"}, "model_arms": {"ByT5-small": {"status": "unavailable", "reason": "dependency gates C02-C08 and S01-S05 not independently verified"}, "base_360m": {"status": "unavailable", "reason": "dependency gates C02-C08 and S01-S05 not independently verified"}, "lora_360m": {"status": "unavailable", "reason": "dependency gates C02-C08 and S01-S05 not independently verified"}}, "pilot": {"status": "not-run", "reason": "model arms unavailable and deterministic baseline leaves no justified pilot headroom"}, "cost": {"gpu_minutes": 0, "paid_api_calls": 0}, "verdict": "INCONCLUSIVE", "raw_output": str(raw), "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "mean_latency_ms": (time.perf_counter() - started) * 1000 / len(documents), "provenance": {"license": manifest["license"], "data_policy": manifest["data_policy"], "precedent": manifest["precedent"]}}
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("baseline", "pilot", "score"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("corpus/applications/transliteration/manifest.json"))
    args = parser.parse_args()
    if args.phase != "baseline":
        raise SystemExit("only baseline is available: model-score dependencies are not verified")
    print(json.dumps(run_baseline(args.run_dir, args.manifest), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
