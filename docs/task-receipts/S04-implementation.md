# S04 implementation receipt — independent task scoring

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Task: `tinyfleet-publication-science-20260908/independent-task-scoring`
- Source commit: `c34aa2c3ff296e92b58e6de5e333a2a7bb2cee3d`
- Result: `PASS — submitted for independent vpn verification`

## Contract delivered

Added `scripts/score_study.py`, `scripts/test_score_study.py`, and
`docs/scoring-rubric.md`. The scorer consumes the frozen manifest and raw prediction JSONL,
rejects duplicate or out-of-matrix keys, preserves failed rows, computes correctness, abstention,
coverage, false accepts, domain slices, clustered bootstrap intervals, confidence calibration, and
latency summaries, and emits the declared deterministic report files plus a separate decision.
Qualitative rows remain unscored without an anonymized rating sheet. Zero coverage reports
undefined accuracy (`null`) and `inconclusive`, never zero or eligible.

## Verification

Prescribed check:

```text
rtk proxy .venv/bin/python scripts/test_score_study.py
exit 0; Ran 4 tests; OK
```

Full script suite:

```text
rtk proxy .venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
exit 0; Ran 137 tests; OK
```

`git diff --check` exited `0`. Source hashes at the committed revision:

```text
scripts/score_study.py       89096c3fda5213deb6253ce77fc590c2ae7febe0d2b7c9f8859eef7265f19213
scripts/test_score_study.py  df9bf3adb7d3dbb77d0d82ec605ba0f184331d67b2879e12416e95dfeef73f75
docs/scoring-rubric.md       bbc315e33d1d62c9ab3fbc7f4ae4543d30f18658481d917a91f9a177f9f34c0b
```

The fixtures independently cover perfect/wrong/abstention arithmetic, a timeout failure,
zero-coverage undefined risk, repeated-row clustering, deterministic rebuild, and duplicate-key
rejection. No generated study claim or serving eligibility is asserted by this implementation.

## Scope and handoff

Only the three S04 implementation files were committed; pre-existing untracked receipts were left
untouched. Submit this source to `vpn` for independent S04 verification.
