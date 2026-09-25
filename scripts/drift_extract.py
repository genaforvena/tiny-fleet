#!/usr/bin/env python3
"""Portable, immutable Git-object extractor for architectural drift inputs."""
import ast
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


EXCLUDED_PARTS = {"generated", "vendor", "node_modules", "runs", "adapters", "corpus"}
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
    rows, corpus, python_sources = [], [], {}
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
            if rel.endswith(".py"):
                python_sources[rel] = text
    rows.sort(key=lambda row: row["path"])
    (out / f"{side}-files.tsv").write_text("path\tblob_sha256\tbytes\tunits\tlanguage\tstatus\treason\n" +
        "\n".join("\t".join(str(row[key]) for key in ("path", "blob_sha256", "bytes", "units", "language", "status", "reason")) for row in rows) + "\n")
    (out / f"{side}-corpus.txt").write_text("\n".join(corpus))
    return {"commit": commit, "rows": rows, "excluded_paths": sum(row["status"] == "excluded" for row in rows),
            "included_paths": sum(row["status"] == "included" for row in rows),
            "python_sources": python_sources}



def python_dependencies(sources):
    """Return exact local Python module imports; never infer dynamic imports."""
    modules = {}
    for path in sources:
        parts = Path(path).with_suffix("").parts
        name = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        modules[name] = path
    edges, failures = set(), []
    for path, text in sources.items():
        parts = Path(path).with_suffix("").parts
        package = list(parts[:-1])
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError:
            failures.append(path)
            continue
        for node in ast.walk(tree):
            candidates = []
            if isinstance(node, ast.Import):
                candidates = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > len(package) + 1:
                    continue
                base = package[:len(package) - node.level + 1] if node.level else []
                prefix = ".".join(base + ([node.module] if node.module else []))
                members = [(prefix + "." if prefix else "") + alias.name for alias in node.names]
                candidates = [member if member in modules else prefix for member in members]
            for candidate in candidates:
                target = candidate
                while target and target not in modules:
                    target = target.rpartition(".")[0]
                if target and modules[target] != path:
                    edges.add((path, modules[target]))
    return edges, failures


def extract(repo, old, new, out):
    repo, out = Path(repo), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    old, new = immutable_sha(old), immutable_sha(new)
    left, right = inventory(repo, old, "old", out), inventory(repo, new, "new", out)
    old_map = {row["path"]: row for row in left["rows"] if row["status"] == "included"}
    new_map = {row["path"]: row for row in right["rows"] if row["status"] == "included"}
    added = set(new_map) - set(old_map)
    deleted = set(old_map) - set(new_map)
    old_by_hash = {}
    for path in sorted(deleted):
        old_by_hash.setdefault(old_map[path]["blob_sha256"], []).append(path)
    renamed = 0
    for path in sorted(added):
        sources = old_by_hash.get(new_map[path]["blob_sha256"], [])
        if sources:
            sources.pop()
            renamed += 1
    changed = sum(old_map[path]["blob_sha256"] != new_map[path]["blob_sha256"]
                  for path in old_map.keys() & new_map.keys())
    delta = {"added_text_paths": len(added) - renamed,
             "deleted_text_paths": len(deleted) - renamed,
             "renamed_text_paths": renamed, "changed_text_paths": changed}
    old_edges, old_failures = python_dependencies(left["python_sources"])
    new_edges, new_failures = python_dependencies(right["python_sources"])
    (out / "old-python-edges.tsv").write_text("source\ttarget\n" +
        "".join(f"{a}\t{b}\n" for a, b in sorted(old_edges)))
    (out / "new-python-edges.tsv").write_text("source\ttarget\n" +
        "".join(f"{a}\t{b}\n" for a, b in sorted(new_edges)))
    edge_delta = [(change, side, source, target, hashes[source]["blob_sha256"],
                   hashes[target]["blob_sha256"])
                  for change, side, edges, hashes in (
                      ("added", "new", new_edges - old_edges, new_map),
                      ("removed", "old", old_edges - new_edges, old_map))
                  for source, target in sorted(edges)]
    (out / "python-edge-delta.tsv").write_text(
        "change\tside\tsource\ttarget\tsource_blob_sha256\ttarget_blob_sha256\n" +
        "".join("\t".join(row) + "\n" for row in edge_delta))
    architecture = {
        "old_python_modules": len(left["python_sources"]),
        "new_python_modules": len(right["python_sources"]),
        "old_local_import_edges": len(old_edges),
        "new_local_import_edges": len(new_edges),
        "added_local_import_edges": sum(row[0] == "added" for row in edge_delta),
        "removed_local_import_edges": sum(row[0] == "removed" for row in edge_delta),
        "old_parse_failures": sorted(old_failures),
        "new_parse_failures": sorted(new_failures)}
    structural = {"old_paths": len(old_map), "new_paths": len(new_map),
                  "old_bytes": sum(row["bytes"] for row in old_map.values()),
                  "new_bytes": sum(row["bytes"] for row in new_map.values()),
                  "old_mesh_refs": mesh_invocations(out / "old-corpus.txt"),
                  "new_mesh_refs": mesh_invocations(out / "new-corpus.txt"), **delta}
    metrics = ("paths", "bytes", "mesh_refs")
    (out / "structural.tsv").write_text(
        "metric\told\tnew\tdelta\n" +
        "".join(f"{key}\t{structural['old_'+key]}\t{structural['new_'+key]}\t"
                f"{structural['new_'+key]-structural['old_'+key]}\n" for key in metrics) +
        "".join(f"{key}\t\t\t{delta[key]}\n" for key in delta))
    result = {"schema": "tiny-fleet.drift-extract/v1",
              "old": {k: v for k, v in left.items() if k not in ("rows", "python_sources")},
              "new": {k: v for k, v in right.items() if k not in ("rows", "python_sources")},
              "delta": delta, "structural": structural, "architecture": architecture}
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
