"""Contract tests for the offline A08 protected-text correction study."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))

from noisy_text_correction import (  # noqa: E402
    StudyError,
    correct_dictionary,
    correct_identity,
    run_baseline,
    score_document,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/applications/noisy-text-correction/manifest.json"


class NoisyTextCorrectionTests(unittest.TestCase):
    def test_identity_preserves_noisy_text_and_dictionary_repairs_one_token(self):
        document = {
            "text": "Order ID ORD-2026-0042 ships to Berlin on 2026-04-01.",
            "reference": "Order ID ORD-2026-0042 ships to Berlin on 2026-04-01.",
            "protected_spans": [{"start": 9, "end": 22, "text": "ORD-2026-0042", "kind": "id"}],
        }
        self.assertEqual(correct_identity("Order ID ORD-2026-0042 ships to Berln on 2026-04-01."),
                         "Order ID ORD-2026-0042 ships to Berln on 2026-04-01.")
        self.assertEqual(correct_dictionary("Order ID ORD-2026-0042 ships to Berln on 2026-04-01.", {"Berln": "Berlin"}),
                         document["reference"])

    def test_score_rejects_malformed_and_detects_protected_mutation(self):
        document = {"text": "ID ORD-2026-0042 city Berlin", "reference": "ID ORD-2026-0042 city Berlin",
                    "protected_spans": [{"start": 3, "end": 16, "text": "ORD-2026-0042", "kind": "id"}]}
        with self.assertRaisesRegex(StudyError, "string"):
            score_document(document, None)
        result = score_document(document, "ID ORD-2026-9999 city Berlin")
        self.assertEqual(result["protected_unchanged"], 0)
        self.assertEqual(result["protected_violation_n"], 1)

    def test_missing_and_ood_inputs_are_explicitly_unmeasurable(self):
        with self.assertRaisesRegex(StudyError, "non-empty"):
            correct_dictionary("", {"x": "y"})
        self.assertEqual(correct_dictionary("unseen qwerty token", {"berln": "Berlin"}), "unseen qwerty token")

    def test_manifest_has_disjoint_multilingual_heldout_units(self):
        documents = validate_manifest(json.loads(MANIFEST.read_text(encoding="utf-8")))
        heldout = [item for item in documents if item["split"] == "heldout"]
        validation = [item for item in documents if item["split"] == "validation"]
        self.assertEqual(len(heldout), 120)
        self.assertEqual(len(validation), 20)
        self.assertEqual(len({item["source_family"] for item in heldout}), 120)
        self.assertEqual({item["language"] for item in heldout}, {"en", "ru"})
        self.assertTrue({item["source_family"] for item in heldout}.isdisjoint({item["source_family"] for item in validation}))

    def test_baseline_writes_raw_outputs_summary_and_unavailable_model_arms(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = run_baseline(Path(temp) / "run", MANIFEST)
            run = Path(temp) / "run"
            self.assertTrue((run / "raw.jsonl").exists())
            self.assertTrue((run / "summary.json").exists())
            self.assertEqual(summary["heldout_n"], 120)
            self.assertIn(summary["verdict"], {"NO_GO_BASELINE_DOMINANT", "INCONCLUSIVE"})
            self.assertEqual(summary["model_arms"]["ByT5-small"]["status"], "unavailable")
            self.assertIn("protected_field", summary["metrics"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
