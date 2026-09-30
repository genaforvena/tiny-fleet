# Confirmatory-v1 scorer blocker — 2026-09-14

Task: `tinyfleet-confirmatory-v1-comparison-20260914/execute-confirmatory-v1-generative-matrix`

## State

The complete real-backend generation pass succeeded and validated all 162 registered records.
Raw artifact:
`runs/drift-confirmatory-v1/execution-confirmatory-v1/generative-v2.jsonl`
SHA-256: `b691c04b3a053c0fff8b6aefbc336fd0e61bd01de03453a76415c53e216bab5b`.
All 162 records have `status=ok`, backend `transformers-pinned-v2`, and runtime Python 3.12.3,
PyTorch 2.14.0+cu130, Transformers 4.57.6, device CPU. `validate_v2_records()` returned `ACCEPT`.

The separate deterministic scorer did not produce a score artifact. Its first invocation exited 1
with `ScorerError("adapter_pair_mismatch")` before calling the embedding backend. In
`scripts/drift_score.py:100-101`, `pair_output_records()` requires old/new adapter digests to match.
That is true for `base` and `prompt-only` (both `null`), but is false by design for `lora`: the
frozen generation registration binds a distinct trained adapter for each repository snapshot.
The scorer digest itself matches the frozen registration (`54142ae236a6a55ff4452e360e2c6867e219b356d56f0ff4c589cd6fb8b8e127`); the defect is its pairing contract, and its tests only cover null adapters.

No frozen input or existing scorer was edited, no partial scores were retained, and no embedding
was requested. The registered Ollama runtime/model are available at the registered versions and
digests. The matrix task is typed-blocked as `experiment-contract` and queued on the scorer-amendment
prerequisite.

## Exact retry event

The initial amended scorer failed independent review because it did not bind the imported generation
validator into its code digest, and its task artifacts were not yet committed. The validator binding
has now been added with a mutation regression, and only scoped artifacts will be landed.
First obtain fresh independent PASS on
`tinyfleet-confirmatory-v1-scorer-binding-fix-20260914/review-validator-bound-scorer`. The scorer
must bind the live validator digest to both the amendment and the frozen registration, while
allowing distinct registered LoRA digests for old/new snapshots. Then run
`tinyfleet-confirmatory-v1-scorer-compat-20260914/score-confirmatory-v1-with-amended-scorer` on the
unchanged raw tape in one separate pass and retain the complete score artifact and its hashes.

This amendment is post-generation but pre-score; no generated output text or embedding values were
inspected before defining the correction. Publishability must disclose this deviation and the
independent review result.
