# D04 implementation receipt

- Result: DONE/PASS — ready for independent D04-V verification.
- Actor: haunt
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `e52da8ddd5c5c8ad1d7b62ad11b753f78b000f67`
- UTC: 2026-09-11
- Scope: `scripts/drift_validate.py`, `scripts/test_drift_validate.py`,
  `docs/drift-validation-registration.md`, and `runs/drift-validation-v1/`

## Implemented contract

The dependency-free validator freezes four separate estimands, requires three
immutable repository identities, requires two distinct reviewers and an
adjudication for disagreements, and rejects model-score fields in evidence
labels. It also rejects an architectural label on a unit explicitly marked
`cosmetic` or `no_change`. The fixture run contains three labeled units, one
cosmetic negative, and no model scores. Its decision is `preliminary`, not a
cross-repository finding, because the external three-repository freeze and
score association are unavailable.

## Verification evidence

The first test run was intentionally red with `ModuleNotFoundError` because
`scripts/drift_validate.py` did not exist. After implementation, the focused
command passed:

```text
rtk proxy .venv/bin/python scripts/test_drift_validate.py
exit=0
stdout/stderr artifact: runs/drift-validation-v1/test_drift_validate.out
sha256: 7481316c728b8b6c2fcbc3737ace7c3ae4910dea6c43945684751fcc1458497d
```

`py_compile` passed for both Python files. The fixture CLI also passed and
produced `validation.json` with status `preliminary`.

Run artifact hashes:

```text
registration.json  052a18bb79d2e17f9e8c3a706d023f832b5fa8223859077e9cab52852a64e27d
labels.jsonl       0f887cbadf43eab8d5fec5b00a34e84e130d684e2777557d1e4a991e17a9db9a
validation.json    a8bd1654331c5149e2a005f79235ef2d20024c2ad50a6602c216187772a96868
decision.md        35aa7ee2fa18394d694ab4f6bc70c1856c83e4704efe578acb45600a78525545
```

## Handoff and limitation

D04-V must inspect this exact committed source in an isolated checkout, mutate
one load-bearing validation predicate, and rerun the negative controls. The
external comparison remains preliminary until that review and a valid
independent-repository freeze. `run-paired-replications` remains queued.
