#!/usr/bin/env python3
"""Contract tests for the offline A06 support-routing study."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))

from support_routing import (  # noqa: E402
    QUEUES,
    StudyError,
    classify_nearest_centroid,
    classify_tfidf_logistic,
    run_baseline,
    score_case,
    validate_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/applications/support-routing/manifest.json"


class SupportRoutingTests(unittest.TestCase):
    def test_declares_eight_queues_and_unknown(self):
        self.assertEqual(len(QUEUES), 8)
        self.assertEqual(classify_tfidf_logistic("password reset fails", QUEUES)["queue"], "account-access")
        self.assertEqual(classify_tfidf_logistic("please delete my account", QUEUES)["queue"], "unknown")

    def test_nearest_centroid_abstains_on_empty_or_ambiguous_input(self):
        self.assertEqual(classify_nearest_centroid("", {"billing": ["invoice"]})["queue"], "unknown")
        self.assertEqual(classify_nearest_centroid("invoice password", {"billing": ["invoice"], "account-access": ["password"]})["queue"], "unknown")

    def test_score_rejects_malformed_or_wrong_queue(self):
        case = {"case_id": "x", "split": "heldout", "source_family": "f", "text": "invoice", "reference": {"queue": "billing", "unknown": False}}
        with self.assertRaisesRegex(StudyError, "declared queue"):
            score_case(case, {"queue": "not-a-queue", "unknown": False})
        self.assertEqual(score_case(case, {"queue": "account-access", "unknown": False})["value"], 0)

    def test_manifest_requires_heldout_screening_and_disjoint_families(self):
        with self.assertRaisesRegex(StudyError, "at least 100"):
            validate_manifest({"schema_version": 1, "application_id": "A06", "model_provenance": {}, "cases": []})

    def test_baseline_writes_raw_outputs_and_explicit_no_go(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = run_baseline(Path(temp) / "run", MANIFEST)
            run = Path(temp) / "run"
            self.assertEqual(summary["heldout_n"], 140)
            self.assertTrue((run / "tfidf-logistic-raw.jsonl").exists())
            self.assertTrue((run / "nearest-centroid-raw.jsonl").exists())
            self.assertEqual(summary["pilot_verdict"], "NO_GO_BASELINE_DOMINANT")
            self.assertEqual(summary["model_arms"], "unavailable: C02-C08 and S01-S05 not verified")
            self.assertLessEqual(summary["tfidf_ood_false_accept_upper_95"], 0.05)


if __name__ == "__main__":
    unittest.main(verbosity=2)
