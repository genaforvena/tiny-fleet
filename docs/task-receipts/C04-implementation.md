# C04 implementation receipt — derived report validation

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Source commit: `280eee8090b44ad6b06842fe6c6468fe7e461812`
- Scope: `scripts/report_contract.py`, `scripts/test_report_contract.py`,
  `docs/deep-evaluation-contract.md`, and the implementation plan.

## Contract delivered

`validate_reports(run_dir)` now parses and validates the JSON/TSV/Markdown derived bundle,
revalidates the raw prediction tape, checks report row membership against the prediction matrix,
recomputes total/scored/correct/false-accept counts and coverage, and rejects malformed, missing,
non-finite, negative, edited, unsafe, orphaned, or all-abstain-useful reports with stable
`REJECT report-*` categories. Artifact validity is returned separately from `result_status` and
`routing_eligible`; a complete negative result is accepted as an artifact while remaining
ineligible to serve.

## Verification

Commands were run from the repository root with isolated stdout/stderr under
`/tmp/tinyfleet-c04-PS8yAo/`:

```text
rtk proxy .venv/bin/python scripts/test_report_contract.py
exit 0; Ran 26 tests in 0.069s; OK
stdout sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
stderr sha256: aaf5ce38252b4f48ab337833e237bdbf7279f373b50724214b685c10cf9a20cb

rtk proxy .venv/bin/python scripts/test_deep_evaluation.py
exit 0; Ran 18 tests in 0.038s; OK
stdout sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
stderr sha256: 3ead1c8890757a77e192ba42615850407c99abb48a0322d7692304b6c852df21

python3 -m py_compile scripts/report_contract.py scripts/test_report_contract.py
exit 0
```

The test fixture covers valid negative-result acceptance plus missing, malformed, non-finite,
negative, edited-count, unsafe-action, omitted-case, and all-abstain-useful tampering cases.

## Handoff

The implementation commit is ready for the independent `verify-validate-derived-reports` VPN gate.
Unrelated pre-existing untracked task receipts were not staged.
