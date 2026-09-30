#!/usr/bin/env python3
"""Measure frozen study labels and text overlap without changing the corpus."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import platform
import re
import sys

SPLITS = ("train", "validation", "heldout", "adversarial")
SAMPLE_LIMIT = 5
NUMBER = re.compile(r"(?<!\w)[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?!\w)")
LIMITATIONS = [
    "Source-group counts are distinct declared source_family labels, not verified independent sources.",
    "Reference-only equality is not full-example leakage: the normalized prompt may differ.",
    "Full-example equality means equality of the stored prompt/reference pair, not proof of causal training contamination.",
    "Numeric-template canonicalization is exploratory similarity, not proof of ancestry or contamination; it may remove meaningful numbers.",
    "Split names and other nonnumeric boilerplate are retained; zero overlap does not establish semantic independence.",
    "Only the four supplied JSONL files are measured; model pretraining data, rendered few-shot inputs, weights and training lineage are not audited.",
    "This audit neither estimates effective sample size nor establishes independent training seeds, registered wins, or deployment readiness.",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    return " ".join(text.split())


def numeric_template(text: str) -> str:
    return normalize(NUMBER.sub("", text))


def strict_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant {value}")


def load_corpus(corpus_dir: Path) -> tuple[dict, dict]:
    rows, bindings = {}, {}
    for split in SPLITS:
        path = corpus_dir / f"{split}.jsonl"
        data = path.read_bytes()
        bindings[split] = {"path": str(path), "sha256": sha256(data), "bytes": len(data)}
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{path}: invalid UTF-8 at byte {exc.start}") from exc
        rows[split] = []
        # JSONL boundaries are LF, not Unicode separators inside JSON strings.
        lines = text.split("\n")
        if lines[-1] == "":
            lines.pop()
        for line_no, line in enumerate(lines, 1):
            where = f"{path}:{line_no}"
            try:
                row = json.loads(line, object_pairs_hook=strict_object, parse_constant=reject_constant)
            except ValueError as exc:
                raise ValueError(f"{where}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{where}: expected a JSON object")
            for field in ("case_id", "source_family", "source_id", "domain", "split", "prompt", "reference"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise ValueError(f"{where}: {field} must be a nonempty string")
            if row["split"] != split:
                raise ValueError(f"{where}: split {row['split']!r} disagrees with file split {split!r}")
            provenance = row.get("provenance")
            if provenance is not None:
                if not isinstance(provenance, dict):
                    raise ValueError(f"{where}: provenance must be an object")
                if "source_family" in provenance and provenance["source_family"] != row["source_family"]:
                    raise ValueError(f"{where}: provenance.source_family disagrees with source_family")
            row["audit_line"] = line_no
            rows[split].append(row)
        if not rows[split]:
            raise ValueError(f"{path}: empty split; refusing a misleading empty audit")
    return rows, bindings


def locator(row: dict) -> dict:
    return {"case_id": row["case_id"], "split": row["split"], "domain": row["domain"], "line": row["audit_line"]}


def index_rows(rows: list, key) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[key(row)].append(row)
    return groups


def overlap(left: list, right: list | None, key, prompt_key=None) -> dict:
    """Count row pairs exactly using buckets; cap representatives, never counts."""
    a = index_rows(left, key)
    b = a if right is None else index_rows(right, key)
    matching_values = pairs = left_rows = right_rows = 0
    examples = []
    for value in sorted(a.keys() & b.keys()):
        x, y = a[value], b[value]
        count = len(x) * (len(x) - 1) // 2 if right is None else len(x) * len(y)
        if prompt_key is not None:
            cx = Counter(prompt_key(row) for row in x)
            cy = cx if right is None else Counter(prompt_key(row) for row in y)
            count -= (sum(n * (n - 1) // 2 for n in cx.values()) if right is None
                      else sum(n * cy.get(p, 0) for p, n in cx.items()))
            participating_x = sum(1 for row in x if len(y) > cy.get(prompt_key(row), 0))
            participating_y = sum(1 for row in y if len(x) > cx.get(prompt_key(row), 0))
        else:
            participating_x, participating_y = len(x), len(y)
        if not count:
            continue
        matching_values += 1
        pairs += count
        left_rows += participating_x
        right_rows += participating_y
        if len(examples) < SAMPLE_LIMIT:
            candidates = combinations(x, 2) if right is None else ((u, v) for u in x for v in y)
            for u, v in candidates:
                if prompt_key is not None and prompt_key(u) == prompt_key(v):
                    continue
                examples.append({"left": locator(u), "right": locator(v)})
                if len(examples) == SAMPLE_LIMIT:
                    break
    result = {"matching_value_count": matching_values, "matching_row_pair_count": pairs,
              "participating_left_rows": left_rows, "representative_case_pairs": examples}
    if right is not None:
        result["participating_right_rows"] = right_rows
    return result


def measurements(left: list, right: list | None, norm) -> dict:
    prompt = lambda row: norm(row["prompt"])
    reference = lambda row: norm(row["reference"])
    full = lambda row: (prompt(row), reference(row))
    return {"prompt": overlap(left, right, prompt),
            "reference": overlap(left, right, reference),
            "input_plus_reference": overlap(left, right, full),
            "reference_only_different_input": overlap(left, right, reference, prompt)}


def counts(rows: list) -> dict:
    return {"rows": len(rows), "unique_case_ids": len({r["case_id"] for r in rows}),
            "unique_source_groups": len({r["source_family"] for r in rows}),
            "unique_source_ids": len({r["source_id"] for r in rows})}


def duplicates(rows: list, field: str) -> dict:
    groups = index_rows(rows, lambda row: row[field])
    repeated = [{"value": value, "occurrences": len(group), "rows": [locator(r) for r in group]}
                for value, group in sorted(groups.items()) if len(group) > 1]
    return {"duplicate_value_count": len(repeated),
            "excess_row_count": sum(g["occurrences"] - 1 for g in repeated), "groups": repeated}


def audit(corpus_dir: Path) -> dict:
    rows, bindings = load_corpus(corpus_dir)
    all_rows = [row for split in SPLITS for row in rows[split]]
    domains = sorted({row["domain"] for row in all_rows})
    by_domain = {split: {domain: [r for r in rows[split] if r["domain"] == domain]
                         for domain in domains} for split in SPLITS}
    report = {"schema": "tiny-fleet.study-independence-audit/v1",
              "script": {"path": str(Path(__file__).resolve()),
                         "sha256": sha256(Path(__file__).read_bytes())},
              "python_version": platform.python_version(), "inputs": bindings,
              "source_group_field": "source_family",
              "input_field": "prompt",
              "normalization": "Unicode whitespace collapsed to ASCII spaces and stripped; case and punctuation retained",
              "numeric_template_regex": NUMBER.pattern,
              "representative_limit_per_measurement": SAMPLE_LIMIT,
              "limitations": LIMITATIONS, "total": counts(all_rows),
              "per_split": {split: {"total": counts(rows[split]),
                                    "domains": {domain: counts(by_domain[split][domain]) for domain in domains}}
                            for split in SPLITS},
              "duplicate_ids": {field: duplicates(all_rows, field) for field in ("case_id", "source_id")},
              "within_split": [], "cross_split": []}
    for split in SPLITS:
        for domain in [None] + domains:
            selected = rows[split] if domain is None else by_domain[split][domain]
            report["within_split"].append({"split": split, "domain": domain,
                "normalized_exact": measurements(selected, None, normalize),
                "exploratory_numeric_template": measurements(selected, None, numeric_template)})
    for left, right in combinations(SPLITS, 2):
        for domain in [None] + domains:
            x = rows[left] if domain is None else by_domain[left][domain]
            y = rows[right] if domain is None else by_domain[right][domain]
            report["cross_split"].append({"left_split": left, "right_split": right, "domain": domain,
                "source_label_overlap": {field: overlap(x, y, lambda row, f=field: row[f])
                                         for field in ("source_family", "source_id")},
                "normalized_exact": measurements(x, y, normalize),
                "exploratory_numeric_template": measurements(x, y, numeric_template)})
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new JSON file; never overwrite")
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError(f"output already exists: {args.output}")
        report = audit(args.corpus_dir)
        payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        # Exclusive creation also closes the race between the check and the write.
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
        print(json.dumps({"status": "measured", "output": str(args.output),
                          "output_sha256": sha256(payload.encode("utf-8")),
                          "rows": report["total"]["rows"]}, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"audit_study_independence: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
