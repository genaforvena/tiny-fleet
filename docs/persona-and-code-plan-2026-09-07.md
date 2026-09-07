# Persona and code specialists — measurement and implementation plan

Task: `tinyfleet-specialists/persona-and-code-plan`
Owner: `genome`
Date: 2026-09-07
Status: `PLAN_READY`

## Scope

Build and evaluate two separate LoRA specialists from the shared
`HuggingFaceTB/SmolLM2-360M-Instruct` base:

1. `persona`: operator style, language, preferences, and mesh vocabulary.
2. `code`: repository conventions, shell/Python patterns, and mesh-tool
   operational knowledge.

The specialists remain separate. No raw private message, voice recording, or
machine-local path is copied into this repository.

## Corpus measurement before training

Measured on 2026-09-07 from node-local inputs, before any new training run:

| input | rows | text chars | bytes | SHA-256 | use |
|---|---:|---:|---:|---|---|
| `~/.mesh/tg-corpus.jsonl` | 815 | 343,321 | 606,559 | `a40fd2d11ade5a09e799bdf4c03590362436782ba48ff5f1a6347ddf1881ba35` | persona candidate source |
| `~/.mesh/operator-field.jsonl` | 4,589 | 0 | 4,156,626 | `f59d555a536106514d71e598fbab8fbadc58a5a6e9c919808c09ba05424e1f3a` | metadata/context only; not language training text |

The Telegram corpus contains 679 `out=false` and 136 `out=true` records,
spanning `2026-08-20T19:00:51Z` through `2026-08-25T10:49:08Z`. This is a
measurement, not permission to publish it: the raw file stays node-local.
The checked-in persona corpus must be redacted/derived JSONL with provenance,
and must exclude secrets, credentials, personal third-party data, and raw
audio. Voice material is an optional future transcription input and is not
part of this run.

The code candidate snapshot was measured from the lte-workstation tracked
`docs/`, `scripts/`, and `tests/` trees: 1,402 files / 29,392,133 bytes,
tree digest
`43279a0550a4a98748360b81476b105c1df78750fabb574439f24828c1f1e15a`. It is
an input reference only; code training examples must be copied into this repo
as license-labelled, immutable, redacted examples or generated from a pinned
snapshot by a reproducible script.

## Corpus construction and splits

Create these checked-in artifacts, with a manifest recording source digest,
generator commit, counts, and split rules:

- `corpus/persona-train.jsonl`
- `corpus/persona-heldout.jsonl`
- `corpus/persona-adversarial.jsonl`
- `corpus/code-train.jsonl`
- `corpus/code-heldout.jsonl`
- `corpus/code-adversarial.jsonl`
- `corpus/persona-code-manifest.json`

Persona examples should preserve the operator's observable style without
memorizing incidents: Russian/English mix, terse imperatives, evidence-first
claims, explicit uncertainty, and mesh vocabulary. Split by conversation or
date bucket, never by individual line, so near-duplicate messages cannot cross
the boundary. Hold out whole prompt families and reserve adversarial cases for
requests outside persona scope or attempts to infer private facts.

Code examples should be instruction/completion records derived from pinned
repository snapshots. Split by file/blob and prompt family; keep related
generated files together. Hold out unseen functions/sections and include
negative cases where the correct answer is abstain/escalate rather than a
plausible shell command.

## Training and evaluation

Add a dedicated reproducible runner rather than extending the toy-domain
defaults in `scripts/train_eval.py`:

```text
python scripts/persona_code.py measure --manifest runs/<id>/manifest.json
python scripts/persona_code.py build --manifest runs/<id>/manifest.json
python scripts/persona_code.py train --domain persona --base HuggingFaceTB/SmolLM2-360M-Instruct
python scripts/persona_code.py train --domain code --base HuggingFaceTB/SmolLM2-360M-Instruct
python scripts/persona_code.py eval --run-dir runs/<id>
```

Use the existing LoRA recipe as the starting point (rank 16, alpha 32,
dropout 0.05, attention and MLP projections), but record every changed
hyperparameter. Pin tokenizer/base revision, seed, sequence length, batch,
gradient accumulation, learning rate, epochs, device, and package versions.
Never substitute prompt-only conditioning or the 135M base for a blocked
360M LoRA run; record `blocked` instead.

Evaluation must include:

- base vs persona vs code held-out loss/perplexity;
- diagonal specialization and cross-domain interference;
- fixed style probes scored against a rubric (language, terseness,
  uncertainty, evidence citation, operator vocabulary);
- code completion tests on unseen files/functions;
- 14+ adversarial/private-fact/out-of-domain abstention cases;
- repeated seeds and a prompt-only control;
- exact dataset/model/evaluator digests and prediction cardinality.

Acceptance is a measured result, not a green training process: publish the
full matrix, confidence/variation where applicable, abstention counts, and
failed controls. A specialist may be routed only after held-out artifacts and
the independent witness review exist. Routing changes are out of scope for
this step.

## Current execution state

The dedicated tiny-fleet environment was inspected and is ready for the
training arm: Python 3.12.3, `torch`, `transformers`, `peft`, `accelerate`,
and `safetensors` are importable; CUDA is available with one NVIDIA RTX 3060
(12,288 MiB). No persona/code training or evaluation was performed by this
plan task. The next exact action is to implement the runner and build the
redacted, manifest-backed splits, then run measure/build before training.

## Verification record

- Prior prerequisite: `docs/coordination-verify-mood-pool-20260907.md` in the
  genome repo; independently passed live routing, fallback, and abstention.
- This artifact is intentionally stored in `/home/mesh-home/tiny-fleet`, the
  dedicated tiny-fleet repository. No tiny-fleet-related file was added to
  `lte-workstation`.
