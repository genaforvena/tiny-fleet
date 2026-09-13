import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from drift_generate import (
    FakeBackend,
    build_effective_input,
    generate,
    generate_v2,
    validate_manifest,
    validate_records,
    validate_v2_manifest,
    validate_v2_records,
)


class DriftGenerateTests(unittest.TestCase):
    def manifest(self):
        return {
            "schema": "tiny-fleet.drift-generative-manifest/v1",
            "model_digest": "model-sha", "scorer_digest": "scorer-sha",
            "arms": ["base", "prompt-only", "lora"], "seeds": [7], "repetitions": [0, 1],
            "prompts": [
                {"repo": "r1", "snapshot": "old", "prompt_id": "p1", "prompt": "old prompt", "source_family": "f-old"},
                {"repo": "r1", "snapshot": "new", "prompt_id": "p1", "prompt": "new prompt", "source_family": "f-new"},
            ],
        }

    def manifest_v2(self):
        template = "Describe this frozen snapshot using only supplied evidence."
        excerpt = "Public API: Client.fetch(request)."
        digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
        prompts = []
        snapshots = []
        for index, repo in enumerate(("flask", "requests", "pydantic")):
            old_commit = f"{index + 1:x}" * 40
            new_commit = f"{index + 4:x}" * 40
            snapshots.append({"repo": repo, "old": old_commit, "new": new_commit})
            for snapshot in ("old", "new"):
                prompts.append({
                    "repo": repo,
                    "source_family": repo,
                    "snapshot": snapshot,
                    "source_commit": old_commit if snapshot == "old" else new_commit,
                    "source_path": f"src/{repo}/api.py",
                    "source_file_sha256": "1" * 64,
                    "prompt_id": "module-responsibility-v2",
                    "snapshot_excerpt": excerpt,
                    "snapshot_excerpt_sha256": digest(excerpt),
                    "lora_adapter": {"path": f"adapters/{repo}-{snapshot}", "digest": ("d" if snapshot == "old" else "e") * 64},
                })
        return {
            "schema": "tiny-fleet.drift-generative-manifest/v2",
            "sample_manifest_sha256": "9" * 64,
            "snapshots": snapshots,
            "base_model": {"model_id": "HuggingFaceTB/SmolLM2-360M-Instruct", "revision": "a" * 40},
            "prompt_template": template,
            "prompt_template_sha256": digest(template),
            "arms": ["base", "prompt-only", "lora"],
            "generation": {"do_sample": True, "temperature": 0.7, "top_p": 0.9, "max_new_tokens": 16},
            "scorer": {"id": "test-scorer", "revision": "c" * 40, "digest": "f" * 64},
            "seeds": [7],
            "repetitions": [0],
            "prompts": prompts,
        }

    def test_matrix_and_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = root / "manifest.json"; manifest.write_text(json.dumps(self.manifest()))
            out = root / "run"
            result = generate(manifest, out, FakeBackend())
            self.assertEqual(result["records"], 12)
            rows = [json.loads(line) for line in (out / "generative.jsonl").read_text().splitlines()]
            self.assertEqual(len({tuple(r[k] for k in ("repo", "snapshot", "arm", "prompt_id", "seed", "repetition")) for r in rows}), 12)
            self.assertTrue(all(r["model_digest"] == "model-sha" and r["scorer_digest"] == "scorer-sha" for r in rows))

    def test_missing_arm_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = root / "manifest.json"; manifest.write_text(json.dumps(self.manifest()))
            out = root / "run"; generate(manifest, out, FakeBackend())
            rows = [json.loads(line) for line in (out / "generative.jsonl").read_text().splitlines() if json.loads(line)["arm"] != "lora"]
            with self.assertRaisesRegex(ValueError, "missing arm"):
                validate_records(json.loads(manifest.read_text()), rows)

    def test_shuffled_snapshot_label_and_contamination_are_rejected(self):
        data = self.manifest()
        validate_manifest(data)
        bad = copy.deepcopy(data); bad["prompts"][1]["snapshot"] = "old"
        with self.assertRaisesRegex(ValueError, "duplicate prompt key"):
            validate_manifest(bad)
        bad = copy.deepcopy(data); bad["prompts"][0]["prompt"] = "old prompt new prompt"
        with self.assertRaisesRegex(ValueError, "contaminated"):
            validate_manifest(bad)

    def test_v2_requires_six_immutable_snapshots_and_pinned_arm_provenance(self):
        manifest = self.manifest_v2()
        self.assertEqual(validate_v2_manifest(manifest), 6)
        bad = copy.deepcopy(manifest)
        bad["prompts"][0]["lora_adapter"]["digest"] = None
        with self.assertRaisesRegex(ValueError, "LoRA adapter digest"):
            validate_v2_manifest(bad)
        bad = copy.deepcopy(manifest)
        bad["prompts"][0]["source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source commit mismatch"):
            validate_v2_manifest(bad)

    def test_v2_records_bind_effective_input_model_adapter_and_scorer(self):
        manifest = self.manifest_v2()
        validate_v2_manifest(manifest)
        records = []
        for prompt in manifest["prompts"]:
            for arm in manifest["arms"]:
                effective_input = build_effective_input(manifest, prompt, arm)
                if arm == "prompt-only":
                    self.assertIn(prompt["source_path"], effective_input)
                records.append({
                    "schema": "tiny-fleet.drift-generative/v2",
                    "repo": prompt["repo"], "snapshot": prompt["snapshot"], "prompt_id": prompt["prompt_id"],
                    "source_commit": prompt["source_commit"], "source_path": prompt["source_path"],
                    "source_file_sha256": prompt["source_file_sha256"],
                    "snapshot_excerpt_sha256": prompt["snapshot_excerpt_sha256"],
                    "arm": arm, "seed": 7, "repetition": 0,
                    "effective_input": effective_input,
                    "effective_input_sha256": hashlib.sha256(effective_input.encode()).hexdigest(),
                    "effective_seed": int(hashlib.sha256(f"7:0:{effective_input}".encode()).hexdigest()[:8], 16) % (2**31),
                    "base_model_id": manifest["base_model"]["model_id"],
                    "base_model_revision": manifest["base_model"]["revision"],
                    "adapter_digest": prompt["lora_adapter"]["digest"] if arm == "lora" else None,
                    "scorer_id": manifest["scorer"]["id"],
                    "scorer_revision": manifest["scorer"]["revision"],
                    "scorer_digest": manifest["scorer"]["digest"],
                    "backend": "transformers",
                    "runtime": {"python": "3.12", "torch": "test", "transformers": "test", "device": "cpu"},
                    "status": "ok", "output": "real output placeholder for validation only",
                })
        self.assertEqual(validate_v2_records(manifest, records), "ACCEPT")
        bad = copy.deepcopy(records)
        next(row for row in bad if row["arm"] == "prompt-only")["adapter_digest"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "adapter digest mismatch"):
            validate_v2_records(manifest, bad)
        for field, value, message in (
            ("effective_input_sha256", "0" * 64, "effective input mismatch"),
            ("effective_seed", 0, "effective seed mismatch"),
            ("base_model_revision", "0" * 40, "base model provenance mismatch"),
            ("scorer_revision", "0" * 40, "scorer provenance mismatch"),
            ("scorer_digest", "0" * 64, "scorer digest mismatch"),
        ):
            bad = copy.deepcopy(records)
            bad[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, message):
                validate_v2_records(manifest, bad)

    def test_v2_refuses_fake_backend_without_writing_run_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(self.manifest_v2()))
            run_dir = root / "run"
            with self.assertRaisesRegex(ValueError, "fixture backends cannot emit v2 records"):
                generate_v2(manifest_path, run_dir, backend=FakeBackend())
            self.assertFalse(run_dir.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
