#!/usr/bin/env python3
"""Versioned scorer for confirmatory-v1's snapshot-specific LoRA pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import drift_generate as generation
import drift_score as legacy


AMENDMENT_SCHEMA = "tiny-fleet.drift-score-amendment/v1"
SCORER_ID = "ollama-embedding-cosine-confirmatory-v1-amendment"
ROOT = Path(__file__).resolve().parents[1]
KEYS = ("repo", "arm", "prompt_id", "seed", "repetition")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def scorer_bundle_digest() -> str:
    """Bind this implementation and the pinned embedding/provenance dependency."""
    digest = hashlib.sha256()
    for path in (
        Path(generation.__file__).resolve(),
        Path(legacy.__file__).resolve(),
        Path(__file__).resolve(),
    ):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(file_sha(path)))
    return digest.hexdigest()


def pair_output_records(records, manifest):
    """Validate the full frozen matrix, then pair snapshots without false adapter equality."""
    generation.validate_v2_records(manifest, records)
    prompt_map = {
        (prompt["repo"], prompt["snapshot"], prompt["prompt_id"]): prompt
        for prompt in manifest["prompts"]
    }
    groups = {}
    for row in records:
        key = tuple(row.get(field) for field in KEYS)
        snapshots = groups.setdefault(key, {})
        if row["snapshot"] in snapshots:
            raise legacy.ScorerError("duplicate_record")
        prompt = prompt_map[(row["repo"], row["snapshot"], row["prompt_id"])]
        expected_adapter = prompt["lora_adapter"]["digest"] if row["arm"] == "lora" else None
        if row.get("adapter_digest") != expected_adapter:
            raise legacy.ScorerError("adapter_registration_mismatch")
        snapshots[row["snapshot"]] = row

    pairs = []
    for key in sorted(groups, key=lambda item: tuple(str(value) for value in item)):
        snapshots = groups[key]
        if set(snapshots) != {"old", "new"}:
            raise legacy.ScorerError("incomplete_pair")
        old, new = snapshots["old"], snapshots["new"]
        if old.get("base_model_revision") != new.get("base_model_revision"):
            raise legacy.ScorerError("base_model_pair_mismatch")
        # Each snapshot's adapter was independently checked against its frozen registration above.
        # Snapshot-specific LoRAs are expected to have different digests.
        if key[1] != "lora" and (old.get("adapter_digest") is not None or new.get("adapter_digest") is not None):
            raise legacy.ScorerError("unexpected_adapter_for_control_arm")
        pairs.append({"key": key, "old": old, "new": new})
    return pairs


def score_pairs(records, manifest, *, embed_fn, model_digest, scorer_digest, model=legacy.DEFAULT_MODEL):
    pairs = pair_output_records(records, manifest)
    texts = [pair[side]["output"] for pair in pairs for side in ("old", "new")]
    embeddings = embed_fn(texts)
    if not isinstance(embeddings, (list, tuple)) or len(embeddings) != len(texts):
        raise legacy.ScorerError("embedding_response_shape")
    if any(not isinstance(vector, (list, tuple)) or len(vector) != legacy.DEFAULT_EMBEDDING_DIMENSION for vector in embeddings):
        raise legacy.ScorerError("embedding_dimension_mismatch")
    scored = []
    for index, pair in enumerate(pairs):
        old, new = pair["old"], pair["new"]
        scored.append({
            "schema": "tiny-fleet.drift-score/confirmatory-v1-amendment",
            **dict(zip(KEYS, pair["key"])),
            "old_output_sha256": sha256_bytes(old["output"].encode("utf-8")),
            "new_output_sha256": sha256_bytes(new["output"].encode("utf-8")),
            "base_model_revision": old["base_model_revision"],
            "old_adapter_digest": old.get("adapter_digest"),
            "new_adapter_digest": new.get("adapter_digest"),
            "embedding_model": model,
            "embedding_model_digest": model_digest,
            "embedding_dimension": legacy.DEFAULT_EMBEDDING_DIMENSION,
            "embedding_runtime": "ollama",
            "embedding_runtime_version": legacy.DEFAULT_OLLAMA_VERSION,
            "scorer_id": SCORER_ID,
            "scorer_code_bundle_sha256": scorer_digest,
            "cosine_similarity": legacy.cosine_similarity(embeddings[index * 2], embeddings[index * 2 + 1]),
            "interpretation_limit": "embedding similarity is not semantic ground truth",
        })
    return scored


def verify_amendment(amendment, *, raw_hash, registration_hash, manifest):
    scorer_path = Path(__file__).resolve()
    dependency_path = Path(legacy.__file__).resolve()
    validator_path = Path(generation.__file__).resolve()
    validator_digest = file_sha(validator_path)
    runner = manifest.get("runner", {})
    if runner.get("source_sha256") != validator_digest:
        raise legacy.ScorerError("validator_registration_mismatch")
    checks = {
        "schema": amendment.get("schema") == AMENDMENT_SCHEMA,
        "raw_records_sha256": amendment.get("raw_records_sha256") == raw_hash,
        "generation_registration_sha256": amendment.get("generation_registration_sha256") == registration_hash,
        "scorer_source_sha256": amendment.get("scorer_source_sha256") == file_sha(scorer_path),
        "scorer_dependency_sha256": amendment.get("scorer_dependency_sha256") == file_sha(dependency_path),
        "validator_source_sha256": amendment.get("validator_source_sha256") == validator_digest,
        "scorer_code_bundle_sha256": amendment.get("scorer_code_bundle_sha256") == scorer_bundle_digest(),
        "embedding_model": amendment.get("embedding_model") == legacy.DEFAULT_MODEL,
        "embedding_model_digest": amendment.get("embedding_model_digest") == legacy.DEFAULT_DIGEST,
        "embedding_runtime_version": amendment.get("embedding_runtime_version") == legacy.DEFAULT_OLLAMA_VERSION,
        "status": amendment.get("status") == "frozen-before-scoring",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise legacy.ScorerError("scoring_amendment_mismatch:" + ",".join(failed))
    return True


def score_file(records_path, manifest_path, amendment_path, output_path):
    records_path = Path(records_path)
    manifest_path = Path(manifest_path)
    amendment_path = Path(amendment_path)
    output_path = Path(output_path)
    raw_bytes = records_path.read_bytes()
    raw_hash = sha256_bytes(raw_bytes)
    registration_hash = file_sha(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    verify_amendment(amendment, raw_hash=raw_hash, registration_hash=registration_hash, manifest=manifest)
    records = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line.strip()]
    digest = scorer_bundle_digest()
    rows = score_pairs(
        records,
        manifest,
        embed_fn=lambda texts: legacy.ollama_embed(
            texts, model=legacy.DEFAULT_MODEL, expected_digest=legacy.DEFAULT_DIGEST,
        ),
        model_digest=legacy.DEFAULT_DIGEST,
        scorer_digest=digest,
    )
    output = {
        "schema": "tiny-fleet.drift-score-file/confirmatory-v1-amendment",
        "raw_records_sha256": raw_hash,
        "generation_registration_sha256": registration_hash,
        "scoring_amendment_sha256": file_sha(amendment_path),
        "scorer_id": SCORER_ID,
        "scorer_code_bundle_sha256": digest,
        "embedding_model": legacy.DEFAULT_MODEL,
        "embedding_model_digest": legacy.DEFAULT_DIGEST,
        "embedding_dimension": legacy.DEFAULT_EMBEDDING_DIMENSION,
        "embedding_runtime": "ollama",
        "embedding_runtime_version": legacy.DEFAULT_OLLAMA_VERSION,
        "claim_limit": "cosine is embedding similarity, not semantic ground truth; objective labels are not behavioral or semantic truth",
        "scores": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": str(output_path), "sha256": file_sha(output_path), "pairs": len(rows), "scorer_code_bundle_sha256": digest}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--amendment", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = score_file(args.records, args.manifest, args.amendment, args.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
