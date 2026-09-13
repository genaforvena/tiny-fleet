# Haunt receipt: unseen confirmatory sample frozen — 2026-09-13

Task: `tinyfleet-drift-confirmatory-prerequisites-20260913/freeze-unseen-confirmatory-sample`
Repository: `/home/mesh-home/tiny-fleet`
Result: **DONE — sample and objective-only labels frozen before inference or smoke; no blocker.**

## Live task and gate audit

Before taking the task, `mesh-task status tinyfleet-drift-confirmatory-prerequisites-20260913`
reported this exact first step open under `haunt`; the owner queue also showed it as open. It was
not stale or already resolved. The instruction matches the current gate: the previous D04 labels
(`runs/drift-validation-v2/labels.jsonl`) and a generic backend smoke predated the earlier
`runs/drift-generative-v2/heldout-excerpts/heldout-excerpts.json` selection. The existing sample is
therefore limited to exploratory/implementation-audit use, as stated by the current scorer receipt
and the resolver receipt. A new material set and labels must precede any future inference/smoke.

## Frozen replacement

`runs/drift-confirmatory-v1/registration.json` registers three distinct new upstream repositories
and six immutable snapshot archives:

| Repository | License | Old tag | New tag | Days |
| --- | --- | --- | --- | ---: |
| `encode/httpx` | BSD-3-Clause | `0.23.1` | `0.28.1` | 749 |
| `python-attrs/attrs` | MIT | `22.2.0` | `24.3.0` | 725 |
| `pytest-dev/pytest` | MIT | `7.2.0` | `8.3.4` | 769 |

The full commit, tree, parent, stable-tag inventory, source URL, canonical-owner metadata, archive
byte length and SHA-256 values are in `selection.json` and `registration.json`. The selection code
is `scripts/select_drift_confirmatory_snapshots.py` (SHA-256
`b8b286e3e47ab0dcad2130afcc8f77f85889693c055b31303222bbf0dad7a3d6`). Selection uses only stable
semantic-version tag and commit-time metadata at fixed 2023-01-01/2025-01-01 anchors, with a
365-day minimum. The three owner namespaces are distinct and the repositories differ from the prior
three-repository v2 sample and its training corpora.

The objective-only label ledger (`labels.jsonl`) has SHA-256
`8bbb3047ebe375d5d0077e563b72d6d74578dfb21e1805fb6df1865038aeb5db`. It registers exactly three
narrow `interface_change` labels, each tied to pinned old/new source/export files and a new-snapshot
changelog entry: `httpx.Client`/`AsyncClient`'s `proxy` constructor argument, `attrs.NothingType`,
and `pytest.Directory`. The source, public-export, test-source and release-note hashes are in the
ledger. These labels make no semantic-generalization claim and are not behavioral ground truth.

`access-chronology.jsonl` records metadata-only selection before source retrieval; the six archive
mtimes run from `2026-09-13T16:13:17.701101583Z` through
`2026-09-13T16:13:20.425074492Z`. The objective evidence was read and hashed only after the source
archives existed; labels were written at `2026-09-13T16:21:10.340416389Z`, and the registration
sealed the freeze at `2026-09-13T16:22:29.895937448Z`. No inference, backend/embedding smoke,
scorer, test run, or comparison was performed on these six snapshots.

The existing v2 validation registration, generation registration, held-out excerpt ledger, and
v2 external manifest remain byte-for-byte unchanged; their recorded hashes were recomputed and
match. The freeze verifier is `scripts/verify_drift_confirmatory_freeze.py`.

## Verification and next action

- `python3 -m json.tool runs/drift-confirmatory-v1/registration.json` — PASS.
- JSONL parsing for three label rows and eight chronology records — PASS.
- `python3 scripts/verify_drift_confirmatory_freeze.py` — PASS; verified all six archive bytes and
  hashes, license copies against archive contents, source/release/test hashes, selection/code
  digests, three labels, and all four preserved prior-registration hashes.
- No blocker was needed because all three pinned public repositories, licenses, and objective label
  evidence were available.

Next: `verify-unseen-sample-registration` (owner `vpn`) independently checks source/license
provenance, disjointness, label chronology and the no-inference claim. The behavioral preflight and
all other comparison gates remain separate; this freeze does not authorize the matrix.
