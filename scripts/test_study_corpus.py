#!/usr/bin/env python3
"""Offline contract gate for the frozen fleet-study corpus."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path

from build_study_corpus import COUNTS, DOMAINS, SPLITS, build


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "corpus" / "study-v1"
MANIFEST = STUDY / "manifest.json"
DATASETS = ROOT / "runs" / "fleet-study-v1" / "datasets.json"
REQUIRED = {
    "case_id", "source_family", "source_id", "domain", "language", "split",
    "prompt", "reference", "expected_route", "expected_action", "provenance", "created_at",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def language_of(text: str) -> str:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return "unknown"
    cyrillic = sum("\u0400" <= char <= "\u04ff" for char in letters)
    return "ru" if cyrillic / len(letters) >= 0.20 else "en"


def load_rows(study: Path):
    manifest = json.loads((study / "manifest.json").read_text())
    rows = []
    for split in SPLITS:
        path = study / f"{split}.jsonl"
        if manifest["sha256"][split] != hashlib.sha256(path.read_bytes()).hexdigest():
            fail(f"hash mismatch: {split}")
        rows.extend(json.loads(line) for line in path.read_text().splitlines() if line)
    return manifest, rows


def validate(study: Path) -> None:
    manifest, rows = load_rows(study)
    if manifest["schema"] != "tiny-fleet.study-corpus.manifest/v1":
        fail("manifest schema")
    if tuple(manifest["domains"]) != DOMAINS:
        fail("domain list")
    if manifest.get("reference_not_in_prompt") is not True:
        fail("reference separation declaration")
    if len(rows) != len(DOMAINS) * sum(COUNTS.values()):
        fail("total rows")
    ids, families, prompts, counts = set(), {}, set(), {domain: {split: 0 for split in SPLITS} for domain in DOMAINS}
    for row in rows:
        if set(row) != REQUIRED:
            fail(f"schema fields: {row.get('case_id')}")
        if row["case_id"] in ids or row["source_family"] in families:
            fail("duplicate case or source family")
        ids.add(row["case_id"])
        families[row["source_family"]] = row["split"]
        normalized_prompt = " ".join(row["prompt"].casefold().split())
        if normalized_prompt in prompts:
            fail(f"duplicate normalized prompt: {row['case_id']}")
        prompts.add(normalized_prompt)
        domain, split = row["domain"], row["split"]
        if domain not in DOMAINS or split not in SPLITS:
            fail("domain/split")
        counts[domain][split] += 1
        if row["language"] not in {"en", "ru"} or language_of(row["prompt"]) != row["language"]:
            fail(f"language mismatch: {row['case_id']}")
        if not row["prompt"].strip() or not row["reference"].strip():
            fail("empty prompt/reference")
        if row["reference"].casefold() in row["prompt"].casefold():
            fail(f"reference leaked into prompt: {row['case_id']}")
        provenance = row["provenance"]
        if provenance.get("kind") != "explicitly_authored" or provenance.get("license") != "CC0-1.0":
            fail("provenance")
        if provenance.get("source_family") != row["source_family"]:
            fail("provenance source family")
        if re.search(r"/home/|\.mesh|telegram|private log|secret", json.dumps(row).casefold()):
            fail("private material")
    expected = {domain: {split: COUNTS[split] for split in SPLITS} for domain in DOMAINS}
    if counts != expected:
        fail(f"counts: {counts}")
    if any(split not in SPLITS for split in families.values()):
        fail("source family crosses split")


def validate_dataset_registration() -> None:
    registration = json.loads(DATASETS.read_text())
    if registration["schema"] != "tiny-fleet.study-datasets/v1":
        fail("dataset registration schema")
    manifest_path = ROOT / registration["corpus_manifest"]
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != registration["corpus_manifest_sha256"]:
        fail("dataset registration manifest hash")
    manifest = json.loads(manifest_path.read_text())
    for split in SPLITS:
        item = registration["files"][split]
        path = ROOT / item["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            fail(f"dataset registration hash: {split}")
        if len(path.read_text().splitlines()) != item["rows"]:
            fail(f"dataset registration rows: {split}")
        if manifest["sha256"][split] != item["sha256"]:
            fail(f"manifest/registration mismatch: {split}")
    if registration.get("reference_not_in_generation_prompt") is not True:
        fail("generation separation declaration")


def validate_legacy_pilot_separation() -> None:
    """The new study prompt space must not reuse legacy toy-pilot records."""
    legacy_texts = set()
    for path in sorted((ROOT / "corpus").glob("*.jsonl")):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            text = row.get("prompt", row.get("text"))
            if isinstance(text, str):
                legacy_texts.add(" ".join(text.casefold().split()))
    for split in SPLITS:
        for line in (STUDY / f"{split}.jsonl").read_text().splitlines():
            row = json.loads(line)
            if not row["source_family"].startswith("authored-"):
                fail("study source family is not explicit/authored")
            if " ".join(row["prompt"].casefold().split()) in legacy_texts:
                fail(f"new corpus reuses legacy pilot prompt: {row['case_id']}")


def four_identical_fixture_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp:
        study = Path(temp) / "study-v1"
        build(study)
        path = study / "heldout.jsonl"
        rows = path.read_text().splitlines()
        duplicate = json.loads(rows[0])
        for index in range(4):
            copied = dict(duplicate)
            copied["case_id"] = f"duplicate-case-{index}"
            copied["source_family"] = f"duplicate-family-{index}"
            rows[index] = json.dumps(copied, sort_keys=True)
        path.write_text("\n".join(rows) + "\n")
        try:
            validate(study)
        except AssertionError:
            return
        fail("four-identical-case regression did not reject")


def main() -> None:
    validate(STUDY)
    validate_dataset_registration()
    validate_legacy_pilot_separation()
    four_identical_fixture_is_rejected()
    print("ACCEPT study corpus: family-disjoint splits, references separated, counts/languages/hashes valid")
    print("NEGATIVE MUTATION PASS: duplicate heldout case rejected")


if __name__ == "__main__":
    main()
