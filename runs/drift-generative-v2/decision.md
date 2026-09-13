# External-snapshot generative arm — registration status

Status: **BLOCKED BEFORE EXPERIMENTAL MATRIX**.

The frozen initial registration in `registration.json` records the sample, base model revision,
prompt template, decoding, seed schedule, and candidate embedding model. Its SHA256 remains
unchanged. The versioned D03 v2 runner contract is now implemented in `scripts/drift_generate.py`;
see `docs/drift-generative-v2-runner-contract.md`. A local-only Transformers backend produced a
nonempty implementation smoke response at the registered immutable SmolLM2 revision. This was
not stored as an experimental record, was not scored, and is not evidence about repository drift.

The experimental matrix remains blocked: six per-snapshot LoRA adapters are not trained, six
held-out excerpts and source-file hashes are not frozen, and deterministic scorer code/revision/
digest are absent. The committed registration remains the preregistration record; this decision
file describes the implementation progress without editing its frozen contents. Existing unrelated
LoRA adapters remain excluded.

After those three inputs have artifacts, create the complete v2 manifest, run the 162-record paired
matrix, retain its raw tape and separate score artifact, and have D04-V independently verify the
labels. Until then there is no experimental comparison result and the original analysis stays
blocked.
