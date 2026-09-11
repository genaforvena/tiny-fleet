# S04 verification receipt — independent task scoring

- Result: `PASS — independently verified`
- Task: `tinyfleet-publication-science-20260908/verify-independent-task-scoring`
- Verifier: `vpn`
- UTC: `2026-09-11`
- Implementation commit: `c34aa2c3ff296e92b58e6de5e333a2a7bb2cee3d`
- Implementation receipt SHA-256: `d985159444a0c1ec52cfdd6fabba29618812537f436440a00e64277447e9b5fb`
- Remote check: `origin/master` was later than the implementation commit; the implementation commit is an ancestor of `origin/master`.

## Independent checks

The implementation receipt and source commit were inspected in an isolated detached worktree.
Committed source hashes matched the receipt:

```text
scripts/score_study.py       89096c3fda5213deb6253ce77fc590c2ae7febe0d2b7c9f8859eef7265f19213
scripts/test_score_study.py  df9bf3adb7d3dbb77d0d82ec605ba0f184331d67b2879e12416e95dfeef73f75
docs/scoring-rubric.md       bbc315e33d1d62c9ab3fbc7f4ae4543d30f18658481d917a91f9a177f9f34c0b
```

From the isolated checkout at the exact implementation commit:

```text
rtk proxy .venv/bin/python scripts/test_score_study.py
Ran 4 tests in 0.024s
OK

rtk proxy .venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
Ran 137 tests in 0.840s
OK

git diff HEAD^ HEAD --check
exit 0
```

The four executable fixtures independently cover perfect/wrong/abstain arithmetic, timeout
failure accounting, zero-coverage undefined risk, repeated-row clustering, deterministic rebuild,
and duplicate-key rejection. The committed implementation preserves failed rows and does not
claim qualitative scoring without anonymized ratings, matching the stated acceptance boundary.

The later working checkout has an unrelated extra `test_drift_generate.py` whose implementation is
absent there; current-head discovery therefore reports 138 tests with one import error. This does
not alter the exact submitted source commit, which passes its complete 137-test suite.

## Verdict

PASS — S04 is independently reproducible at the owner-submitted commit. No implementation changes
were required. No later successor task was taken or modified.
