# A07 implementation receipt — PII highlighting with residual-risk reporting

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `b7caf0d4765f3a202d251656fbaa52def91ba25b`
- UTC: `2026-09-09`
- Scope: `scripts/applications/redaction_assistance.py`, `scripts/test_app_redaction_assistance.py`, `corpus/applications/redaction-assistance/`, `runs/applications/redaction-assistance/`, `docs/applications/redaction-assistance.md`, `docs/task-receipts/A07-check-20260909.txt`
- Primary precedent: <https://arxiv.org/abs/2605.09973>

## Result

READY FOR INDEPENDENT VPN VERIFICATION. The implementation adds a synthetic
CC0-1.0 multilingual fixture with 120 independent heldout source families, 60
English and 60 Russian documents, four declared PII types, and four format
families. The deterministic regex baseline returns exact character spans,
matched text, type, and a review confidence. Raw JSONL predictions preserve
every heldout row and scores; the summary reports per-type exact-offset
precision/recall, false negatives, Wilson 95% intervals, latency, and explicit
residual risks.

The finite baseline point estimates are perfect for all four types, but each
type has only 30 heldout examples and its Wilson 95% lower bound is `0.886483`.
That is below the preregistered recall threshold `0.99`, so the result is
`INCONCLUSIVE`, not `NULL`, `NO_GO`, or evidence of complete anonymization.
The model arm is explicitly unavailable until the shared C02-C08 and S01-S05
verification gates complete. No model score, pilot, deployment, or private
record was used.

## Verification performed

```text
rtk proxy .venv/bin/python scripts/test_app_redaction_assistance.py — exit 0 (5 tests)
rtk proxy .venv/bin/python scripts/applications/redaction_assistance.py --phase baseline --run-dir runs/applications/redaction-assistance --manifest corpus/applications/redaction-assistance/manifest.json — exit 0
git diff --check — exit 0
```

Check output: `docs/task-receipts/A07-check-20260909.txt`.

Artifact SHA-256 values at submitted source revision:

- `corpus/applications/redaction-assistance/manifest.json` — `c13695a68ddee326bf1e312a9ac776a3ccd0b436bb41a9574809161af95cc4d2`
- `runs/applications/redaction-assistance/regex-raw.jsonl` — `b9eec6416a1dfbc0caae9da431e0c43ecf03ef557f0228915f621da69d9eae31`
- `runs/applications/redaction-assistance/summary.json` — `474f2819f1fa4d74b9f66eb05f9aa3be1adab0fa2501f05f9945b1610ba12cd5`

## Exact next action

VPN must inspect `b7caf0d4765f3a202d251656fbaa52def91ba25b` in an isolated
checkout, rerun tests and baseline into a new temporary directory, recompute
the source-family/type counts and hashes, mutate one load-bearing span or
validation behavior to observe FAIL then restore PASS, and inspect an unseen
OOD document before writing `A07-verification.md`.
