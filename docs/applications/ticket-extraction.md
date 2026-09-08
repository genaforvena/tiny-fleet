# A02 — ticket text to evidence-backed JSON

Status: **NO-GO; deterministic baseline-only exploration.** This is an
offline synthetic CC0 study. The extractor emits `product`, `version`,
`issue`, and `requested_action`, each nullable, plus exact character spans.
It performs no model, network, filesystem-under-test, or ticket-system call.

## Registration and provenance

The frozen manifest is
`corpus/applications/ticket-extraction/manifest.json`: development (10),
validation (10), and heldout (100) cases, with one source family per case and
labels for absent fields, contradictions, malformed input, and quoted prompt
injection. The heldout minimum is met, but this synthetic screening set is not
evidence of production prevalence or generalization.

NuExtract-tiny is the primary feasibility precedent:
<https://huggingface.co/numind/NuExtract-tiny>. At registration it was public,
MIT-licensed, and pinned to revision
`0f3834d3e119430e81ab797bda6e95ed85c4407c` (retrieved 2026-09-08). Its model
card describes extractive JSON-template usage and a Qwen1.5-0.5B base model.
The model was not downloaded or scored. Base 360M and neural prerequisite
gates C02–C08/S01–S05 were not verified, so no neural arm or pilot was run.

## Baseline and preregistered gate

`baseline-20260908` contains deterministic regex+dictionary predictions and
raw rows. Heldout results are 400/400 fields correct, 100/100 cases with exact
evidence spans, and 0 unsupported fields. The zero-failure one-sided 95%
upper bound for the unsupported-field rate is
`1 - 0.05**(1/400) = 0.7461%`, below the 1% threshold. This does not establish
the full A02 gate: no paired model improvement or cost comparison exists, and
the baseline has no observed headroom on these fixtures. Therefore the bounded
verdict is `NO_GO_BASELINE_DOMINANT`, not a claim that a neural extractor is
inferior.

No adapter pilot, deployment, routing change, paid API call, or real-ticket
data acquisition was performed. VPN must rerun in an isolated output path,
inspect raw rows, and add unseen negative cases before independent verification.

## Reproduction

```text
rtk proxy .venv/bin/python scripts/applications/build_ticket_corpus.py
rtk proxy .venv/bin/python scripts/applications/ticket_extraction.py --phase baseline --run-dir runs/applications/ticket-extraction/baseline-20260908
rtk proxy .venv/bin/python scripts/test_app_ticket_extraction.py
```
