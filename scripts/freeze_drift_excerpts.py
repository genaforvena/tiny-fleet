#!/usr/bin/env python3
"""Select hash-bound source excerpts from the frozen external sample."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath


PACKAGE_ROOTS = {
    "flask": {"old": "src/flask", "new": "src/flask"},
    "requests": {"old": "requests", "new": "src/requests"},
    "pydantic": {"old": "pydantic", "new": "pydantic"},
}
PROMPT_ID = "snapshot-component-description-v1"
PROMPT_TEMPLATE = (
    "Using only the supplied snapshot excerpt, describe the module's documented public responsibility "
    "and explicit behavioral guarantees. Cite the supplied path. Do not infer changes outside the "
    "excerpt; say 'not stated' when evidence is absent."
)
LINES_PER_EXCERPT = 80


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def select_common_source_path(repo_id, old_paths, new_paths, old_root, new_root):
    def relative_map(paths, root):
        prefix = PurePosixPath(root)
        result = {}
        for raw_path in paths:
            path = PurePosixPath(raw_path)
            try:
                relative = path.relative_to(prefix)
            except ValueError:
                continue
            if relative.suffix != ".py" or any(part.lower() in {"test", "tests", "testing"} for part in relative.parts):
                continue
            result[relative.as_posix()] = raw_path
        return result

    old = relative_map(old_paths, old_root)
    new = relative_map(new_paths, new_root)
    candidates = sorted(set(old) & set(new))
    if not candidates:
        raise ValueError(f"no common native Python module for {repo_id}")
    relative = min(candidates, key=lambda path: hashlib.sha256(f"{repo_id}\0{path}".encode()).hexdigest())
    return relative, old[relative], new[relative]


def git(repo_dir, *args):
    return subprocess.run(
        ["git", f"--git-dir={repo_dir}", *args], check=True, capture_output=True
    ).stdout


def tree_paths(repo_dir, commit, source_root):
    raw = git(repo_dir, "ls-tree", "-r", "--name-only", commit, "--", source_root)
    return [line for line in raw.decode("utf-8").splitlines() if line]


def read_blob(repo_dir, commit, path):
    return git(repo_dir, "show", f"{commit}:{path}")


def select_excerpts(sample_manifest_path, repo_cache_dir, output_dir):
    sample_manifest_path = Path(sample_manifest_path)
    repo_cache_dir = Path(repo_cache_dir)
    output_dir = Path(output_dir)
    sample_bytes = sample_manifest_path.read_bytes()
    sample = json.loads(sample_bytes)
    sample_hash = sha_bytes(sample_bytes)
    repo_rows = {row["repo_id"]: row for row in sample["repositories"]}
    prompts = []
    licenses = []
    output_dir.mkdir(parents=True, exist_ok=True)
    snippet_dir = output_dir / "excerpts"
    license_dir = output_dir / "licenses"
    snippet_dir.mkdir(exist_ok=True)
    license_dir.mkdir(exist_ok=True)

    for repo_id in sorted(PACKAGE_ROOTS):
        repo = repo_rows[repo_id]
        repo_dir = repo_cache_dir / f"{repo_id}.git"
        commits = {row["label"]: row["commit"] for row in repo["snapshots"]}
        roots = PACKAGE_ROOTS[repo_id]
        old_paths = tree_paths(repo_dir, commits["old"], roots["old"])
        new_paths = tree_paths(repo_dir, commits["new"], roots["new"])
        relative, old_path, new_path = select_common_source_path(
            repo_id, old_paths, new_paths, roots["old"], roots["new"]
        )
        selection_digest = hashlib.sha256(f"{repo_id}\0{relative}".encode()).hexdigest()
        for snapshot, path in (("old", old_path), ("new", new_path)):
            commit = commits[snapshot]
            source_bytes = read_blob(repo_dir, commit, path)
            source_text = source_bytes.decode("utf-8")
            excerpt = "\n".join(source_text.splitlines()[:LINES_PER_EXCERPT])
            if not excerpt.strip():
                raise ValueError(f"empty excerpt for {repo_id}/{snapshot}:{path}")
            license_info = repo["license"]
            license_row = next(row for row in license_info["snapshots"] if row["commit"] == commit)
            license_bytes = read_blob(repo_dir, commit, license_row["path"])
            license_hash = sha_bytes(license_bytes)
            if license_hash != license_row["sha256"]:
                raise ValueError(f"license hash mismatch for {repo_id}/{snapshot}")
            license_name = f"{repo_id}-{snapshot}-LICENSE.txt"
            (license_dir / license_name).write_bytes(license_bytes)
            excerpt_name = f"{repo_id}-{snapshot}.txt"
            (snippet_dir / excerpt_name).write_text(excerpt, encoding="utf-8")
            prompts.append({
                "repo": repo_id,
                "source_family": repo["owner_namespace"],
                "snapshot": snapshot,
                "source_commit": commit,
                "source_path": path,
                "source_file_sha256": sha_bytes(source_bytes),
                "prompt_id": PROMPT_ID,
                "snapshot_excerpt": excerpt,
                "snapshot_excerpt_sha256": sha_bytes(excerpt.encode("utf-8")),
                "excerpt_path": f"excerpts/{excerpt_name}",
                "selection_key_sha256": selection_digest,
                "lora_adapter": None,
            })
            licenses.append({
                "repo": repo_id,
                "snapshot": snapshot,
                "spdx": license_info["spdx"],
                "source_path": license_row["path"],
                "source_sha256": license_hash,
                "saved_path": f"licenses/{license_name}",
            })

    data = {
        "schema": "tiny-fleet.drift-heldout-excerpts/v1",
        "sample_manifest_path": str(sample_manifest_path),
        "sample_manifest_sha256": sample_hash,
        "selection_policy": {
            "candidate_set": "common native Python modules under each repository's top-level package roots, excluding test trees",
            "ranking": "minimum SHA256(repo_id + NUL + normalized module path)",
            "excerpt": f"first {LINES_PER_EXCERPT} source lines from the selected common module at each exact commit",
            "label_score_access": "selector reads only the frozen sample manifest and source trees; it never opens label or score artifacts",
        },
        "temporal_limit": {
            "status": "strict blind-order precondition unmet",
            "reason": "the objective D04 labels were frozen before this selection task was dispatched, and a non-experimental pinned-model smoke ran earlier; neither artifact was consumed by this deterministic selector, but the temporal order cannot be represented as pre-label/pre-inference",
            "consequence": "use this excerpt ledger for audit and implementation validation only; any confirmatory comparison requires a newly frozen unseen sample or explicit independent review",
        },
        "prompt_template": PROMPT_TEMPLATE,
        "prompt_template_sha256": sha_bytes(PROMPT_TEMPLATE.encode("utf-8")),
        "lines_per_excerpt": LINES_PER_EXCERPT,
        "prompts": prompts,
        "licenses": licenses,
    }
    output_path = output_dir / "heldout-excerpts.json"
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": str(output_path), "sha256": sha_bytes(output_path.read_bytes()), "excerpts": len(prompts), "sample_manifest_sha256": sample_hash}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-manifest", required=True, type=Path)
    parser.add_argument("--repo-cache-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(select_excerpts(args.sample_manifest, args.repo_cache_dir, args.output_dir), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
