"""Contract tests for the offline A07 redaction-assistance study."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))

from redaction_assistance import (  # noqa: E402
    StudyError,
    detect_regex,
    run_baseline,
    score_document,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/applications/redaction-assistance/manifest.json"


class RedactionAssistanceTests(unittest.TestCase):
    def test_regex_returns_exact_offsets_for_multilingual_pii(self):
        text = "Имя: Анна Кузнецова; Email: anna.k@example.org; ID: ACCT-2026-0042."
        rows = detect_regex(text)
        self.assertEqual(
            [(row["type"], row["text"], text[row["start"] : row["end"]]) for row in rows],
            [
                ("name", "Анна Кузнецова", "Анна Кузнецова"),
                ("email", "anna.k@example.org", "anna.k@example.org"),
                ("account_id", "ACCT-2026-0042", "ACCT-2026-0042"),
            ],
        )

    def test_regex_does_not_invent_spans_for_ood_text(self):
        self.assertEqual(detect_regex("The service completed successfully."), [])

    def test_score_rejects_malformed_or_out_of_bounds_predictions(self):
        document = {
            "document_id": "x",
            "split": "heldout",
            "source_family": "f",
            "format_family": "plain",
            "language": "en",
            "text": "Email: a@example.org",
            "entities": [{"type": "email", "start": 7, "end": 20, "text": "a@example.org"}],
        }
        with self.assertRaisesRegex(StudyError, "bounds"):
            score_document(document, [{"type": "email", "start": -1, "end": 20, "text": "a@example.org"}])
        with self.assertRaisesRegex(StudyError, "text"):
            score_document(document, [{"type": "email", "start": 7, "end": 20, "text": "wrong@example.org"}])

    def test_manifest_has_independent_multilingual_heldout_documents(self):
        documents = validate_manifest(json.loads(MANIFEST.read_text(encoding="utf-8")))
        heldout = [document for document in documents if document["split"] == "heldout"]
        self.assertEqual(len(heldout), 120)
        self.assertEqual(len({document["source_family"] for document in heldout}), 120)
        self.assertEqual({document["language"] for document in heldout}, {"en", "ru"})
        self.assertGreaterEqual(len({entity["type"] for document in heldout for entity in document["entities"]}), 4)

    def test_baseline_writes_raw_outputs_and_residual_risk_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = run_baseline(Path(temp) / "run", MANIFEST)
            run = Path(temp) / "run"
            self.assertTrue((run / "regex-raw.jsonl").exists())
            self.assertTrue((run / "summary.json").exists())
            self.assertIn(summary["verdict"], {"NO_GO", "INCONCLUSIVE"})
            self.assertIn("residual_risks", summary)
            self.assertEqual(summary["model_arm"]["status"], "unavailable")


if __name__ == "__main__":
    unittest.main(verbosity=2)
