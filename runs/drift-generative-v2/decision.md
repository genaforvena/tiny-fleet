# External-snapshot generative arm — registration status

Status: **BLOCKED BEFORE EXPERIMENTAL MATRIX**.

The frozen initial registration in `registration.json` records the sample, base model revision,
prompt template, decoding, seed schedule, and candidate embedding model. Its SHA256 remains
unchanged. The versioned D03 v2 runner contract is now implemented in `scripts/drift_generate.py`;
see `docs/drift-generative-v2-runner-contract.md`. A local-only Transformers backend produced a
nonempty implementation smoke response at the registered immutable SmolLM2 revision. This was
not stored as an experimental record, was not scored, and is not evidence about repository drift.

Six held-out excerpts are frozen with exact source-commit, source-file, excerpt, and license hashes
in `heldout-excerpts/heldout-excerpts.json`. The selector chose a common package-native module per
repository by a deterministic hash ranking and retained the first 80 source lines. The versioned
scorer is registered separately in `execution-scorer.json`; it checks Ollama 0.33.2 and the exact
all-minilm model digest, then scores only complete old/new pairs. The original registration remains
byte-for-byte unchanged. Existing unrelated LoRA adapters remain excluded.

The experimental matrix is still blocked because six per-snapshot LoRA adapters are not trained.
There is also a temporal limitation: score-blind D04 objective labels had already been frozen and
a generic non-experimental model smoke had already run before excerpt selection. The selector did
not access either artifact, but this cannot satisfy strict blind ordering. Treat any use of this
sample as implementation audit or exploratory analysis only; confirmatory use requires a newly
frozen unseen sample or explicit independent review.

After all six adapters and their tree digests have artifacts, create the complete v2 manifest, run
the 162-record paired matrix, retain its raw tape and separate score artifact, and have D04-V
independently verify the labels. Until then there is no experimental comparison result and the
original analysis stays blocked.
