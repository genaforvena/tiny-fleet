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

Six per-snapshot LoRA adapters have now been trained from the frozen license-filtered corpora and
registered in `adapter-registration.json` (SHA256
`3896fd9fd5df55775caf37fc6432d420ce97658967a8b7a3cce42b2c97671db7`). Each adapter tree and
training-run manifest digest was recomputed; all six runs completed on the pinned base revision,
and all six file-disjoint adaptation validation losses decreased. These validation metrics are
training diagnostics, not evidence about external semantic truth.

The independent D04-V review passes only for the three source-backed objective interface labels;
it does not establish semantic ground truth, behavioral outcomes, or blinded access history. The
behavioral preflight has only two passing snapshot suites; four arms remain blocked. The exact v2
execution artifacts are still under independent verification, and no complete 162-record manifest
or raw output tape exists. In addition, score-blind D04 labels and a generic non-experimental model
smoke preceded excerpt selection. The selector did not access either artifact, but this cannot
satisfy strict blind ordering. Treat any use of this sample as implementation audit or exploratory
analysis only; confirmatory use requires a newly frozen unseen sample or independent review that
explicitly covers the ordering limitation.

After the behavioral blockers are resolved, exact v2 execution-artifact verification passes, and
the blind-order limitation has a valid disposition, complete the registered v2 manifest and run
the 162-record paired matrix; retain its raw tape and separate score artifact. Until these exact
gates pass, there is no experimental comparison result and the original analysis stays blocked.
