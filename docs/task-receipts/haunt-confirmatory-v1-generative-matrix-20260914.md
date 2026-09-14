# Confirmatory-v1 generative matrix — 2026-09-14

Task: `tinyfleet-confirmatory-v1-comparison-20260914/execute-confirmatory-v1-generative-matrix`

## Artifacts

- Raw pinned-backend output:
  `runs/drift-confirmatory-v1/execution-confirmatory-v1/generative-v2.jsonl`
  SHA-256 `b691c04b3a053c0fff8b6aefbc336fd0e61bd01de03453a76415c53e216bab5b`.
- Runtime/provenance manifest:
  `runs/drift-confirmatory-v1/execution-confirmatory-v1/manifest-v2.json`
  SHA-256 `77c70b6c381d486a341722d2cddddd2b56fd031a062157a35e5bfca42f68aafc`.
- Deterministic score output:
  `runs/drift-confirmatory-v1/execution-confirmatory-v1/scores-v1.json`
  SHA-256 `f45c9436755740f650c1fd66fd648070ae31f7ff9a39081023595d2423f159da`.
- Pre-score scorer amendment:
  `runs/drift-confirmatory-v1/execution-confirmatory-v1/scoring-amendment-v1.json`
  SHA-256 `f92f9acf77c18d629bb2f5b9ebbbfc34c609dd38a6e6bb9b61fdb8796b8e8eb7`.

## Execution and verification

The generation registration remained byte-for-byte unchanged at SHA-256
`157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`. The paired behavioral
closeout remained at `fd36f832d08601ba21debc3735bc8f6489a33a0d4415ba91485850de1c1800f5`; the
independent VPN receipt records PASS at
`docs/task-receipts/vpn-confirmatory-v1-independent-gate-verification-20260914.md`.
The registration's `comparison_authorized` flag remains false and was not edited. The current v2
runner did not treat it as a hard stop; execution followed the assigned task's explicit conditional.

Generation command:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/drift_generate.py \
  --manifest runs/drift-confirmatory-v1/generative-registration.json \
  --run-dir runs/drift-confirmatory-v1/execution-confirmatory-v1 --device cpu
```

The real pinned backend produced 162/162 successful records across base, prompt-only, and
snapshot-specific LoRA arms. Runtime metadata records Python 3.12.3, PyTorch 2.14.0+cu130,
Transformers 4.57.6, device CPU, and backend `transformers-pinned-v2`. `validate_v2_records()`
returned `ACCEPT`.

The original registered scorer exited before embedding with `adapter_pair_mismatch`: it required
old/new adapter digests to be equal even though the frozen manifest assigns distinct snapshot LoRAs.
No frozen scorer or registration was changed. A separately versioned amendment was frozen after
generation and before scoring, binding the raw tape, original registration, embedding runtime and
all scorer/validator source digests. Witness independently reviewed the pushed amendment and
published PASS in
`/home/mesh-home/lte-workstation/docs/task-receipts/witness-confirmatory-v1-scorer-validator-binding-review-20260914.md`.

The amended scorer then processed all 162 raw outputs in one separate pass. The score contains
81/81 complete old/new pairs (27 per arm), uses Ollama 0.33.2 and `all-minilm:latest` at registered
digest `1b226e2802dbb772b5fc32a58f103ca1804ef7501331012de126ab22f67475ef`, and records each
paired output hash and both snapshot adapter digests. Validation confirmed all keys unique and
complete, all cosine values finite and within [-1, 1], and all rows carry the interpretation limit
that cosine is embedding similarity, not semantic ground truth.

The amendment is post-generation/pre-score and must be disclosed in the reader-facing conclusions.
The scores are not semantic or behavioral truth; the three objective labels are not behavior or
semantic ground truth. This receipt reports execution only and makes no cross-repository finding.
