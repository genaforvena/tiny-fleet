import copy
import json
import tempfile
import unittest
from pathlib import Path

from score_study import score_run


class ScoreStudyTests(unittest.TestCase):
    def make_run(self, outputs=None, *, all_abstain=False):
        root = Path(tempfile.mkdtemp())
        datasets = root / "datasets"
        datasets.mkdir()
        heldout = [
            {"case_id": "h1", "domain": "toy_passage_ppl", "source_family": "f1", "reference": "yes"},
            {"case_id": "h2", "domain": "toy_passage_ppl", "source_family": "f1", "reference": "no"},
            {"case_id": "h3", "domain": "executable_code", "source_family": "f2", "reference": "run"},
        ]
        adversarial = [
            {"case_id": "a1", "domain": "adversarial_safety", "source_family": "f3",
             "reference": "refuse", "expected_action": "refuse"},
        ]
        for name, rows in (("heldout", heldout), ("adversarial", adversarial)):
            (datasets / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        (root / "manifest.json").write_text(json.dumps({
            "schema": "tiny-fleet.study-run-manifest/v1",
            "datasets": {"heldout": {"path": "datasets/heldout.jsonl"},
                         "adversarial": {"path": "datasets/adversarial.jsonl"}},
            "prediction_matrix": {"models": ["candidate"], "seeds": [17], "repetitions": [0]},
        }))
        if outputs is None:
            outputs = {"h1": "yes", "h2": "wrong", "h3": "run", "a1": "refuse"}
        rows = []
        for case_id, output in outputs.items():
            row = {"schema": "tiny-fleet.study-prediction/v1", "case_id": case_id,
                   "model": "candidate", "arm": "candidate", "seed": 17, "repetition": 0,
                   "runtime_status": "ok", "output": output, "action": output,
                   "confidence": 0.8, "latency_ms": 10.0}
            if all_abstain:
                row["runtime_status"] = "timeout"
                row.pop("output")
                row.pop("action")
                row["error"] = "timeout"
            rows.append(row)
        (root / "predictions-candidate.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        return root

    def test_known_arithmetic_and_failure_denominator(self):
        root = self.make_run()
        result = score_run(root)
        self.assertEqual(result["scores"]["total_predictions"], 4)
        self.assertEqual(result["scores"]["scored_predictions"], 4)
        self.assertEqual(result["scores"]["correct_predictions"], 3)
        self.assertEqual(result["scores"]["false_accepts"], 0)
        self.assertEqual(result["decision"]["routing_eligible"], False)
        self.assertEqual(result["decision"]["result_status"], "negative")

    def test_timeout_is_failure_and_zero_coverage_is_undefined(self):
        result = score_run(self.make_run(all_abstain=True))
        self.assertEqual(result["scores"]["total_predictions"], 4)
        self.assertEqual(result["scores"]["scored_predictions"], 0)
        self.assertIsNone(result["scores"]["accuracy"])
        self.assertEqual(result["decision"]["result_status"], "inconclusive")
        self.assertFalse(result["decision"]["routing_eligible"])

    def test_rebuild_is_byte_deterministic_and_clusters_bootstrap(self):
        root = self.make_run()
        first = score_run(root)
        second = score_run(root)
        self.assertEqual(first["files_sha256"], second["files_sha256"])
        self.assertIn("cluster_bootstrap", first["scores"])
        self.assertEqual(first["scores"]["cluster_bootstrap"]["clusters"], 3)

    def test_duplicate_raw_key_is_invalid(self):
        root = self.make_run()
        path = root / "predictions-candidate.jsonl"
        text = path.read_text()
        path.write_text(text + text.splitlines()[0] + "\n")
        with self.assertRaisesRegex(ValueError, "duplicate prediction key"):
            score_run(root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
