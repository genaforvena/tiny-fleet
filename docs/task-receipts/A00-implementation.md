# A00 implementation receipt — application-protocol

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Source revision: `89ff4bdbf6d29bf9cdd5e1e5bb019c53e0649a25`
- UTC: `2026-09-08`
- Scope: `docs/applications.md`, `scripts/application_screen.py`, `scripts/test_application_screen.py`, `runs/applications/registry.json`, `docs/task-receipts/A00-check-20260908.txt`

## Result

READY FOR INDEPENDENT VPN VERIFICATION. The offline registry contains exactly
A01–A10, each with source URL/license, explicit per-application CC0-1.0 data
license, explicit non-LLM competitor, metric, preregistered gate, input/output
schema, 30 GPU-minute/one-job/no-paid-API ceiling, registered state, and empty
run-hash list. The validator performs no model, network, operating-system, or
live-mesh action. It rejects missing data licenses, duplicate source families,
unreasoned missing values, and uncalibrated probabilities; `no-go` and
`inconclusive` are valid terminal states.

## Checks

Command:

```text
rtk proxy .venv/bin/python scripts/test_application_screen.py
```

Exit status: `0` (`7` tests passed).

Captured stdout/stderr: `docs/task-receipts/A00-check-20260908.txt`

Captured stdout/stderr SHA-256: `c22f3a854dcae8cef52a7feaf3ee5c2664c0060efeceefcc35367f3254620aeb`

Additional command:

```text
rtk proxy .venv/bin/python scripts/application_screen.py --registry runs/applications/registry.json --validate
```

Exit status: `0`; output: `{"applications": 10, "registry": "runs/applications/registry.json", "status": "valid"}`.

The tests hand-check the exact one-sided bound `1 - 0.05**(1/n)`: minimum
independent zero-failure samples are `299` for a 1% upper bound and `598` for
0.5%. They also remove A01's `data_license` and require the validator to
reject the registry. `git diff --check` also exited `0` before commit.

## Exact next action

Push this repair commit and this corrected receipt, verify remote containment,
then ask VPN to resume the same independent gate:

```text
rtk git push origin master
rtk proxy env MESH_TASK_ACTOR=haunt mesh-task done tinyfleet-applications-20260908 application-protocol /home/mesh-home/tiny-fleet/docs/task-receipts/A00-implementation.md "Submitted for independent VPN verification; registry and offline contract checks PASS"
```
