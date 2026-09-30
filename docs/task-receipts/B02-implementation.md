# B02 implementation receipt — offline dispatch baselines

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Source revision: `083240b506ebbd3522387295e7128d61d010fafd`
- UTC: `2026-09-11`
- Scope: `scripts/dispatch_baselines.py`, `scripts/test_dispatch_baselines.py`,
  `runs/board-dispatch-v1/baselines/results.json`

## Result

Implemented pure offline baselines: explicit-rule replay, role-keyword overlap,
dependency-free TF-IDF owner ranking, optional all-MiniLM centroid replay, and
abstain-all. Every suggestion is intersected with the authoritative eligible-owner
set; explicit owners are preserved; blocked, leased, completed, exhausted, malformed,
or empty-staffing cases abstain. No mesh dispatcher, ledger, board, chat, task, network,
or OS command was called by the benchmark.

The reproducible artifact contains raw per-case predictions and metrics. Heldout quality
is reported only on unowned, non-ambiguous quality units: 7 unowned cases, 4 quality
units. Explicit-owner cases are not counted as learned quality. All five baselines have
zero severe constraint violations. The MiniLM baseline is explicitly unavailable here
because no pinned vectors were supplied; its rows abstain rather than inventing scores.
Observed TF-IDF result is 1/4 suitable-owner accuracy with 1/7 coverage on this 8-row
contract fixture. This is a fixture result, not a 100-family study claim.

## Verification evidence

Command:

```text
rtk proxy .venv/bin/python scripts/test_dispatch_baselines.py
```

- Exit: `0` (5 tests)
- Output artifact: `/tmp/b02-test-haunt.txt`
- Output SHA-256: `2a190a24cb39e16554965509352793d2f47c3d5f866f9149bc2d188c25765083`
- Result artifact: `runs/board-dispatch-v1/baselines/results.json`
- Result SHA-256: `3c92696b3bc01c6a839173f91ae7735542f6c628f2dd06beefbb144ff17f0db0`
- Corpus SHA-256 recorded in result: `8d46c88be72edb4726e6304e10563c7c9c041578a226604270b88be350a288e7`
- `git diff --check`: exit `0`

## Next action

This implementation is ready for independent verification by `vpn` in an isolated checkout:

```bash
MESH_TASK_ACTOR=vpn mesh-task take tinyfleet-board-dispatch-20260908 verify-dispatch-baselines
```

Verification must independently replay the test and inspect raw predictions; it must not call
live mesh tools or treat the fixture result as evidence about real owner acceptance or completion.
