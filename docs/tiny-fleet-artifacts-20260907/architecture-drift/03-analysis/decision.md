# Step-3 decision

Status: **PRELIMINARY — STRUCTURAL AND PAIRED BOUNDED BEHAVIORAL SMOKE PASS; LEXICAL AND GENERATIVE GATES BLOCKED**

The frozen external sample is internally usable for the declared structural summary. The
eight manifest entries were checked against the two pinned Git objects: all blob IDs, byte
counts, and SHA-256 hashes match; the two old-snapshot absences are intentional and match the
manifest. The selected parent-to-child window contains two additions and two modifications,
with the license unchanged. Both immutable archives also pass the same
`scripts/mesh-task --test` smoke test; command, exit code, duration, stdout/stderr
hashes, runtime metadata, and per-snapshot outputs are retained in this directory.

This is not a publishable cross-repository result. The lexical arm lacks a pinned tokenizer
and concept dictionary. The old snapshot has no `scripts/test-mesh-board`, so the preregistered
comparable replacement `scripts/uxn/test-board-check` was run from both immutable archives in
the separately pinned runtime recorded in `runtime-lock.json`; both passed with exit 0. This is
bounded common-component smoke evidence, not a semantic drift finding.
The generative arm lacks prompts, seeds, model/scorer revisions, raw outputs, and uncertainty
data. These states remain `blocked`, never zero or null.

## Exact next action

The runtime and comparable board test are now supplied. Supply the missing lexical/generative
inputs before any publishable conclusion; retain this exact manifest and reject any changed
commit or manifest hash. Do not replace this result with a moving `HEAD` comparison.
