#!/usr/bin/env python3
"""Portable, immutable Git-object extractor for architectural drift inputs."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


EXCLUDED_PARTS = {"generated", "vendor", "node_modules"}
LANGUAGE = {".py": "python", ".sh": "shell", ".md": "markdown", ".json": "json",
            ".tsv": "tsv", ".txt": "text", ".yaml": "yaml", ".yml": "yaml"}
INVOCATION = re.compile(r"(?:^|[;&|]\s*)(?:\.\/)?(mesh-[a-z0-9-]+)(?:\s|$)")


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def immutable_sha(value):
    if not re.fullmatch(r"[0-9a-fA-F]{40}", value):
        raise ValueError("commit must be an immutable 40-hex object id")
    return value.lower()


def inventory(repo, commit, side, out):
    raw = git(repo, "ls-tree", "-r", "-l", "-z", commit)
    rows, corpus = [], []
    for item in raw.split(b"\0"):
        if not item:
            continue
        header, rel_bytes = item.split(b"\t", 1)
        mode, kind, blob, size = header.decode().split()
        rel = rel_bytes.decode("utf-8")
        data = git(repo, "cat-file", "blob", blob)
        reason = None
        if set(Path(rel).parts) & EXCLUDED_PARTS:
            reason = "generated-or-vendor-path"
        elif b"\0" in data:
            reason = "binary"
        else:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                reason = "malformed-encoding"
        row = {"path": rel, "blob_sha256": hashlib.sha256(data).hexdigest(),
               "bytes": len(data), "units": text.count("\n") if reason is None else 0,
               "language": LANGUAGE.get(Path(rel).suffix.lower(), "other"),
               "status": "excluded" if reason else "included", "reason": reason or ""}
        rows.append(row)
        if reason is None:
            corpus.append(f"### {rel}\n{text}")
    rows.sort(key=lambda row: row["path"])
    (out / f"{side}-files.tsv").write_text("path\tblob_sha256\tbytes\tunits\tlanguage\tstatus\treason\n" +
        "\n".join("\t".join(str(row[key]) for key in ("path", "blob_sha256", "bytes", "units", "language", "status", "reason")) for row in rows) + "\n")
    (out / f"{side}-corpus.txt").write_text("\n".join(corpus))
    return {"commit": commit, "rows": rows, "excluded_paths": sum(row["status"] == "excluded" for row in rows),
            "included_paths": sum(row["status"] == "included" for row in rows)}


def extract(repo, old, new, out):
    repo, out = Path(repo), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    old, new = immutable_sha(old), immutable_sha(new)
    left, right = inventory(repo, old, "old", out), inventory(repo, new, "new", out)
    old_map = {row["path"]: row for row in left["rows"] if row["status"] == "included"}
    new_map = {row["path"]: row for row in right["rows"] if row["status"] == "included"}
    old_blobs = {row["blob_sha256"] for row in old_map.values()}
    new_blobs = {row["blob_sha256"] for row in new_map.values()}
    added = set(new_map) - set(old_map)
    deleted = set(old_map) - set(new_map)
    renamed = sum(new_map[path]["blob_sha256"] in old_blobs for path in added)
    delta = {"added_text_paths": len(added) - renamed, "deleted_text_paths": len(deleted) - renamed,
             "renamed_text_paths": renamed, "changed_text_paths": len(old_blobs ^ new_blobs)}
    structural = {"old_paths": len(old_map), "new_paths": len(new_map),
                  "old_bytes": sum(row["bytes"] for row in old_map.values()),
                  "new_bytes": sum(row["bytes"] for row in new_map.values()),
                  "old_mesh_refs": mesh_invocations(out / "old-corpus.txt"),
                  "new_mesh_refs": mesh_invocations(out / "new-corpus.txt"), **delta}
    (out / "structural.tsv").write_text("metric\told\tnew\tdelta\n" + "\n".join(
        f"{key}\t{structural.get('old_'+key, '')}\t{structural.get('new_'+key, '')}\t{value}"
        for key, value in delta.items()) + "\n")
    result = {"schema": "tiny-fleet.drift-extract/v1", "old": {k: v for k, v in left.items() if k != "rows"},
              "new": {k: v for k, v in right.items() if k != "rows"}, "delta": delta, "structural": structural}
    (out / "manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def mesh_invocations(path):
    return sum(1 for line in path.read_text().splitlines() if INVOCATION.search(line))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(extract(args.repo, args.old, args.new, args.run_dir), sort_keys=True))


if __name__ == "__main__":
    main()
