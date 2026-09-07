# Architecture-drift completion: repository and mesh audit

Audit date: 2026-09-07  
Auditor: `haunt`  
Scope: `tiny-fleet` repository, the prior drift protocol, and mesh-only Tiny Fleet artifacts.  
Disposition: **AUDIT COMPLETE; completion is not claimed.**

## Executive result

The repository has a documented architectural-drift hypothesis and a protocol that now
requires pinned snapshots, separate structural/lexical/behavioral/generative estimands,
controls, raw outputs, and a fail-closed run bundle. The repository does **not** yet contain
the requested cross-repository completion bundle, and the mesh cache does not contain enough
raw evidence to promote the old drift headline to a reproducible result.

The current repository is clean at commit
`b9d2752c1c105f8d0f130501ed303bd3e1d83d9b` (`Add pinned persona and code LoRA specialists`,
2026-09-07T11:43:23Z). The earlier report remains a preliminary historical claim:
`docs/tiny-fleet-drift-report.md` names v2 as mutable `HEAD`, retains no raw generative
outputs or scorer metadata, and reports a `mesh_refs` value that the shipped extractor does
not reproduce.

## Present in the repository

| Area | Evidence | Audit disposition |
|---|---|---|
| Drift hypothesis/report | `docs/tiny-fleet-drift-report.md` | Present, historical/preliminary |
| Protocol | `docs/cross-repository-drift-protocol.md` | Present; defines four estimands, controls, run bundle, and blocked states |
| Prior baseline audit | `docs/architectural-drift-baseline-audit-2026-09-06.md` | Present; correctly records missing raw generative evidence |
| Evaluation contract/validator | `docs/deep-evaluation-contract.md`, `scripts/deep_evaluation.py` | Present; applies to model evaluations, not yet a cross-repo drift run |
| Existing evaluation run | `runs/persona-code/{manifest,measure,eval-all,train-*.json}` | Present, but unrelated to the requested architecture-drift sample |
| Repository snapshot | `b9d2752c1c105f8d0f130501ed303bd3e1d83d9b` | Immutable current anchor observed |
| Cross-repo completion bundle | `docs/tiny-fleet-artifacts-20260907/architecture-drift/` | **Absent before this audit; this file is the first artifact** |

Tracked inventory is 59 files at the audited commit. The repository contains corpus,
adapter, router, and evaluation artifacts, but no `runs/<architecture-drift-id>/` bundle with
the protocol's `registration.json`, environment record, corpus manifest, splits/leakage
report, structural/lexical/behavioral tables, controls, raw generative JSONL, scores, and
decision file for this study.

## Mesh-only evidence inspected

The mesh cache at `/home/mesh-home/.mesh/tiny-fleet/` contains:

- `drift-series.jsonl`, one recorded structural snapshot dated 2026-09-03 at cached commit
  `a8b73e01`, with 1,439 files, 29,541.0 KB, vocabulary 88,724, and `mesh_refs` 4,020;
- extracted v1/v2 source trees and prompt/Modelfile training inputs;
- two preflight manifests, the latest at
  `preflight_20260907T115204Z.json`;
- an offline fixture manifest with an intentional duplicate-blob case and an excluded
  generated-file case.

The latest preflight says structural and lexical arms are ready, prompt-only is ready, and
LoRA/QLoRA is blocked because `torch`, `transformers`, and `peft` are absent (despite an
available `nvidia-smi`). This is a real dependency block, not a proxy fine-tuning result.

The inspected mesh artifact hashes are:

```text
cb18fa3d2e6d40119314b9145b756e33a5f5ba6cfc3aaddbba1cf2c2afc2e9bd  drift-series.jsonl
c15414b85cd610dbd2733f987034da8ee669c7a73dd52df30ae45f5e281d42cf  preflight_20260907T115204Z.json
0fcb05519273bfbb19b0dcbadc744524d671a9f529bc3680df480d1b85465da8  training/Modelfile.v1
0466dcd6713be5c64d95664b1205a008f4380e529e04edbdc0f3b80c457b3c0d  training/Modelfile.v2
```

These hashes identify retained evidence; they do not substitute for the missing raw
comparison outputs, prompt/repetition records, model digests, seeds, embedding model
revision, or confidence intervals.

## Stale or non-reproducible claims

1. `docs/tiny-fleet-drift-report.md` labels the v2 snapshot `HEAD` rather than an immutable
   commit. The retained mesh series points to `a8b73e01`, so the report's “Sep 3” state is not
   the current repository state and must not be silently rewritten.
2. The report claims v2 `mesh-*` references of 30,326. The installed extractor's documented
   metric is a fixed allowlist sum, and the retained v2 snapshot records 4,020. These are
   different definitions; the old headline cannot be reused without naming and recomputing
   the metric.
3. The report's generative table (cosines, average 0.4946, drift score 0.5054, and qwen
   comparison) has no retained `results/` bundle. It is therefore not independently
   reproducible from the inspected artifacts.
4. The report presents one average drift score while the newer protocol explicitly separates
   structural, lexical, behavioral, and generative estimands. The old average must remain
   historical, not become the cross-repository verdict.

## Wiring and capability checks

The installed mesh wrapper `/home/mesh-home/.local/bin/mesh-tiny-fleet` is wired for
`extract`, Modelfile-based `train`, `compare`, `drift`, and `preflight`; it writes working
state under `~/.mesh/tiny-fleet`. Its `train` path creates Ollama models from system prompts
and few-shot examples; that is prompt conditioning, not genuine weight training. The
`preflight` path correctly marks genuine fine-tuning blocked when dependencies are absent.

The scheduled snapshot wrapper `/home/mesh-home/.local/bin/mesh-tiny-fleet-snapshot` is
wired for a weekly cadence and appends to `drift-series.jsonl`. Its `--test` is only a smoke
test; it does not prove that a scheduled run produced a fresh artifact. No claim of scheduler
liveness is made here.

## Verification performed

Commands run from `/home/mesh-home/tiny-fleet` on 2026-09-07:

```text
.venv/bin/python scripts/fleet_benchmark.py --test   -> fleet benchmark: 24/24
.venv/bin/python -m py_compile scripts/*.py          -> exit 0
mesh-tiny-fleet-snapshot --test                      -> tiny-fleet-snapshot: OK
```

Runtime probes found Ollama 0.33.2 and `nvidia-smi` available. Python imports for `torch`,
`transformers`, `peft`, and `safetensors` were all absent. These checks verify the current
offline repository contract and the declared preflight block; they do not verify an
architecture-drift analysis.

## Handoff to the remaining chain

The next artifact must freeze a bounded external-repository sample with immutable revisions,
license evidence, acquisition hashes, and explicit unavailable material under
`02-external-sample/`. After that, the analysis step must run only against that frozen sample
and write raw inputs and per-repository outputs under `03-analysis/`. The final step must
assemble and checksum the bundle, preserve blocked arms as blocked, run focused checks, then
commit and push the repository.

No conclusion about cross-repository architectural drift is warranted from this audit alone.
