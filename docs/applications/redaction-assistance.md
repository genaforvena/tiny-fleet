# A07 PII highlighting with residual-risk reporting

Status: offline regex baseline, 2026-09-09. This is a human-review aid, not an
automatic anonymizer and not a measured Tiny Fleet model benefit.

The CC0-1.0 fixture in
`corpus/applications/redaction-assistance/manifest.json` expands to 12
development, 20 validation, and 120 heldout documents. The heldout set has 120
unique source families, 60 English and 60 Russian documents, four declared PII
types (`name`, `email`, `phone`, and `account_id`), and four format families.
All documents are synthetic; no private mesh or user records are included.

The baseline returns character offsets, the matched text, type, and a review
confidence. Its raw JSONL preserves every heldout prediction and score. The
summary reports exact-offset precision and recall with Wilson 95% intervals,
false negatives, and residual risks. A finite perfect point estimate does not
clear the preregistered recall gate: with 30 examples per type, the lower 95%
bound is 0.886483, below the required 0.99. The resulting verdict is
`INCONCLUSIVE`, not a null and not evidence of complete anonymization.

The GLiNER2-PII preprint is recorded as a feasibility precedent only:
[arXiv:2605.09973](https://arxiv.org/abs/2605.09973). Its multilingual
synthetic span-extraction result does not establish a Tiny Fleet benefit.

Run the deterministic screen with:

```text
rtk proxy .venv/bin/python scripts/test_app_redaction_assistance.py
rtk proxy .venv/bin/python scripts/applications/redaction_assistance.py --phase baseline --run-dir runs/applications/redaction-assistance
```

The model arm is unavailable until the shared C02-C08 and S01-S05 dependency
gates are independently verified. Even if later model scoring is authorized,
suggestions remain subject to human review; regex can miss unseen spellings,
obfuscation, OCR noise, and undeclared entity types.
