#!/usr/bin/env python3
import unittest

from train_drift_adapters import chunk_tokens, run_root_for_plan, select_chunks
from train_study_adapters import DOMAINS, derive_rows, sha_json, training_specs


class DriftAdapterTrainingHelpersTests(unittest.TestCase):
    def test_study_specs_define_exactly_pooled_plus_four_provenance_bound_adapters(self):
        registration = {"study_id": "fleet-study-v1", "model": {"base_id": "HuggingFaceTB/SmolLM2-360M-Instruct",
            "base_revision": "a10cc1512eabd3dde888204e902eca88bddb4951", "adapter": {"r": 16, "alpha": 32,
            "dropout": 0.05, "target_modules": ["q_proj"], "max_length": 256, "learning_rate": 0.0002, "epochs": 1}}}
        specs = training_specs(registration, b"manifest", b"train")
        self.assertEqual(set(specs), {"pooled", *DOMAINS})
        self.assertEqual(specs["pooled"]["domains"], list(DOMAINS))
        self.assertEqual(specs["toy_passage_ppl"]["domains"], ["toy_passage_ppl"])
        self.assertEqual(specs["pooled"]["config_sha256"], sha_json(specs["pooled"]["config"]))

    def test_study_rows_are_derived_only_from_the_frozen_domain_and_keep_provenance(self):
        rows = [{"domain": "a", "source_family": "family-a", "prompt": "p1", "reference": "r1"},
                {"domain": "b", "source_family": "family-b", "prompt": "p2", "reference": "r2"}]
        self.assertEqual(derive_rows(rows, "specialist", "a"), ["p1\nAnswer: r1"])
        self.assertEqual(len(derive_rows(rows, "pooled")), 2)
        with self.assertRaisesRegex(ValueError, "no frozen training rows"):
            derive_rows(rows, "specialist", "missing")
    def test_training_artifacts_stay_bound_to_the_plan_sample(self):
        self.assertEqual(run_root_for_plan({"schema": "tiny-fleet.drift-adapter-training-plan/v1"}),
                         "runs/drift-generative-v2")
        self.assertEqual(run_root_for_plan({"schema": "tiny-fleet.drift-confirmatory-adapter-training-plan/v1"}),
                         "runs/drift-confirmatory-v1")

    def test_chunking_is_nonoverlapping_and_drops_short_tail(self):
        chunks = chunk_tokens(list(range(11)), max_length=4, minimum_tokens=4)
        self.assertEqual(chunks, [(0, 1, 2, 3), (4, 5, 6, 7)])

    def test_sample_budget_uses_stable_path_and_index_hash_order(self):
        chunks = [
            {"source_path": "pkg/a.py", "chunk_index": 0, "input_ids": (1, 2, 3, 4)},
            {"source_path": "pkg/a.py", "chunk_index": 1, "input_ids": (5, 6, 7, 8)},
            {"source_path": "pkg/b.py", "chunk_index": 0, "input_ids": (9, 10, 11, 12)},
        ]
        selected = select_chunks("flask", "old", chunks, token_budget=8, max_length=4)
        reordered = select_chunks("flask", "old", list(reversed(chunks)), token_budget=8, max_length=4)
        self.assertEqual(selected, reordered)
        self.assertEqual(sum(len(row["input_ids"]) for row in selected), 8)
        self.assertNotEqual(selected, chunks)

    def test_budget_cannot_select_zero_training_tokens(self):
        with self.assertRaisesRegex(ValueError, "positive token budget"):
            select_chunks("flask", "old", [], token_budget=0, max_length=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
