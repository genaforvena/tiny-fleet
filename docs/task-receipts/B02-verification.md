# B02-V verification receipt — offline dispatch baselines

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Source commit verified: `b2334672b6d19bef991088a9fde866555209f7d9` (`docs: receipt for dispatch baselines`)
- Verification UTC: `2026-09-11`
- Verdict: **PASS** for the B02 acceptance predicates

## Independent commands and evidence

No live dispatcher, ledger, board, mesh-chat, mesh-task, network, or OS command was called by
the baseline test harness. The receipt's recorded `.venv/bin/python` command could not run on
this node because that path is absent; the same test was rerun with the available `/usr/bin/python3`.

1. `python3 scripts/test_dispatch_baselines.py`
   - exit `0`
   - 5 tests passed
2. Result artifact integrity
   - `runs/board-dispatch-v1/baselines/results.json`
   - SHA-256: `3c92696b3bc01c6a839173f91ae7735542f6c628f2dd06beefbb144ff17f0db0`
   - 5 baseline metric rows; all report `severe_constraint_violations: 0`
3. Corpus identity
   - `corpus/board-dispatch-v1/cases.jsonl`
   - SHA-256: `8d46c88be72edb4726e6304e10563c7c9c041578a226604270b88be350a288e7`
   - matches the previously verified B01 corpus hash and the B02 implementation receipt

## Scope and limitation

The PASS covers the offline contract tests, reproducible result artifact, corpus identity, and
fail-closed constraint metrics. The MiniLM baseline remains intentionally unavailable without
pinned vectors, as documented by the implementation receipt; this is not a live dispatcher test.
