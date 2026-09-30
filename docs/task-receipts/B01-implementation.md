# B01 implementation receipt — advisory dispatch corpus

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11T17:32:00Z`
- Scope: `docs/board-dispatch-study.md`, `corpus/board-dispatch-v1/cases.jsonl`,
  `runs/board-dispatch-v1/registration.json`, `scripts/test_dispatch_corpus.py`

## Change

Added an immutable registration and 12 authored, sanitized cases split by family across train,
validation, and heldout. Cases carry explicit as-of state, eligible owners, dependency/lease and
retry inputs, independently reviewed labels, ambiguity, and adversarial controls. The contract is
advisory-only: no live dispatcher, Ledger, board, or private log is read or changed.

## Verification

Command:

```text
rtk proxy .venv/bin/python scripts/test_dispatch_corpus.py
```

- Exit: `0`
- Output artifact: `/tmp/b01-test.p2uqk1.txt`
- Output SHA-256: `c791a78159bda6e07ac9a5d0bc25ae9a1126aa75035dee43e89fbed1ba801e3e`
- Result: `ACCEPT 12 sanitized cases; advisory-only; immutable registration`

The gate verifies registration and corpus hashes, split counts, family isolation, typed fields,
owner whitelists, sanitization, independent label provenance, explicit-owner preservation, and
ambiguity coverage. The 8 heldout families are a contract fixture, not the plan's 100-family
exploratory quality claim; no model quality result is asserted.

## Next action

Commit and push this scoped change, then submit
`tinyfleet-board-dispatch-20260908/verify-dispatch-corpus-contract` to `vpn`.
