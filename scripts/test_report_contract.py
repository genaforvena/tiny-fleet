#!/usr/bin/env python3
"""Contract tests for derived report validation."""

import csv
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from deep_evaluation import ValidationError
from report_contract import validate_reports
from test_deep_evaluation import DeepEvaluationValidatorTests


class ReportContractTests(unittest.TestCase):
    def make_run(self):
        root = DeepEvaluationValidatorTests().make_run()
        (root / "scores.json").write_text(json.dumps({
            "schema": "tiny-fleet.deep-eval.scores/v1",
            "result_status": "negative",
            "total_predictions": 4,
            "scored_predictions": 4,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "false_accepts": 0,
        }))
        (root / "slices.tsv").write_text(
            "slice\tvalue\tcount\tscored\tcorrect\taccuracy\n"
            "domain\tfixture\t4\t4\t0\t0.0\n"
        )
        (root / "calibration.tsv").write_text(
            "bin\tcount\tconfidence_sum\tcorrect\tece\tbrier\n"
            "0\t4\t3.0\t0\t0.75\t0.5625\n"
        )
        (root / "routing.tsv").write_text(
            "case_id\tmodel\tseed\trepetition\texpected_route\tactual_route\tdecision\n"
            "heldout-1\tbase\t17\t0\tspecialist:fixture\tspecialist:fixture\tanswer\n"
            "heldout-1\tcandidate\t17\t0\tspecialist:fixture\tspecialist:fixture\tanswer\n"
            "adversarial-1\tbase\t17\t0\tspecialist:fixture\tspecialist:fixture\tanswer\n"
            "adversarial-1\tcandidate\t17\t0\tspecialist:fixture\tspecialist:fixture\tanswer\n"
        )
        (root / "adversarial.tsv").write_text(
            "case_id\tmodel\tseed\trepetition\texpected_action\tactual_action\tforbidden_output\treviewed\n"
            "adversarial-1\tbase\t17\t0\tanswer\tanswer\tfalse\ttrue\n"
            "adversarial-1\tcandidate\t17\t0\tanswer\tanswer\tfalse\ttrue\n"
        )
        (root / "cost.tsv").write_text(
            "metric\tvalue\tunit\tcount\n"
            "p50_latency\t2.5\tms\t4\n"
            "p95_latency\t2.5\tms\t4\n"
        )
        (root / "decision.md").write_text(
            "result_status: negative\n"
            "routing_eligible: false\n"
            "coverage: 1.0\n"
            "next_action: collect a powered replication\n"
        )
        return root

    def test_accepts_complete_negative_bundle_but_not_routing_eligible(self):
        result = validate_reports(self.make_run())
        self.assertEqual(result, {
            "artifact_valid": True,
            "result_status": "negative",
            "routing_eligible": False,
        })

    def test_rejects_missing_report(self):
        root = self.make_run()
        (root / "slices.tsv").unlink()
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-missing slices.tsv$"):
            validate_reports(root)

    def test_rejects_invalid_json_and_tsv(self):
        root = self.make_run()
        (root / "scores.json").write_text("{")
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-schema scores.json"):
            validate_reports(root)
        root = self.make_run()
        (root / "routing.tsv").write_text("not\ta\tvalid\treport\n")
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-schema routing.tsv"):
            validate_reports(root)

    def test_rejects_nonfinite_or_negative_report_numbers(self):
        root = self.make_run()
        path = root / "slices.tsv"
        path.write_text(path.read_text().replace("\t4\t4\t0\t0.0", "\t-1\t4\t0\t0.0"))
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-schema slices.count"):
            validate_reports(root)
        root = self.make_run()
        path = root / "cost.tsv"
        path.write_text(path.read_text().replace("\t2.5\tms\t4", "\tnan\tms\t4"))
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-schema cost.value"):
            validate_reports(root)

    def test_rejects_edited_primary_count(self):
        root = self.make_run()
        scores = json.loads((root / "scores.json").read_text())
        scores["correct_predictions"] = 4
        (root / "scores.json").write_text(json.dumps(scores))
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-reconciliation correct_predictions"):
            validate_reports(root)

    def test_rejects_unsafe_action_mislabeled_safe(self):
        root = self.make_run()
        path = root / "adversarial.tsv"
        text = path.read_text().replace("\tanswer\tanswer\tfalse\ttrue", "\tanswer\trefuse\tfalse\ttrue", 1)
        path.write_text(text)
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-reconciliation adversarial"):
            validate_reports(root)

    def test_rejects_omitted_failed_case(self):
        root = self.make_run()
        path = root / "routing.tsv"
        lines = path.read_text().splitlines()
        path.write_text("\n".join(lines[:-1]) + "\n")
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-cardinality routing.tsv"):
            validate_reports(root)

    def test_rejects_all_abstain_report_claimed_useful(self):
        root = self.make_run()
        predictions = []
        for line in (root / "predictions.jsonl").read_text().splitlines():
            prediction = json.loads(line)
            prediction.update({"status": "timeout", "output": None, "confidence": None,
                               "latency_ms": None, "unavailable_reason": "fixture timeout"})
            predictions.append(json.dumps(prediction))
        (root / "predictions.jsonl").write_text("\n".join(predictions) + "\n")
        scores = json.loads((root / "scores.json").read_text())
        scores.update({"result_status": "positive", "scored_predictions": 0, "accuracy": 0.0})
        (root / "scores.json").write_text(json.dumps(scores))
        (root / "decision.md").write_text(
            "result_status: positive\n"
            "routing_eligible: true\n"
            "coverage: 0.0\n"
            "useful: true\n"
        )
        with self.assertRaisesRegex(ValidationError, r"^REJECT report-quality all predictions abstain"):
            validate_reports(root)


if __name__ == "__main__":
    unittest.main()
