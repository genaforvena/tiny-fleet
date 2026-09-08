# A01 — offline read-only command interpretation

Status: **NO-GO; baseline-only exploration.** This is an offline simulator. It
only returns one of ten declared read-only function records or `unknown`; it
does not call the operating system, a model, or a service.

## Registration

The frozen CC0 synthetic manifest is
`corpus/applications/command-intents/manifest.json`. It has development (10),
validation (10), and heldout (120) cases. Source-family identifiers never cross
splits. Heldout includes safe unknown/delete requests, mixed-action rejection is
covered by unit test, and the parser tests include RU and EN plus negation.

FunctionGemma 270M is the primary feasibility precedent:
<https://ai.google.dev/gemma/docs/mobile-actions>. Its gated Hugging Face
repository could not be read on 2026-09-08 because this environment has no
credentials, so its revision is recorded as unavailable rather than invented;
it was not downloaded or scored. C02–C08 and S01–S05 are also not independently
verified, so no base-360M or FunctionGemma score has been run.

## Baseline and gate

`baseline-20260908` contains deterministic regex/grammar predictions and the
summary generated from them. On the synthetic heldout rows it scores exact
function-plus-arguments accuracy 120/120 and accepts 0/50 unknown rows. The
one-sided 95% upper bound for the unknown false-accept rate is 5.82%, computed
as `1 - 0.05**(1/50)`; it does **not** meet the preregistered <=1% gate (which
needs at least 299 independent zero-failure unknown units). The observed set is
therefore a baseline check, not a precision claim.

No adapter pilot is justified: the deterministic baseline has no observed
headroom on this narrow synthetic set, the rare-error gate is underpowered, the
optional comparator is unavailable, and the neural prerequisites remain
unverified. No deployment or routing change is authorized by this result.

## Reproduction

```text
rtk proxy .venv/bin/python scripts/applications/build_command_intent_corpus.py
rtk proxy .venv/bin/python scripts/applications/command_intents.py --phase baseline --run-dir runs/applications/command-intents/baseline-20260908 --manifest corpus/applications/command-intents/manifest.json
rtk proxy .venv/bin/python scripts/test_app_command_intents.py
```

VPN must use a new output directory, rerun the baseline, inspect the manifest
and raw JSONL, and add unseen negative cases before deciding the independent
verification gate.
