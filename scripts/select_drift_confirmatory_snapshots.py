#!/usr/bin/env python3
"""Select the unseen confirmatory snapshot pairs from pinned public repositories.

Selection is intentionally metadata-only: it considers stable semantic-version
tags and commit timestamps, never source contents, labels, tests, scores, or model
outputs. Run against complete bare clones containing all upstream tags.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path


ANCHORS = ("2023-01-01T00:00:00Z", "2025-01-01T00:00:00Z")
MIN_WINDOW_DAYS = 365
REPOSITORIES = (
    ("httpx", "https://github.com/encode/httpx.git", "encode", "Python HTTP client"),
    ("attrs", "https://github.com/python-attrs/attrs.git", "python-attrs", "Python data model library"),
    ("pytest", "https://github.com/pytest-dev/pytest.git", "pytest-dev", "Python test framework"),
)
STABLE_SEMVER = re.compile(r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, stderr=subprocess.PIPE
    ).strip()


def iso_epoch(value: str) -> int:
    return int(dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def stable_tags(repo: Path) -> list[dict[str, object]]:
    raw = git(repo, "for-each-ref", "--format=%(refname:short)%00%(objectname)%00%(*objectname)", "refs/tags")
    refs = []
    for line in raw.splitlines():
        tag, object_id, peeled = line.split("\0")
        match = STABLE_SEMVER.fullmatch(tag)
        if match:
            refs.append((tag, peeled or object_id, tuple(int(part) for part in match.groups())))
    commits = sorted({commit for _tag, commit, _version in refs})
    if not commits:
        raise ValueError(f"no stable semantic-version tags in {repo}")
    metadata = git(repo, "show", "-s", "--format=%H%x00%ct%x00%cI%x00%T%x00%P%x1e", *commits)
    by_commit = {}
    for record in metadata.split("\x1e"):
        if not record.strip():
            continue
        record = record.strip()
        commit, epoch, committed, tree, parents = record.split("\0")
        by_commit[commit] = {
            "commit": commit,
            "commit_epoch": int(epoch),
            "commit_time": committed,
            "tree": tree,
            "parents": parents.split() if parents else [],
        }
    rows = []
    for tag, commit, version in refs:
        rows.append({"tag": tag, "version": version, **by_commit[commit]})
    if not rows:
        raise ValueError(f"no stable semantic-version tags in {repo}")
    return rows


def select_at(rows: list[dict[str, object]], anchor: str) -> dict[str, object]:
    cutoff = iso_epoch(anchor)
    eligible = [row for row in rows if int(row["commit_epoch"]) <= cutoff]
    if not eligible:
        raise ValueError(f"no stable tag at or before {anchor}")
    return max(eligible, key=lambda row: (row["commit_epoch"], row["version"], str(row["tag"]), str(row["commit"])))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True, help="directory containing <repo_id>.git bare clones")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repositories = []
    for repo_id, url, owner, role in REPOSITORIES:
        path = args.cache / f"{repo_id}.git"
        if not path.is_dir():
            raise SystemExit(f"missing bare repository: {path}")
        rows = stable_tags(path)
        pair = [select_at(rows, anchor) for anchor in ANCHORS]
        window_days = (int(pair[1]["commit_epoch"]) - int(pair[0]["commit_epoch"])) // 86400
        if window_days < MIN_WINDOW_DAYS:
            raise SystemExit(f"{repo_id}: selected snapshots only {window_days} days apart")
        for row in pair:
            row.pop("commit_epoch")
            row["archive_sha256"] = None
            row["license_path"] = None
            row["license_sha256"] = None
        repositories.append({
            "repo_id": repo_id,
            "identity": url.removesuffix(".git"),
            "owner_namespace": owner,
            "role": role,
            "selection_candidate_count": len(rows),
            "stable_tag_inventory": [
                {"tag": row["tag"], "commit": row["commit"], "commit_time": row["commit_time"]}
                for row in sorted(rows, key=lambda row: str(row["tag"]))
            ],
            "snapshots": [dict(label=label, **row) for label, row in zip(("old", "new"), pair)],
            "window_days": window_days,
        })
    result = {
        "schema": "tiny-fleet.drift-confirmatory-selection/v1",
        "selection_code": "scripts/select_drift_confirmatory_snapshots.py",
        "selection_policy": {
            "sample_kind": "purposive fixed set; not random or population-representative",
            "repositories": "three distinct canonical public GitHub repositories under distinct owner namespaces, not used by the prior v1/v2 sample or adapter corpus",
            "stable_tag_rule": STABLE_SEMVER.pattern,
            "anchors_utc": list(ANCHORS),
            "tag_rule": "resolve every matching annotated or lightweight tag to its commit; use committer timestamp; choose latest commit timestamp not later than each anchor; ties: greatest numeric version tuple, then tag, then commit ID",
            "minimum_window_days": MIN_WINDOW_DAYS,
            "data_firewall": "metadata-only selection; no source blobs, diffs, labels, tests, scores, smoke, or inference read by this selector",
        },
        "repositories": repositories,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
