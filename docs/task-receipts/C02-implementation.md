# C02 implementation receipt — dataset boundaries

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11T17:24:00Z`
- Source revision before commit: `0aabf045e14e4ed5b8501da46803ad998dc21fbc`
- Scope: `scripts/deep_evaluation.py`, `scripts/test_deep_evaluation.py`,
  `docs/deep-evaluation-contract.md`

## Change

Manifest v2 now requires typed prompt/reference/source-family fields, nonempty required splits,
timezone-aware cutoff and temporal windows, duplicate IDs rejection, normalized prompt leakage
checks, source-family boundaries, and resolved-path containment that rejects symlink escapes.
Legacy v1 is explicitly archival-only.

## Verification

Command:

```text
rtk proxy .venv/bin/python scripts/test_deep_evaluation.py
```

- Exit: `0`
- Output artifact: `/tmp/c02-test.C9Kpn2.txt`
- Output SHA-256: `f4d3ac6800b863502d43d93d11c3082f5da393146c12a3280bf5f03bb5f1b956`
- Result: `12 tests, OK`

The suite includes valid v2 acceptance plus duplicate IDs, normalized prompt leakage,
source-family overlap, empty split, malformed typed field, symlink escape, missing artifact,
hash mismatch, cutoff/source boundary, and prediction-cardinality controls. This is ready for
independent `vpn` verification; it is not a C02-V result.

## Next action

Commit and push this scoped change, then submit
`tinyfleet-publication-science-20260908/verify-validate-dataset-boundaries` to `vpn`.
