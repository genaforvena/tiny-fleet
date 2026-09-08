# A00 verification receipt — PASS

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `89ff4bdbf6d29bf9cdd5e1e5bb019c53e0649a25`
- Verification receipt base revision: `263d6cf`
- UTC: `2026-09-08`
- Result: **PASS — A00 acceptance gate is satisfied.**

## Independent checkout and commands

The submitted source revision was checked out detached at
`/tmp/tinyfleet-a00v-20260908-0203`. Its local `.venv` was a symlink to the
already-installed repository interpreter only; all outputs below are newly
written under `/tmp/tinyfleet-a00v-output-20260908-0203`, not in an author run
directory.

1. `rtk proxy .venv/bin/python scripts/test_application_screen.py` exited `0`:
   seven tests passed. Output `test-pass.txt` SHA-256:
   `c910028474bf3b05f0d320ea3e9982a6b83e8252ba160f26154e5e5edc8d2236`.
   The restored rerun also exited `0` with that same hash.
2. `rtk proxy .venv/bin/python scripts/application_screen.py --registry
   runs/applications/registry.json --validate` exited `0`, reporting ten
   applications and `status: valid`. Output `validate-pass.txt` SHA-256:
   `9c3ec54de3f528c086d07902bb4901f32e0b14b4eec795d2ba80bdffde181532`.
3. The committed author artifact `docs/task-receipts/A00-check-20260908.txt`
   recomputes to the corrected claimed SHA-256
   `c22f3a854dcae8cef52a7feaf3ee5c2664c0060efeceefcc35367f3254620aeb`.
   Its textual content matches the independent suite output except for the
   nondeterministic reported duration (`0.003s` versus `0.001s`), so its byte
   hash is not expected to equal an independently timed run.
4. Independent counterexample absent from the author positives: replacing
   A01's in-memory `data_license` with `Apache-2.0 external corpus` raised
   `RegistryError: A01: data_license must be CC0-1.0`; command exit `0`
   confirms the rejection. Output `data-license-counterexample.txt` SHA-256:
   `882ff7ddda73beaf65488e581a6c7a5beb781c6cbd9d4dbcc87bc8b319c748fd`.
5. Deliberate isolated source mutation changed the validator's CC0 prefix
   guard from `CC0-1.0` to `CC0-9.9`. The exact suite then exited `1`, with
   two registry-dependent tests failing. Output
   `data-license-guard-mutation-fail.txt` SHA-256:
   `5eb454654fabbb544dfa435ee0db06781df9fc5aadea32a123d24816d92229d8`.
   The source was restored before the final passing rerun.

## Acceptance evidence

The validator and a separate registry inspection established exactly A01-A10,
all in `registered` state with empty run-hash lists, each carrying a non-empty
`CC0-1.0; locally authored synthetic ... fixtures only` data license. Each
also has the frozen 30 GPU-minute, one-job, no-paid-API cap. The existing test
suite independently checks the 299/598 one-sided rare-error arithmetic,
source-family independence, non-defaultable missing values, calibrated
probabilities, terminal no-go state, and required data licenses. `git diff
--check` on the detached submitted revision exited `0`.

The registry is an offline, reproducible pre-scoring contract; this PASS does
not establish the future applications' model quality, corpus manifests, or
experimental results.

## Exact next action

Commit and push this renewed VPN receipt, verify that its commit is contained
by `origin/master`, then settle
`tinyfleet-applications-20260908/verify-application-protocol` with this path.
