# Haunt receipt: freeze v2 held-out excerpts and scorer

Task: `tinyfleet-drift-v2-implementation-20260913/freeze-v2-heldout-and-scorer`  
Code and excerpt commit: `6c8cf98adb641086384a344233a466a9e53fb040`.

Frozen six source excerpts from the registered Flask, Requests, and Pydantic old/new commits in
`runs/drift-generative-v2/heldout-excerpts/heldout-excerpts.json`. The deterministic source-only
selector hashes common native module paths, excludes test trees, retains the first 80 source lines,
and records source commit/path/file hashes, excerpt hashes, and the matching license text hashes.
Selected paths are Flask `cli.py`, Requests `structures.py`, and Pydantic `config.py` at each
snapshot. The ledger SHA256 is
`ef117c462697932c461645c356302907ad3ab9275d49ab0be5ccf52b358ccba6`.

The versioned scorer is `scripts/drift_score.py`, SHA256
`54142ae236a6a55ff4452e360e2c6867e219b356d56f0ff4c589cd6fb8b8e127`, registered at the code
commit above in `runs/drift-generative-v2/execution-scorer.json`. It verifies Ollama 0.33.2 and
the exact `all-minilm:latest` digest before embedding, requires 384-dimensional finite vectors,
uses deterministic `math.fsum` cosine calculation, and refuses incomplete/error pairs. It retains
raw input file and per-output hashes in an eventual score artifact and states that embedding
similarity is not semantic ground truth. `embedding-backend-smoke.json` records the generic
one-vector endpoint smoke; neither vector nor score was retained.

The original frozen `registration.json` remains byte-for-byte unchanged at SHA256
`df8c67e0c2f4dd31fc673b8af1438d6c3496f79d90a436521b945a304d44fe02`.

Temporal limitation: D04 score-blind objective labels were frozen before this selection task was
dispatched, and an earlier generic non-experimental model smoke also preceded excerpt selection.
The selector did not open labels or scores, but it cannot establish strict pre-label/pre-inference
ordering retroactively. This ledger is for implementation audit or exploratory analysis; a
confirmatory use requires a newly frozen unseen sample or explicit independent review. No
experimental matrix, output, or score was produced. Six per-snapshot LoRA adapters remain missing.

Verification:

- `scripts/test_freeze_drift_excerpts.py`: 2 passed.
- `scripts/test_drift_score.py`: 7 passed.
- `scripts/test_drift_generate.py`: 6 passed, including source-path conditioning and v2 provenance.
- Local Ollama 0.33.2 / registered all-minilm digest smoke: one generic 384-dimensional embedding;
  vector discarded.
- Re-ran excerpt freezing from the exact sample manifest and bare source repositories; all six
  source/license checks passed and the ledger hash remained stable.

Next gate: train and hash the six snapshot-specific adapters. Before any confirmatory interpretation,
resolve the temporal blind-order limitation with a newly frozen unseen sample or independent review.
