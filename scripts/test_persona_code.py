#!/usr/bin/env python3
"""Dependency-free regression tests for the persona/code runner contract."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts" / "persona_code.py"
MANIFEST = ROOT / "runs" / "persona-code" / "manifest.json"


def test_self_test_accepts_manifest() -> None:
    result = subprocess.run(
        [sys.executable, str(RUNNER), "self-test", "--manifest", str(MANIFEST)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "self-test: ok" in result.stdout


def test_existing_eval_has_case_artifact_contract() -> None:
    result = ROOT / "runs" / "persona-code" / "eval-all.json"
    payload = json.loads(result.read_text())
    assert payload["schema"] == "persona-code.eval/v2"
    assert len(payload["predictions"]) == 24
    assert payload["prediction_cardinality"] == len(payload["predictions"])
    assert len(payload["adversarial"]) == 84
    assert payload["adversarial_cardinality"] == len(payload["adversarial"])
    for row in payload["predictions"]:
        assert {"case_id", "model", "split", "output", "decision"} <= row.keys()
    for row in payload["adversarial"]:
        assert row["expected_action"] == "abstain"
        assert {"case_id", "model", "predicted_action", "output"} <= row.keys()


if __name__ == "__main__":
    for test in (test_self_test_accepts_manifest, test_existing_eval_has_case_artifact_contract):
        test()
    print("persona-code tests: 2/2")
