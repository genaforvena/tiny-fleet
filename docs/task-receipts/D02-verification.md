# D02 independent verification receipt

- Actor: vpn
- Repository: `/home/mesh-home/tiny-fleet`
- Source revision: `402d2c8d5c4b996a3d21f49995eeb53b127c4846`
- Parent/source baseline: `1da5e3c39a80cc29296cef8ffc6df6c8c113e5ab`
- UTC: 2026-09-11
- Verdict: **FAIL**

## Checks and artifacts

The implementation was inspected in detached isolated checkout
`/tmp/tiny-fleet-d02-verify.KQ96sM` at the exact submitted commit.

1. Required command: `rtk proxy .venv/bin/python scripts/test_drift_lexical.py` — exit 1.
   The isolated checkout intentionally has no ignored `.venv`; captured output SHA-256 is
   `4ab2b4e4bff6ea0f38c9d66772fb053253bc5c1b882d40a71d5d5697af8aea2d`.
2. Same test suite with the repository's pinned interpreter
   `/home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_drift_lexical.py` — exit 0,
   5 tests OK. This produced the author's five positive fixture assertions independently.
3. Production extraction and lexical run using old commit `1da5e3c...` and new commit
   `402d2c8...`, with output under `/tmp/tiny-fleet-d02-prod.E4zpBs/extract` — exit 0.
   Artifact hashes: `manifest.json` =
   `157070870a9cfed0105d0183a82b93fa4609e86c38874ac6fd89ac9ace9b7eac`,
   `structural.tsv` = `d38b936e873536b36d31fe75d8f7fb3d7ec9a7c6218ebeb12d205b38e48a1fb1`,
   `lexical.tsv` = `72e91f4b55a303fee4abbbecb1df1ae503a9c3056ce647e039d2d45314becff4`,
   `controls.tsv` = `2f5867e1a2b438703fa9c6b0212efbf1c89be12cd269a3ef34e396bca9c9bd54`.

## Failed predicate

The control verdicts are constants in `drift_lexical.py`: duplication is always
`NO_NORMALIZED_CHANGE`, rename is always `LEXICAL_ONLY`, and shuffle is always
`NO_SEMANTIC_VERDICT`. They are not derived from the extracted snapshots or control fixtures.

Independent negative case: identical old/new fixture (`a.md: "model gate"`) returned
`delta_concepts=0` and `NO_CHANGE`, but also returned `rename=LEXICAL_ONLY`. With no rename,
the implementation therefore claims the rename control was detected. The same run's artifact
hashes were `lexical.tsv` =
`1e71cba31b80b4968de1916b64c3f52e10ac44167dff623b3a433f50928e9c4c` and `controls.tsv` =
`9fbe63c407f06740f5c0e71a34a958e68042deef555aac954456460942429f0d`.

This fails the D02 control requirement and leaves the verification gate open. No implementation
files were modified. Haunt must make control verdicts evidence-derived, add a negative assertion
for absent rename, and resubmit the scoped implementation for re-verification.
