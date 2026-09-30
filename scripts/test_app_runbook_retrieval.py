"""Contract tests for the offline A04 cited-runbook retrieval study."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))

from runbook_retrieval import (  # noqa: E402
    StudyError,
    bm25_retrieve,
    run_baseline,
    score_case,
    validate_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/applications/runbook-retrieval/manifest.json"


class RunbookRetrievalTests(unittest.TestCase):
    def test_retrieval_returns_at_most_five_paragraph_ids(self):
        paragraphs = [{"paragraph_id": f"p-{i}", "text": "restart service cache"} for i in range(8)]
        result = bm25_retrieve("restart service", paragraphs)
        self.assertLessEqual(len(result), 5)
        self.assertTrue(all(isinstance(item, str) for item in result))

    def test_no_answer_is_explicit_when_no_support_exists(self):
        paragraphs = [{"paragraph_id": "p-1", "text": "rotate logs weekly"}]
        result = bm25_retrieve("replace the office carpet", paragraphs)
        self.assertEqual(result, [])

    def test_score_rejects_malformed_and_false_citation(self):
        case = {"case_id": "x", "split": "heldout", "source_family": "f", "manual_id": "m", "query": "restart", "gold_paragraph_ids": ["p-1"], "available_paragraph_ids": ["p-1"], "answerable": True}
        with self.assertRaisesRegex(StudyError, "outside the manual"):
            score_case(case, {"paragraph_ids": ["not-in-manual"]})
        self.assertEqual(score_case(case, {"paragraph_ids": []})["recall_at_5"], 0)

    def test_manifest_requires_disjoint_manual_families_and_ood(self):
        with self.assertRaisesRegex(StudyError, "nonempty"):
            validate_manifest({"schema_version": 1, "application_id": "A04", "model_provenance": {"EmbeddingGemma": {"model_id": "x", "revision": "x", "license": "x", "source_url": "x"}}, "manuals": [], "cases": []})

    def test_baseline_writes_raw_outputs_and_explicit_no_go(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = run_baseline(Path(temp) / "run", MANIFEST)
            run = Path(temp) / "run"
            self.assertEqual(summary["heldout_n"], 160)
            self.assertTrue((run / "bm25-raw.jsonl").exists())
            self.assertTrue((run / "summary.json").exists())
            self.assertEqual(summary["pilot_verdict"], "NO_GO_BASELINE_DOMINANT")
            self.assertLessEqual(summary["no_answer_false_accept_upper_95"], 0.05)


if __name__ == "__main__":
    unittest.main(verbosity=2)
