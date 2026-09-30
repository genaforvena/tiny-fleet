#!/usr/bin/env python3
"""Deterministic, digest-checked cosine scoring for paired generated outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.request
from pathlib import Path


SCORER_ID = "ollama-embedding-cosine-v1"
DEFAULT_MODEL = "all-minilm:latest"
DEFAULT_DIGEST = "1b226e2802dbb772b5fc32a58f103ca1804ef7501331012de126ab22f67475ef"
DEFAULT_OLLAMA_VERSION = "0.33.2"
DEFAULT_EMBEDDING_DIMENSION = 384
DEFAULT_ENDPOINT = "http://localhost:11434"
KEYS = ("repo", "arm", "prompt_id", "seed", "repetition")


class ScorerError(ValueError):
    """Typed refusal for incomplete or unverifiable scoring inputs."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def scorer_source_digest() -> str:
    return sha256_bytes(Path(__file__).read_bytes())


def cosine_similarity(left, right) -> float:
    try:
        a = [float(value) for value in left]
        b = [float(value) for value in right]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ScorerError("embedding_schema") from exc
    if not a or len(a) != len(b):
        raise ScorerError("embedding_shape")
    if not all(math.isfinite(value) for value in a + b):
        raise ScorerError("embedding_nonfinite")
    a_norm = math.sqrt(math.fsum(value * value for value in a))
    b_norm = math.sqrt(math.fsum(value * value for value in b))
    if not a_norm or not b_norm:
        raise ScorerError("embedding_zero_norm")
    result = math.fsum(x * y for x, y in zip(a, b)) / (a_norm * b_norm)
    if not math.isfinite(result):
        raise ScorerError("similarity_nonfinite")
    return max(-1.0, min(1.0, result))


def verify_model_digest(tags, model, expected_digest):
    models = tags.get("models") if isinstance(tags, dict) else None
    if not isinstance(models, list):
        raise ScorerError("embedding_model_tags_schema")
    matches = [row for row in models if isinstance(row, dict) and row.get("name") == model]
    if len(matches) != 1 or matches[0].get("digest") != expected_digest:
        raise ScorerError("embedding_model_digest_mismatch")
    return matches[0]["digest"]


def verify_runtime_version(version_payload, expected_version):
    version = version_payload.get("version") if isinstance(version_payload, dict) else None
    if version != expected_version:
        raise ScorerError("embedding_runtime_version_mismatch")
    return version


def pair_output_records(records):
    groups = {}
    for row in records:
        if not isinstance(row, dict) or row.get("schema") != "tiny-fleet.drift-generative/v2":
            raise ScorerError("record_schema")
        if row.get("status") != "ok" or not isinstance(row.get("output"), str) or not row["output"]:
            raise ScorerError("non_success_record")
        if row.get("snapshot") not in {"old", "new"}:
            raise ScorerError("snapshot_label")
        if not row.get("base_model_revision"):
            raise ScorerError("base_model_provenance")
        key = tuple(row.get(field) for field in KEYS)
        if any(value is None for value in key):
            raise ScorerError("record_key_missing")
        snapshots = groups.setdefault(key, {})
        if row["snapshot"] in snapshots:
            raise ScorerError("duplicate_record")
        snapshots[row["snapshot"]] = row
    if not groups:
        raise ScorerError("no_records")
    pairs = []
    for key in sorted(groups, key=lambda item: tuple(str(value) for value in item)):
        snapshots = groups[key]
        if set(snapshots) != {"old", "new"}:
            raise ScorerError("incomplete_pair")
        old, new = snapshots["old"], snapshots["new"]
        if old.get("base_model_revision") != new.get("base_model_revision"):
            raise ScorerError("base_model_pair_mismatch")
        if old.get("adapter_digest") != new.get("adapter_digest"):
            raise ScorerError("adapter_pair_mismatch")
        pairs.append({"key": key, "old": old, "new": new})
    return pairs


