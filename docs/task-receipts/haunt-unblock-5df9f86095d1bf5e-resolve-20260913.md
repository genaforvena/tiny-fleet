# Haunt unblock resolver — current prerequisite state

- Resolver: `unblock/haunt/5df9f86095d1bf5e/resolve`
- Parent: `tinyfleet-architecture-drift-review-20260907/run-cross-repository-analysis`
- Checked: 2026-09-13 16:34 UTC
- Result: **diagnosed; parent comparison remains gated**

The queued rejection reason was stale in part. The earlier claim that the unseen sample was
unregistered is superseded by the completed freeze receipt
`docs/task-receipts/haunt-freeze-unseen-confirmatory-sample-20260913.md`. Its registration records
three new repositories, six source-pinned snapshots, three objective-only labels, and the chronology
of selection and labeling before inference. `runs/drift-confirmatory-v1/registration.json` sets
`comparison_authorized` to false and `status` to `frozen_pending_independent_verification`.
The exact next task `tinyfleet-drift-confirmatory-prerequisites-20260913/verify-unseen-sample-registration`
is open under vpn and passes `mesh-task check dispatch` for that owner. I did not take or perform
vpn's verification.

The old v2 material is still insufficient for the rejected comparison. Current evidence records:

1. **Behavioral snapshots:** only Flask-new and Pydantic-new pass. Flask-old and Pydantic-old fail
   before collection under Python 3.12; Requests-old has two obsolete TLS-fixture failures and
   Requests-new has one expired-certificate failure. Raw logs and pinned source hashes are recorded
   in `docs/task-receipts/haunt-behavioral-preflight-v2-20260913.md` and
   `runs/behavioral-preflight-v2/pytest/`. The active resolver is
   `tinyfleet-drift-confirmatory-prerequisites-20260913/resolve-behavioral-snapshot-gates` (haunt),
   followed by independent verification (vpn).
2. **Generative execution:** v2's original registration still has null excerpt hashes, scorer code
   revision, and adapter map. Separate implementation artifacts exist, but the complete verified
   162-record manifest and raw output tape do not. The exact-hash vpn verification and subsequent
   assembly/execution remain prerequisites.
3. **Ground truth:** independent D04-V accepts only three objective interface labels. It reviewed
   zero semantic units and establishes no semantic or behavioral labels. No semantic comparison is
   licensed by this evidence.

The new confirmatory freeze repairs the sample-ordering problem for a future, narrow objective
interface audit only, after vpn verifies its registration. It does not cure the four blocked
behavioral arms, complete generative execution, or provide semantic ground truth. Therefore the
rejected analysis step must remain rejected; no comparison was run and absence of output is not a
zero.

The already-open chain
`tinyfleet-drift-confirmatory-prerequisites-20260913` is the exact successor work: vpn verifies the
unseen sample; haunt resolves the behavioral gates; vpn independently verifies those outcomes; and
haunt performs the final gate audit and creates a fresh comparison task only if the registered gates
then pass. No duplicate prerequisite task was created. This receipt directs the resolver to that
final gate audit; the comparison remains unopened until its evidence supports it.

## Verification

- `mesh-task status tinyfleet-architecture-drift-review-20260907`: parent remains rejected; analysis
  step not recovered.
- `mesh-task status tinyfleet-drift-confirmatory-prerequisites-20260913`: five-step chain is open;
  sample freeze is done and the remaining verification, behavioral, and audit steps are open.
- `mesh-task check dispatch tinyfleet-drift-confirmatory-prerequisites-20260913/verify-unseen-sample-registration vpn`:
  exit 0.
- No model inference, behavioral comparison, generative scoring, or cross-repository comparison was
  run by this resolver.

Next action: complete the existing prerequisite chain, re-audit its evidence, and create a fresh
exact-owner comparison task only if every applicable gate is verified.
