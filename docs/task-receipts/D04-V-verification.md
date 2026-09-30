# D04-V verification receipt

- Result: PASS — independent verification completed at the submitted source revision.
- Task: `tinyfleet-drift-science-20260908/verify-validate-architectural-ground-truth`
- Reviewer: vpn
- UTC: 2026-09-11
- Source revision: `e52da8ddd5c5c8ad1d7b62ad11b753f78b000f67`
- Checkout: detached isolated worktree `/tmp/tiny-fleet-d04v-fH7Q8T`

## Evidence

The exact required command passed from the isolated checkout:

```text
rtk proxy .venv/bin/python scripts/test_drift_validate.py
Ran 4 tests in 0.013s
OK
```

The worktree had no committed-source diff after verification. `py_compile`
passed for both Python files, and the fixture CLI regenerated `validation.json`
with status `preliminary`, three repositories, three units, and four separate
estimands. The fixture remains preliminary because scores and external
association are intentionally blinded; this verification does not unlock the
paired-replications successor.

Source and fixture hashes from the isolated checkout:

```text
scripts/drift_validate.py                         40334ea3874acf2904efe712d227290599eaf145af473c6fcc628d527fa261cc
scripts/test_drift_validate.py                     75325d6b08439cb0b633a81eeba5a67d9a1e268be4205f42344a8e0cd10abf4f
runs/drift-validation-v1/registration.json        052a18bb79d2e17f9e8c3a706d023f832b5fa8223859077e9cab52852a64e27d
runs/drift-validation-v1/labels.jsonl              0f887cbadf43eab8d5fec5b00a34e84e130d684e2777557d1e4a991e17a9db9a
runs/drift-validation-v1/validation.json           a8bd1654331c5149e2a005f79235ef2d20024c2ad50a6602c216187772a96868
runs/drift-validation-v1/decision.md               35aa7ee2fa18394d694ab4f6bc70c1856c83e4704efe578acb45600a78525545
```

## Mutation and negative controls

The load-bearing predicate `adjudication == change_class` was mutated to its
inverse. The same test command failed (`mutation_exit=1`): the valid fixture
errored and two negative tests failed with the wrong error, proving the suite
observes the predicate. The predicate was restored and the clean suite passed.

Five independent malformed-input checks all rejected as required:

1. non-40-hex immutable snapshot ID — `snapshot must be immutable 40-hex commit`;
2. unregistered repository label — `label repository is not registered`;
3. duplicate reviewers — `two distinct reviewers required`;
4. unresolved reviewer disagreement — `adjudication required after reviewer disagreement`;
5. score field leakage — `label leakage: model scores are forbidden`.

No later successor was taken.
