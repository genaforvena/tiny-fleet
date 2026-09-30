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
from analyze_model_terminology_drift import (delta_alignment, exact_sign_flips, main,
                                           lexical_shift, preference, read_jsonl, validate_nll)
from model_terminology_drift import likelihood_input, unigram_score


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


if __name__ == "__main__":
    unittest.main()
