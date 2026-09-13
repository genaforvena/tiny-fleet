# Frozen-input availability — 2026-09-13

## Repository inputs

All three required public external repositories were reachable over HTTPS and their pinned Git
objects were acquired into a temporary bare Git database before freeze. All six tag-to-commit
resolutions, root license texts, parent IDs, tree IDs, and canonical archive hashes were verified.
The exact identities, pairs, and hashes are in `sample-manifest.json`. No required external
repository input is missing.

The original local `lte-workstation` pilot manifest remains unchanged at
`../02-external-sample/sample-manifest.json` (SHA-256 recorded in the new manifest).

## Inputs not acquired for the comparison arms

These are exact arm-level blockers, not missing repository inputs. No comparison was run.

| arm/input | state | exact missing event | consequence |
|---|---|---|---|
| Behavioral | blocked / not preflighted | No clean pinned environment run receipt exists for both commits of each of the three repositories. | Do not score an empty test result; run a paired environment preflight before the behavioral arm. |
| Generative | blocked / not registered | No frozen prompt matrix, model digest, adapter digest, scorer revision, seed/repetition schedule, or raw paired-output tape exists for these six repository snapshots. | No generative comparison or generative claim. |
| Ground-truth validation | not started | No preregistered label ledger for the frozen sample has been created. | D04 remains downstream; labels must be frozen without access to model scores. |

No unavailable external repository, repository license, pinned tag, or pinned Git object is being
used to justify a zero. If a future acquisition fails, record the exact URL, commit/ref, command,
timestamp, and failure output hash in that run's decision artifact, then block only the affected
arm.

