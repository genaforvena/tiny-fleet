# Confirmatory held-out sample freeze — 2026-09-13

Status: **FROZEN, awaiting independent verification; no inference or smoke run.**

Three new public upstreams were selected by a metadata-only, fixed-anchor rule: HTTPX
(`encode`, BSD-3-Clause), attrs (`python-attrs`, MIT), and pytest (`pytest-dev`, MIT). Each
contributes its selected old/new stable release snapshots, for six immutable commits in total.
Exact refs, commit/tree/parent identities, the complete stable-tag inventory, repository metadata,
archive and license hashes, and the selection code are bound by `registration.json`.

Three objective-only interface labels were derived from the pinned source/export diffs and each
new snapshot's own changelog: HTTPX's `proxy` constructor argument, `attrs.NothingType`, and
`pytest.Directory`. The exact evidence paths and hashes are in `labels.jsonl`. No semantic or
behavioral interpretation is registered, and these three positive labels do not establish a
general ground-truth set.

The original v2 registrations and sample remain unchanged and are hash-pinned in the replacement
registration. Source retrieval followed metadata-only selection. The source archives are retained
as read-only tar files. No inference, backend/embedding smoke, scoring, tests, or comparison ran on
these six snapshots. The original comparison matrix remains gated until this sample passes VPN's
independent registration audit and every separate arm gate passes.

Retry/next event: `verify-unseen-sample-registration` independently checks source identity and
license hashes, prior-material disjointness, label chronology, and the no-inference claim. This
artifact does not authorize a comparison.
