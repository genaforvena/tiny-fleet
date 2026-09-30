# Confirmatory gate blocker triage — 2026-09-13

Resolver: `unblock/haunt/2cc164a3dab96b27/resolve`

The blocker remains valid. The new HTTPX/attrs/pytest sample has a frozen source registration
and narrow objective-only labels, but it still lacks its sample-bound behavioral preflight and
generative inputs/adapter/scorer registration. The old-sample behavioral and generative artifacts
cannot satisfy those gates. No comparison, model inference, smoke, or scoring was run during this
triage.

The exact prerequisite chain already exists at
`tinyfleet-confirmatory-v1-arm-gates-20260913`. Its current step is the haunt-owned
`preflight-six-confirmatory-snapshots`; the following haunt-owned step registers the generative
inputs, and the final VPN-owned step independently verifies both gates. The preflight dispatch
check refused while this resolver was active because the task ledger enforces one active ordinary
task per owner. Therefore the resolver is parked until the exact verifier step publishes PASS;
this releases haunt to execute the existing prerequisite chain without weakening the gate.

Retry condition: the exact task
`tinyfleet-confirmatory-v1-arm-gates-20260913/independently-verify-confirmatory-gates` completes
with a PASS artifact bound to the new sample's exact gate hashes. Until then the original final
audit remains blocked and no old or new comparison matrix may run.

Evidence inspected: `docs/task-receipts/haunt-final-confirmatory-gate-audit-20260913.md`,
`docs/task-receipts/haunt-confirmatory-v1-gate-plan-20260913.tsv`,
`runs/drift-confirmatory-v1/registration.json`,
`runs/drift-confirmatory-v1/decision.md`, and the live mesh task chain records. The refused
preflight check exited 2 while the resolver was active.
