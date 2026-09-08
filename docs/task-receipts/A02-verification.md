# A02 independent verification receipt — ticket-extraction

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Exact source commit: `69e3eb46c7b381c278262449e0d47cb352ed928a`
- Verification checkout: detached isolated worktree at `/tmp/a02-v-fAKKAc`
- Verdict: **BLOCKED**

## Exact acceptance check

The required command was run from the isolated checkout:

```text
rtk proxy .venv/bin/python scripts/test_app_ticket_extraction.py
exit 1
rtk: Failed to execute command: .venv/bin/python: No such file or directory (os error 2)
```

The source commit contains no `.venv` and no committed Python executable. This is an
environment/dependency blocker, not a test failure. The same issue prevents the exact
baseline reproduction command using `.venv/bin/python`.

## Independent evidence obtained

Using the system `python3` 3.12.3 in the same isolated checkout and isolated output directory:

```text
python3 scripts/test_app_ticket_extraction.py
exit 0 — Ran 7 tests; OK
python3 scripts/applications/ticket_extraction.py --phase baseline --run-dir /tmp/a02-v-fAKKAc/verification-output/baseline-python3
exit 0 — heldout_n=100, field_correct=400, field_total=400,
field_precision=1.0, field_recall=1.0, unsupported_field_n=0,
span_exact_case_n=100, pilot_verdict=NO_GO_BASELINE_DOMINANT
```

Recomputed source/artifact hashes:

```text
corpus/applications/ticket-extraction/manifest.json
7b539de4d1d123ae3975cbbcc70192965f852cca15e46e6f5ecea5ac80a9f866
runs/applications/ticket-extraction/baseline-20260908/regex-dictionary-raw.jsonl
bf76823764f36a0a94351aee9dcbbd76161cca320fcad4084bb09cb9535650b3
runs/applications/ticket-extraction/baseline-20260908/summary.json
0837c47a02e3a3255268e2c7d584d71e01dc89e1f693c2a8ec0efb5fbf29cf3c
```

The committed raw output has 120 rows: 100 heldout, 10 validation, and 10 development.
Recomputed heldout totals are 400/400 fields, 0 unsupported fields, and 100/100 exact-span
cases. The cited zero-failure one-sided upper bound recomputes to `0.0074613555287995625`
(0.7461%). The manifest has 120 cases and source families do not cross splits.

Unseen negative probes were also run: quoted `Product: Fake` text is not extracted; a
prompt-injection line is excluded while adjacent labelled evidence remains extractable;
contradictory distinct product labels abstain; case-insensitive labels are accepted. These
probes found no contrary result for the claimed deterministic behavior.

## Residual limitation / correction

The exact mandated command remains unverified until the repository’s documented `.venv` is
restored or the task instruction is corrected to name an available interpreter. Keyed haunt
correction requested: `A02-V-ENV` — provide the pinned environment/interpreter, then rerun the
exact command and replace this BLOCKED receipt with a fresh PASS/FAIL receipt.
