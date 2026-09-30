#!/usr/bin/env python3
import math
import unittest

import torch

from loss_metrics import aggregate_perplexity, masked_labels, summed_nll


class LossMetricsTest(unittest.TestCase):
    def test_manual_logits_score_only_shifted_non_padding_targets(self):
        input_ids = torch.tensor([[1, 2, 3, 0], [4, 5, 0, 0]])
        attention_mask = torch.tensor([[1, 1, 1, 0], [1, 1, 0, 0]])
        labels = masked_labels(input_ids, attention_mask)
        self.assertTrue(torch.equal(labels, torch.tensor([[1, 2, 3, -100], [4, 5, -100, -100]])))

        logits = torch.zeros((2, 4, 6), dtype=torch.float32)
        nll, count = summed_nll(logits, labels)
        self.assertEqual(count, 3)
        self.assertAlmostEqual(float(nll), 3 * math.log(6), places=6)

    def test_padding_ids_and_logits_do_not_change_loss(self):
        mask = torch.tensor([[1, 1, 1, 0], [1, 1, 0, 0]])
        labels = masked_labels(torch.tensor([[1, 2, 3, 0], [4, 5, 0, 0]]), mask)
        changed_labels = masked_labels(torch.tensor([[1, 2, 3, 99], [4, 5, 98, 97]]), mask)
        baseline_logits = torch.zeros((2, 4, 6))
        changed_logits = baseline_logits.clone()
        changed_logits[0, 3] = 999.0
        changed_logits[1, 2:] = 999.0
        baseline = summed_nll(baseline_logits, labels)
        changed = summed_nll(changed_logits, changed_labels)
        self.assertEqual(changed[1], baseline[1])
        self.assertAlmostEqual(float(changed[0]), float(baseline[0]), places=6)
        self.assertAlmostEqual(float(baseline[0]), 3 * math.log(6), places=6)

    def test_one_token_examples_have_no_targets(self):
        labels = masked_labels(torch.tensor([[7]]), torch.tensor([[1]]))
        self.assertEqual(summed_nll(torch.zeros((1, 1, 8)), labels), (0.0, 0))
        with self.assertRaises(ValueError):
            aggregate_perplexity(0.0, 0)

    def test_aggregate_uses_target_count_not_input_length(self):
        # Three scored targets across two examples: the old input-length weighting
        # would divide by five and produce a different perplexity.
        self.assertAlmostEqual(aggregate_perplexity(3 * math.log(6), 3), 6.0, places=6)
        self.assertNotAlmostEqual(aggregate_perplexity(3 * math.log(6), 5), 6.0, places=4)


if __name__ == "__main__":
    unittest.main()
