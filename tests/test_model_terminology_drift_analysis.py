"""Consumer-visible inference and undefined-lexical edge cases."""
import contextlib
import io
import json
import tempfile
import sys
import unittest
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_model_terminology_drift import (analyze, delta_alignment, exact_sign_flips, main, lexical_shift,
                                             preference, read_jsonl, validate_matrix, validate_nll)
from model_terminology_drift import (SCHEMA, expected_generation_rows, expected_likelihood_rows,
                                    expected_training_rows, likelihood_input, unigram_score)
from train_drift_adapters import select_chunks


class AnalysisTests(unittest.TestCase):
    def test_three_repository_sign_flip_floor_and_ties(self):
        positive = exact_sign_flips([1.0, 2.0, 3.0])
        self.assertEqual(positive["one_sided_p"], 0.125)
        self.assertEqual(positive["attainable_one_sided_p_floor"], 0.125)
        self.assertEqual(exact_sign_flips([0.0, 0.0, 0.0])["one_sided_p"], 1.0)
        unchanged_control = exact_sign_flips([1.0, 0.0, 3.0])
        self.assertEqual(unchanged_control["one_sided_p"], 0.25)
        self.assertEqual(unchanged_control["attainable_one_sided_p_floor"], 0.25)
        self.assertEqual(exact_sign_flips([0.0, 0.0, 0.0])["attainable_one_sided_p_floor"], 1.0)
        with self.assertRaises(ValueError):
            exact_sign_flips([1.0] * 12)

    def test_classification_ties_and_preference_sign(self):
        result = preference({("old", "old"): 2.0, ("new", "old"): 2.0,
                             ("old", "new"): 4.0, ("new", "new"): 1.0})
        self.assertEqual(result["balanced_snapshot_accuracy"], 0.75)
        self.assertEqual(result["diagonal_self_preference"], 1.5)

    def test_failed_nan_or_wrong_denominator_cannot_enter_numeric_claim(self):
        for changes in ({"status": "error"}, {"target_tokens": 9}, {"nll_sum": float("nan")},
                        {"mean_token_nll": 3.0}, {"target_tokens": True}):
            row = {"status": "ok", "target_tokens": 10, "nll_sum": 20.0, "mean_token_nll": 2.0}
            row.update(changes)
            errors = []
            self.assertFalse(validate_nll(row, 10, "cell", errors))
            self.assertTrue(errors)

    def test_alignment_retains_zero_vocab_and_direction_reversal(self):
        source = lexical_shift("old_name old_name", "new_name new_name")
        forward = delta_alignment(source, lexical_shift("old_name", "new_name"))
        reverse = delta_alignment(source, lexical_shift("new_name", "old_name"))
        empty = delta_alignment(source, lexical_shift("", ""))
        self.assertAlmostEqual(forward["cosine_delta_alignment"], 1.0)
        self.assertAlmostEqual(reverse["cosine_delta_alignment"], -1.0)
        self.assertEqual(forward["source_delta_mass_coverage"], 1.0)
        self.assertEqual(reverse["signed_source_delta_mass_agreement"], 0.0)
        self.assertIsNone(empty["cosine_delta_alignment"])
        self.assertTrue(empty["zero_vocabulary"])
        self.assertEqual(empty["source_delta_mass_coverage"], 0.0)

    def test_one_sided_empty_generation_has_no_directional_alignment(self):
        source = lexical_shift("old_name", "new_name")
        for old, new in (("", "new_name"), ("old_name", ""), ("!!!", "new_name")):
            alignment = delta_alignment(source, lexical_shift(old, new))
            self.assertTrue(alignment["zero_vocabulary"])
            self.assertIsNone(alignment["cosine_delta_alignment"])
        self.assertIsNone(delta_alignment(lexical_shift("", "new_name"),
                                         lexical_shift("old_name", "new_name"))["cosine_delta_alignment"])

    def test_missing_run_refuses_claim_and_cannot_overwrite_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "report.json"
            arguments = ["--run-dir", str(root / "missing"), "--output", str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(arguments), 1)
            report = json.loads(output.read_text())
            self.assertFalse(report["complete"])
            self.assertFalse(report["positive_usefulness_claim"])
            self.assertIsNone(report["likelihood"])
            self.assertIsNone(report["generation_lexical"])
            self.assertIsNone(report["repeated_fitting"])
            self.assertTrue(report["errors"])
            original = output.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(arguments)
            self.assertEqual(output.read_bytes(), original)

    def test_interrupted_tape_keeps_valid_rows_and_failed_line_number(self):
        with tempfile.TemporaryDirectory() as temporary:
            tape = Path(temporary) / "tape.jsonl"
            tape.write_bytes(b'{"status":"error","error":"failed seed"}\n\xff\n{"status":"ok"}\n')
            errors, invalid_lines = [], []
            rows = read_jsonl(tape, errors, invalid_lines)
            self.assertEqual([row["status"] for row in rows], ["error", "ok"])
            self.assertEqual(rows[0]["error"], "failed seed")
            self.assertEqual(invalid_lines, [2])
            self.assertTrue(errors)

    def test_shuffle_preserves_scored_multiset_and_unigram_likelihood(self):
        target = {"heldout": {"input_ids": list(range(32))}}
        case = {"unigram_counts": {str(token): count for token, count in
                Counter([0] * 50 + [1] * 20 + list(range(32))).items()}}
        original = likelihood_input(case, target, "unigram", "original")
        shuffled = likelihood_input(case, target, "unigram", "token_shuffle")
        self.assertEqual(shuffled["input_ids"][0], original["input_ids"][0])
        self.assertEqual(Counter(shuffled["input_ids"][1:]), Counter(original["input_ids"][1:]))
        self.assertNotEqual(shuffled["input_ids"][1:], original["input_ids"][1:])
        self.assertAlmostEqual(unigram_score(case, original, 32, 1.0)["nll_sum"],
                               unigram_score(case, shuffled, 32, 1.0)["nll_sum"], places=12)
    def test_failed_matrix_cell_is_reported(self):
        expected = [{"repo": "flask", "stage": "baseline", "model_snapshot": "new",
                     "target_snapshot": "old", "control": "original", "arm": "lora",
                     "input_sha256": "input", "target_tokens": 2}]
        failed = {**expected[0], "status": "error", "error": "worker stopped",
                  "protocol_sha256": "protocol", "elapsed_s": 0.0}
        errors = []
        validate_matrix([failed], expected, ("repo", "stage", "model_snapshot", "target_snapshot", "control", "arm"),
                        "likelihood", "protocol", errors)
        self.assertTrue(any("status=error; worker stopped" in error for error in errors))

    def test_selected_training_window_is_deterministic_and_exact(self):
        chunks = [{"source_path": f"src/{i:02}.py", "chunk_index": 0,
                   "input_ids": list(range(i * 256, (i + 1) * 256))} for i in range(20)]
        first = select_chunks("flask", "new", chunks, token_budget=4096, max_length=256)
        second = select_chunks("flask", "new", list(reversed(chunks)), token_budget=4096, max_length=256)
        self.assertEqual(first, second)
        self.assertEqual(sum(len(chunk["input_ids"]) for chunk in first), 4096)
        self.assertEqual(len(first), 16)

    def test_expected_six_snapshot_row_matrix_and_identity(self):
        protocol, cases = self.synthetic_inputs()
        likelihood = expected_likelihood_rows(protocol, cases)
        generations = expected_generation_rows(protocol, cases)
        training = expected_training_rows(protocol, cases)
        self.assertEqual((len(likelihood), len(generations), len(training)), (132, 201, 132))
        identity = protocol["identity"]
        self.assertEqual(sum(all(row.get(key) == value for key, value in identity.items() if key != "decode_id")
                             and row["decode_id"] == "identity" for row in generations), 1)
        self.assertEqual(sum(row["kind"] == "pass" for row in training), 114)

    @staticmethod
    def synthetic_inputs():
        from model_terminology_drift import PROMPTS
        repos = ("flask", "pydantic", "requests")
        snapshots = ("old", "new")
        prompts = [{"prompt_id": prompt["prompt_id"], "text": prompt["text"]} for prompt in PROMPTS]
        base_inputs = [{"prompt_id": prompt["prompt_id"], "text": prompt["text"], "input_ids": [1, 2, 3]}
                       for prompt in prompts]
        cases = {"base_generation_inputs": base_inputs, "conditions": []}
        conditions = []
        for repo in repos:
            for snapshot in snapshots:
                text = repo if repo == "requests" else f"{repo}-{snapshot}"
                case = {"repo": repo, "snapshot": snapshot, "conditioning_ids": [1, 2],
                        "heldout": {"source_path": f"{repo}.py", "text": text, "input_ids": [1, 2, 3]},
                        "unigram_counts": {"1": 3, "2": 2, "3": 1},
                        "train_chunks": [{"input_ids": [1, 2]}],
                        "validation_chunks": [{"input_ids": [1, 2]}],
                        "generation_inputs": [{"prompt_id": prompt["prompt_id"],
                                              "text": f"context {prompt['text']}", "input_ids": [1, 2, 3]}
                                             for prompt in prompts]}
                cases["conditions"].append(case)
                conditions.append({"repo": repo, "snapshot": snapshot, "adapter_digest": f"{repo}-{snapshot}"})
        protocol = {"source_revision": "0" * 40, "stages": ["baseline", "repeat4", "repeat19"], "conditions": conditions,
                    "prompts": prompts, "identity": {"repo": "flask", "snapshot": "old", "stage": "baseline",
                        "arm": "lora", "prompt_id": prompts[0]["prompt_id"], "decode_id": "greedy"},
                    "base_model": {}, "training": {}, "generation": {"max_new_tokens": 96},
                    "controls": {"unigram_alpha": 1.0}, "runtime": {}, "budget": {"model_wall_seconds": 21600},
                    "tokenizer": {"vocab_size": 128}, "cached_model": {"files": {}}}
        return protocol, cases

    def test_complete_synthetic_run_reaches_numeric_report(self):
        import hashlib
        import math
        from unittest.mock import patch
        from drift_generate import adapter_tree_digest
        from model_terminology_drift import (expected_generation_rows, expected_likelihood_rows,
                                              expected_training_rows, likelihood_input)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "run"
            run.mkdir()
            protocol, cases = self.synthetic_inputs()
            (run / "protocol.json").write_text(json.dumps(protocol, sort_keys=True))
            (run / "cases.json").write_text(json.dumps(cases, sort_keys=True))
            protocol_digest = hashlib.sha256((run / "protocol.json").read_bytes()).hexdigest()
            cases_digest = hashlib.sha256((run / "cases.json").read_bytes()).hexdigest()
            lookup = {(case["repo"], case["snapshot"]): case for case in cases["conditions"]}
            rows = []
            for spec in expected_likelihood_rows(protocol, cases):
                target = lookup[(spec["repo"], spec["target_snapshot"])]
                if spec["arm"] == "unigram":
                    model = lookup[(spec["repo"], spec["model_snapshot"])]
                    ids = likelihood_input(model, target, "unigram", spec["control"])["input_ids"]
                    denominator = sum(model["unigram_counts"].values()) + protocol["controls"]["unigram_alpha"] * protocol["tokenizer"]["vocab_size"]
                    nll = math.fsum(-math.log((model["unigram_counts"].get(str(token), 0) + 1.0) / denominator)
                                    for token in ids[1:])
                else:
                    nll = float(spec["target_tokens"])
                rows.append({**spec, "status": "ok", "nll_sum": nll,
                             "mean_token_nll": nll / spec["target_tokens"], "elapsed_s": 0.01,
                             "protocol_sha256": protocol_digest})
            tapes = {"likelihood.jsonl": rows}
            generation_rows = []
            for spec in expected_generation_rows(protocol, cases):
                output = f"synthetic {spec['repo']} {spec['snapshot']} {spec['stage']} {spec['arm']} {spec['prompt_id']} {spec['decode_id']}"
                generation_rows.append({**spec, "status": "ok", "output": output,
                    "output_sha256": hashlib.sha256(output.encode()).hexdigest(), "generated_tokens": 8,
                    "cap_hit": False, "empty_output": False, "elapsed_s": 0.01, "protocol_sha256": protocol_digest})
            tapes["generations.jsonl"] = generation_rows
            training_rows = []
            for spec in expected_training_rows(protocol, cases):
                losses = {"chunks": 1, "target_tokens": 1, "nll_sum": 1.0, "mean_token_nll": 1.0}
                row = {**spec, "status": "ok", "elapsed_s": 0.01, "protocol_sha256": protocol_digest,
                       "train": losses}
                if spec["kind"] == "diagnostic":
                    row["validation"] = losses
                else:
                    row.update(optimizer_steps=1, selected_tokens=4096)
                training_rows.append(row)
            tapes["training.jsonl"] = training_rows
            tapes["failures.jsonl"] = []
            for name, data in tapes.items():
                (run / name).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in data))
            checkpoints = {}
            protocol_conditions = {(row["repo"], row["snapshot"]): row for row in protocol["conditions"]}
            for case in cases["conditions"]:
                condition = protocol_conditions[(case["repo"], case["snapshot"])]
                for stage, passes in (("repeat4", 4), ("repeat19", 19)):
                    key = f"{case['repo']}-{case['snapshot']}/{stage}"
                    directory = run / "checkpoints" / key
                    directory.mkdir(parents=True)
                    (directory / "adapter_model.safetensors").write_bytes(key.encode())
                    (directory / "continuation.json").write_text(json.dumps({
                        "protocol_sha256": protocol_digest, "original_adapter_digest": condition["adapter_digest"],
                        "additional_passes": passes, "selected_tokens": 4096}, sort_keys=True))
                    checkpoints[key] = adapter_tree_digest(directory)
            tape_sha, counts = {}, {}
            for name, data in tapes.items():
                content = (run / name).read_bytes()
                tape_sha[name] = hashlib.sha256(content).hexdigest()
                counts[name] = {"rows": len(data), "ok": sum(row.get("status") == "ok" for row in data),
                                "error": 0, "invalid_json_lines": []}
            (run / "receipt.json").write_text(json.dumps({
                "schema": SCHEMA + "/receipt", "status": "complete", "protocol_sha256": protocol_digest,
                "cases_sha256": cases_digest, "tape_sha256": tape_sha, "counts": counts, "failures": [],
                "total_model_wall_s": 1.0, "peak_rss_gib": 1.0, "checkpoints": checkpoints}, sort_keys=True))
            with patch("analyze_model_terminology_drift.validate_fixed_settings"), \
                    patch("analyze_model_terminology_drift.validate_inputs", return_value=([], True)):
                report = analyze(run, model_cache=root / "cache")
                self.assertTrue(report["complete"], report["errors"])
                self.assertEqual(report["errors"], [])
                self.assertEqual(report["expected_counts"]["likelihood.jsonl"], 132)
                self.assertEqual(len(report["likelihood"]["cells"]), 6)
                self.assertEqual(len(report["generation_lexical"]["paired_outputs"]), 216)
                self.assertEqual(len(report["repeated_fitting"]["pass_records"]), 114)
                self.assertIsInstance(report["direct_answer"], str)
                self.assertEqual(report["model_cache_verification"]["status"], "verified")

                likelihood_path = run / "likelihood.jsonl"
                likelihood_rows = [json.loads(line) for line in likelihood_path.read_text().splitlines()]
                likelihood_rows[0].update(status="error", error="synthetic failed cell")
                likelihood_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in likelihood_rows))
                receipt_path = run / "receipt.json"
                receipt = json.loads(receipt_path.read_text())
                content = likelihood_path.read_bytes()
                receipt["tape_sha256"]["likelihood.jsonl"] = hashlib.sha256(content).hexdigest()
                receipt["counts"]["likelihood.jsonl"] = {
                    "rows": len(likelihood_rows), "ok": len(likelihood_rows) - 1,
                    "error": 1, "invalid_json_lines": []}
                receipt_path.write_text(json.dumps(receipt, sort_keys=True))
                refused = analyze(run, model_cache=root / "cache")
            self.assertFalse(refused["complete"])
            self.assertIsNone(refused["likelihood"])
            self.assertTrue(any("synthetic failed cell" in error for error in refused["errors"]))
            self.assertEqual(refused["model_cache_verification"]["status"], "verified")


if __name__ == "__main__":
    unittest.main()
