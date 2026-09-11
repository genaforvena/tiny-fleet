import copy
import json
import tempfile
import unittest
from pathlib import Path

from drift_generate import FakeBackend, generate, validate_manifest, validate_records


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
