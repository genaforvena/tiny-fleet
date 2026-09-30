#!/usr/bin/env python3
import json
from pathlib import Path
import tempfile
import unittest

from audit_study_independence import load_corpus, SPLITS


class StudyIndependenceTests(unittest.TestCase):
    def test_unicode_separators_inside_strings_are_not_record_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for split in SPLITS:
                rows = [
                    {"case_id": f"{split}-{i}", "source_id": f"source-{split}-{i}",
                     "source_family": f"family-{split}-{i}", "domain": "passage",
                     "split": split, "prompt": prompt, "reference": "answer"}
                    for i, prompt in enumerate(("first\u2028second\u2029third", "next record"))
                ]
                # CRLF is also a valid physical JSONL boundary.
                (root / f"{split}.jsonl").write_bytes(
                    ("\r\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
                     + "\r\n").encode("utf-8")
                )
            loaded, _ = load_corpus(root)
            for split in SPLITS:
                self.assertEqual([r["prompt"] for r in loaded[split]],
                                 ["first\u2028second\u2029third", "next record"])
                self.assertEqual([r["audit_line"] for r in loaded[split]], [1, 2])

    def test_blank_physical_record_is_not_silently_discarded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = {"case_id": "case", "source_id": "source", "source_family": "family",
                   "domain": "passage", "split": "train", "prompt": "input", "reference": "answer"}
            (root / "train.jsonl").write_text(json.dumps(row) + "\n\n")
            with self.assertRaisesRegex(ValueError, r"train\.jsonl:2: invalid JSON"):
                load_corpus(root)


if __name__ == "__main__":
    unittest.main()
