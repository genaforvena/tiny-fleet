# Confirmatory-v1 corpus and adapter preflight

Task: `tinyfleet-confirmatory-v1-gate-closure-20260913/complete-sample-bound-corpora-and-adapters`

**Completed for all six registered snapshots.** Six source inventories, license-filtered train/validation corpora, corpus manifests, a sample-bound training plan, six trained LoRA adapters, and a sample-bound adapter registration are retained under `runs/drift-confirmatory-v1/`. The exact sample registration and held-out excerpt ledger hashes are carried through the artifacts. The behavioral gate remains blocked by the separate HTTPX-new Trio timeout warning; generation, scoring, and comparison remain closed.

## Frozen inputs and plan

- Sample registration: `runs/drift-confirmatory-v1/registration.json`, SHA-256 `f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`.
- Held-out excerpt ledger: `runs/drift-confirmatory-v1/heldout-excerpts/heldout-excerpts.json`, SHA-256 `d37c62534a429d7659b78d44f4f7bc2e6ca2d56ee14a1eb101b81e00d245c83a`.
- Builder: `scripts/build_drift_confirmatory_corpus.py`; training uses the sample-aware branch in `scripts/train_drift_adapters.py`.
- Training plan: `runs/drift-confirmatory-v1/training-corpora/training-plan.json`, SHA-256 `6d256ef9cf0c67f76e0898ef7d557062559fd129e52decbf8f65a1c8a68b693d`.
- Resource/run preflight: `runs/drift-confirmatory-v1/training-corpora/resource-preflight.json`, SHA-256 `6e07c13e696485a2fc157de7c50b68086e0d073b5682ebda70bb37d8ab9b9881`.
- Adapter registration: `runs/drift-confirmatory-v1/adapter-registration.json`, SHA-256 `aca4c62e360b92d27223707f86a340d471113bcfb9042658426e121be47cfc6a`.
- Training progress: `runs/drift-confirmatory-v1/training-runs/training-progress.json`, SHA-256 `8bc568f2d69515d6b7ea13c72beb7c85a78de42c028281949b9dc4419442c58b`.

Each `training-corpora/<repo>-<snapshot>/manifest.json` binds the source archive digest and commit, exact sample registration, held-out ledger, excluded source module, complete inventory hash, and train/validation hashes. The six excerpt source modules are excluded from both splits. File-disjoint train and validation splits were independently checked when loading the plan for training.

| Snapshot | Train rows | Validation rows | Adapter-tree SHA-256 |
|---|---:|---:|---|
| attrs-old | 10 | 2 | `c180cd1efcf012d91057c76d1dea5c0635ecab0a966b33831fc118ad3977090d` |
| attrs-new | 10 | 2 | `bb47fd26c057d345ff82009e2d6603a7a16e938956ce767ca7146352f71404de` |
| httpx-old | 19 | 3 | `6edc191006c7b51366ab3af95f09d1797d3b557d91e6ef481e68861fb0fab052` |
| httpx-new | 19 | 3 | `38bccff100199c2e92aae4f2fe907bf52a63bb41826ea8395f67f1f9030d3778` |
| pytest-old | 59 | 7 | `640881b4de8a24b60a4b6fe0e73a367513a5ef791acd9783032ee526303ea089` |
| pytest-new | 59 | 7 | `8c3d48d75ffd8760877c3b235801f991ac74b573f7ff4995f42e2a0030d287c9` |

## Runtime and resource evidence

Training used the already-installed `/home/mesh-home/.venv-ai` environment: Python 3.12.3, PyTorch 2.13.0+cu130, Transformers 5.14.1, PEFT 0.19.1, safetensors 0.8.0, CUDA 13.0, RTX 3060. No package installation was performed. The first system-Python attempt failed before model load because that interpreter had no `torch`; its run record and wrapper logs are preserved in `training-runs/attempt-system-python-attrs-new/`.

The resource guard initially observed 424 MiB free VRAM against the 8192 MiB admission threshold. `mesh-heavy-run` preempted only its declared managed GPU services, admitted runs at 11,911 MiB or greater, and released each lease afterward. All six completed run records report successful restoration to the exact initially active service set: voice clone, room gigaam, and Ollama. The resource measurements, run hashes, and per-run restoration checks are in `resource-preflight.json` and `training-runs/<repo>-<snapshot>/run.json`.

## Verification and boundary

Verified all six corpus manifests, plan hashes, held-out exclusions, file-disjoint splits, run-to-corpus bindings, adapter-tree digests, adapter-registration links, and successful resource restoration. Focused tests passed:

```text
PYTHONPATH=scripts python3 scripts/test_build_drift_confirmatory_corpus.py
PYTHONPATH=scripts python3 scripts/test_train_drift_adapters.py
python3 -m py_compile scripts/build_drift_confirmatory_corpus.py scripts/train_drift_adapters.py
```

The generation registration remains `blocked-before-generation`. No generation runner, scorer, label analysis, or snapshot comparison ran. The independent verifier still needs to check both this artifact set and the blocked behavioral preflight before it reports the combined gate result.
