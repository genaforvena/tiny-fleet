#!/usr/bin/env python3
"""Contract tests for the offline application-screening registry."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from application_screen import (  # noqa: E402
    RegistryError,
    load_registry,
    minimum_zero_failure_sample,
    validate_case,
    validate_registry,
    zero_failure_upper_bound,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "runs/applications/registry.json"


class ApplicationScreenTests(unittest.TestCase):
    def test_registry_has_ten_complete_offline_hypotheses(self):
        registry = load_registry(REGISTRY)
        validate_registry(registry)
        self.assertEqual(len(registry["applications"]), 10)
        self.assertEqual(
            {item["application_id"] for item in registry["applications"]},
            {f"A{i:02d}" for i in range(1, 11)},
        )
        self.assertTrue(all(item["state"] == "registered" for item in registry["applications"]))
        self.assertTrue(all(item["run_hashes"] == [] for item in registry["applications"]))

    def test_zero_failure_bound_requires_299_and_598_independent_cases(self):
        self.assertEqual(minimum_zero_failure_sample(0.01), 299)
        self.assertEqual(minimum_zero_failure_sample(0.005), 598)
        self.assertLessEqual(zero_failure_upper_bound(299), 0.01)
        self.assertGreater(zero_failure_upper_bound(298), 0.01)

    def test_duplicate_source_family_is_not_a_valid_independent_sample(self):
        with self.assertRaisesRegex(RegistryError, "source_family"):
            validate_case(
                {
                    "case_id": "x2",
                    "split": "heldout",
                    "source_family": "same-as-x1",
                    "input": {"text": "different"},
                    "reference": {"label": "ok"},
                    "score": {"value": 1, "denominator": 1, "is_probability": False},
                },
                seen_source_families={"same-as-x1"},
            )

    def test_missing_values_are_null_with_reason_not_zero(self):
        with self.assertRaisesRegex(RegistryError, "missing field"):
            validate_case(
                {
                    "case_id": "x1",
                    "split": "validation",
                    "source_family": "family-1",
                    "input": {"text": "unknown"},
                    "reference": {"label": None},
                    "score": {"value": 0, "denominator": 1, "is_probability": False},
                }
            )

    def test_uncalibrated_score_cannot_be_called_probability(self):
        with self.assertRaisesRegex(RegistryError, "calibrated"):
            validate_case(
                {
                    "case_id": "x1",
                    "split": "validation",
                    "source_family": "family-1",
                    "input": {"text": "ok"},
                    "reference": {"label": "ok"},
                    "score": {"value": 0.8, "denominator": 1, "is_probability": True, "calibrated": False},
                }
            )

    def test_no_go_is_a_valid_terminal_screening_state(self):
        registry = json.loads(json.dumps(load_registry(REGISTRY)))
        registry["applications"][0]["state"] = "no-go"
        validate_registry(registry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
