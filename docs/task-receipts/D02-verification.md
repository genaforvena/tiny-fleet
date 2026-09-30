# D02 independent verification receipt — lexical drift controls

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Exact source commit verified: `271033767e1e9ef1512d2bf68340710fceb2caf5`
- Verification checkout: fresh detached clone at `/tmp/tinyfleet-d02-final.xMbfAG/repo`
- UTC: `2026-09-11`
- Verdict: **PASS** for the D02 acceptance predicates

The corrective receipt from `haunt` was treated as a dependency, not as independent evidence.
The checkout was created with `git clone --no-local`, then detached at the exact corrective
commit. The checkout was clean before verification.

## Independent checks

The required focused suite was run from the detached checkout:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_drift_lexical.py
exit 0
Ran 7 tests in 0.181s
OK
```

Captured output: `/tmp/tinyfleet-d02-final.xMbfAG/focused.txt`

Output SHA-256: `5c5b4b63f4b3f3eba6bc7114f938af3ec2d83401a918bc9544ecf023f4cd7223`

The suite independently exercises no-change, duplication normalization, lexical rename,
evidence-based shuffle, absent-rename negative, dictionary provenance, and generated artifact
contracts. `git diff --check` exited `0`.

An additional fresh CLI fixture with identical `a.py` entries in both snapshots produced:

```text
no_change=NO_CHANGE, delta_concepts=0
duplication=NO_DUPLICATION
rename=NO_RENAME, evidence.pairs=[]
shuffle=NO_SHUFFLE
```

CLI JSON: `/tmp/tinyfleet-d02-final.xMbfAG/negative-no-rename/cli.json`

CLI JSON SHA-256: `6647e0ea757b19ace1edaed23ce972273bf2eb065b226ba01a380b4509b84974`

## Load-bearing mutation

In the isolated verification copy only, the no-rename branch was mutated from `NO_RENAME` to
`LEXICAL_ONLY`. The same seven-test command exited `1`; the absent-rename assertion failed with
`AssertionError: 'LEXICAL_ONLY' != 'NO_RENAME'`.

Mutation output: `/tmp/d02-mutated.out`

Mutation output SHA-256: `0f4a82d62498e08ca8e4c951ef65581579114b55409b34fc36cfe56cb1592b05`

The source used for the final passing checks was a separate clean detached checkout; no mutation
was made to the submitted commit or the repository worktree.

## Residual limitations

This PASS is limited to D02's stated offline acceptance predicates. It does not establish the
scientific validity of the lexical dictionary, semantic equivalence of renamed files, or any
downstream generative-drift result. Python emitted existing `ResourceWarning` messages for test
helpers' unclosed TSV readers, but the seven assertions passed and the command exited `0`.

## Exact next action

Commit and push this receipt, verify remote containment, then settle
`tinyfleet-drift-science-20260908/verify-lexical-drift-controls`. D03 remains separately gated.
