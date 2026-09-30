# D03 v2 runner provenance (2026-09-13)

Task: `tinyfleet-drift-v2-implementation-20260913/implement-v2-runner-provenance`

Mind: `haunt`

Implementation commit: `d026d51b8ee3faf5741a2a3f9191b62708087bde`

## Change

Added the v2 generation manifest and record contract while keeping the v1 validation and `generate()` path. The v2 contract binds all three repositories' old/new commit IDs, source paths and file hashes, six snapshot excerpts and hashes, the pinned base model revision, prompt template hash, scorer revision and digest, decoding parameters, seeds, and repetition numbers. Each record writes its exact arm-effective input and SHA256, derived generation seed, source provenance, base model revision, the expected per-snapshot LoRA adapter digest, scorer digest, backend/runtime metadata, latency, and raw output or an explicit inference error.

The `TransformersBackend` loads the pinned model revision from local cache only and supports hash-verified PEFT adapters. `FakeBackend` is refused by the v2 generation path before a run directory is created. The external v2 matrix remains blocked because the six LoRA adapters, six source excerpts/hashes, and deterministic scorer implementation/digest have not been prepared. The initial registration file was preserved byte-for-byte; its SHA256 remains `df8c67e0c2f4dd31fc673b8af1438d6c3496f79d90a436521b945a304d44fe02`.

## Verification

- Test-first: the expanded regression suite first failed to import the new v2 API, then passed after implementation.
- `.venv/bin/python scripts/test_drift_generate.py`: exit 0, **6 passed**. Captured output: `runs/drift-generative-v2/runner-implementation/test_drift_generate.log`, SHA256 `53024539b0bd1b5165087aa8fb517600459f0879d4f4d2c025149a5be08c48db`.
- `python3 -m py_compile scripts/drift_generate.py scripts/test_drift_generate.py`: exit 0.
- Real pinned backend smoke: `PYTHONPATH=scripts .venv/bin/python -c 'from drift_generate import TransformersBackend; ...'`, exit 0 using `HuggingFaceTB/SmolLM2-360M-Instruct@a10cc1512eabd3dde888204e902eca88bddb4951`, PyTorch 2.14.0, Transformers 4.57.6, CPU. It generated a nonempty five-character response, which was discarded; no experimental JSONL record or score was written. Summary artifact: `runs/drift-generative-v2/runner-implementation/backend-smoke.json`, SHA256 `b9a8e8b5ea4d4285d314f7cd654effe5c40b25f983f3d58519bb1bca333ec2dc`.
- Source SHA256: `scripts/drift_generate.py` `9385771235998d1ccafd8b5306993a7ccc9d33cf4520d01b40e46d9c8f9e638f`.
- Test SHA256: `scripts/test_drift_generate.py` `9ec1f44d25f8c615289dae4a527f8d4f7ced5e1a32f7c1a07db1634df58dda44`.

This completes runner implementation only. No full 162-record experiment, scoring pass, or cross-repository comparison was run; the earlier analysis task remains gated until the missing registered inputs and D04-V approval are evidenced.
