# C06 verification receipt — immutable training runs

- Actor: `haunt` (independent verification lane)
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Implementation receipt SHA-256: `39267c45f3a67c0dd7193cbda3a20faf0d3003510664782ab574474803cb6899`
- Submitted implementation revision: `a9f6b67d179bcb64e56d7dfe770104a1c19923d6`
- Remote receipt revision checked: `d41852c2bb8760e4a6ecd4e0ddd68d46cbf9e090`
- Result: **PASS — DONE**

## Independent evidence

Verification used a detached worktree at commit `d41852c`, with the existing repository
`.venv` linked into that temporary checkout. The first literal command in the fresh worktree
was blocked before Python because the worktree has no environment:

```text
rtk proxy .venv/bin/python scripts/test_run_manifest.py
exit 1 — rtk: .venv/bin/python: No such file or directory
```

After linking the existing pinned environment (no packages installed), the same command passed:

```text
rtk proxy .venv/bin/python scripts/test_run_manifest.py
exit 0 — Ran 4 tests ... OK
stdout/stderr: /tmp/tinyfleet-c06-v-WcKbbC/baseline-with-venv.txt
SHA-256: a2dae5bbe4d4693d8327518df40c21d9ad367224a4898a7d4e907dbcfecf76c5
```

The required load-bearing mutation changed the input-hash predicate from mismatch rejection to
match rejection. It failed as expected (`exit 1`; 1 failure and 3 errors), proving the test gate
observes the implementation:

```text
/tmp/tinyfleet-c06-v-WcKbbC/mutated.txt
SHA-256: 7e47282dab948775a9f720401beaa00d12c8ebdca1a3c45e7b062dcd651160e7
```

The original predicate was restored and passed again:

```text
/tmp/tinyfleet-c06-v-WcKbbC/restored.txt
SHA-256: 2660fb6da7e3a282291bcc352d0064538571eaa9f08e99eff5c97e28ad0c566b
rtk proxy .venv/bin/python scripts/test_persona_code.py — exit 0; persona-code tests: 2/2
rtk proxy .venv/bin/python -m compileall -q scripts/run_manifest.py scripts/test_run_manifest.py scripts/persona_code.py scripts/train_eval.py — exit 0
rtk git diff --check — exit 0
```

Independent negative control: a manifest whose hashed input path escapes its root was rejected
before run allocation (`input escapes manifest root: ../outside.txt`), output SHA-256
`ede0ba8d816e3d3ef546bc325e1b0b941083494e4591514e84ffc410d98fb1d6`.

The submitted implementation is an ancestor of `origin/master` (`git merge-base --is-ancestor`
exit 0), and its implementation diff is scoped to `docs/task-receipts/C06-implementation.md`.
No model training was launched; heavy replication remains outside this verification task.
