# Small-model terminology-drift study: measured result

**Status:** the exploratory usefulness criterion failed. This is not a semantic-accuracy or architectural-drift finding.

## Result

A prospective CPU experiment repeatedly fitted six existing LoRA adapters for Flask, Requests, and Pydantic snapshots using a pinned SmolLM2-360M-Instruct base. The Requests excerpts are byte-identical across snapshots, so the changed-source comparison contains only two repository pairs (Flask and Pydantic); Requests is an unchanged control.

| Fitting stage | LoRA | Base | Training-context prompt-only | Unigram |
|---|---:|---:|---:|---:|
| Original adapters | 0.75 | 0.50 | 0.75 | 0.75 |
| 4 additional passes | 0.75 | 0.50 | 0.75 | 0.75 |
| 19 additional passes | 0.50 | 0.50 | 0.75 | 0.75 |

Accuracy uses the two changed pairs only. The preregistered repeat-19 criterion required LoRA to strictly outperform all three controls; it did not. The one-sided sign-flip value of 0.25 is the attainable floor for the two-unit diagonal-preference statistic, not evidence of classifier superiority. Token-shuffled repeat-19 accuracy was 0.25 for LoRA, 0.50 for prompt-only, and 0.75 for unigram.

The strict analysis validated 132/132 likelihood rows, 201/201 generation rows, 132/132 training rows, and 12/12 continued checkpoints. It recorded zero failed or empty outputs; 195/201 generations hit the 96-token cap. Runtime was 12,397.6 model-wall seconds (about 3 h 26 min 38 s), with 4.09 GiB peak RSS. Training loss decreased and held-out self-loss increased for all six adapters after repeat 19. That is evidence of fitting/overfit, not a useful drift signal.

Generation evidence is weak: all 32 raw outputs in the 16 repeat-19 changed-source LoRA pairs were capped; mean source/output cosine alignment was -0.0218 (range -0.1332 to 0.0718), with 1.52–10.95% changed-term coverage. These correlated probes are not independent replications. No human semantic labels were collected; semantic precision and pretraining contamination remain unknown.

## Reproduce and inspect

The measurement was prepared and source-bound to code revision
`96246410981ab9c0424ebcce4538fce52800564e`; the base model revision is
`a10cc1512eabd3dde888204e902eca88bddb4951`. Reproduction is limited to the
preserved internal worktree: the frozen input root is
`.mishe-tauftauf/research/terminology-drift-candidate/` (as bound by
`input_root` in the protocol). That ignored tree is not in a fresh clone, and
the commands below do not acquire or restore it; the protocol's `files` map
binds the six source archives and other inputs. Copy the preserved tree to an
unused location before running; do not overwrite it. With that input tree
available, install the recorded CPU dependencies and run in fresh directories:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0
.venv/bin/python -m pip install -r requirements-model-drift.txt
# If absent, cache the exact pinned base without runner-side downloading:
.venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="HuggingFaceTB/SmolLM2-360M-Instruct",
    revision="a10cc1512eabd3dde888204e902eca88bddb4951",
    allow_patterns=["*.json", "*.safetensors", "*.model"],
)
PY
# Use unused output directories; prepare/run refuse changed inputs or source.
.venv/bin/python scripts/model_terminology_drift.py --prepare --run-dir /tmp/model-drift-study
.venv/bin/python scripts/model_terminology_drift.py --run --run-dir /tmp/model-drift-study
.venv/bin/python scripts/analyze_model_terminology_drift.py --run-dir /tmp/model-drift-study --output /tmp/model-drift-analysis.json
```

The runner is CPU/fp32, cache-only, sequential and no-overwrite; it binds
inputs and implementing-source hashes and enforces a six-hour model-execution
cap. The exact completed run remains local under
`.mishe-tauftauf/research/terminology-drift-20260930/`, not Git. The SHA-256
values for its protocol, receipt, analysis and three measured tapes match
`.mishe-tauftauf/artifacts/model-drift-measured-results-20260930.json`.
Independent read-only review of those bindings judged the result safe to report
cautiously; see `.mishe-tauftauf/artifacts/model-drift-results-independent-review-20260930.json`.
These internal hashes establish consistency, not authenticated execution
provenance. Later source revisions are not retroactively treated as the
measured implementation.

## Scope and historical correction

This result concerns a small-model terminology-drift instrument, not the separate registered four-estimand architectural study. The latter compares six immutable Flask, Requests, and Pydantic snapshots and remains incomplete; see the [architectural execution plan](architectural-drift-execution.md) and [cross-repository protocol](cross-repository-drift-protocol.md).

This page replaces the preliminary 2026-09-03 report formerly stored here. That report used a mutable `HEAD` snapshot, retained no raw generation tape or scorer metadata, and made unsupported semantic interpretations; its numerical claims are not current findings. The historical audit remains at `docs/architectural-drift-baseline-audit-2026-09-06.md`.