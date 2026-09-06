# Deep-evaluation validator verification

Date: 2026-09-06

The dependency-free validator and its contract harness are present at:

- `scripts/deep_evaluation.py`
- `scripts/test_deep_evaluation.py`

Verification from the tiny-fleet virtual environment:

```text
......
Ran 6 tests in 0.011s
OK
fleet benchmark: 24/24
```

The six validator tests include complete-fixture acceptance and deliberate rejection of missing
artifacts, case leakage, source/cutoff split violations, manifest hash mismatch, and prediction
cardinality errors. The harness is dependency-free. The system Python could not run the existing
fleet benchmark because `numpy` is absent; `.venv/bin/python` supplied the declared evaluation
dependencies and passed it.

This settles the fixture/validator implementation step. The next step is independent witness review
of the methodology and fixtures; no real specialist result is claimed until that review and the
full Architectural Drift Report track complete.
