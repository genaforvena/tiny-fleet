"""Padding-safe causal language-model loss accounting."""

import math

import torch
import torch.nn.functional as F


def masked_labels(input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Copy input IDs and make padding unavailable as causal-LM labels."""
    if input_ids.shape != attention_mask.shape:
        raise ValueError("input_ids and attention_mask must have the same shape")
    labels = input_ids.clone()
    labels = labels.masked_fill(attention_mask == 0, -100)
    return labels


def summed_nll(logits: torch.Tensor, labels: torch.Tensor) -> tuple[float, int]:
    """Return summed next-token NLL and its valid target count.

    Causal targets are labels[:, 1:], predicted by logits[:, :-1]. ``-100``
    labels are ignored, including padding and one-token examples.
    """
    if logits.ndim != 3 or labels.ndim != 2 or logits.shape[:2] != labels.shape:
        raise ValueError("logits must be [batch, sequence, vocab] and labels [batch, sequence]")
    shifted_logits = logits[:, :-1, :].contiguous()
    shifted_labels = labels[:, 1:].contiguous()
    target_count = int((shifted_labels != -100).sum().item())
    if target_count == 0:
        return 0.0, 0
    nll = F.cross_entropy(
        shifted_logits.view(-1, shifted_logits.shape[-1]),
        shifted_labels.view(-1),
        ignore_index=-100,
        reduction="sum",
    )
    return float(nll.detach().cpu()), target_count


def aggregate_perplexity(nll_sum: float, target_count: int) -> float:
    """Compute corpus PPL from total NLL and total scored targets."""
    if target_count <= 0:
        raise ValueError("cannot aggregate perplexity with zero scored targets")
    return math.exp(float(nll_sum) / target_count)
