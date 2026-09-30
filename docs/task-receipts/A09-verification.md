# A09-V independent verification receipt — transliteration

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Exact source commit verified: `6d3b554713af8b8646ba842515b20e55e406cf41`
- Verification checkout: fresh detached isolated worktree at `/tmp/tiny-fleet-a09-verify-20260909`
- Interpreter: `/home/mesh-home/tiny-fleet/.venv/bin/python` (the detached worktree has no local `.venv`)
- Independent run: `/tmp/a09-independent-FWtyJX/baseline`
- Verdict: **REJECT — receipt hash typo; implementation evidence otherwise reproduces**

## Exact acceptance checks

The mandated test suite ran from the detached checkout:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_app_transliteration.py
exit 0 — Ran 5 tests; OK
```

The baseline was rerun into an isolated output directory:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python \
  scripts/applications/transliteration.py --phase baseline \
  --run-dir /tmp/a09-independent-FWtyJX/baseline
exit 0 — wrote raw.jsonl and summary.json
```

The independent raw artifact is 304 rows: 24 development, 40 validation, and 240 heldout
rows. The heldout set has 120 independent source families. Recomputed heldout results are:

```text
identity exact                         0/540
deterministic lexicon exact          540/540
protected IDs unchanged             120/120 for both baselines
protected violations                       0
```

The regenerated summary remains `INCONCLUSIVE`, with all model arms unavailable, pilot not run,
and zero GPU minutes and paid API calls. The unseen negative
`ORD-2026-9001 qwerty novoe-slovo` was returned unchanged; neither unknown token occurs in the
manifest. `git diff --check` passed in the isolated checkout.

## Hash finding

The independent raw artifact and the author's raw artifact are byte-identical. Their valid
SHA-256 is:

```text
bf7b5e768d07dbb7bad309226d6dcced00fe8bc1833ac08b1a62c521bcb16b5c
```

The implementation receipt currently lists a different 63-character value, missing one `b`:

```text
bf7b5e768d07db7bad309226d6dcced00fe8bc1833ac08b1a62c521bcb16b5c
```

The generated `summary.json` correctly records the valid 64-character hash. This is a receipt
defect, not a mismatch in the raw output or baseline computation. A09-V is therefore rejected
until `A09-implementation.md` is corrected and the verification is reconciled. A10 and later
remain held.
