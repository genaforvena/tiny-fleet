# A06 — support queue routing

Status: **NO-GO; baseline-only exploration.** This study routes synthetic CC0
support messages to eight fixed queues or `unknown`. It is offline-only and does
not change fleet routing or invoke an operating system, network, or model.

## Registration and provenance

The frozen manifest is `corpus/applications/support-routing/manifest.json`.
It contains 16 development/validation cases and 140 heldout cases, with one
unique source family per case. The heldout set has 80 known-queue cases and 60
OOD cases; the queue definitions are frozen in the manifest before scoring.

EmbeddingGemma is the feasibility precedent, not a Tiny Fleet result. Google
DeepMind describes it as a 308M-parameter multilingual embedding model aimed at
on-device use and reduced memory; see
<https://deepmind.google/models/gemma/embeddinggemma/>. The manifest records
`google/embeddinggemma-300m` with revision
`unavailable-gated-no-credential-2026-09-09` and Gemma terms. No model was
downloaded or scored because C02–C08 and S01–S05 are not independently verified.

## Baselines and result

The runner measures TF-IDF logistic classification and nearest centroid on the
development split, then writes raw predictions for all splits. On heldout known
queues, macro-F1 was 0.6612 for TF-IDF logistic and 0.6492 for nearest centroid.
TF-IDF accepted 0/60 OOD cases; the exact one-sided 95% upper bound is 4.87%,
which clears the preregistered 5% OOD gate. The result is a bounded
`NO_GO_BASELINE_DOMINANT`: no pilot is justified without model-prerequisite
verification and measurable headroom over this simple baseline. The scores are
descriptive for this synthetic corpus, not a production performance claim.

Raw outputs and summary are under `runs/applications/support-routing/`.

## Reproduction

```text
rtk proxy .venv/bin/python scripts/applications/support_routing.py \
  --phase baseline --run-dir runs/applications/support-routing
rtk proxy .venv/bin/python scripts/test_app_support_routing.py
```

The optional `pilot` and `score` phases intentionally stop until the named
cross-chain dependencies are independently verified.
