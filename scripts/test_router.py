#!/usr/bin/env python3
"""Contract tests for explicit router failure boundaries."""
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

import numpy as np

from router import route_query


CENTROIDS = {
    "guitar": np.array([1.0, 0.0]),
    "sourdough": np.array([0.0, 1.0]),
}


class RouterFailureBoundaryTests(unittest.TestCase):
    def test_zero_query_embedding_abstains_with_machine_readable_reason(self):
        route, detail = route_query("guitar", CENTROIDS, lambda _: np.zeros((1, 2)))
        self.assertEqual(route, "abstain")
        self.assertEqual(detail["reason"], "invalid_embedding_norm")
        self.assertIsNone(detail["best_similarity"])
        self.assertIsNone(detail["margin"])

    def test_nonfinite_query_embeddings_abstain(self):
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(value=value):
                route, detail = route_query(
                    "guitar", CENTROIDS, lambda _, value=value: np.array([[value, 0.0]])
                )
                self.assertEqual(route, "abstain")
                self.assertEqual(detail["reason"], "invalid_embedding_nonfinite")

    def test_wrong_dimension_and_empty_query_embeddings_abstain(self):
        for embedding in (np.array([[1.0]]), np.empty((0, 2))):
            with self.subTest(shape=embedding.shape):
                route, detail = route_query("guitar", CENTROIDS, lambda _: embedding)
                self.assertEqual(route, "abstain")
                self.assertEqual(detail["reason"], "invalid_embedding_shape")

    def test_invalid_centroid_abstains_without_routing(self):
        route, detail = route_query(
            "guitar", {"guitar": np.zeros(2), "sourdough": np.array([0.0, 1.0])},
            lambda _: np.array([[1.0, 0.0]]),
        )
        self.assertEqual(route, "abstain")
        self.assertEqual(detail["reason"], "invalid_centroid_norm")

    def test_backend_failure_and_invalid_json_are_explicit(self):
        for error, reason in (
            (subprocess.TimeoutExpired("curl", 1), "embedding_timeout"),
            (subprocess.CalledProcessError(7, "curl", stderr="network down"),
             "embedding_backend_failure"),
        ):
            with self.subTest(reason=reason), patch("router.subprocess.run", side_effect=error):
                route, detail = route_query("guitar", CENTROIDS)
                self.assertEqual(route, "abstain")
                self.assertEqual(detail["reason"], reason)
        with patch("router.subprocess.run", return_value=subprocess.CompletedProcess(
            "curl", 0, stdout="{not-json", stderr=""
        )):
            route, detail = route_query("guitar", CENTROIDS)
        self.assertEqual(route, "abstain")
        self.assertEqual(detail["reason"], "embedding_invalid_json")

    def test_operator_first_does_not_invoke_poisoned_embedder(self):
        def poisoned(_):
            raise AssertionError("embedding must not run for operator requests")

        model = {"features": {}, "classes": []}
        with patch("router.is_operator_query", return_value=True), patch(
            "router.respond", return_value="operator response"
        ):
            route, detail = route_query("operator request", CENTROIDS, poisoned, model)
        self.assertEqual((route, detail), ("operator", "operator response"))

    def test_valid_fixture_behavior_and_scores_are_retained(self):
        route, detail = route_query(
            "guitar", CENTROIDS, lambda _: np.array([[1.0, 0.0]]),
            {"features": {}, "classes": []},
        )
        self.assertEqual(route, "specialist:guitar")
        self.assertAlmostEqual(detail["best_similarity"], 1.0)
        self.assertAlmostEqual(detail["margin"], 1.0)
        self.assertEqual(detail["reason"], "routed")


if __name__ == "__main__":
    unittest.main()
