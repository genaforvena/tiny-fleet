# Unblock resolver — current D04 comparison gates

- Resolver: `unblock/haunt/df95bf7b4125c078/resolve`
- Parent history: `tinyfleet-architecture-drift-review-20260907/run-cross-repository-analysis` (rejected)
- Repository: `/home/mesh-home/tiny-fleet`
- Audited source revision: `7001b53bc0f12b8f1f3f6495cd2b983aa152cb3a`
- Result: **still gated; the old rejection's explanation is stale in detail, but the comparison remains ineligible**.

## Live evidence

The current v2 work supersedes several particulars in the rejection text. Separate artifacts now
exist for all six held-out excerpts, the scorer, six trained adapters, and an objective-only D04
label subset. Their current hashes are:

| Artifact | SHA-256 |
|---|---|
| `runs/drift-generative-v2/heldout-excerpts/heldout-excerpts.json` | `ef117c462697932c461645c356302907ad3ab9275d49ab0be5ccf52b358ccba6` |
| `runs/drift-generative-v2/execution-scorer.json` | `d914993163725123e76b09c30d78c534dfdd75cdca33c1e4f5e5eeb9f5013027` |
| `runs/drift-generative-v2/adapter-registration.json` | `3896fd9fd5df55775caf37fc6432d420ce97658967a8b7a3cce42b2c97671db7` |
| `runs/drift-validation-v2/labels.jsonl` | `51c2c0cb4c1976c4e5a4e013bb28d0d2e5b1e9cef8bf8be5e7693c40189a7b72` |
| VPN independent v2 execution-artifact receipt | `9103a5a38fca67b60320e886601636314e71744cd76be7d418759ebd11dcd60f` |
| Behavioral preflight receipt | `59621df0c3c221fa6478c8741f9e8779f0c5394988e822f3ef1bcf1dea039ded` |

The independent receipt reports 96 adapter/provenance checks and 22 native tests passing, but its
overall gate result is **FAIL**: the frozen excerpt ledger says strict blind-order was unmet because
objective labels and a generic model smoke predated excerpt selection. It explicitly limits these
excerpts to implementation audit/exploratory use. No experimental outputs or scores are registered.
The original frozen `registration.json` remains unchanged and is not the complete v2 execution
manifest.

The D04-V receipt verifies three source-backed public-interface labels only. It records zero
semantic units reviewed, no semantic generalization, and no behavioral or dependency labels. It
does not repair the ordering failure or authorize semantic claims.

The behavioral preflight remains two passing suites and four blocked arms: Flask old and Pydantic
old fail collection under Python 3.12 warning-as-error behavior; Requests old has two TLS fixture
failures from removed `ssl.wrap_socket`; Requests new has one mTLS failure from an expired fixture
certificate. On this node only Python 3.12 is installed; Docker is available but has only `alpine`
cached. No compatible historical runtime or replacement fixture evidence is present. The exact
retry event is a source-pinned compatible runtime or a separately reviewed harness overlay that
leaves snapshot sources and assertions unchanged, with complete paired logs and dependency/image
digests.

## Decision and coordination

The live `execute-v2-generative-matrix` task says execution follows a passing independent audit.
That audit failed the strict ordering predicate, so running it now would contradict its own
precondition. The six-excerpt sample and labels must be replaced by a new score-blind, unseen sample
with labels frozen before any inference or smoke. The behavioral arms also need their exact runtime
or fixture retry event. No structural, lexical, behavioral, generative, scoring, or cross-repository
comparison was run here.

Created `tinyfleet-drift-confirmatory-prerequisites-20260913` with this ordered path:

1. Haunt freezes the replacement unseen sample and objective labels before inference.
2. VPN independently verifies source/license provenance, disjointness, chronology, hashes, and the
   no-inference claim.
3. Haunt resolves the four behavioral arms or records their exact typed external blocker.
4. VPN independently verifies the paired outcomes and provenance.
5. Haunt performs a final gate audit. Only a fully passing audit may create a fresh exact-owner
   comparison task linked to the rejected history and gate hashes. Otherwise this final step stays
   typed-blocked with the missing datum and retry event.

The currently open v2 matrix task is now blocked on
`tinyfleet-drift-confirmatory-prerequisites-20260913/final-gate-audit-and-fresh-task`; it must not
run against the audit-only sample. The original rejected analysis remains rejected and was not
recovered. The earlier resolver receipt `unblock-haunt-bdf0bd563436ad74-resolve-20260913-r2.md`
correctly prevented a comparison at that time, but its gate snapshot predates VPN's completed
independent verification and the subsequent live matrix task.

## Verification and next action

- Recomputed hashes for the behavioral receipt, objective-label receipt, VPN independent receipt,
  excerpt ledger, scorer registration, adapter registration, and labels; all match this record.
- Read the current task-ledger states: the original analysis remains rejected; the v2 implementation
  chain has reached its matrix step; the new prerequisite chain is open at its first Haunt step.
- No model inference, scorer invocation, or comparison command was run.

Next: take `tinyfleet-drift-confirmatory-prerequisites-20260913/freeze-unseen-confirmatory-sample`.
Retry the original comparison only by creating a fresh exact-owner task after the final audit proves
all gates; do not use `mesh-task recover` on the rejected step.
