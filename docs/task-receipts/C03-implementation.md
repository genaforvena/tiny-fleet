# C03 implementation receipt — prediction identity

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Source revision: `f9145e840ae5c519f3f9bc3b65c9109332428dfb`
- Result: **PASS — ready for independent vpn verification**

## Scoped changes

- `scripts/deep_evaluation.py` now validates the manifest-declared prediction matrix with
  `Counter`-based exact keys `(case_id, model, seed, repetition)`.
- Predictions require typed input hashes, rendered input, output/route/action, confidence kind,
  latency and status. It rejects unknown/duplicate/extra/missing rows, stale hashes, reference
  leakage, non-finite or negative values, invalid status rows, and missing timeout/error reasons.
- Manifest validation requires unique model IDs, integer seed metadata, candidate SHA-256 revision,
  raw-output schema and migration report, rendering template/config digests, and verifies any
  declared local model artifact hashes before publication validation.
- `scripts/test_deep_evaluation.py` adds the duplicate-pair reproducer and typed negative/timeout
  cases. `docs/deep-evaluation-contract.md` records the v1 raw-output and prediction contract.

## Verification

Test-first sequence: the new regressions were observed failing against the old `(case_id, model)`
set validator; after implementation the exact task check passed:

```text
Command: rtk proxy .venv/bin/python scripts/test_deep_evaluation.py
Exit: 0
Output: Ran 18 tests ... OK
Artifact: /tmp/tinyfleet-c03-check-20260911.txt
SHA-256: 072555cd4923ed584eb86b106266ef70c65af42eaf5a8cd972aff089b8d16087
```

Also ran `git diff --check` on the three scoped files successfully. The source revision was pushed
to `origin/master`; remote ancestry check `git merge-base --is-ancestor HEAD origin/master` exited 0.

Next action: independent `vpn` verification at
`tinyfleet-publication-science-20260908/verify-validate-prediction-identity`.
