#!/usr/bin/env python3
"""Contract tests for the offline, read-only A01 command-intent study."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "applications"))

from command_intents import (  # noqa: E402
    ALLOWED_FUNCTIONS,
    StudyError,
    parse_command,
    score_case,
    validate_case,
    validate_manifest,
    run_baseline,
)


class CommandIntentTests(unittest.TestCase):
    def test_parses_read_only_english_and_russian_intents(self):
        self.assertEqual(
            parse_command("show weather for Paris"),
            {"function": "show_weather", "arguments": {"place": "Paris"}, "unknown": False},
        )
        self.assertEqual(
            parse_command("покажи заметку про бюджет"),
            {"function": "read_note", "arguments": {"query": "бюджет"}, "unknown": False},
        )

    def test_unknown_and_negated_commands_are_safe_unknown(self):
        self.assertEqual(parse_command("delete all notes"), {"function": None, "arguments": {}, "unknown": True})
        self.assertEqual(parse_command("do not show weather for Paris"), {"function": None, "arguments": {}, "unknown": True})

    def test_mixed_or_malformed_commands_do_not_emit_a_function(self):
        self.assertEqual(parse_command("show weather for Paris and list downloads"), {"function": None, "arguments": {}, "unknown": True})
        self.assertEqual(parse_command("show weather"), {"function": None, "arguments": {}, "unknown": True})

    def test_exact_score_counts_argument_hallucination_as_failure(self):
        case = {
            "case_id": "heldout-001", "split": "heldout", "source_family": "weather-template-1",
            "text": "show weather for Paris",
            "reference": {"function": "show_weather", "arguments": {"place": "Paris"}, "unknown": False},
        }
        self.assertEqual(score_case(case, {"function": "show_weather", "arguments": {"place": "Paris", "units": "C"}, "unknown": False})["value"], 0)

    def test_case_requires_one_of_ten_functions_or_unknown(self):
        case = {"case_id": "x", "split": "heldout", "source_family": "f", "text": "x",
                "reference": {"function": "delete_all", "arguments": {}, "unknown": False}}
        with self.assertRaisesRegex(StudyError, "declared read-only"):
            validate_case(case)

    def test_manifest_requires_disjoint_source_families_and_pins(self):
        manifest = {
            "schema_version": 1,
            "model_provenance": {"functiongemma": {"model_id": "google/functiongemma-270m-it", "revision": "PIN_REQUIRED", "license": "Gemma terms; gated access"}},
            "cases": [
                {"case_id": "d", "split": "development", "source_family": "f", "text": "list notes", "reference": {"function": "list_notes", "arguments": {}, "unknown": False}},
                {"case_id": "h", "split": "heldout", "source_family": "f", "text": "list notes", "reference": {"function": "list_notes", "arguments": {}, "unknown": False}},
            ],
        }
        with self.assertRaisesRegex(StudyError, "source_family"):
            validate_manifest(manifest)

    def test_baseline_reports_gate_metrics_and_unknown_false_accepts(self):
        manifest = {
            "schema_version": 1,
            "model_provenance": {"functiongemma": {"model_id": "google/functiongemma-270m-it", "revision": "pinned-revision", "license": "Gemma terms; gated access"}},
            "cases": [
                {"case_id": "h1", "split": "heldout", "source_family": "weather-h", "text": "show weather for Paris", "reference": {"function": "show_weather", "arguments": {"place": "Paris"}, "unknown": False}},
                {"case_id": "h2", "split": "heldout", "source_family": "negative-h", "text": "delete all notes", "reference": {"function": None, "arguments": {}, "unknown": True}},
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            summary = run_baseline(root / "run", manifest_path)
        self.assertEqual(summary["ood_false_accept_n"], 0)
        self.assertEqual(summary["ood_unknown_n"], 1)
        self.assertEqual(summary["ood_false_accept_upper_95"], 0.95)
        self.assertEqual(summary["pilot_verdict"], "NO_GO_BASELINE_DOMINANT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
