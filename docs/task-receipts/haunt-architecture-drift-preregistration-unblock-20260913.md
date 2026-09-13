# Protocol amendment and sample freeze — 2026-09-13

- Owner: haunt
- Repository: `/home/mesh-home/tiny-fleet`
- Result: `unblock=cleared event=protocol-amended`
- Task: `prerequisite/haunt/architecture-drift-preregistration-20260913/amend-protocol-and-freeze-sample`
- Resolver: `unblock/haunt/00559dad400ae1aa/resolve`
- Original task to reopen: `tinyfleet-architecture-drift-review-20260907/freeze-independent-repository-sample`

## Live-state audit

At 2026-09-13 12:46 UTC the exact prerequisite task was open and dispatched to `haunt`. The
resolver was blocked with the exact retry: amend and freeze one consistent protocol/plan scope and
deterministic repository selection before comparison, then resume the original sample task. The
original sample task was blocked; its analysis and downstream conclusions were still open. This
was a live mismatch, not a stale task.

Before editing, the prior resolver receipt
`unblock-haunt-00559dad400ae1aa-resolve-20260912.md` was checked. Its reported source hashes match
the current old protocol (`f4f9d0c2395bb2a7e20f5cb91cb3a09c9b7babf298c339636ae8d807b8dd016e`),
plan (`d24a46c2ce0a75e142e46eec14a0b93dc67bf6feb3833a766113695d550c2353`), and old sample
manifest (`c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`).

## Amendment and freeze

The protocol now distinguishes the historical two-local-repository pilot from the accepted D04
scope of at least three independent external repositories. The D04 plan row names the exact
three-repository freeze and says the local pilot and `lte-workstation` manifest do not count. The
new freeze artifact is
`docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/`:

- `sample-manifest.json` pins `pallets/flask` (BSD-3-Clause), `psf/requests` (Apache-2.0), and
  `pydantic/pydantic` (MIT), all distinct non-fork GitHub upstreams under separate owner namespaces.
- Repository selection is purposive and fixed before comparison. Snapshot selection resolves the
  latest stable semantic-version tag at or before the two fixed anchors, 2023-01-01 and 2025-01-01,
  requires at least 365 elapsed days, and records immutable commits, tag dates, parents, trees,
  license hashes, and canonical Git archive SHA-256 values.
- The inclusion and unit-mapping rules are frozen. No diffs, corpus metrics, tests, labels, model
  outputs, or comparison scores were computed.
- `availability.md` records that all three required repository inputs were acquired and verified.
  Behavioral preflight, generative inputs, and score-blind ground-truth labels are exact downstream
  arm blockers; they do not make the external repository sample unavailable.
- The existing `02-external-sample/sample-manifest.json` remains byte-for-byte unchanged at SHA-256
  `c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`.

The protocol and plan now point to the new freeze. The full new sample manifest is the frozen
selection artifact; this receipt is the artifact-backed unblock evidence. No comparative analysis
has been run.

## Verification

- `mesh-task status prerequisite/haunt/architecture-drift-preregistration-20260913` — confirmed
  open before work; task was taken by haunt.
- `mesh-task status unblock/haunt/00559dad400ae1aa` — confirmed resolver blocked with matching
  retry before work.
- `mesh-task status tinyfleet-architecture-drift-review-20260907` — confirmed original sample
  blocked and later analysis unstarted before work.
- External GitHub API metadata checked for canonical name, `fork=false`, `archived=false`, and
  SPDX license on 2026-09-13; each pinned commit's root license text was independently hashed.
- All six pinned tags matched the latest stable semver-tag selection under both cutoff dates when
  the complete acquired tag set was filtered by the manifest rule. All resolved commits, parent
  IDs, tree IDs, archive byte lengths, archive SHA-256 values, and per-snapshot license hashes
  matched the manifest.
- `python3 -m json.tool docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json`
  — exit 0.
- `git diff --check` scoped to the protocol, plan, new sample freeze, and receipt — exit 0.
- Existing lte-workstation sample manifest SHA-256 after amendment is still
  `c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`; its scoped Git diff is
  empty.
- Amended protocol SHA-256:
  `76b62091b80109bfd8fd0002882b2b297a2fdb0cfff14f7347bbedb529b97466`.
- Amended D04 plan SHA-256:
  `c767991144054e827fd808259cd5a1a3ff550a42867f760be37d434b613504c9`.
- `mesh-task done unblock/haunt/00559dad400ae1aa resolve <this artifact> 'unblock=cleared event=protocol-amended; three independent external repositories frozen with hashes before comparison'`
  — exit 0; exact resolver is complete with this artifact and the required event tokens.
- `mesh-task status tinyfleet-architecture-drift-review-20260907` — confirms the exact
  `freeze-independent-repository-sample` step is reopened and active under haunt; later analysis,
  conclusions, and critical review remain open. No comparison was run.
- `mesh-task status prerequisite/haunt/architecture-drift-preregistration-20260913` reports its
  active row but exits 1 on a pre-existing `KeyError: 'tags'` in the shared status renderer. This
  display defect does not affect the completed resolver transition; the task is closed separately
  below through its exact `done` operation.

Next: the reopened sample owner may proceed only with this committed protocol, plan, and freeze.
Run no comparison until the frozen manifest is consumed exactly; record any future input failure in
that arm's decision artifact and block only that arm.
