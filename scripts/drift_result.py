#!/usr/bin/env python3
"""Publish one immutable, source-keyed local drift extraction bundle.

A staged bundle is UNKNOWN, never silently replaced. A final bundle is the
receipt: a crash after rename is reconciled by verifying its exact contents.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

from drift_extract import extract, immutable_sha


FILES = ("old-files.tsv", "new-files.tsv", "old-corpus.txt", "new-corpus.txt",
         "old-python-edges.tsv", "new-python-edges.tsv", "python-edge-delta.tsv",
         "structural.tsv", "manifest.json")


class Unknown(Exception):
    pass


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def identity(repo, old, new):
    repo = repo.resolve(strict=True)
    if not (repo / ".git").exists():
        raise Unknown("repo is not a Git worktree")
    old, new = immutable_sha(old), immutable_sha(new)
    for commit in (old, new):
        kind = subprocess.check_output(["git", "-C", str(repo), "cat-file", "-t", commit], text=True).strip()
        if kind != "commit":
            raise Unknown("snapshot is not a commit")
    source = sha(Path(__file__).resolve().with_name("drift_extract.py"))
    spec = {"repo": str(repo), "old": old, "new": new, "extractor_sha256": source}
    key = hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return spec, key


def verify(directory, spec, key):
    receipt = directory / "receipt.json"
    if directory.is_symlink() or not directory.is_dir() or receipt.is_symlink() or not receipt.is_file():
        raise Unknown("result or receipt missing or symlinked")
    row = json.loads(receipt.read_text())
    if row.get("version") != 1 or row.get("identity") != spec or row.get("key") != key:
        raise Unknown("receipt identity conflict")
    hashes = row.get("files")
    if not isinstance(hashes, dict) or set(hashes) != set(FILES):
        raise Unknown("receipt file set conflict")
    if {p.name for p in directory.iterdir()} != set(FILES) | {"receipt.json"}:
        raise Unknown("result file set conflict")
    for name in FILES:
        path = directory / name
        if path.is_symlink() or not path.is_file() or sha(path) != hashes[name]:
            raise Unknown(f"result changed: {name}")
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("old", {}).get("commit") != spec["old"] or manifest.get("new", {}).get("commit") != spec["new"]:
        raise Unknown("manifest snapshot conflict")
    edges = (directory / "python-edge-delta.tsv").read_text().splitlines()[1:]
    counts = manifest.get("architecture", {})
    if sum(line.startswith("added\tnew\t") for line in edges) != counts.get("added_local_import_edges") or sum(line.startswith("removed\told\t") for line in edges) != counts.get("removed_local_import_edges"):
        raise Unknown("edge delta count conflict")
    if len(edges) != counts["added_local_import_edges"] + counts["removed_local_import_edges"]:
        raise Unknown("edge delta rows malformed")
    return receipt


def operate(repo, old, new, root, publish=False, kill_after_rename=False):
    spec, key = identity(repo, old, new)
    root = root.resolve(strict=True)
    final, pending = root / key, root / (".pending-" + key)
    with (root / ("." + key + ".lock")).open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if final.exists() or final.is_symlink():
            receipt = verify(final, spec, key)
            return {"status": "settled", "key": key, "receipt": str(receipt)}
        if pending.exists() or pending.is_symlink():
            raise Unknown(f"staged bundle requires inspection: {pending}")
        if not publish:
            return {"status": "eligible", "key": key}
        pending.mkdir(mode=0o700)
        extract(spec["repo"], spec["old"], spec["new"], pending)
        hashes = {name: sha(pending / name) for name in FILES}
        receipt = {"version": 1, "identity": spec, "key": key, "files": hashes}
        (pending / "receipt.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
        for name in (*FILES, "receipt.json"):
            with (pending / name).open("rb") as stream:
                os.fsync(stream.fileno())
        fd = os.open(pending, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        verify(pending, spec, key)
        os.rename(pending, final)
        fd = os.open(root, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        if kill_after_rename:
            os.kill(os.getpid(), signal.SIGKILL)
        return {"status": "settled", "key": key, "receipt": str(verify(final, spec, key))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--kill-after-rename", action="store_true")
    args = parser.parse_args()
    if args.kill_after_rename and not args.publish:
        parser.error("fault injection requires --publish")
    try:
        result = operate(args.repo, args.old, args.new, args.root, args.publish, args.kill_after_rename)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Unknown, OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"drift result UNKNOWN: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
