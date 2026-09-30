#!/usr/bin/env python3
import json
import copy
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from study_runner import ARMS, FakeBackend, load_corpus, render_input, run, validate_corpus

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/study-v1/manifest.json"


class StudyRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.rows = load_corpus(MANIFEST)
        validate_corpus(cls.manifest, cls.rows)

    def test_expected_matrix_and_split_guards(self):
        self.assertEqual(len(ARMS), 7)
        self.assertEqual({r["case_id"] for r in self.rows["heldout"]}, {r["case_id"] for r in self.rows["heldout"]})
        self.assertTrue(all(r["reference"] not in render_input(r, "prompt-only", self.rows["train"]) for r in self.rows["heldout"]))
        with self.assertRaises(ValueError):
            bad = json.loads(json.dumps(self.manifest)); rows = copy.deepcopy(self.rows)
            rows["validation"][0]["source_family"] = rows["train"][0]["source_family"]
            validate_corpus(bad, rows)

    def test_fake_backend_keeps_case_ids_and_input_separation(self):
        with tempfile.TemporaryDirectory() as td:
            summary = run(MANIFEST, Path(td), "prompt-only", 17, FakeBackend(), limit=3)
            self.assertEqual(summary["records"], 3)
            self.assertEqual(summary["ok"], 3)
            records = [json.loads(x) for x in (Path(td) / "predictions-prompt-only.jsonl").read_text().splitlines()]
            self.assertEqual([r["case_id"] for r in records], [r["case_id"] for r in self.rows["heldout"][:3]])
            self.assertTrue(all(not r["reference_in_input"] for r in records))
            self.assertTrue(all(r["case_prompt_sha256"] and r["rendered_input_sha256"] for r in records))

    def test_timeout_is_a_failure_record_not_a_filled_prediction(self):
        with tempfile.TemporaryDirectory() as td:
            rows = {k: list(v) for k, v in self.rows.items()}; rows["heldout"][0]["prompt"] += " __TIMEOUT__"
            original = MANIFEST.parent / "manifest.json"
            temp_root = Path(td) / "corpus" / "study-v1"; temp_root.mkdir(parents=True)
            for split, values in rows.items():
                path = temp_root / f"{split}.jsonl"; path.write_text("".join(json.dumps(x) + "\n" for x in values))
            manifest = json.loads(original.read_text()); manifest["files"] = {k: f"corpus/study-v1/{k}.jsonl" for k in rows}
            manifest["rows_per_file"] = {k: len(v) for k, v in rows.items()}
            temp_manifest = temp_root / "manifest.json"; temp_manifest.write_text(json.dumps(manifest))
            summary = run(temp_manifest, Path(td) / "run", "base", 1, FakeBackend(), limit=1)
            self.assertEqual(summary["failed"], 1)
            record = json.loads((Path(td) / "run/predictions-base.jsonl").read_text())
            self.assertEqual(record["runtime_status"], "timeout")
            self.assertNotIn("output", record)


if __name__ == "__main__":
    unittest.main(verbosity=2)
