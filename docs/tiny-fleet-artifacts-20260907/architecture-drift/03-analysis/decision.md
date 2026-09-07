# Step-3 decision

Status: **PRELIMINARY — STRUCTURAL ARM PASS; LEXICAL, BEHAVIORAL, AND GENERATIVE ARMS BLOCKED**

The frozen external sample is internally usable for the declared structural summary. The
eight manifest entries were checked against the two pinned Git objects: all blob IDs, byte
counts, and SHA-256 hashes match; the two old-snapshot absences are intentional and match the
manifest. The selected parent-to-child window contains two additions and two modifications,
with the license unchanged.

This is not a publishable cross-repository result. The lexical arm lacks a pinned tokenizer
and concept dictionary. The behavioral arm lacks a clean pinned runtime and paired execution
records. The generative arm lacks prompts, seeds, model/scorer revisions, raw outputs, and
uncertainty data. These states remain `blocked`, never zero or null.

## Exact next action

Provide or generate a protocol-compliant run environment and raw records for the missing
arms, then rerun the analysis against this exact manifest and reject any changed commit or
manifest hash. Do not replace this result with a moving `HEAD` comparison.
