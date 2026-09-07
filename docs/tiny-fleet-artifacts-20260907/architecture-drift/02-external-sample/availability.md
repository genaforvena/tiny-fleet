# Availability and exclusions

The freeze contains provenance and hashes for a bounded text sample. It does not contain
or imply the following unavailable material:

| material | state | consequence |
|---|---|---|
| raw generative outputs, prompts, seeds, model digests, scorer revision | unavailable in the inspected external evidence | generative arm remains blocked |
| a clean environment for both pinned commits | not established by this freeze | behavioral arm is not run here |
| dependency/model/adapter artifacts for cross-repository comparison | unavailable | no fine-tuning or prompt-conditioned result is claimed |
| mesh runtime caches, credentials, secrets, and node-local state | excluded by policy and not redistributed | cannot be treated as repository corpus |
| unchanged repository paths | excluded by the declared changed-path rule | sample is bounded, not a full-repository corpus |

The next analysis step must consume this manifest, refuse moving revisions, and record any
additional unavailable arm as `blocked` rather than zero.

