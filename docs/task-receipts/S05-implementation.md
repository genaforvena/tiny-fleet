# S05 implementation receipt — selective routing calibration

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Task: `tinyfleet-publication-science-20260908/calibrate-selective-routing`
- Result: `PASS — submitted for independent vpn verification`

## Contract delivered

Added `scripts/calibrate_router.py`, `scripts/test_calibrate_router.py`, updated
`scripts/router.py` to accept a frozen calibration gate, and generated
`runs/fleet-study-v1/router.json`. Calibration consumes validation rows only, rejects
heldout labels, freezes embedding/corpus provenance, searches a declared similarity/margin
grid under a false-accept bound, and emits `no-eligible-router` when coverage cannot be
earned honestly. The comparison fixture evaluates lexical, nearest-centroid, gated,
oracle, and abstain-all methods on identical saved validation cases. Route details retain
both similarities and machine-readable failure reasons; model refusal is a separate field.

The fixture includes an explicit OOD validation probe and the adversarial distance case
`-0.20/-0.80`; zero query vectors fail closed. No heldout labels are read by calibration.

## Verification

Prescribed check:

```text
.venv/bin/python scripts/test_calibrate_router.py
exit 0; Ran 4 tests in 0.002s; OK
stdout sha256: c5d2da6fb6f389a8c11fa78271b24833e02d2ac997a065520297aa26a3cc3810
```

Regression and syntax checks:

```text
.venv/bin/python scripts/test_router.py
exit 0; Ran 7 tests in 0.004s; OK
stdout sha256: 21c7e48d0b1ec908feef784bbce1fa55f2c9a7acf76382fa7578754a78bd1ed8
.venv/bin/python -m compileall -q scripts/calibrate_router.py scripts/router.py scripts/test_calibrate_router.py
exit 0; stdout sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
git diff --check
exit 0; stdout sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Artifact/source hashes before commit:

```text
runs/fleet-study-v1/router.json       042b3a43b087aff7f6a6bd8971053cee292b7309ab32ee3e08d3854fec933ef9
scripts/calibrate_router.py           f3a3a4cd04d6a40a9a127123a03cc08ecc5c3f6589a632f0a113476c4f928697
scripts/test_calibrate_router.py      6fd85731247b1837084db8a24487de68af6135f3c0103595f1304ff87e7c04c7
scripts/router.py                      544037eb33b34016316c593f703e87ddd1332c0201ad997798248a03fc408c36
```

The artifact is a fixture calibration, not a heldout result or universal safety claim.
Independent vpn verification must inspect the source revision and recompute these hashes.