def score_pairs(records, *, embed_fn, model_digest, scorer_digest, model=DEFAULT_MODEL, runtime_version=DEFAULT_OLLAMA_VERSION):
    pairs = pair_output_records(records)
    texts = [row[side]["output"] for row in pairs for side in ("old", "new")]
    try:
        embeddings = embed_fn(texts)
    except ScorerError:
        raise
    except Exception as exc:
        raise ScorerError("embedding_backend_failure") from exc
    if not isinstance(embeddings, (list, tuple)) or len(embeddings) != len(texts):
        raise ScorerError("embedding_response_shape")
    if any(not isinstance(vector, (list, tuple)) or len(vector) != DEFAULT_EMBEDDING_DIMENSION for vector in embeddings):
        raise ScorerError("embedding_dimension_mismatch")
    scored = []
    for index, pair in enumerate(pairs):
        old, new = pair["old"], pair["new"]
        scored.append({
            "schema": "tiny-fleet.drift-score/v1",
            **dict(zip(KEYS, pair["key"])),
            "old_output_sha256": sha256_bytes(old["output"].encode("utf-8")),
            "new_output_sha256": sha256_bytes(new["output"].encode("utf-8")),
            "base_model_revision": old["base_model_revision"],
            "adapter_digest": old.get("adapter_digest"),
            "embedding_model": model,
            "embedding_model_digest": model_digest,
            "embedding_dimension": DEFAULT_EMBEDDING_DIMENSION,
            "embedding_runtime": "ollama",
            "embedding_runtime_version": runtime_version,
            "scorer_id": SCORER_ID,
            "scorer_code_sha256": scorer_digest,
            "cosine_similarity": cosine_similarity(embeddings[index * 2], embeddings[index * 2 + 1]),
            "interpretation_limit": "embedding similarity is not semantic ground truth",
        })
    return scored


def _request_json(url, payload=None):
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        raise ScorerError("embedding_backend_failure") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScorerError("embedding_response_json") from exc


def ollama_embed(texts, *, model=DEFAULT_MODEL, expected_digest=DEFAULT_DIGEST, endpoint=DEFAULT_ENDPOINT):
    verify_runtime_version(_request_json(f"{endpoint.rstrip('/')}/api/version"), DEFAULT_OLLAMA_VERSION)
    tags = _request_json(f"{endpoint.rstrip('/')}/api/tags")
    verify_model_digest(tags, model, expected_digest)
    payload = _request_json(f"{endpoint.rstrip('/')}/api/embed", {"model": model, "input": texts})
    raw = payload.get("embeddings") if isinstance(payload, dict) else None
    if not isinstance(raw, list) or len(raw) != len(texts):
        raise ScorerError("embedding_response_shape")
    return raw


def score_file(input_path, output_path, *, model=DEFAULT_MODEL, expected_digest=DEFAULT_DIGEST, endpoint=DEFAULT_ENDPOINT):
    input_path, output_path = Path(input_path), Path(output_path)
    input_bytes = input_path.read_bytes()
    records = [json.loads(line) for line in input_bytes.decode("utf-8").splitlines() if line.strip()]
    digest = scorer_source_digest()
    rows = score_pairs(
        records,
        embed_fn=lambda texts: ollama_embed(texts, model=model, expected_digest=expected_digest, endpoint=endpoint),
        model_digest=expected_digest,
        scorer_digest=digest,
        model=model,
    )
    output = {
        "schema": "tiny-fleet.drift-score-file/v1",
        "raw_records_sha256": sha256_bytes(input_bytes),
        "scorer_id": SCORER_ID,
        "scorer_code_sha256": digest,
        "embedding_model": model,
        "embedding_model_digest": expected_digest,
        "embedding_dimension": DEFAULT_EMBEDDING_DIMENSION,
        "embedding_runtime": "ollama",
        "embedding_runtime_version": DEFAULT_OLLAMA_VERSION,
        "claim_limit": "embedding similarity is not semantic ground truth",
        "scores": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": str(output_path), "sha256": sha256_bytes(output_path.read_bytes()), "pairs": len(rows), "scorer_code_sha256": digest}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True, type=Path, help="v2 JSONL raw output records")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-digest", default=DEFAULT_DIGEST)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    args = parser.parse_args(argv)
    print(json.dumps(score_file(args.records, args.output, model=args.model, expected_digest=args.model_digest, endpoint=args.endpoint), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
