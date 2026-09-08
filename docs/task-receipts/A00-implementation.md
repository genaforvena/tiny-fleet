# A00 implementation receipt — application-protocol

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Source revision: `6e394e48e65fb07e8ad495c0bd900cd51a2998c7`
- UTC: `2026-09-08`
- Scope: `docs/applications.md`, `scripts/application_screen.py`, `scripts/test_application_screen.py`, `runs/applications/registry.json`

## Result

READY FOR INDEPENDENT VPN VERIFICATION. The offline registry contains exactly
A01–A10, each with source URL/license, explicit non-LLM competitor, metric,
preregistered gate, input/output schema, 30 GPU-minute/one-job/no-paid-API
ceiling, registered state, and empty run-hash list. The validator performs no
model, network, operating-system, or live-mesh action. It rejects duplicate
source families, unreasoned missing values, and uncalibrated probabilities;
`no-go` and `inconclusive` are valid terminal states.

## Checks

Command:

```text
rtk proxy .venv/bin/python scripts/test_application_screen.py
```

Exit status: `0` (`6` tests passed).

Captured stdout/stderr: `docs/task-receipts/A00-check-20260908.txt`

Captured stdout/stderr SHA-256: `85078c38fa46ea226ab5b345e21b84ed9e378963fbb552f8adbf4bf16ad6a25`

Additional command:

```text
rtk proxy .venv/bin/python scripts/application_screen.py --registry runs/applications/registry.json --validate
```

Exit status: `0`; output: `{"applications": 10, "registry": "runs/applications/registry.json", "status": "valid"}`.

The tests hand-check the exact one-sided bound `1 - 0.05**(1/n)`: minimum
independent zero-failure samples are `299` for a 1% upper bound and `598` for
0.5%. `git diff --check` also exited `0` before commit.

## Exact next action

Push the two scoped commits, verify remote containment, then submit the
implementation step to the independent VPN gate:

```text
rtk git push origin master
rtk proxy env MESH_TASK_ACTOR=haunt mesh-task done tinyfleet-applications-20260908 application-protocol /home/mesh-home/tiny-fleet/docs/task-receipts/A00-implementation.md "Submitted for independent VPN verification; registry and offline contract checks PASS"
```
