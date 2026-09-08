# Tiny Fleet install/unblock receipt

Date: 2026-09-08 UTC  
Repository: `/home/mesh-home/tiny-fleet`  
Source revision before this receipt: `ad42068128c979a60586bf09bdae5c214e21e7d6`

## Live preflight

The assigned chain was still open and its prior lease had expired. The repository venv was
present, but `protobuf` was absent. The first BbyWVY probe failed in `AutoTokenizer` with the
published tokenizer's list-shaped `extra_special_tokens`; after the fallback attempted to decode
the tokenizer metadata, it reported the missing protobuf dependency. The repository had no
dictionary, lexicon, vocab, or token-list artifact outside the model cache.

## Action and versions

Commands actually run:

```text
.venv/bin/pip install 'protobuf>=5,<7'
.venv/bin/python -m py_compile scripts/bbywvy_test.py
timeout 240 .venv/bin/python scripts/bbywvy_test.py
```

Installed/runtime versions:

```text
Python 3.12.3
pip 24.0
accelerate 1.14.0
numpy 2.5.3
peft 0.20.0
protobuf 6.33.6
safetensors 0.8.0
tokenizers 0.22.2
torch 2.14.0
transformers 4.57.6
GPU NVIDIA GeForce RTX 3060, driver 595.84, 12288 MiB
```

`requirements-eval.txt` now records `protobuf>=5,<7` so the repaired path is reproducible.
`scripts/bbywvy_test.py` passes the two published special tokens as the mapping expected by the
current Transformers loader. No model files were edited or replaced.

## Verified result

The repaired command exited `0`: tokenizer loaded, the 362M-parameter BbyWVY model loaded on
CUDA, and all six identity, quantum-honesty, casual, factual, math, and followup cases produced
non-empty output. The durable selected raw output is
`docs/task-receipts/haunt-install-unblock-20260908-generative-output.txt`.

The generative-data blocker is therefore resolved for this six-case smoke probe, but this is not
a publishable training/evaluation bundle: prompts, seed, sampling configuration, model revision,
and scorer are not frozen by the legacy script. The broader generative study remains blocked by
its own contract until that bundle is built.

## Remaining typed block

`BLOCKED_DICTIONARY_INPUT`: no dictionary/lexicon artifact exists in this repository, and no
operator-approved source, language, normalization, version, or corpus was specified. Installing
another package would invent the missing scientific input rather than retry the blocked arm. The
tokenizer is live and independently verified; the dictionary arm remains explicitly blocked.

## Hashes

These hashes are captured after the successful retry:

```text
scripts/bbywvy_test.py: 377521b04612de877b18caf046157d772293e23539f8d11817ee771cad598a8a
requirements-eval.txt: 6686fb131440a3db9a1cbf8bd89efc0dd5ab550fbef144d504a381188d018dcb
docs/task-receipts/haunt-install-unblock-20260908-generative-output.txt: 86ca31e69f15883e1ec36fbdca97c5c1aaf3d822203a47b2b98c7a3a52d550f0
```
