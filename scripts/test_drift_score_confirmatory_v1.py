#!/usr/bin/env python3
"""Tests for the separately registered confirmatory-v1 scoring amendment."""

import json
import unittest
from pathlib import Path

from drift_generate import build_effective_input, _effective_seed
from drift_score_confirmatory_v1 import pair_output_records, score_pairs, verify_amendment


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "runs/drift-confirmatory-v1/generative-registration.json"


def fixture_records(manifest):
    rows = []
    for prompt in manifest["prompts"]:
        for arm in manifest["arms"]:
            adapter = prompt["lora_adapter"]["digest"] if arm == "lora" else None
            effective = build_effective_input(manifest, prompt, arm)
            for seed in manifest["seeds"]:
                for repetition in manifest["repetitions"]:
                    rows.append({
                        "schema": "tiny-fleet.drift-generative/v2",
                        **{key: prompt[key] for key in (
                            "repo", "snapshot", "prompt_id", "source_family",
                            "source_commit", "source_path", "source_file_sha256",
                            "snapshot_excerpt_sha256",
                        )},
                        "arm": arm,
                        "seed": seed,
                        "repetition": repetition,
                        "effective_input": effective,
                        "effective_input_sha256": __import__("hashlib").sha256(effective.encode()).hexdigest(),
                        "effective_seed": _effective_seed(seed, repetition, effective),
                        "base_model_id": manifest["base_model"]["model_id"],
                        "base_model_revision": manifest["base_model"]["revision"],
                        "adapter_digest": adapter,
                        "scorer_id": manifest["scorer"]["id"],
                        "scorer_revision": manifest["scorer"]["revision"],
                        "scorer_digest": manifest["scorer"]["digest"],
                        "backend": "transformers-pinned-v2",
                        "runtime": {"python": "3.12.3", "torch": "2.14.0", "transformers": "4.57.6", "device": "cpu"},
                        "status": "ok",
                        "output": "synthetic test output",
                    })
    return rows


class ConfirmatoryScorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(REGISTRATION.read_text(encoding="utf-8"))
        cls.records = fixture_records(cls.manifest)

    def test_pairs_snapshot_specific_registered_adapters_without_changing_raw_digest(self):
        pairs = pair_output_records(self.records, self.manifest)
        self.assertEqual(len(pairs), 81)
        lora_pairs = [pair for pair in pairs if pair["key"][1] == "lora"]
        self.assertEqual(len(lora_pairs), 27)
        self.assertTrue(all(pair["old"]["adapter_digest"] != pair["new"]["adapter_digest"] for pair in lora_pairs))

    def test_rejects_an_adapter_digest_not_bound_to_registered_snapshot(self):
        mutated = [dict(row) for row in self.records]
        row = next(row for row in mutated if row["arm"] == "lora" and row["snapshot"] == "new")
        row["adapter_digest"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "adapter digest mismatch"):
            pair_output_records(mutated, self.manifest)

    def test_scoring_amendment_binds_raw_tape_registration_and_code(self):
        amendment = json.loads((ROOT / "runs/drift-confirmatory-v1/execution-confirmatory-v1/scoring-amendment-v1.json").read_text())
        raw_path = ROOT / "runs/drift-confirmatory-v1/execution-confirmatory-v1/generative-v2.jsonl"
        raw_hash = __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest()
        registration_hash = __import__("hashlib").sha256(REGISTRATION.read_bytes()).hexdigest()
        self.assertTrue(verify_amendment(amendment, raw_hash=raw_hash, registration_hash=registration_hash, manifest=self.manifest))
        with self.assertRaisesRegex(Exception, "scoring_amendment_mismatch:raw_records_sha256"):
            verify_amendment(amendment, raw_hash="0" * 64, registration_hash=registration_hash, manifest=self.manifest)

    def test_refuses_validator_digest_that_differs_from_frozen_runner_registration(self):
        amendment = json.loads((ROOT / "runs/drift-confirmatory-v1/execution-confirmatory-v1/scoring-amendment-v1.json").read_text())
        raw_path = ROOT / "runs/drift-confirmatory-v1/execution-confirmatory-v1/generative-v2.jsonl"
        raw_hash = __import__("hashlib").sha256(raw_path.read_bytes()).hexdigest()
        registration_hash = __import__("hashlib").sha256(REGISTRATION.read_bytes()).hexdigest()
        changed_manifest = dict(self.manifest)
        changed_manifest["runner"] = dict(self.manifest["runner"])
        changed_manifest["runner"]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(Exception, "validator_registration_mismatch"):
            verify_amendment(
                amendment,
                raw_hash=raw_hash,
                registration_hash=registration_hash,
                manifest=changed_manifest,
            )

    def test_scores_all_pairs_with_distinct_registered_lora_digests(self):
        calls = []

        def embed(texts):
            calls.append(len(texts))
            return [[1.0] + [0.0] * 383 for _ in texts]

        rows = score_pairs(
            self.records,
            self.manifest,
            embed_fn=embed,
            model_digest=self.manifest["scorer"]["embedding_model_digest"],
            scorer_digest="registered-amendment-digest",
        )
        self.assertEqual(len(rows), 81)
        self.assertEqual(calls, [162])
        self.assertTrue(all(row["cosine_similarity"] == 1.0 for row in rows))
        self.assertTrue(all("not semantic ground truth" in row["interpretation_limit"] for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
