#!/usr/bin/env python3
"""Offline contract gate for the frozen advisory dispatch corpus."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "runs/board-dispatch-v1/registration.json"
CORPUS = ROOT / "corpus/board-dispatch-v1/cases.jsonl"
REQUIRED = {"case_id", "family_id", "split", "task_id", "sanitized_text", "explicit_owner",
            "eligible_owner_ids", "role_descriptions", "dependency_state", "lease_state",
            "retry_budget", "observed_at", "label"}


def fail(message):
    raise AssertionError(message)


def main():
    reg = json.loads(REG.read_text())
    if reg.get("schema") != "tiny-fleet.board-dispatch.registration/v1" or not reg.get("advisory_only"):
        fail("registration schema/advisory_only")
    if reg["corpus"] != str(CORPUS.relative_to(ROOT)):
        fail("registration corpus path")
    digest = hashlib.sha256(CORPUS.read_bytes()).hexdigest()
    if reg["corpus_sha256"] != digest:
        fail(f"registration hash expected={reg['corpus_sha256']} observed={digest}")
    rows = [json.loads(line) for line in CORPUS.read_text().splitlines() if line]
    if not rows or len(rows) != sum(reg["splits"].values()):
        fail("row count")
    ids, families, counts = set(), {}, {}
    forbidden = ("/home/", "@", "ilya", "private", "secret")
    for row in rows:
        if set(row) != REQUIRED:
            fail(f"row fields {row.get('case_id')}")
        if row["case_id"] in ids or not isinstance(row["case_id"], str):
            fail("duplicate case_id")
        ids.add(row["case_id"])
        split = row["split"]
        if split not in {"train", "validation", "heldout"}:
            fail("split")
        counts[split] = counts.get(split, 0) + 1
        families.setdefault(row["family_id"], set()).add(split)
        if any(term in row["sanitized_text"].lower() for term in forbidden):
            fail("private or unsanitized text")
        if not isinstance(row["explicit_owner"], (str, type(None))) or not isinstance(row["eligible_owner_ids"], list):
            fail("typed case fields")
        if not set(row["label"]["allowed_owner_set"]).issubset(set(row["eligible_owner_ids"])):
            fail("owner outside eligible set")
        if row["label"]["review"] != "independent":
            fail("label provenance")
        if row["explicit_owner"] and row["label"]["allowed_owner_set"]:
            fail("explicit owner replaced by advisory label")
    if counts != reg["splits"]:
        fail("split counts")
    if any(len(splits) > 1 for splits in families.values()):
        fail("family crosses split")
    if not any(row["explicit_owner"] for row in rows) or not any(row["label"]["needs_clarification"] for row in rows):
        fail("missing explicit-owner/ambiguity controls")
    print(f"ACCEPT {len(rows)} sanitized cases; advisory-only; immutable registration")


if __name__ == "__main__":
    main()
