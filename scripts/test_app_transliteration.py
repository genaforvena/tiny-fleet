"""Contract tests for the offline A09 transliteration study."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))

from transliteration import (  # noqa: E402
    StudyError,
    run_baseline,
    score_document,
    transliterate,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/applications/transliteration/manifest.json"


class TransliterationTests(unittest.TestCase):
    def test_transliterates_known_words_and_preserves_literal_id(self):
        text = "ORD-2026-0042 klient v Moskva"
        result = transliterate(text, {"klient": "клиент", "v": "в", "Moskva": "Москва"})
        self.assertEqual(result, "ORD-2026-0042 клиент в Москва")
        self.assertEqual(result.split()[0], "ORD-2026-0042")

    def test_unknown_words_abstain_and_malformed_input_is_rejected(self):
        self.assertEqual(transliterate("ORD-2026-9001 qwerty", {"klient": "клиент"}), "ORD-2026-9001 qwerty")
        with self.assertRaisesRegex(StudyError, "non-empty"):
            transliterate("", {})

    def test_score_excludes_protected_span_and_reports_ambiguity(self):
        document = {"noisy_text": "ORD-2026-0042 mir", "clean_text": "ORD-2026-0042 мир",
                    "protected_tokens": ["ORD-2026-0042"], "ambiguous": True}
        result = score_document(document, "ORD-2026-9999 мир")
        self.assertEqual(result["protected_unchanged"], 0)
        self.assertEqual(result["ambiguous"], 1)
        self.assertEqual(result["scored_word_n"], 1)

    def test_manifest_has_independent_multilingual_heldout_units(self):
        documents = validate_manifest(json.loads(MANIFEST.read_text(encoding="utf-8")))
        heldout = [item for item in documents if item["split"] == "heldout"]
        validation = [item for item in documents if item["split"] == "validation"]
        self.assertEqual(len(heldout), 120)
        self.assertEqual(len(validation), 20)
        self.assertEqual(len({item["source_family"] for item in heldout}), 120)
        self.assertEqual({item["language"] for item in heldout}, {"ru-latn", "ru-cyrl"})
        self.assertTrue({item["source_family"] for item in heldout}.isdisjoint({item["source_family"] for item in validation}))

    def test_baseline_writes_raw_outputs_summary_and_model_status(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = run_baseline(Path(temp) / "run", MANIFEST)
            run = Path(temp) / "run"
            self.assertTrue((run / "raw.jsonl").exists())
            self.assertTrue((run / "summary.json").exists())
            self.assertEqual(summary["heldout_n"], 120)
            self.assertIn(summary["verdict"], {"NO_GO", "INCONCLUSIVE"})
            self.assertEqual(summary["model_arms"]["ByT5-small"]["status"], "unavailable")
            self.assertIn("ambiguous_n", summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
