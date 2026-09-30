#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))
from log_normalization import FIELDS, StudyError, parse_log, run_baseline, score_case, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus/applications/log-normalization/manifest.json"


class LogNormalizationTests(unittest.TestCase):
    def test_extracts_fields_and_span_without_diagnosis(self):
        result = parse_log("2026-04-01T00:00:00Z component=api error=EAPI01 operation=read root cause unknown")
        self.assertEqual(result["component"], "api")
        self.assertEqual(result["error_code"], "EAPI01")
        self.assertEqual(result["evidence_span"], "2026-04-01T00:00:00Z component=api error=EAPI01 operation=read")
        self.assertNotIn("root_cause", result)

    def test_missing_timestamp_and_malformed_data_stay_null(self):
        result = parse_log("component=api message=benign warning")
        self.assertEqual(result["component"], "api")
        self.assertIsNone(result["timestamp"])
        self.assertIsNone(result["error_code"])
        self.assertEqual(result["evidence_span"], "api")

    def test_contract_rejects_extra_prediction_field(self):
        case = {"case_id": "x", "split": "heldout", "source_family": "f", "text": "x",
                "reference": {field: None for field in FIELDS}}
        with self.assertRaisesRegex(StudyError, "exactly"):
            score_case(case, {**{field: None for field in FIELDS}, "root_cause": "timeout"})

    def test_manifest_has_independent_screening_set(self):
        cases = validate_manifest(json.loads(MANIFEST.read_text()))
        heldout = [case for case in cases if case["split"] == "heldout"]
        self.assertEqual(len(heldout), 120)
        self.assertEqual(len({case["source_family"] for case in heldout}), 120)

    def test_baseline_writes_raw_output_and_no_go(self):
        with tempfile.TemporaryDirectory() as temp:
            summary = run_baseline(Path(temp) / "run", MANIFEST)
            self.assertEqual(summary["heldout_n"], 120)
            self.assertEqual(summary["heldout_exact_rate"], 1.0)
            self.assertEqual(summary["unsupported_field_rate"], 0.0)
            self.assertEqual(summary["pilot_verdict"], "NO_GO_BASELINE_DOMINANT")
            self.assertTrue((Path(temp) / "run/regex-template-raw.jsonl").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
