#!/usr/bin/env python3
"""Contract tests for offline board-dispatch baselines."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dispatch_baselines import (  # noqa: E402
    TfidfOwnerRanker,
    authoritative_guard,
    load_cases,
    rank_explicit,
    rank_role_keyword,
    run,
)


ROOT = Path(__file__).resolve().parents[1]


class DispatchBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(ROOT / "corpus/board-dispatch-v1/cases.jsonl")

    def test_authoritative_guard_fails_closed_and_intersects_whitelist(self):
        case = copy.deepcopy(self.cases[0])
        self.assertEqual(authoritative_guard(case, ["sense", "forged"]), ["sense"])
        case["dependency_state"] = "blocked"
        self.assertIsNone(authoritative_guard(case, ["sense"]))
        case = copy.deepcopy(self.cases[0])
        case["eligible_owner_ids"] = []
        self.assertIsNone(authoritative_guard(case, ["sense"]))

    def test_explicit_owner_is_preserved_even_when_text_suggests_other_role(self):
        case = copy.deepcopy(self.cases[6])
        self.assertEqual(rank_explicit(case), ["genome"])
        case["eligible_owner_ids"] = ["dev"]
        self.assertIsNone(rank_explicit(case))

    def test_learned_baselines_never_replace_explicit_or_admit_inadmissible_case(self):
        ranker = TfidfOwnerRanker(self.cases)
        for method in (rank_role_keyword, ranker.rank):
            self.assertEqual(method(self.cases[6]), ["genome"])
            blocked = copy.deepcopy(self.cases[7])
            self.assertIsNone(method(blocked))

    def test_quality_separates_unowned_from_explicit_and_keeps_raw_predictions(self):
        result = run(self.cases)
        self.assertEqual(len(result["predictions"]), 5)
        for metrics in result["metrics"]:
            self.assertEqual(metrics["heldout_unowned"], 7)
            self.assertEqual(metrics["quality_units"], 4)
            self.assertEqual(metrics["severe_constraint_violations"], 0)
            self.assertIn("latency_ms_p95", metrics)
        self.assertIsNone(result["predictions"]["abstain-all"]["bd-005"])

    def test_cli_writes_reproducible_offline_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.json"
            import subprocess
            completed = subprocess.run([sys.executable, str(ROOT / "scripts/dispatch_baselines.py"), "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            artifact = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(artifact["schema"], "tiny-fleet.board-dispatch.baselines/v1")
            self.assertEqual(len(artifact["predictions"]), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
