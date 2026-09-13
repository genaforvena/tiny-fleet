# Independent v2 execution-artifact verification — 2026-09-13

Task: `tinyfleet-drift-v2-implementation-20260913/independently-verify-v2-execution-artifacts`  
Checkout: isolated worktree at current tiny-fleet `master` commit `b933de59c37ec488cc95e9c232e77a27a592e1a0`.

## Verdict

- **PASS — D03 v2 runner contract.** `scripts/drift_generate.py` validates the six immutable source rows, pinned base-model and scorer provenance, prompt digest, schedule, and all three arms. The runner builds and hashes each arm's effective input, writes source/model/adapter/scorer/runtime provenance into records, rejects fixture backends before creating output, and validates the complete matrix before writing. `scripts/test_drift_generate.py`: 6/6 passed.
- **PASS, smoke scope only — real backend provenance.** The tracked `runner-implementation/backend-smoke.json` identifies `transformers-pinned-v2`, base model `HuggingFaceTB/SmolLM2-360M-Instruct` at revision `a10cc1512eabd3dde888204e902eca88bddb4951`, Transformers 4.57.6 and PyTorch 2.14.0, with a nonempty response and no adapter. The implementation loads that immutable revision with `local_files_only=True`; the smoke says its raw response was discarded. This proves a real pinned backend smoke, not a completed v2 matrix.
- **PASS — frozen excerpt bytes and registered hashes.** Recomputed the ledger SHA-256 `ef117c462697932c461645c356302907ad3ab9275d49ab0be5ccf52b358ccba6`; all six excerpt files match both their recorded excerpt digests and the exact excerpt strings in the ledger. All six rows carry the expected immutable source commit, path, and full source-file hash fields. The scorer registration's frozen-registration digest also matches (`df8c67e0c2f4dd31fc673b8af1438d6c3496f79d90a436521b945a304d44fe02`).
- **FAIL — strict pre-inference/blind-order condition.** The excerpt ledger explicitly says `strict blind-order precondition unmet`; D04 objective labels predate excerpt selection and a non-experimental pinned-model smoke preceded selection. The selector did not read labels or scores, but those facts cannot establish strict pre-label/pre-inference ordering retroactively. Accordingly, these excerpts can support implementation audit/exploratory use only; confirmatory use needs a newly frozen unseen sample or explicit independent review. No experimental generation records or scores are registered (`experimental_outputs=none`, `scores=none`).
- **PASS — scorer digest.** Recomputed `scripts/drift_score.py` SHA-256 `54142ae236a6a55ff4452e360e2c6867e219b356d56f0ff4c589cd6fb8b8e127`, matching the scorer registration; registered source commit `6c8cf98adb641086384a344233a466a9e53fb040` exists in this checkout. `scripts/test_drift_score.py`: 7/7 passed.
- **PASS — six adapter provenance chains and hashes.** An independent script checked 96 invariants: six registration/run-manifest digests, base-model and source-snapshot links, training-plan/trainer hashes, corpus manifest/train/validation/inventory/license hashes, adapter tree digests, and every recorded adapter-file digest. All 96 passed. The registered common base is SmolLM2 revision `a10cc1512eabd3dde888204e902eca88bddb4951`; all six runs are `complete` and bind the expected per-snapshot source commit and corpus digests.
- **Current-state confirmation.** At this checkout, `haunt-final-v2-gate-audit-20260913.md` still identifies this exact independent verification step as active and confirms no assembled 162-record manifest or raw output tape exists; it independently records the same ordering limit. Thus the task is not stale and the request matches current code/state.

## Native tests

Ran directly in the isolated checkout with the repository's `unittest` test entry points (the supplied `.venv` and system Python do not have `pytest` installed):

| Suite | Result |
| --- | ---: |
| `scripts/test_drift_generate.py` | 6 passed |
| `scripts/test_drift_score.py` | 7 passed |
| `scripts/test_freeze_drift_excerpts.py` | 2 passed |
| `scripts/test_train_drift_adapters.py` | 3 passed |
| `scripts/test_build_drift_train_corpus.py` | 4 passed |

Total: 22 passed, 0 failed. No implementation artifact was edited and no model generation was run during this audit. The original `/home/mesh-home/tiny-fleet` checkout was not modified.

## Next constraint

Keep the present sample limited to implementation audit/exploratory interpretation. Before confirmatory execution or claims, freeze a new unseen sample before any model inference, or obtain explicit independent review of the blind-order limitation.
