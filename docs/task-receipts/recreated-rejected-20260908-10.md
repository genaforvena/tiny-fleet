# Recreated task receipt: install and retry Tiny Fleet

Date: 2026-09-08 UTC  
Task: `recreated-rejected-20260908-10/install-and-retry-tinyfleet`  
Repository: `/home/mesh-home/tiny-fleet`  
Revision tested: `5f830db9eb9eca775cc6601d19470d8318c20780`

## Commands and result

```text
.venv/bin/pip install 'protobuf>=5,<7'
.venv/bin/python -m py_compile scripts/bbywvy_test.py
timeout 240 .venv/bin/python scripts/bbywvy_test.py
```

The install command reported `protobuf 6.33.6` already satisfied. Compilation passed. The
retry loaded the BbyWVY tokenizer and 362M-parameter model on the NVIDIA RTX 3060 CUDA device;
all six identity, quantum-honesty, casual, factual, math, and followup cases returned non-empty
output. The probe exited `0`.

Full captured stdout/stderr, including model output, is in:

`docs/task-receipts/recreated-rejected-20260908-10-20260908T085150Z-retry.txt`

SHA-256: `ecc42de83efb6b35f0b16f77b0e22bfb1fa6019274b31703fe80abd122ce24c5`

## Typed residual block

`BLOCKED_DICTIONARY_INPUT`: no dictionary, lexicon, vocabulary, or token-list artifact is present
for the requested dictionary arm, and no operator-approved source, language, normalization, or
version was supplied. Installing another package would invent the scientific input rather than
retry it. The tokenizer/runtime and generative smoke path are verified; the dictionary arm remains
blocked with its missing input named.

## Environment

Python 3.12.3; protobuf 6.33.6; torch 2.14.0+cu130; transformers 4.57.6; CUDA available;
GPU NVIDIA GeForce RTX 3060.
