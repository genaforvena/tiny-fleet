# C08 implementation receipt — enforce decision consumer

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: 2026-09-11
- Submitted source revision: `e65c78d5b1bb042aeef390a01813d5ab773a9912`
- Scope: `scripts/policy_consumer.py`, `scripts/test_policy_consumer.py`, `README.md`

## Result

Added `dispatch_decision(decision, execute, review, escalate)`, a callback-only
consumer for structured policy decisions. It invokes `execute` only for a valid
`allow` decision with `require_approval=False`; review and escalation route to
their respective callbacks; block, approval-needed, unknown, missing, and
malformed decisions hold without invoking any callback.

Updated the README middleware example to use the consumer rather than allowing
review decisions to fall through to execution. The documentation now describes
the policy as a deterministic lexical baseline with uncalibrated confidence,
finite observed fixture runtime, and limited threat coverage. Review
paraphrases are explicitly documented as regression observations, not safety
claims.

## Verification

The new test was first run before implementation and failed with
`ModuleNotFoundError: No module named 'policy_consumer'`; after implementation
it passed. The final checks were run from the repository root through the
pinned environment:

```text
rtk proxy .venv/bin/python scripts/test_policy_consumer.py       # exit 0; policy consumer: 4/4
rtk proxy .venv/bin/python scripts/operator_policy.py --test     # exit 0; held-out 41/41, adversarial 14/14, safety decisions 8/8
rtk proxy .venv/bin/python scripts/fleet_benchmark.py --test     # exit 0; fleet benchmark 24/24
rtk git diff --check                                             # exit 0
```

Captured output hashes:

- `scripts/operator_policy.py --test`: `6d00f66f55c03c0bc48f3f49fc08040fb4a3ca10837ac35ab08806148d896d74`
- `scripts/fleet_benchmark.py --test`: `9b278027e97aa3c0299d3242beba62227bd884ada4d1fdcd83d1f18fe2040193`

## Limitations

The consumer proves callback routing and does not execute shell commands or
actions itself. The policy classifier remains a lexical fixture with
uncalibrated confidence and limited threat coverage; this task does not claim
general safety or broad policy recall.

## Next action

Ready for independent `vpn` verification of C08, including isolated inspection,
the exact consumer check, and a counterexample absent from the positive
examples. This implementation does not settle the verification gate.
