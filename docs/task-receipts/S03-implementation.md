# S03 implementation receipt — controlled model and router comparisons

- Result: `PASS — submitted for independent verification`
- Task: `tinyfleet-publication-science-20260908/matched-baseline-runner`
- Owner: `haunt`
- UTC: `2026-09-11`
- Repository: `/home/mesh-home/tiny-fleet`
- Source files: `scripts/study_runner.py`, `scripts/test_study_runner.py`, `runs/fleet-study-v1/config.json`

## Implementation

`study_runner.py` implements the declared CLI (`--manifest PATH --run-dir PATH --arm NAME --seed INT`)
for the seven-arm matrix: `base`, `prompt-only`, `pooled-lora`, and one specialist arm per
heldout domain. It validates the frozen corpus before loading a backend, draws prompt-only context
only from train prompts, and never places scorer references in generation input. Every case is
written incrementally to JSONL with case/rendered-input hashes, pinned model/config identity,
latency, and an explicit `runtime_status`; timeout and other failures remain records without a
synthetic output.

The fake backend test covers identical heldout IDs, input separation, source-family leakage, and a
timeout record. The real backend uses local-only Transformers loading at the pinned
`HuggingFaceTB/SmolLM2-360M-Instruct` revision
`a10cc1512eabd3dde888204e902eca88bddb4951`.

## Verification commands and evidence

Prescribed check, exit `0`:

```text
rtk proxy .venv/bin/python scripts/test_study_runner.py
Ran 3 tests in 0.063s
OK
```

The full fake seven-arm matrix ran 400 heldout cases per arm, 2,800 records total, all with
`runtime_status=ok` and zero failures. Matrix output directory:
`/tmp/tiny-fleet-s03-matrix.tO40gJ`.

```text
base                         400/400  19335c60442c4543f3bd6bfbb2f5fc9acf8095d824fee729eb6d79d715b8eced
prompt-only                  400/400  1cb323f9511dddb30f1bfa048e2d6f8aaf9c5f3d201dc8b316ae49fc8a81c277
pooled-lora                  400/400  aba9cd8aae8af2d300a76852c75e4a402c1db4e2c9d80433c1e2379d0a3f94d6
specialist:toy_passage_ppl  400/400  1d1c576783a0d8a4cbeb39f66248981e89d0962361b5054db554c1cd168ce292
specialist:executable_code  400/400  59c2f75e250d3cf1402468b5c1966f0a9e9e1f16e201f66c37782ed4ab5e700d
specialist:rated_style      400/400  7d01bae640620f4ada7e6d524259dd762139924d202070d6c02d009adca83805
specialist:adversarial_safety 400/400 c5b581d3c334d4c689042464ae82f0de35969397e8ce18fcb7315a1d81cc4151
```

Real preflight, exit `0`, isolated output `/tmp/tiny-fleet-s03-preflight.16EaoC`:

```text
arm=base records=1 ok=1 failed=0
predictions SHA-256: 8c587b566b9e747afa5a56c932dc04e993aeb221f48f443a1a8036816900f261
config SHA-256:       edb88915b804237ee7f697a88ed352f011829d9b285000ce8c417b979d65c3c2
summary SHA-256:      1abe53abcc687d77bb96ee2ac519ceca4d20f483ef941d7b207821998b485054
```

The preflight record contains a non-empty generated answer, `runtime_status=ok`, the pinned model
revision, and `reference_in_input=false`.

## Scope and residual limitations

This receipt records the implementation and local evidence only. It does not claim adapter training
or inferential scores: those belong to later study work and independent `vpn` verification. S03-V
remains the next gate; S04/S05 are untouched.
