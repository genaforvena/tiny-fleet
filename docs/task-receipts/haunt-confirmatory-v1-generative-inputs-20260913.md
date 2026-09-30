# Confirmatory-v1 generative input registration — 2026-09-13

Task: `tinyfleet-confirmatory-v1-arm-gates-20260913/register-confirmatory-generative-inputs`

Result: **PARTIAL FREEZE; generative gate BLOCKED before generation.** The exact sample-bound
excerpt ledger, prompt contract, 162-record arm schedule, base-model revision, scorer code revision,
and runner revision are frozen. The six confirmatory training corpora and LoRA adapters do not
exist, so the runner is not eligible to execute. `comparison_authorized` remains false.

## Frozen inputs

- Sample registration: `runs/drift-confirmatory-v1/registration.json`, SHA-256
  `f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`.
- Objective-only labels: `runs/drift-confirmatory-v1/labels.jsonl`, SHA-256
  `8bbb3047ebe375d5d0077e563b72d6d74578dfb21e1805fb6df1865038aeb5db`; three public-interface
  labels only. The selector verified this digest but did not read label contents.
- Six held-out excerpts: `runs/drift-confirmatory-v1/heldout-excerpts/heldout-excerpts.json`,
  SHA-256 `d37c62534a429d7659b78d44f4f7bc2e6ca2d56ee14a1eb101b81e00d245c83a`. The deterministic
  selector chooses the common native Python module minimizing SHA-256 of repository ID, NUL, and
  normalized path, then freezes its first 80 lines from each exact old/new archive. The six excerpt
  files and source-file digests are individually bound in the ledger.
- Generation registration: `runs/drift-confirmatory-v1/generative-registration.json`, SHA-256
  `c5588407a51fc825c2a38bbedb0bc86afb964285e5af39a4b6f43b59969cbcde`. It pins
  `HuggingFaceTB/SmolLM2-360M-Instruct@a10cc1512eabd3dde888204e902eca88bddb4951`, arms `base`,
  `prompt-only`, and `lora`, temperature 0.7, top-p 0.9, 128 new tokens, seeds 17/29/43, and
  repetitions 0/1/2 (162 records).
- Scorer: `scripts/drift_score.py` at checkout `2a9f04f44742fffd2b68b6196b10783b77c9a1c6`,
  source SHA-256 `54142ae236a6a55ff4452e360e2c6867e219b356d56f0ff4c589cd6fb8b8e127`; registered
  embedding model `all-minilm:latest` digest
  `1b226e2802dbb772b5fc32a58f103ca1804ef7501331012de126ab22f67475ef`. Embedding similarity is
  not semantic ground truth.
- Runner: `scripts/drift_generate.py` at checkout `2a9f04f44742fffd2b68b6196b10783b77c9a1c6`,
  source SHA-256 `adc416a6e5d47b464c82b13d07b1cfffd0cd5e03c6a45a9f7772e51cfe4632c7`.

## Exact blockers

1. No confirmatory-v1 license-filtered corpora, inventories, corpus manifests, or training plan are
   present. The existing corpus builder and training plan bind to the disjoint Flask/Requests/
   Pydantic v2 sample and cannot serve as confirmatory-v1 provenance. Retry after a builder emits
   six inventories, six corpus manifests, train/validation hashes, and a plan bound to the six
   registered archives and this excerpt ledger.
2. No adapter was trained for any of the six confirmatory snapshots. V2 adapter artifacts name
   different commits and are ineligible. Retry after those corpora are frozen and a separate
   training task registers each adapter tree digest and run manifest.
3. The pinned runner requires every prompt row to carry a non-empty adapter path and 64-hex digest.
   This registration leaves those values null, so the runner must reject it before generation.
4. Excerpt selection happened after the objective-only label freeze. The selector is deterministic
   and label-content-blind, but this is not a pre-label freeze. The independent gate audit must
   accept this chronology for the narrow objective-only study or require a new unseen sample.

## Verification

- `scripts/freeze_confirmatory_v1_excerpts.py` generated six excerpts after checking registration,
  label-ledger, and all six archive hashes.
- JSON parsing passed for both registrations and the excerpt ledger.
- An offline binding check verified registration and label hashes, all six source-file and excerpt
  hashes against the frozen archives, two snapshot prompts per repository, the 162-record schedule,
  and null adapter digests.
- No inference, model/backend smoke, scoring, or comparison was run.

Next: `vpn` independently audits the exact hashes, blockers, label scope, chronology, and
no-inference claim. Keep the original final confirmatory gate audit closed unless that task reports
an exact `PASS`.
