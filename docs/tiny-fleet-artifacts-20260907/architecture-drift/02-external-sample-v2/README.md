# Frozen external-repository sample v2

Status: **frozen before comparison; analysis not run**  
Freeze: 2026-09-13 12:53 UTC  
Study: `tinyfleet-architecture-drift-review-20260907`

This freeze resolves the mismatch between the old two-local-repository pilot in protocol v1 and
the accepted D04 requirement for at least three independent external repositories. The sample is
the three public upstreams in `sample-manifest.json`: Flask, Requests, and Pydantic. Selection is
purposive and fixed, not random; it supports a bounded cross-repository check for these upstreams,
not a population-wide generalization claim.

The sample was acquired from each canonical GitHub HTTPS URL. Stable release tags were resolved to
immutable commit IDs, license evidence was checked at both pinned snapshots, and a canonical Git
archive SHA-256 was calculated for each exact commit. These acquisition and provenance hashes are
in the manifest. The archive hashes cover snapshot contents as serialized by `git archive --format=tar`;
they are not analysis outputs.

The older local-pilot file
`../02-external-sample/sample-manifest.json` remains byte-for-byte unchanged. Its one
`lte-workstation` repository is historical pilot evidence and does not count toward the three
external repositories.

No diffs, corpus metrics, behavioral tests, labels, model outputs, or comparison scores were
computed to create this freeze. Do not start comparison until this artifact and the matching
protocol/plan amendment are reviewed and committed. Use the exact commits and inclusion policy in
the manifest; never replace a pin with `HEAD` or change a pair after seeing results.

