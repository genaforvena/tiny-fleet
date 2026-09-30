# Unblock diagnosis: external sample contract — 2026-09-12

- Task: `unblock/haunt/00559dad400ae1aa/resolve`
- Original task: `tinyfleet-architecture-drift-review-20260907/freeze-independent-repository-sample`
- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Checked: 2026-09-12 03:04 UTC
- Result: **BLOCKED — preregistration scope decision required**

## Evidence checked

1. `docs/cross-repository-drift-protocol.md` (SHA-256
   `f4f9d0c2395bb2a7e20f5cb91cb3a09c9b7babf298c339636ae8d807b8dd016e`) defines protocol v1's
   registered pilot as two local repositories: `tiny-fleet` and `lte-workstation`. Its general
   selection section says at least two materially different repositories.
2. `docs/plans/drift-science-20260908.tsv` (SHA-256
   `d24a46c2ce0a75e142e46eec14a0b93dc67bf6feb3833a766113695d550c2353`) makes D04 depend on a
   frozen sample of at least three independent external repositories.
3. `docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample/sample-manifest.json`
   (SHA-256 `c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`) contains one
   external repository (`lte-workstation`) and two pinned snapshots. Its README says analysis was
   not run. `availability.md` records the clean environments and generative artifacts unavailable.
4. Live `mesh-task status tinyfleet-architecture-drift-review-20260907` confirms the sample step is
   blocked with the three-external-repository retry condition; later analysis and conclusions are
   not started. `tinyfleet-board-dispatch-20260908/tiny-dispatch-selector` remains active and owned
   by `haunt`; its implementation was not changed.

## Disposition

There is no safe factual edit that reconciles these scopes: choosing the two-repository pilot would
waive the active D04 prerequisite, while choosing three external repositories would supersede the
registered pilot. The plan and protocol do not identify which registered scope is authoritative for
the external study, nor do they freeze the additional repository identities, licenses, snapshot
pairs/windows, or inclusion rules. Selecting those after the existing sample was frozen would be a
new preregistration decision, not a mechanical repair. No additional repositories are claimed to be
unavailable; the evidence establishes a contract gap, not an availability failure.

The original `lte-workstation` manifest remains untouched. The unblock task is returned to a typed
dependency block pending an owner-authored scope resolution. Retry by amending and freezing one
consistent protocol/plan scope and its deterministic repository selection before comparative
analysis; then resume the original sample task. B03 remains available to its existing owner.

## Verification

- `mesh-task status tinyfleet-architecture-drift-review-20260907` — exit 0; confirms blocker and
  downstream steps still open.
- `mesh-task status tinyfleet-board-dispatch-20260908` — exit 0; confirms B03 active under haunt.
- `git -C /home/mesh-home/tiny-fleet status --short --branch` — showed pre-existing unrelated dirty
  files before this receipt was written; they are not included in this disposition.

Next action: obtain the protocol owner's scope decision (two-repository pilot or three-external
repository sample), amend and freeze that contract, then resume
`tinyfleet-architecture-drift-review-20260907/freeze-independent-repository-sample`.
