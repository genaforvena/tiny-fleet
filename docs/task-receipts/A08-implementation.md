# A08 implementation receipt: noisy-text-correction

Result: `INCONCLUSIVE` baseline exploration, ready for independent A08-V.

## Scope

- Task: `tinyfleet-applications-20260908/noisy-text-correction`
- Source files: `scripts/applications/noisy_text_correction.py`,
  `scripts/test_app_noisy_text_correction.py`
- Data: `corpus/applications/noisy-text-correction/manifest.json`
- Documentation: `docs/applications/noisy-text-correction.md`
- Run: `runs/applications/noisy-text-correction/baseline-20260909/`
- Source revision: the implementation commit containing these files; verify
  the exact hash from repository history before independent verification.

## Verification

Command:

```text
rtk proxy .venv/bin/python scripts/test_app_noisy_text_correction.py
```

Exit code: `0`; 5 tests passed. The tests cover exact deterministic repair,
protected-field mutation detection, missing/OOD input behavior, disjoint
multilingual heldout units, and raw/summary artifact creation.

Command:

```text
rtk proxy .venv/bin/python scripts/applications/noisy_text_correction.py --phase baseline --run-dir runs/applications/noisy-text-correction/baseline-20260909
```

Exit code: `0`. The run created `raw.jsonl` and `summary.json` for 120
heldout documents plus 20 validation documents. Raw output SHA-256:
`555f1ab7808d5d01324c770e58fc594b48ea17ff55364d6a4214e4aed8b988fd`.

Observed heldout metrics:

- identity mean CER: `0.042258360055`
- dictionary/edit-distance mean CER: `0.000000000000`
- relative CER reduction: `1.0` (finite observed baseline comparison)
- protected fields unchanged: `120/120`; corruption `0.0%`
- ByT5-small and 360M LoRA: unavailable pending C02-C08 and S01-S05
- pilot: not run; GPU minutes `0`, paid API calls `0`

The verdict is `INCONCLUSIVE`, because the model arms are unavailable and
source-family uncertainty intervals are not estimable from singleton
synthetic families. No deployment or live-routing change was made.

## Independent verification handoff

The next ledger step is VPN-owned:
`tinyfleet-applications-20260908/verify-noisy-text-correction`. VPN must
rerun the check in isolated output paths, inspect the raw artifacts, recompute
counts and hashes, and include an unseen negative case. A08-V and later remain
held until the coordinator releases them.
