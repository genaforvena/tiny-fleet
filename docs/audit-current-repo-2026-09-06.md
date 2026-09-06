# tiny-fleet repository audit

Date: 2026-09-06  
Scope: `tinyfleet-specialists/audit-current-repo`  
Source commit observed: `4e87f2e` (`docs: lead with architectural drift results, highlight use case`)

## Disposition

The offline operator/router contract is reproducible and currently passes. The repository is not
yet ready for the deep-evaluation or mesh-wiring steps: the specialist corpora are legacy toy
fixtures without provenance and split metadata, no frozen evaluation run bundle exists, and the
live model-training/reproduction dependencies are not installed in the evaluation environment.

The next safe step is `design-deep-evals`: turn the existing methodology into a manifest/report
contract and add negative controls before collecting a new mood corpus or wiring a specialist.

## What is actually present

| Area | Inventory | Evidence |
|---|---|---|
| Router | `scripts/router.py`; domains `guitar`, `sourdough`; operator-first; abstain margin `0.10` | source inspection |
| Operator model | `models/operator-policy.json` (8 KiB), trained from `operator-train.jsonl`, evaluated against `operator-test.jsonl` and adversarial cases | source + tracked artifact |
| Adapters | `adapters/lora-guitar/adapter_model.safetensors` and `adapters/lora-sourdough/adapter_model.safetensors`, 34,793,120 bytes each; shared `adapter_config.json` hash `1587da...fe38c` | filesystem inspection |
| Specialist corpora | guitar `48 train/12 test`; sourdough `48 train/12 test` | line counts |
| Operator corpora | `65 train`, `41 test`, `14 adversarial` | line counts |
| Evaluation code | `scripts/fleet_benchmark.py --test` | real run below |
| Method | `docs/evaluation-methodology.md` defines manifests, leakage, calibration, routing, cost, and decision gates | source inspection |
| Environment | `.venv` contains the isolated NumPy floor; system and venv probes do not provide `torch`, `transformers`, `peft`, or `safetensors` | import probes |

The adapter files are real artifacts, but their README/config do not constitute a run manifest. The
repository has no `runs/<run-id>/` bundle containing `manifest.json`, predictions, scores, slices,
calibration, routing, cost, and decision files as required by the methodology.

## Corpus and evaluation gaps

The guitar and sourdough rows use only `topic` and `text`. Operator rows use prompt/response fields
and adversarial expectations. None of the inspected rows carries the methodology-required stable
`case_id`, `source_id`, `created_at`, `domain`, `language`, `split`, `expected_route`,
`expected_action`, and redaction/provenance record. The current 4:1 train/test split is therefore a
toy partition, not evidence of source/time separation or leakage control.

The current benchmark proves the bounded offline contract and adapter-file integrity, not real
perplexity, calibration, selective risk, cost, or generalisation. `router.py`'s live embedding path
also shells out to Ollama/all-minilm, so it was not exercised by the offline run.

## Reproduction and promise disposition

The original operator requests are preserved in `docs/plans/tinyfleet-operator-promises-20260906.md`:
BbyWVY-360M reproduction, small-model replacement choice, operator-style material, mesh-code
specialisation, and the shared 360M base. This audit does not claim BbyWVY reproduction: the model
and GPU training stack were not present in this environment, and no download or training run was
started. That remains an explicit later obligation rather than a silently successful historical
closure.

## Verification record

Run from `/home/mesh-home/tiny-fleet` on 2026-09-06:

```text
.venv/bin/python scripts/fleet_benchmark.py --test
fleet benchmark: 24/24
.venv/bin/python -m py_compile scripts/*.py
```

The benchmark breakdown was: safety decisions `4/4`, operator adversarial `14/14`, router contract
`4/4`, specialist inventory `2/2`. The two specialist weight files were each checked at exactly
`34,793,120` bytes. The py_compile command completed without errors.

## Handoff gates

1. `design-deep-evals` must add the frozen manifest/report schema and deliberate leakage/missing-
   artifact negative controls.
2. Only after that should `mood-corpus` create RU/EN train/held-out/adversarial data with provenance
   and redaction evidence.
3. Any BbyWVY or SmolLM2 training claim must include the required run bundle and an environment
   record; the current `24/24` result must not be promoted to a training result.
