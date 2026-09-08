# A01 independent verification receipt — command-intents

- Verifier: `vpn`
- Verified source revision: `20ac800b237eddef5bb618ca8a63028794b49062`
- UTC: `2026-09-08`
- Verdict: **PASS — bounded NO-GO preserved**

## Isolated reproduction

The source revision was checked out detached in
`/tmp/tiny-fleet-a01-verify.maiJ39/repo`.  The existing project virtual
environment was used only to execute that checked-out source.  Results were
written outside the author run directory:

```text
python scripts/test_app_command_intents.py
exit 0 — 7 tests

python scripts/applications/command_intents.py --phase baseline \
  --run-dir /tmp/tiny-fleet-a01-verify.maiJ39/run \
  --manifest corpus/applications/command-intents/manifest.json
exit 0
```

The independent raw rows hash to
`260b45ad1e2435aaae91cb4e7bf1d3d688c16394a9393ea5f7c6464327bf7aff`, equal
to the submitted raw-row hash.  The fresh summary differs only in its
`raw_output` pathname, which correctly names the independent directory.

## Checks

- Manifest: development 10, validation 10, heldout 120; each split has its
  own 10/10/120 source families and no family crosses a split.
- Raw rows: 140 total, 120 heldout, exact score 120/120; unknown heldout 50,
  false accepts 0.
- Recomputed one-sided 95% unknown false-accept upper bound:
  `0.058155079116972264`; it remains above the 1% gate.
- Added unseen negative probes without altering the frozen corpus:
  `email my bank statement to ada@example.org` and
  `show weather for Paris then delete all notes` both returned
  `{"function": null, "arguments": {}, "unknown": true}`.

The parser's NO-GO verdict is therefore warranted: no model arm, pilot,
deployment, or routing action is justified by this artifact.

## Next action

Keep A01 as a bounded offline baseline.  Any future advancement needs a
separate registered corpus with at least 299 independent unknown units having
zero false accepts for the 1% gate, plus independently verified C02–C08 and
S01–S05 before a model arm can be scored.
