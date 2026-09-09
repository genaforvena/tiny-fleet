"""Contract tests for the offline A05 duplicate-incident study."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))

from duplicate_incidents import (  # noqa: E402
    StudyError,
    normalize,
    predict_bm25,
    predict_normalized_hash,
    run_baseline,
    score_case,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/applications/duplicate-incidents/manifest.json"


class DuplicateIncidentTests(unittest.TestCase):
    def test_normalization_is_case_and_punctuation_insensitive(self):
        self.assertEqual(normalize("Service ERROR #7!"), "service error 7")

    def test_hash_matches_exact_ticket_and_abstains_on_unknown(self):
        incidents = {"i-1": {"incident_id": "i-1", "text": "service error 7: restart required"}}
        case = {"case_id": "x", "split": "heldout", "source_family": "f", "time_period": "t", "ticket": "SERVICE ERROR 7 restart required", "candidate_incident_ids": ["i-1"], "reference": {"incident_id": "i-1", "abstain": False}}
        self.assertEqual(predict_normalized_hash(case, incidents)["incident_id"], "i-1")
        case["ticket"] = "unrelated text"
        self.assertTrue(predict_normalized_hash(case, incidents)["abstain"])

    def test_score_rejects_malformed_and_non_candidate_match(self):
        case = {"case_id": "x", "split": "heldout", "source_family": "f", "time_period": "t", "ticket": "service error", "candidate_incident_ids": ["i-1"], "reference": {"incident_id": None, "abstain": True}}
        with self.assertRaisesRegex(StudyError, "not a candidate"):
            score_case(case, {"incident_id": "i-2", "abstain": False}, {"i-1"})
        with self.assertRaisesRegex(StudyError, "agree"):
            score_case(case, {"incident_id": None, "abstain": False}, {"i-1"})

    def test_manifest_has_independent_heldout_matches_and_no_matches(self):
        incidents, cases = validate_manifest(json.loads(MANIFEST.read_text()))
        self.assertEqual(len([case for case in cases if case["split"] == "heldout"]), 120)
        self.assertTrue(any(case["reference"]["abstain"] for case in cases))
        self.assertEqual(len({case["source_family"] for case in cases if case["split"] == "heldout"}), 120)
        self.assertEqual(len(incidents), 132)

    def test_manifest_rejects_incomplete_screening_set(self):
        with self.assertRaisesRegex(StudyError, "incidents and cases must be nonempty"):
            validate_manifest({"schema_version": 1, "application_id": "A05", "model_provenance": {"EmbeddingGemma": {"model_id": "google/embeddinggemma-300m", "revision": "57c266a740f537b4dc058e1b0cda161fd15afa75", "license": "x", "source_url": "https://x"}}, "incidents": [{"incident_id": "i", "split": "heldout"}], "cases": []})

    def test_baseline_writes_raw_outputs_and_no_go_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = run_baseline(Path(temp) / "run", MANIFEST)
            run = Path(temp) / "run"
            self.assertTrue((run / "normalized-hash-raw.jsonl").exists())
            self.assertTrue((run / "character-ngram-raw.jsonl").exists())
            self.assertTrue((run / "bm25-raw.jsonl").exists())
            self.assertTrue((run / "summary.json").exists())
            self.assertEqual(summary["pilot_verdict"], "INCONCLUSIVE")
            self.assertEqual(summary["all_MiniLM"]["status"], "unavailable")
            self.assertEqual(summary["baselines"]["normalized-hash"]["false_accept_n"], 0)
            self.assertEqual(summary["baselines"]["normalized-hash"]["candidate_retrieval_recall"], 1.0)
            self.assertEqual(summary["baselines"]["normalized-hash"]["pair_precision"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
