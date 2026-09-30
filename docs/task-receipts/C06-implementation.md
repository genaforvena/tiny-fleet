# C06 implementation receipt — immutable training runs

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Source revision: `a9f6b67d179bcb64e56d7dfe770104a1c19923d6`
- Result: **PASS — ready for independent `vpn` verification**

## Scoped changes

- Added dependency-free `scripts/run_manifest.py` to verify every manifest input hash before
  optional model loading, resolve base/tokenizer revisions, Python/NumPy/Torch seeds, device,
  dtype, batch, accumulation, max length and train/eval configuration, and allocate a unique
  `run-dir/adapters/<arm>-seed-<seed>` output.
- Existing completed runs and seed-colliding adapters are rejected. Resume requires an explicit
  checkpoint and matching frozen config/data hashes. Completion is marked with `COMPLETE.json`.
- Integrated manifest preparation, seed selection, batch/gradient accumulation, optimizer-step
  and examples-seen reporting into `scripts/persona_code.py` and the legacy `scripts/train_eval.py`.
- Added `scripts/test_run_manifest.py` with corrupt-input-before-loader, batch=2/accumulation=2
  step-count, seed isolation, resolved-config, and completed-run cases.

## Verification

Test-first sequence: the new test initially failed with `ModuleNotFoundError: No module named
run_manifest`; after implementation the exact task check passed:

```text
Command: rtk proxy .venv/bin/python scripts/test_run_manifest.py
Exit: 0
Output artifact: /tmp/tinyfleet-c06-test-20260911.txt
SHA-256: cc27108ee14fc0dd96a5d3b283adecfdd927cb4fa2b4596bdb05169fc8bbf606
Output: Ran 4 tests ... OK
```

Additional checks:

```text
rtk proxy .venv/bin/python scripts/test_persona_code.py — exit 0; persona-code tests: 2/2
rtk proxy .venv/bin/python -m compileall -q scripts/run_manifest.py scripts/test_run_manifest.py scripts/persona_code.py scripts/train_eval.py — exit 0
rtk git diff --check — exit 0
```

No model training was launched. The CPU fixture verifies the stated C06 acceptance only; heavy
replication remains separately scoped. The implementation commit was pushed and remote ancestry
was verified before this receipt was submitted.

Next action: independent `vpn` verification at
`tinyfleet-publication-science-20260908/verify-immutable-training-runs`.
