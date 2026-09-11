#!/usr/bin/env python3
"""Reproducible descriptive lexical measurements for a D01 extraction run."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[1]
DICTIONARY = ROOT / "docs" / "concepts-v1.json"
TOKEN_RE = re.compile(r"(?u)\b[\w]+\b")


def tokenize(text):
    return TOKEN_RE.findall(text.casefold())


def dictionary_source():
    raw = DICTIONARY.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def corpus(run_dir, snapshot):
    path = Path(run_dir) / f"{snapshot}-corpus.txt"
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^### (.+)\n", text)
    return [(parts[i], parts[i + 1]) for i in range(1, len(parts), 2)]


def classifications(run_dir):
    result = {}
    for snapshot in ("old", "new"):
        with (Path(run_dir) / f"{snapshot}-files.tsv").open(newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["status"] == "included":
                    suffix = Path(row["path"]).suffix.lower()
                    result[(snapshot, row["path"])] = "docs" if suffix in {".md", ".txt"} else "code"
                else:
                    result[(snapshot, row["path"])] = "vendor"
    return result


def measure(run_dir, snapshot, terms):
    classes = classifications(run_dir)
    rows = []
    for path, text in corpus(run_dir, snapshot):
        tokens = tokenize(text)
        counts = Counter(tokens)
        included = len(tokens)
        category = classes.get((snapshot, path), "code")
        for term in terms:
            raw = counts[term]
            rows.append({"snapshot": snapshot, "unit": path, "category": category, "concept": term,
                         "raw_count": raw, "included_tokens": included,
                         "rate_per_10000": round(raw * 10000 / included, 6) if included else None})
    return rows


def aggregate(rows, terms):
    out = []
    for snapshot in ("old", "new"):
        selected = [r for r in rows if r["snapshot"] == snapshot]
        for category in ("all", "code", "docs", "vendor"):
            group = selected if category == "all" else [r for r in selected if r["category"] == category]
            tokens = sum(r["included_tokens"] for r in group)
            for term in terms:
                hits = sum(r["raw_count"] for r in group if r["concept"] == term)
                out.append({"snapshot": snapshot, "category": category, "concept": term,
                            "raw_count": hits, "included_tokens": tokens,
                            "rate_per_10000": round(hits * 10000 / tokens, 6) if tokens else None,
                            "unique_units": len({r["unit"] for r in group if r["concept"] == term and r["raw_count"]})})
    return out


def file_evidence(run_dir):
    """Return the immutable file inventory used to classify structural controls."""
    evidence = {}
    for snapshot in ("old", "new"):
        with (Path(run_dir) / f"{snapshot}-files.tsv").open(newline="") as handle:
            evidence[snapshot] = {
                row["path"]: row for row in csv.DictReader(handle, delimiter="\t")
                if row["status"] == "included"
            }
    return evidence


def lexical_profiles(rows):
    return {
        (row["snapshot"], row["concept"]): row["rate_per_10000"]
        for row in rows if row["category"] == "all"
    }


def same_lexical_profile(rows):
    profiles = lexical_profiles(rows)
    terms = {term for _, term in profiles}
    return all(profiles.get(("old", term)) == profiles.get(("new", term)) for term in terms)


def structural_controls(run_dir, rows):
    files = file_evidence(run_dir)
    old, new = files["old"], files["new"]
    old_paths, new_paths = set(old), set(new)
    added, deleted = new_paths - old_paths, old_paths - new_paths
    old_hashes = {row["blob_sha256"] for row in old.values()}
    duplicate_paths = {
        path for path in added
        if new[path]["blob_sha256"] in old_hashes
        and any(old_path in new and new[old_path]["blob_sha256"] == new[path]["blob_sha256"]
                for old_path in old_paths & new_paths)
    }
    rename_pairs = [
        (old_path, new_path) for old_path in deleted for new_path in added
        if old[old_path]["blob_sha256"] == new[new_path]["blob_sha256"]
    ]
    changed_paths = {
        path for path in old_paths & new_paths
        if old[path]["blob_sha256"] != new[path]["blob_sha256"]
    }
    profile_unchanged = same_lexical_profile(rows)
    return {
        "duplication": {
            "evidence": {"duplicate_paths": sorted(duplicate_paths)},
            "verdict": ("NO_NORMALIZED_CHANGE" if duplicate_paths and profile_unchanged
                        else "NORMALIZED_CHANGE" if duplicate_paths else "NO_DUPLICATION"),
        },
        "rename": {
            "evidence": {"pairs": [{"old": old_path, "new": new_path}
                                    for old_path, new_path in rename_pairs]},
            "verdict": ("LEXICAL_ONLY" if rename_pairs and profile_unchanged else
                        "LEXICAL_CHANGE" if rename_pairs else "NO_RENAME"),
        },
        "shuffle": {
            "evidence": {"changed_paths": sorted(changed_paths)},
            "verdict": ("NO_SEMANTIC_VERDICT" if changed_paths and profile_unchanged
                        else "LEXICAL_CHANGE" if changed_paths else "NO_SHUFFLE"),
        },
    }


def analyze(run_dir):
    definition, dictionary_sha256 = dictionary_source()
    terms = [term.casefold() for term in definition["terms"]]
    rows = aggregate(measure(run_dir, "old", terms) + measure(run_dir, "new", terms), terms)
    by_key = {(r["snapshot"], r["category"], r["concept"]): r for r in rows}
    delta = 0
    for term in terms:
        old = by_key[("old", "all", term)]
        new = by_key[("new", "all", term)]
        if old["rate_per_10000"] != new["rate_per_10000"]:
            delta += 1
    controls = {
        "no_change": {"verdict": "NO_CHANGE" if delta == 0 else "CHANGED", "delta_concepts": delta},
    }
    controls.update(structural_controls(run_dir, rows))
    (Path(run_dir) / "lexical.tsv").write_text(
        "snapshot\tcategory\tconcept\traw_count\tincluded_tokens\trate_per_10000\tunique_units\n" +
        "".join("\t".join(str(r[k]) if r[k] is not None else "" for k in ("snapshot", "category", "concept", "raw_count", "included_tokens", "rate_per_10000", "unique_units")) + "\n" for r in rows))
    (Path(run_dir) / "controls.tsv").write_text("control\tverdict\tdelta_concepts\n" +
        "".join(f"{name}\t{item['verdict']}\t{item.get('delta_concepts', '')}\n" for name, item in controls.items()))
    return {"schema": "tiny-fleet.drift-lexical/v1", "dictionary_sha256": dictionary_sha256,
            "tokenizer": definition["tokenizer"], "terms": terms, "delta_concepts": delta, "controls": controls}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(analyze(args.run_dir), sort_keys=True))


if __name__ == "__main__":
    main()
