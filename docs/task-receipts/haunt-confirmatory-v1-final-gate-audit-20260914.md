# Confirmatory-v1 final gate audit — PASS; comparison task queued

Task: `tinyfleet-drift-confirmatory-prerequisites-20260913/final-gate-audit-and-fresh-task`
Audit date: 2026-09-14 UTC

## Verdict

**PASS to create a fresh exact-owner comparison task. No generation, scoring, comparison, or matrix
was run during this audit.** The previously rejected analysis remains rejected; its stale v2 matrix
successor is superseded below.

## Original rejection and replacement scope

`tinyfleet-architecture-drift-review-20260907/run-cross-repository-analysis` remains rejected. Its
recorded inputs are the earlier Flask/Requests/Pydantic sample whose excerpt selection followed
objective labels and a generic model smoke; the independent v2 review marked those data audit-only.
The current replacement is the distinct confirmatory-v1 HTTPX/attrs/pytest sample. It was selected
from stable-tag and commit metadata before retrieving snapshot contents; objective labels were
written later and before any inference or smoke. The excerpt selector uses a fixed hash ranking over
common source-module paths and verifies the label-ledger digest without reading label contents.
The disclosed temporal limitation remains: excerpt selection followed the objective-label freeze,
although selection is deterministic and label-content-blind. The labels are narrow objective
public-interface labels, not semantic or behavioral ground truth.

## Exact current gates

The frozen generation registration is
`runs/drift-confirmatory-v1/generative-registration.json`, SHA-256
`157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`. Its six prompts bind all six
trained adapter paths/digests, sample-bound excerpts and corpora, and the scorer source digest. Its
status remains `blocked-before-generation` and `comparison_authorized=false`; this audit does not
edit that frozen file.

The paired behavioral closeout is
`runs/behavioral-preflight-confirmatory-v1-paired-closeout-20260914.json`, SHA-256
`fd36f832d08601ba21debc3735bc8f6489a33a0d4415ba91485850de1c1800f5`. It records PASS with exit 0
for both snapshots of attrs, HTTPX, and pytest, including the supported HTTPX-new AnyIO 4.9.0 +
Trio 0.26.1 full-suite retry.

VPN's independent gate-level PASS is recorded in
`docs/task-receipts/vpn-confirmatory-v1-independent-gate-verification-20260914.md`. It independently
rehashed the exact closeout and registration above, recomputed behavioral log/freeze/source archive
digests, verified all adapter and corpus bindings and the held-out/label ledgers, and confirmed no
generation, inference, scoring, or comparison was invoked.

The sample registration, label ledger, and held-out excerpt ledger are respectively pinned at
`f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`,
`8bbb3047ebe375d5d0077e563b72d6d74578dfb21e1805fb6df1865038aeb5db`, and
`d37c62534a429d7659b78d44f4f7bc2e6ca2d56ee14a1eb101b81e00d245c83a`.

## Task transition

The open task `tinyfleet-drift-v2-implementation-20260913/execute-v2-generative-matrix` is tied to
the rejected earlier sample, so it must not be resumed. The new chain
`tinyfleet-confirmatory-v1-comparison-20260914` starts with the exact-owner comparison task and
carries forward reader-facing conclusions and critical publishability review in sequence. Its first
step must recheck these exact hashes and the recorded independent PASS before doing any work. If a
required gate hash changed, or the runner treats `comparison_authorized=false` as a hard stop, it
must stop and publish a typed blocker rather than mutate frozen registration or run a partial matrix.

## Verification

- Re-read the frozen sample registration, chronology, excerpt selector and held-out excerpt ledger.
- Re-read the full paired closeout and current VPN independent PASS receipt; recomputed hashes for
  both closeout and generation registration.
- Confirmed the stale v2 matrix remains an open task and the original analysis remains rejected.
- No model inference, generation, scoring, comparison, or matrix was run.
