# A03 log normalization

Status: bounded baseline screen, `NO_GO_BASELINE_DOMINANT`.

The frozen CC0 manifest contains 24 development, 24 validation and 120 heldout
source-family units. The heldout set includes known-format records, missing
timestamps/fields, benign warnings and malformed records. The parser extracts
only `component`, `error_code`, `operation`, `timestamp` and the literal
`evidence_span`; it has no root-cause output and leaves absent values null.

The regex/template baseline produced 120/120 exact heldout records (100%),
including 104/104 known-format records, with zero unsupported-field values.
Mean CPU latency was 0.0196 ms per case on the collection node. Since the
simple baseline already meets the exact-record and known-format gates, and the
model-score dependencies C02–C08 and S01–S05 are not verified, no 360M adapter
pilot was justified. This is a baseline-dominant no-go for the candidate screen,
not evidence that a model could never improve on another corpus.

Raw output: `runs/applications/log-normalization/regex-template-raw.jsonl`.
Run summary: `runs/applications/log-normalization/summary.json`.
Primary feasibility precedent: [NuExtract-tiny](https://huggingface.co/numind/NuExtract-tiny);
its existence is not a Tiny Fleet result.

Reproduce with:

```bash
rtk proxy .venv/bin/python scripts/test_app_log_normalization.py
rtk proxy .venv/bin/python scripts/applications/log_normalization.py --phase baseline --run-dir runs/applications/log-normalization
```
