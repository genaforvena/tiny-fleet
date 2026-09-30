# S05 independent verification — selective routing calibration

- Verification task: `tinyfleet-publication-science-20260908/verify-calibrate-selective-routing`
- Repository: `/home/mesh-home/tiny-fleet`
- Verified source commit: `fcf4ab3c05ad9f1ecaec15baf53c5a083dc8446c`
- Verification checkout: detached worktree at `/tmp/tinyfleet-s05v-SoQ8ii/repo`
- Verification status: `PASS`

## Scope and source audit

The task was live and open when claimed. S05 and S05-V in the current plan require validation-only
calibration, the declared absolute-similarity/margin grid, the `-0.20/-0.80` adversarial fixture,
frozen calibration provenance, separate model refusal, and an honest `no-eligible-router` result.
The submitted source commit contains exactly the S05 files named by the plan. No later publication
successor was taken.

Recomputed source/artifact SHA-256 values:

```text
scripts/calibrate_router.py           f3a3a4cd04d6a40a9a127123a03cc08ecc5c3f6589a632f0a113476c4f928697
scripts/test_calibrate_router.py      6fd85731247b1837084db8a24487de68af6135f3c0103595f1304ff87e7c04c7
scripts/router.py                     544037eb33b34016316c593f703e87ddd1332c0201ad997798248a03fc408c36
runs/fleet-study-v1/router.json       042b3a43b087aff7f6a6bd8971053cee292b7309ab32ee3e08d3854fec933ef9
docs/task-receipts/S05-implementation.md a29ffee9a9c9fd70657671e34cdafb9ed42cb04180154b61c5474d895c54fb8e
```

The generated router artifact independently reports `eligible-router`, validation `n=13`,
coverage `12/13 = 0.923076923`, routed false accepts `0`, `similarity_min=0.0`, and
`margin_min=0.0`; the one OOD validation case abstains for `absolute_similarity`.

## Independent execution

All output was written under `/tmp/tinyfleet-s05v-SoQ8ii/verify`, outside the repository’s
completed author-run artifacts.

```text
rtk proxy .venv/bin/python scripts/test_calibrate_router.py
exit 0; Ran 4 tests in 0.002s; OK
stdout sha256: c5d2da6fb6f389a8c11fa78271b24833e02d2ac997a065520297aa26a3cc3810

rtk proxy .venv/bin/python scripts/test_router.py
exit 0; Ran 7 tests in 0.002s; OK
stdout sha256: 74c03fc16fde9a2dfeff03db0ec8f472a5a8dfed04e9e982a912b4b7f64faee3

rtk proxy .venv/bin/python -m compileall -q scripts/calibrate_router.py scripts/router.py scripts/test_calibrate_router.py
exit 0; stdout sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

independent validation-only, absolute-distance, zero-vector, heldout, and impossible-population checks
exit 0; stdout sha256: 3091a1ba02fab642a165a851585276b22e477ff6abb388727a16ef06dac77f20
```

The independent checks confirmed: heldout input is rejected; zero query vectors abstain with
`zero_query_embedding`; `[-0.20, -0.80]` against the positive fixture centroids abstains with
`absolute_similarity`; and an all-OOD validation population returns `no-eligible-router` with
zero coverage. Router regression checks covered zero/nonfinite/wrong-shape embeddings, invalid
centroids, backend failures/invalid JSON, operator precedence, and retained route scores.

The first detached-worktree attempt correctly failed because `.venv` is an ignored, non-repository
path (`exit 1`, missing `.venv/bin/python`). The isolated checkout then used a symlink to the
existing project venv only; the literal prescribed commands above passed. No packages were
installed and no author artifacts were overwritten.

## Verdict

`PASS`: all S05 acceptance predicates are independently evidenced. This verifies the bounded
calibration fixture only; it does not establish a universal safety claim or heldout study result.
