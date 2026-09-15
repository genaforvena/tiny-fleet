#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_study_matrix import build_matrix, execution_arms, require_adapters, selected_matrix_rows, wait_for_gpu


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "runs/fleet-study-v1/registration.json"


class StudyMatrixTests(unittest.TestCase):
    def test_cli_help_is_real_and_exits_successfully(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "run_study_matrix.py"), "--help"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--registration", result.stdout)
        self.assertIn("--run-root", result.stdout)

    def test_matrix_expands_registered_arms_and_seeds_without_duplicates(self):
        registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
        matrix = build_matrix(registration)

        self.assertEqual(len(matrix), len(registration["arms"]) * len(registration["statistics"]["seeds"]))
        keys = [(row["arm"], row["seed"]) for row in matrix]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual([row["seed"] for row in matrix[:len(registration["arms"])]], [17] * len(registration["arms"]))

    def test_default_execution_selects_each_registered_arm_seed_once(self):
        registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
        selected = selected_matrix_rows(registration)
        self.assertEqual(len(selected), 15)
        self.assertEqual(
            {(row["arm"], row["seed"]) for row in selected},
            {(row["arm"], row["seed"]) for row in build_matrix(registration)},
        )

    def test_matrix_rejects_duplicate_registered_arm_ids(self):
        registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
        registration["arms"].append(dict(registration["arms"][0]))

        with self.assertRaises(ValueError):
            build_matrix(registration)

    def test_registered_router_arms_expand_to_explicit_specialists(self):
        self.assertEqual(len(execution_arms("simple_router")), 4)
        self.assertEqual(execution_arms("routed_specialists"), execution_arms("simple_router"))
        self.assertEqual(execution_arms("base"), ("base",))

    def test_real_adapter_arm_refuses_missing_artifact_without_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError, "missing trained adapter artifacts"):
                require_adapters(Path(td), "pooled_adapter")

    def test_verification_only_smoke_writes_all_registered_arms_without_training(self):
        with tempfile.TemporaryDirectory() as td:
            run_root = Path(td) / "smoke"
            result = subprocess.run([
                sys.executable, str(Path(__file__).parent / "run_study_matrix.py"),
                "--registration", str(REGISTRATION), "--run-root", str(run_root),
                "--seeds", "17", "--max-cases", "2", "--max-train-steps", "2",
                "--verification-only",
            ], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((run_root / "smoke-summary.json").read_text())
            self.assertTrue(summary["verification_only"])
            self.assertFalse(summary["training_executed"])
            self.assertEqual(summary["rows"], len(json.loads(REGISTRATION.read_text())["arms"]))
            self.assertEqual(len(list(run_root.glob("seed-17/*/predictions*.jsonl"))), 5)

    def test_execution_refuses_non_empty_run_root(self):
        with tempfile.TemporaryDirectory() as td:
            run_root = Path(td) / "occupied"
            run_root.mkdir()
            (run_root / "sentinel").write_text("keep")
            result = subprocess.run([
                sys.executable, str(Path(__file__).parent / "run_study_matrix.py"),
                "--registration", str(REGISTRATION), "--run-root", str(run_root),
                "--verification-only",
            ], capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to overwrite", result.stderr)

    def test_real_execution_rejects_manual_subset_overrides(self):
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run([
                sys.executable, str(Path(__file__).parent / "run_study_matrix.py"),
                "--registration", str(REGISTRATION), "--run-root", str(Path(td) / "run"),
                "--seeds", "17", "--max-cases", "2",
            ], capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("autonomous", result.stderr.lower())

    def test_real_execution_rejects_manual_manifest_override(self):
        with tempfile.TemporaryDirectory() as td:
            result = subprocess.run([
                sys.executable, str(Path(__file__).parent / "run_study_matrix.py"),
                "--registration", str(REGISTRATION), "--run-root", str(Path(td) / "run"),
                "--manifest", str(Path(td) / "other-manifest.json"),
            ], capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("autonomous", result.stderr.lower())

    def test_gpu_preflight_waits_for_busy_device_then_returns_live_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "calls"
            smi = Path(td) / "nvidia-smi"
            smi.write_text(
                "#!/bin/sh\n"
                "n=$(cat '$STATE' 2>/dev/null || echo 0)\n"
                "n=$((n+1)); printf '%s\\n' \"$n\" > '$STATE'\n"
                "[ \"$n\" -lt 2 ] && echo 100 || echo 300\n"
            .replace("$STATE", str(state)))
            smi.chmod(0o755)
            receipt = wait_for_gpu(200, str(smi), poll_s=0, timeout_s=2)
            self.assertEqual(receipt["status"], "admitted")
            self.assertEqual(receipt["free_mb"], 300)
            self.assertGreaterEqual(receipt["samples"], 2)
            self.assertEqual(receipt["min_free_mb"], 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
