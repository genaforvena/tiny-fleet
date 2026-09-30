# B01-V verification receipt — frozen advisory dispatch corpus

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Source commit: `1341eac` (`feat: freeze advisory board dispatch corpus`)
- Verification UTC: `2026-09-11`
- Verdict: **PASS** for the B01 acceptance predicates

## Independent commands and evidence

The source commit was checked out in an independent clone at
`/tmp/b01-vpn-cwmNO0/clone`. No live dispatcher, board, ledger, mesh-chat, or mesh-task call
was made by the verification harness.

1. `python3 scripts/test_dispatch_corpus.py`
   - exit `0`
   - output: `ACCEPT 12 sanitized cases; advisory-only; immutable registration`
   - output SHA-256: `c791a78159bda6e07ac9a5d0bc25ae9a1126aa75035dee43e89fbed1ba801e3e`
2. Raw corpus recomputation from `corpus/board-dispatch-v1/cases.jsonl`
   - 12 rows; split counts train=2, validation=2, heldout=8
   - 12 unique case IDs and 12 family IDs; no family crosses splits
   - at least one explicit-owner case and one ambiguity case present
   - corpus SHA-256: `8d46c88be72edb4726e6304e10563c7c9c041578a226604270b88be350a288e7`
3. Mutation gate: replaced the registration corpus hash with 64 zeroes.
   - exit `1` as required
   - output SHA-256: `0a6a4a2c874afcbc53b0207605487726e9853bf311da70057c383b3a51fdb0f7`
   - failure identified the expected/observed hash mismatch
4. Restored mutation and reran `python3 scripts/test_dispatch_corpus.py`.
   - exit `0`
   - output SHA-256 matched the original: `c791a78159bda6e07ac9a5d0bc25ae9a1126aa75035dee43e89fbed1ba801e3e`

## Scope and limitation

The contract is advisory-only and the fixture is sanitized; the 8 heldout families are a contract
fixture, not the plan's 100-family exploratory quality claim. This receipt verifies the frozen
registration, split/family isolation, typed and privacy-safe fields, independent label provenance,
explicit-owner preservation, ambiguity coverage, and mutation-sensitive integrity guard.
