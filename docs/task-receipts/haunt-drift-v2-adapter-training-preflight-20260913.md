# Haunt receipt: v2 adapter training preflight

Task: `tinyfleet-drift-v2-implementation-20260913/train-six-v2-snapshot-adapters`.  
Frozen corpus/code commit: `d7b4558b7ac85a1134849b7e2fe7e8fa3740cae2`; stale TSV cleanup: `ddd5f713dd8d2c13f01214bc33a927b97def495c`.

The six source-only training/validation corpora and complete tracked-file inventories are in
`runs/drift-generative-v2/training-corpora/`. They are bound to the three-repository sample manifest
(`07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59`) and the six-excerpt ledger
(`ef117c462697932c461645c356302907ad3ab9275d49ab0be5ccf52b358ccba6`). The selected held-out
module is excluded from its matching snapshot corpus; tests, generated/vendor trees, non-Python
files, malformed/binary data, non-regular objects, and explicit nonmatching SPDX files are excluded.
The verified root license text is retained per snapshot. Inventory rows record each tracked path,
Git object ID, byte length, SHA256, inclusion status, and reason. Totals: 205 included Python files
and 1,326 excluded tracked files.

The pinned plan is `training-plan.json`, SHA256
`e82978c938be4c51ed8924e18ee1fcc45a51558cecd88cd1e6319c2670ae5c39`. It selects the frozen
SmolLM2-360M-Instruct revision, seed 17, one pass, up to 16,384 training tokens and 4,096
file-disjoint validation tokens per adapter, 256-token windows, batch one with four-step gradient
accumulation, AdamW at 2e-4, and rank-8/alpha-16 LoRA over the registered attention and MLP
projections. The plan pins the corpus builder, training runner, sample, excerpt ledger, and scorer
registration digests. Source inventory/corpus tests passed 4/4; deterministic training helper tests
passed 3/3; the six exact corpus/hash/tokenizer preflights passed. Requests/old has 2,309 available
validation tokens; its smaller validation set is preserved without padding or substitution.

Current resource reading at 2026-09-13T15:22:56Z: RTX 3060 12,288 MiB, 784 MiB free, no existing
GPU lease, and all three lease-managed services active (`mesh-voice-clone`, `mesh-room-gigaam`,
`ollama`). MemAvailable was 14,980 MiB and SwapFree 6,279 MiB. Training runs one snapshot at a
time through `mesh-heavy-run` with an 8,192 MiB RAM ceiling, an 8,192 MiB minimum free VRAM, GPU
preemption enabled, and a 1,800-second lease. The lease captures prior service states, stops only
its allowlisted services, and restores those states on exit; the runner records pre-run, in-run,
and post-run lease/service state and refuses to count a run unless the exact original state returns.
If admission cannot be obtained, the run remains queued with its plan and is not replaced by CPU
training.

No adapter has been trained yet. The original registration remains unchanged. This remains
implementation/exploratory work because the earlier objective labels and generic model smoke
preceded held-out selection; confirmatory use still needs a new unseen sample or independent review.

Next action: execute
`rtk proxy .venv/bin/python scripts/train_drift_adapters.py --all --plan runs/drift-generative-v2/training-corpora/training-plan.json`
from `/home/mesh-home/tiny-fleet`, then verify each adapter tree digest and post-lease restoration.
