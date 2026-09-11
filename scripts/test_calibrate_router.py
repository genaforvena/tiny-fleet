import json
import tempfile
import unittest
from pathlib import Path

from calibrate_router import CalibrationError, calibrate, compare_methods, route_with_calibration


class CalibrateRouterTests(unittest.TestCase):
    def cases(self):
        return [
            {"case_id": "g1", "split": "validation", "domain": "guitar", "text": "guitar strings", "ood": False},
            {"case_id": "g2", "split": "validation", "domain": "guitar", "text": "guitar chords", "ood": False},
            {"case_id": "s1", "split": "validation", "domain": "sourdough", "text": "bread starter", "ood": False},
            {"case_id": "s2", "split": "validation", "domain": "sourdough", "text": "flour starter", "ood": False},
            {"case_id": "o1", "split": "validation", "domain": None, "text": "quantum physics", "ood": True},
            {"case_id": "adversarial-distance", "split": "adversarial", "domain": None, "text": "adversarial", "ood": True,
             "similarities": {"guitar": -0.20, "sourdough": -0.80}},
        ]

    def embeddings(self):
        return {"g1": [1.0, 0.0], "g2": [0.9, 0.1], "s1": [0.0, 1.0], "s2": [0.1, 0.9], "o1": [-1.0, -1.0],
                "adversarial-distance": [-0.20, -0.80]}

    def test_calibration_uses_validation_only_and_freezes_gate(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = calibrate(self.cases()[:-1], self.embeddings(), embedding_digest="embed-v1", corpus_hash="corpus-v1",
                                 out_path=Path(td) / "router.json")
            self.assertEqual(artifact["calibration_method"], "validation_grid_abs_margin")
            self.assertEqual(artifact["corpus_hash"], "corpus-v1")
            self.assertIn("similarity_min", artifact)
            self.assertIn("margin_min", artifact)
            self.assertEqual(artifact["cases"]["validation_n"], 5)

    def test_heldout_labels_are_rejected(self):
        with self.assertRaisesRegex(CalibrationError, "heldout"):
            calibrate(self.cases()[:-1] + [{**self.cases()[0], "split": "heldout"}], self.embeddings(),
                      embedding_digest="e", corpus_hash="c")

    def test_methods_share_cases_and_impossible_population_is_honest(self):
        rows = compare_methods(self.cases()[:-1], self.embeddings())
        self.assertEqual({row["case_id"] for row in rows["gated"]}, {"g1", "g2", "s1", "s2", "o1"})
        self.assertEqual(rows["abstain_all"][0]["route"], "abstain")
        impossible = [{**case, "domain": "guitar", "ood": True} for case in self.cases()[:-1]]
        with tempfile.TemporaryDirectory() as td:
            result = calibrate(impossible, self.embeddings(), embedding_digest="e", corpus_hash="c",
                               out_path=Path(td) / "router.json", false_accept_bound=0.0)
            self.assertEqual(result["verdict"], "no-eligible-router")

    def test_absolute_distance_and_zero_vector_gate(self):
        with self.assertRaisesRegex(CalibrationError, "zero"):
            calibrate(self.cases()[:-1], {**self.embeddings(), "g1": [0.0, 0.0]}, embedding_digest="e", corpus_hash="c")
        artifact = calibrate(self.cases()[:-1], self.embeddings(), embedding_digest="e", corpus_hash="c")
        detail = route_with_calibration([0.0, 0.0], artifact)
        self.assertEqual(detail["route"], "abstain")
        self.assertEqual(detail["reason"], "zero_query_embedding")
        distance = route_with_calibration([-.20, -.80], {**artifact, "centroids": {"guitar": [-1, 0], "sourdough": [0, -1]},
                                                        "similarity_min": -0.1, "margin_min": 0.0})
        self.assertIn(distance["reason"], {"absolute_similarity", "low_margin", "routed"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
