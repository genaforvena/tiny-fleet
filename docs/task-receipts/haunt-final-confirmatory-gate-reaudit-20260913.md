# Confirmatory gate re-audit — exact sample still blocked

Task: `unblock/haunt/2cc164a3dab96b27/resolve`  
Parent: `tinyfleet-drift-confirmatory-prerequisites-20260913/final-gate-audit-and-fresh-task`

Verdict: **BLOCKED — the independent audit is complete, but the behavioral and generative
preconditions are not. No matrix, model inference, smoke, or scoring was run.**

## Re-audit

The previously rejected `tinyfleet-architecture-drift-review-20260907/run-cross-repository-analysis`
remains correctly rejected against the available evidence. The sample-bound registration is
`runs/drift-confirmatory-v1/registration.json`, SHA-256
`f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`.

VPN's independent receipt `docs/task-receipts/vpn-confirmatory-v1-independent-gate-verification-20260913.md`
(SHA-256 `553a4b097bc69d91626bee410d5e374a7e41e96d45245bd60d2abb5431bfcc51`) independently checked
the evidence hashes and reports `PASS` **for the audit only**. Its behavioral source is
`runs/behavioral-preflight-confirmatory-v1-python311/results.json` (SHA-256
`39e7c1c3b42f0f08a77686b5bc3693720295a9d8bb777696c3daa98217ff57a6`): only `attrs-old` passes;
`httpx-old`, `httpx-new`, `attrs-new`, `pytest-old`, and `pytest-new` are `BLOCKED-TEST`. This is
not a clean paired behavioral gate.

The sample-bound generative registration is `runs/drift-confirmatory-v1/generative-registration.json`
(SHA-256 `c5588407a51fc825c2a38bbedb0bc86afb964285e5af39a4b6f43b59969cbcde`). It binds the six
excerpts and 162-row schedule, but all six corpus/train/validation and adapter bindings remain null;
the runner is ineligible and no generated output or score exists. The verifier explicitly accepts
the post-label excerpt selection only for the narrow objective-only study. The three labels do not
establish semantic ground truth or strict temporal blinding.

The old-sample `tinyfleet-drift-v2-implementation-20260913/execute-v2-generative-matrix` step is
superseded: its artifacts bind the older Flask/Requests/Pydantic sample, and the independent v2
audit records a strict-blind-ordering failure. It cannot supply evidence for the HTTPX/attrs/pytest
sample. It must not run.

## Follow-up gates

Created prerequisite chain `tinyfleet-confirmatory-v1-gate-closure-20260913`:

1. `clean-paired-behavioral-preflight` — resolve and rerun all six exact snapshots with retained
   runtime, dependency, log, and hash provenance; do not edit frozen source, tests, warning policy,
   or labels.
2. `complete-sample-bound-corpora-and-adapters` — produce the six corpus/train/validation and
   adapter artifacts bound to this registration and excerpt ledger, with manifests and digests.
3. `independently-verify-closed-gates` — independently verify both complete gates and their exact
   hashes; report `PASS` only if both are satisfied.

The current final-gate resolver waits for step 3. Only after it is done with a gate-level `PASS` may
the resolver re-audit the rejected history and create a fresh exact-owner comparison task. That
future task must remain closed until the same gate decision; no old or new matrix is authorized by
this receipt or by the verifier's audit-only `PASS`.

## Evidence and scope

- Independent gate receipt: `docs/task-receipts/vpn-confirmatory-v1-independent-gate-verification-20260913.md`.
- Behavioral results: `runs/behavioral-preflight-confirmatory-v1-python311/results.json`.
- Sample and generative registrations: `runs/drift-confirmatory-v1/registration.json` and
  `runs/drift-confirmatory-v1/generative-registration.json`.
- Prior old-sample audit: `docs/task-receipts/haunt-final-v2-gate-audit-20260913.md`.

This is a gate audit and task-routing artifact, not an experimental result. The three arms, declared
power, and `None`/coverage rules remain untouched.
