"""Consumer-visible integrity and interpretation checks for LTE drift analysis."""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lte_snapshot_compression as runner


class SnapshotAnalysisTests(unittest.TestCase):
    def cases(self):
        return {"heldout_pairs": [
            {"source_path": "changed.py", "changed": True, "score_bytes": {"old": 8, "new": 16}},
            {"source_path": "identity.sh", "changed": False, "score_bytes": {"old": 4, "new": 8}},
        ]}

    def likelihood_rows(self, omit_unigram=False):
        cases = self.cases()
        rows = []
        for item in cases["heldout_pairs"]:
            path = item["source_path"]
            for model in ("old", "new"):
                for seed in runner.SEEDS:
                    for stage in runner.STAGES:
                        for target in ("old", "new"):
                            mean = 1.0
                            if item["changed"]:
                                mean = {("old", "old"): 1.0, ("new", "old"): 2.0,
                                        ("old", "new"): 3.0, ("new", "new"): 2.0}[(model, target)]
                            rows.append({"model_snapshot": model, "seed": seed, "stage": stage,
                                         "target_snapshot": target, "source_path": path,
                                         "changed": item["changed"], "status": "ok",
                                         "nll_sum": mean * 4, "target_tokens": 4, "mean_token_nll": mean})
        for target in ("old", "new"):
            for item in cases["heldout_pairs"]:
                rows.append({"model_snapshot": "shared", "seed": None, "stage": 0,
                             "target_snapshot": target, "source_path": item["source_path"],
                             "changed": item["changed"], "arm": "base", "status": "ok",
                             "nll_sum": 12, "target_tokens": 4, "mean_token_nll": 3.0})
            for model, mean in (("old", 4.0), ("new", 5.0)):
                for item in cases["heldout_pairs"]:
                    row = {"model_snapshot": model, "seed": None, "stage": 0,
                           "target_snapshot": target, "source_path": item["source_path"],
                           "changed": item["changed"], "arm": "unigram", "status": "ok",
                           "nll_sum": mean * 4, "target_tokens": 4, "mean_token_nll": mean}
                    rows.append(row)
        if omit_unigram:
            rows.pop()
        return rows

    def training_rows(self):
        rows = []
        for snapshot in ("old", "new"):
            for seed in runner.SEEDS:
                for number in range(1, 20):
                    rows.append({"snapshot": snapshot, "seed": seed, "pass": number, "status": "ok",
                                 "selected_tokens": 4})
                for number in runner.STAGES:
                    rows.append({"snapshot": snapshot, "seed": seed, "pass": number,
                                 "kind": "diagnostic", "status": "ok"})
        return rows

    def run_analysis(self, omit_unigram=False, bad_token_budget=False, source_sha256=None):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            protocol = {"source_tree": {"old": "old-tree", "new": "new-tree"},
                        "training": {"tokens": 4, "validation_tokens": 4}}
            (run_dir / "protocol.json").write_text(json.dumps(protocol) + "\n", encoding="utf-8")
            likelihood = self.likelihood_rows(omit_unigram=omit_unigram)
            training = self.training_rows()
            if bad_token_budget:
                next(row for row in training if row.get("kind", "update") == "update")["selected_tokens"] = 3
            for name, rows in (("likelihood.jsonl", likelihood), ("training.jsonl", training)):
                (run_dir / name).write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            receipt = {"schema": runner.SCHEMA + "/receipt", "status": "complete",
                       "source_sha256": source_sha256 or protocol["source_tree"],
                       "protocol_sha256": runner.file_sha256(run_dir / "protocol.json"),
                       "likelihood_sha256": runner.file_sha256(run_dir / "likelihood.jsonl"),
                       "likelihood_rows": len(likelihood),
                       "training_sha256": runner.file_sha256(run_dir / "training.jsonl"),
                       "training_rows": len(training)}
            (run_dir / "receipt.json").write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            with patch.object(runner, "validate_prepared", return_value=(protocol, self.cases())):
                return runner.analyze(run_dir)

    def test_split_keeps_versions_and_duplicate_blobs_together(self):
        entries = {
            "old": [
                {"status": "included", "path": "docs/a.md", "content_sha256": "blob-a"},
                {"status": "included", "path": "docs/c.md", "content_sha256": "blob-c"},
            ],
            "new": [
                {"status": "included", "path": "docs/a.md", "content_sha256": "blob-b"},
                {"status": "included", "path": "docs/b.md", "content_sha256": "blob-a"},
                {"status": "included", "path": "docs/c.md", "content_sha256": "blob-c"},
            ],
        }
        split = runner._component_splits(entries)
        self.assertEqual(split[("old", "docs/a.md")], split[("new", "docs/a.md")])
        self.assertEqual(split[("old", "docs/a.md")], split[("new", "docs/b.md")])
        self.assertEqual(split[("old", "docs/c.md")], split[("new", "docs/c.md")])

    def test_analysis_reports_crossed_preference_and_baselines(self):
        result = self.run_analysis()
        self.assertEqual(result["denominators"], {"changed_paths": 1, "unchanged_paths": 1,
                         "paired_paths": 2, "expected_lora_rows": 72, "expected_base_rows": 4,
                         "expected_unigram_rows": 8})
        stage = result["stages"]["19"]
        self.assertEqual(stage["seeds_with_both_preferences"], 3)
        self.assertEqual(stage["nats_per_token"]["changed"]["base_on_old"], 3.0)
        self.assertEqual(stage["nats_per_token"]["changed"]["unigram_new_on_new"], 5.0)
        self.assertEqual(stage["nats_per_token"]["unchanged"]["lora_new_seed17_on_old"], 1.0)
        self.assertAlmostEqual(stage["bits_per_source_byte"]["changed"]["base_on_old"],
                               12 / (8 * math.log(2)))

    def test_missing_baseline_row_cannot_produce_complete_analysis(self):
        with self.assertRaisesRegex(ValueError, "unigram denominator mismatch"):
            self.run_analysis(omit_unigram=True)

    def test_receipt_rejects_mutated_likelihood_tape(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            protocol = {"source_tree": {"old": "old-tree", "new": "new-tree"},
                        "training": {"tokens": 4, "validation_tokens": 4}}
            (run_dir / "protocol.json").write_text(json.dumps(protocol) + "\n", encoding="utf-8")
            likelihood, training = self.likelihood_rows(), self.training_rows()
            (run_dir / "likelihood.jsonl").write_text("".join(json.dumps(row) + "\n" for row in likelihood), encoding="utf-8")
            (run_dir / "training.jsonl").write_text("".join(json.dumps(row) + "\n" for row in training), encoding="utf-8")
            receipt = {"schema": runner.SCHEMA + "/receipt", "status": "complete",
                       "source_sha256": protocol["source_tree"],
                       "protocol_sha256": runner.file_sha256(run_dir / "protocol.json"),
                       "likelihood_sha256": runner.file_sha256(run_dir / "likelihood.jsonl"),
                       "likelihood_rows": len(likelihood),
                       "training_sha256": runner.file_sha256(run_dir / "training.jsonl"),
                       "training_rows": len(training)}
            (run_dir / "receipt.json").write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            with (run_dir / "likelihood.jsonl").open("a", encoding="utf-8") as stream:
                stream.write("{}\n")
            with patch.object(runner, "validate_prepared", return_value=(protocol, self.cases())):
                with self.assertRaisesRegex(ValueError, "likelihood tape does not match complete receipt"):
                    runner.analyze(run_dir)

    def test_receipt_source_tree_must_match_protocol(self):
        with self.assertRaisesRegex(ValueError, "receipt source-tree binding mismatch"):
            self.run_analysis(source_sha256={"old": "wrong-tree", "new": "new-tree"})

    def test_training_rows_require_exact_selected_token_budget(self):
        with self.assertRaisesRegex(ValueError, "training token budget mismatch"):
            self.run_analysis(bad_token_budget=True)

    def test_underfilled_preparation_budget_is_rejected(self):
        chunks = [{"input_ids": [1, 2]}]
        with self.assertRaisesRegex(ValueError, "expected 3, got 2"):
            runner._require_token_budget(chunks, 3, "old", "train")

    def test_heldout_byte_denominator_excludes_context_only_token(self):
        class Tokenizer:
            def __call__(self, text, **kwargs):
                return {"input_ids": [10, 11, 12],
                        "offset_mapping": [(0, 1), (1, 2), (2, 3)]}

        input_ids, score_bytes = runner._heldout_prefix("α β", Tokenizer())
        self.assertEqual(input_ids, [10, 11, 12])
        self.assertEqual(score_bytes, len(" β".encode("utf-8")))

    def test_cgroup_limit_uses_tightest_ancestor_and_enforces_ceiling(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "cgroup"
            membership = Path(raw) / "membership"
            job = root / "slice" / "job"
            job.mkdir(parents=True)
            (root / "memory.max").write_text("8388608", encoding="ascii")
            (root / "slice" / "memory.max").write_text("4194304", encoding="ascii")
            (job / "memory.max").write_text("max", encoding="ascii")
            membership.write_text("0::/slice/job\n", encoding="ascii")
            limit = runner._effective_cgroup_memory_bytes(root, membership)
            self.assertEqual(limit, 4194304)
            runner._require_cgroup_memory_limit(4, limit)
            with self.assertRaisesRegex(RuntimeError, "at most 3 MB"):
                runner._require_cgroup_memory_limit(3, limit)

    def test_run_directory_in_worktree_must_be_ignored(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "worktree"
            source = Path(raw) / "source-repository"
            root.mkdir()
            source.mkdir()
            subprocess.run(["git", "init", "--quiet", str(root)], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (root / ".gitignore").write_text(".private/\n", encoding="utf-8")
            ignored = runner._private_run_dir(source, root / ".private" / "run")
            self.assertEqual(ignored, root / ".private" / "run")
            with self.assertRaisesRegex(ValueError, "must be ignored"):
                runner._private_run_dir(source, root / "raw-run")
            with self.assertRaisesRegex(ValueError, "inside the source repository"):
                runner._private_run_dir(source, source / "raw-run")


if __name__ == "__main__":
    unittest.main()
