#!/usr/bin/env python3
import unittest

from drift_score import (
    ScorerError,
    cosine_similarity,
    pair_output_records,
    score_pairs,
    verify_model_digest,
    verify_runtime_version,
)


class DriftScoreTests(unittest.TestCase):
    def test_cosine_similarity_is_stable_and_rejects_zero_vectors(self):
        self.assertEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)
        with self.assertRaisesRegex(ScorerError, "zero_norm"):
            cosine_similarity([0.0, 0.0], [1.0, 0.0])

    def test_pairs_old_and_new_by_experiment_identity(self):
        old = self.record("old", "older output")
        new = self.record("new", "newer output")
        pairs = pair_output_records([new, old])
        self.assertEqual(len(pairs), 1)
        self.assertEqual((pairs[0]["old"]["snapshot"], pairs[0]["new"]["snapshot"]), ("old", "new"))

    def test_pairing_rejects_missing_or_duplicate_snapshots(self):
        with self.assertRaisesRegex(ScorerError, "incomplete_pair"):
            pair_output_records([self.record("old", "one")])
        with self.assertRaisesRegex(ScorerError, "duplicate_record"):
            pair_output_records([self.record("old", "one"), self.record("old", "two"), self.record("new", "three")])

    def test_model_digest_must_match_exact_registered_model(self):
        tags = {"models": [{"name": "all-minilm:latest", "digest": "abc123"}]}
        verify_model_digest(tags, "all-minilm:latest", "abc123")
        with self.assertRaisesRegex(ScorerError, "embedding_model_digest_mismatch"):
            verify_model_digest(tags, "all-minilm:latest", "different")

    def test_ollama_runtime_version_must_match_registered_version(self):
        verify_runtime_version({"version": "0.33.2"}, "0.33.2")
        with self.assertRaisesRegex(ScorerError, "embedding_runtime_version_mismatch"):
            verify_runtime_version({"version": "0.33.3"}, "0.33.2")

    def test_scoring_binds_outputs_and_disclaims_semantic_ground_truth(self):
        records = [self.record("old", "same"), self.record("new", "same")]
        rows = score_pairs(records, embed_fn=lambda texts: [[1.0] + [0.0] * 383 for _ in texts], model_digest="abc123", scorer_digest="def456")
        self.assertEqual(rows[0]["cosine_similarity"], 1.0)
        self.assertEqual(rows[0]["embedding_model_digest"], "abc123")
        self.assertEqual(rows[0]["scorer_code_sha256"], "def456")
        self.assertIn("not semantic ground truth", rows[0]["interpretation_limit"])

    def test_scoring_refuses_unregistered_embedding_dimension(self):
        records = [self.record("old", "same"), self.record("new", "same")]
        with self.assertRaisesRegex(ScorerError, "embedding_dimension_mismatch"):
            score_pairs(records, embed_fn=lambda texts: [[1.0, 0.0] for _ in texts], model_digest="abc123", scorer_digest="def456")

    @staticmethod
    def record(snapshot, output):
        return {
            "schema": "tiny-fleet.drift-generative/v2",
            "repo": "flask",
            "snapshot": snapshot,
            "arm": "base",
            "prompt_id": "snapshot-component-description-v1",
            "seed": 17,
            "repetition": 0,
            "status": "ok",
            "output": output,
            "base_model_revision": "model-revision",
            "adapter_digest": None,
        }


if __name__ == "__main__":
    unittest.main(verbosity=2)
