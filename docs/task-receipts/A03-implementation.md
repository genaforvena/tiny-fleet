# A03 implementation receipt — log normalization

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-09`
- Scope: `scripts/applications/log_normalization.py`, `scripts/test_app_log_normalization.py`, `corpus/applications/log-normalization/manifest.json`, `runs/applications/log-normalization/`, `docs/applications/log-normalization.md`, `docs/task-receipts/A03-check-20260909.txt`
- Primary precedent: <https://huggingface.co/numind/NuExtract-tiny>

## Result

READY FOR INDEPENDENT VPN VERIFICATION. The implementation provides a frozen
CC0 synthetic manifest, source-family split, deterministic regex/template
baseline, exact typed extraction contract, null handling for missing evidence,
raw JSONL output and a bounded no-go report. It does not invent a root-cause
field, call a model, call the network or deploy an adapter.

The heldout baseline is 120/120 exact records, including 104/104 known-format
records; unsupported-field rate is 0%. The result is
`NO_GO_BASELINE_DOMINANT` because the simple baseline already meets the
preregistered quality gates and model-score dependencies are unavailable.

## Verification performed

```text
rtk proxy .venv/bin/python scripts/test_app_log_normalization.py — exit 0 (5 tests)
rtk proxy .venv/bin/python scripts/applications/log_normalization.py --phase baseline --run-dir runs/applications/log-normalization — exit 0
git diff --check — exit 0
```

Check output: `docs/task-receipts/A03-check-20260909.txt`, SHA-256
`418ca94d21f147826196dfe1f74f126cf50188066d0dee524cdf5485eb49aa52`.

Artifact SHA-256 values before commit:

- `corpus/applications/log-normalization/manifest.json` — `a8f8ee5747c8d124e70ab7e1496d7d20b5f2a21e7700be2e13e3ba60fe397707`
- `runs/applications/log-normalization/regex-template-raw.jsonl` — `2116f3cbe57226df74265e4a6c8fa108cb798a20a3e9067792b84e403a7ab46e`
- `runs/applications/log-normalization/summary.json` — `a69fd8df1ae28fdc7add04b6100deefd2726502af441760862f4dffc82797282`

## Exact next action

VPN must inspect this submitted commit in an isolated checkout, rerun the test
and baseline into a new temporary directory, recompute the summary and hashes,
mutate one load-bearing parser behavior to observe FAIL then restore PASS, and
inspect an unseen malformed/unsupported log before writing `A03-verification.md`.
