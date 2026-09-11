#!/usr/bin/env python3
"""Dependency-free validator for a frozen tiny-fleet evaluation run."""

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path


REQUIRED = (
    "config.json", "environment.txt", "predictions.jsonl", "scores.json",
    "slices.tsv", "calibration.tsv", "routing.tsv", "adversarial.tsv",
    "cost.tsv", "decision.md",
)
SPLITS = ("train", "validation", "heldout", "adversarial")
ROW_FIELDS = (
    "case_id", "source_id", "created_at", "domain", "language", "split",
    "expected_route", "expected_action", "prompt", "reference", "source_family", "provenance",
)


class ValidationError(ValueError):
    """A stable, operator-facing contract rejection."""


def reject(category, detail):
    raise ValidationError(f"REJECT {category} {detail}".rstrip())


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path, category="manifest-mismatch"):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        reject(category, f"{path.name}: {exc}")


def load_rows(path, expected_split):
    rows = []
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        reject("missing-artifact", path.name)
    for line_no, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            reject("manifest-mismatch", f"{path.name}:{line_no}: {exc}")
        missing = [field for field in ROW_FIELDS if field not in row]
        if missing:
            reject("manifest-mismatch", f"{path.name}:{line_no}: missing {','.join(missing)}")
        if row["split"] != expected_split:
            reject("split-boundary", f"{row['case_id']} declares {row['split']} in {expected_split}")
        if not isinstance(row["case_id"], str) or not row["case_id"]:
            reject("manifest-mismatch", f"{path.name}:{line_no}: case_id")
        for field in ("source_id", "domain", "language", "prompt", "reference", "source_family"):
            if not isinstance(row[field], str) or not row[field].strip():
                reject("manifest-mismatch", f"{path.name}:{line_no}: {field}")
        rows.append(row)
    return rows


def parse_timestamp(value, label):
    if not isinstance(value, str) or not re.search(r"(?:Z|[+-]\d\d:\d\d)$", value):
        reject("split-boundary", f"{label} must be timezone-aware")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        reject("split-boundary", f"{label} invalid timestamp")


def normalize_prompt(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def validate_run(run_dir):
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        reject("missing-artifact", "manifest.json")
    manifest = load_json(manifest_path)
    if manifest.get("schema") not in {"tiny-fleet.deep-eval.manifest/v1", "tiny-fleet.deep-eval.manifest/v2"}:
        reject("manifest-mismatch", "schema")
    if manifest.get("schema") != "tiny-fleet.deep-eval.manifest/v2":
        reject("manifest-mismatch", "legacy v1 is archival-only")
    for name in REQUIRED:
        if not (run_dir / name).is_file():
            reject("missing-artifact", name)
    config_hash = sha256(run_dir / "config.json")
    if manifest.get("config_sha256") != config_hash:
        reject("manifest-mismatch", f"config.json sha256 expected={manifest.get('config_sha256')} observed={config_hash}")
    datasets = manifest.get("datasets", {})
    all_rows = []
    cutoff = manifest.get("cutoff")
    cutoff_dt = parse_timestamp(cutoff, "cutoff")
    temporal = manifest.get("temporal")
    if not isinstance(temporal, dict):
        reject("manifest-mismatch", "temporal")
    train_end = parse_timestamp(temporal.get("train_end"), "train_end")
    heldout_start = parse_timestamp(temporal.get("heldout_start"), "heldout_start")
    if train_end > heldout_start:
        reject("split-boundary", "contradictory temporal windows")
    for split in SPLITS:
        spec = datasets.get(split)
        if not isinstance(spec, dict) or not spec.get("path"):
            reject("manifest-mismatch", f"datasets.{split}")
        if not isinstance(spec["path"], str) or Path(spec["path"]).is_absolute():
            reject("manifest-mismatch", f"dataset outside run: {spec.get('path')}")
        path = (run_dir / spec["path"]).resolve()
        try:
            path.relative_to(run_dir.resolve())
        except ValueError:
            reject("manifest-mismatch", f"dataset outside run: {spec['path']}")
        if not path.is_file():
            reject("missing-artifact", spec["path"])
        rows = load_rows(path, split)
        if not rows:
            reject("manifest-mismatch", f"empty {split}")
        observed_hash = sha256(path)
        if spec.get("sha256") != observed_hash:
            reject("manifest-mismatch", f"{spec['path']} sha256 expected={spec.get('sha256')} observed={observed_hash}")
        if spec.get("rows") != len(rows):
            reject("manifest-mismatch", f"{spec['path']} rows expected={spec.get('rows')} observed={len(rows)}")
        for row in rows:
            created = parse_timestamp(row["created_at"], row["case_id"])
            if created > cutoff_dt:
                reject("split-boundary", f"{row['case_id']} after cutoff {cutoff}")
            if split == "train" and created > train_end:
                reject("split-boundary", f"{row['case_id']} after train_end")
            if split == "heldout" and created < heldout_start:
                reject("split-boundary", f"{row['case_id']} before heldout_start")
            if split in ("heldout", "adversarial") and created > cutoff_dt:
                reject("split-boundary", f"{row['case_id']} after cutoff {cutoff}")
            row["_split_file"] = split
        all_rows.extend(rows)
    by_case = {}
    by_source = {}
    by_family = {}
    seen_ids = set()
    for row in all_rows:
        case = row["case_id"]
        split = row["_split_file"]
        if (split, case) in seen_ids:
            reject("manifest-mismatch", f"duplicate case_id={case} in {split}")
        seen_ids.add((split, case))
        if case in by_case and by_case[case]["_split_file"] != row["_split_file"]:
            reject("leakage", f"case_id={case} crosses {by_case[case]['_split_file']}/{row['_split_file']}")
        by_case[case] = row
        by_source.setdefault(row["source_id"], set()).add(row["_split_file"])
        by_family.setdefault(row["source_family"], set()).add(split)
    for family, splits in by_family.items():
        if ("train" in splits and "validation" in splits) or ("validation" in splits and "heldout" in splits):
            reject("split-boundary", f"source_family={family} crosses {'/'.join(sorted(splits))}")
    for source, splits in by_source.items():
        if "train" in splits and any(split in splits for split in ("heldout", "adversarial")):
            reject("split-boundary", f"source_id={source} crosses {'/'.join(sorted(splits))}")
    texts = {}
    for row in all_rows:
        text = normalize_prompt(row["prompt"])
        if text in texts and texts[text]["_split_file"] != row["_split_file"]:
            reject("leakage", f"normalized prompt crosses {texts[text]['_split_file']}/{row['_split_file']}")
        texts[text] = row
    expected = {(row["case_id"], model) for row in all_rows if row["_split_file"] in ("heldout", "adversarial")
                for model in manifest.get("controls", []) + [manifest.get("candidate", {}).get("id")]}
    seen = set()
    for line in (run_dir / "predictions.jsonl").read_text().splitlines():
        try:
            prediction = json.loads(line)
        except json.JSONDecodeError as exc:
            reject("prediction-cardinality", str(exc))
        pair = (prediction.get("case_id"), prediction.get("model"))
        if pair not in expected:
            reject("prediction-cardinality", f"unexpected {pair}")
        seen.add(pair)
    if seen != expected:
        reject("prediction-cardinality", f"expected={len(expected)} observed={len(seen)}")
    return "ACCEPT"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    try:
        print(validate_run(args.run_dir))
    except ValidationError as exc:
        print(exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
