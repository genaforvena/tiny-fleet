# C04 independent verification receipt — derived report validation

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Submitted implementation receipt: `docs/task-receipts/C04-implementation.md`
- Implementation receipt SHA-256: `1e17e732a779a922353b20fe925afd313be297686f7028d6efdafaf862478043`
- Exact source revision verified: `280eee8090b44ad6b06842fe6c6468fe7e461812`
- Remote continuity: `HEAD == origin/master == 220b2aa29c877c37134e5c4b4ee3343f1b2f69f3`

## Checks and evidence

From the Tiny Fleet repository, independently reran:

```text
.venv/bin/python scripts/test_report_contract.py
exit 0; Ran 26 tests; OK

.venv/bin/python scripts/test_deep_evaluation.py
exit 0; Ran 18 tests; OK

python3 -m py_compile scripts/report_contract.py scripts/test_report_contract.py
exit 0

.venv/bin/python -m unittest -v scripts.test_report_contract scripts.test_deep_evaluation
exit 0; Ran 44 tests; OK
```

The report-contract tests include a complete negative-result bundle accepted as a valid artifact,
while remaining routing-ineligible. They also mutate missing reports, malformed JSON/TSV,
non-finite and negative numeric fields, edited primary counts, unsafe-action labels, omitted raw
prediction rows, and an all-abstain bundle falsely claiming usefulness; each case rejected with its
typed `REJECT report-*` category. The deep-evaluation suite independently covers raw artifact,
cardinality, leakage, split-boundary, stale-input, typed-failure, and symlink containment guards.

## Result

**PASS** — C04 derived-report validation is independently verified at the canonical remote source
revision. No implementation files were changed by this verification.

Residual limitation: this verifies the dependency-free contract and its fixtures; it does not claim
a live model evaluation or publication-quality experiment result.
