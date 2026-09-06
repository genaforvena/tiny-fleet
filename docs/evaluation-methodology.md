# Deep evaluation methodology for tiny specialists

The useful question is not “does the tiny model sound plausible?” It is whether a small model has
learned a bounded capability, knows when it does not know, preserves the operator/codebase contract,
and improves a real mesh path without silently taking over its failure modes. Every claim needs an
artifact: dataset manifest, immutable split hash, raw predictions, score table, and environment
record.

## Data adequacy and actual training gate

“Enough data” is a measured design decision, not a row count copied between domains. Before
training, preregister the estimand, smallest effect worth detecting, confidence level, target
interval width, and power or precision calculation. The frozen manifest must show positive counts
for every required split and declared repo/snapshot/domain/language/time slice, enough independent
sources for the intended generalisation claim, and a held-out reserve for later verification. A
slice that misses its minimum count or source diversity is `insufficient-data` and cannot be pooled
into a stronger headline result.

The methodology must include a real fine-tuning arm. Prompt-only Modelfiles are a control, not a
fine-tuned model. A publishable run pins the base model and revision, executes LoRA/QLoRA (or an
equivalent genuine weight-update procedure) on the frozen training split, records environment,
seed, configuration, training log, resource use, adapter/model hash, and before/after predictions,
and compares it with base and prompt-only controls on identical held-out cases. If the runtime is
unavailable, the failed preflight is recorded and the result remains non-publishable; prompt
conditioning may not be relabeled as fine-tuning.

## Evaluation matrix

Evaluate every candidate against the same frozen cases and the same base-model control.

| axis | question | minimum evidence |
|---|---|---|
| reproduction | can the run be repeated from the pinned base, commit, seed, and config? | manifest + environment + run log |
| capability | did the specialist improve its declared narrow skill? | held-out task score and bootstrap interval |
| generalisation | does it survive paraphrase, RU/EN switches, spelling noise, and unseen sources? | stratified held-out slices |
| contamination | did train data or near-duplicates leak into evaluation? | IDs, near-duplicate report, temporal cutoff |
| abstention | does it refuse low-margin or out-of-domain cases? | OOD confusion matrix and risk-coverage curve |
| calibration | do confidence and routing margin predict correctness? | reliability bins, ECE/Brier, selective risk |
| operator contract | does it preserve operator-first safety and escalation semantics? | adversarial policy suite |
| code culture | does it reproduce idioms without stale/forbidden code? | held-out convention rubric + structural lint |
| routing | does the fleet choose the right specialist and avoid collisions? | per-domain routing matrix and margin distribution |
| systems cost | is replacement cheaper or fast enough? | p50/p95 latency, peak memory, cold start, fallback rate |
| regression | did the candidate damage the control? | paired delta table and non-inferiority bounds |

The base model, reference model, and candidate are controls, not interchangeable “baselines.” Report
paired per-example deltas so a mean win cannot hide a catastrophic slice regression.

## Dataset protocol

Every specialist has disjoint `train`, `validation`, `heldout`, and `adversarial` sets. Split by
source and time before normalization, then run near-duplicate detection across every boundary. The
held-out set contains people/files/time periods absent from training. The adversarial set is authored
from observed failure modes, not sampled from the training distribution.

Each JSONL row carries stable `case_id`, `source_id`, `created_at`, `domain`, `language`, `split`,
`expected_route`, `expected_action`, and a redaction/provenance record. Freeze a manifest with counts,
hashes, and the exact cutoff; a corpus-size claim without it is not reproducible.

For the operator-style specialist, separate style from mesh facts: test style transfer on unseen
content and factual recall on newly written facts. For the code specialist, split by file and time,
hold out entire tools, and score conventions (error handling, artifact discipline, routing, handoff)
separately from token overlap or exact-match completion.

## Scoring and decision gates

Produce raw predictions first; compute scores in a second deterministic pass. Reports include:

1. task score by slice with bootstrap confidence intervals;
2. selective risk at coverage 25/50/75/90% and the risk-coverage curve;
3. confusion matrices for specialist choice, abstain, escalate, and operator-first cases;
4. calibration (ECE/Brier/reliability), not only router top-1 accuracy;
5. paired candidate-minus-control deltas, including worst slice and worst case;
6. cost/latency/memory distributions and fallback/timeout counts.

A candidate is eligible for a real mesh lane only when it wins its narrow capability, does not regress
the safety/adversarial suite, has a useful abstention boundary, and has reproducible artifacts.
“Better perplexity” alone never qualifies it for routing. A high-confidence-only win must remain behind
abstain/escalate and publish its coverage.

A drift result is publishable only when data adequacy, genuine fine-tuning, leakage controls,
negative controls, calibration/uncertainty, independent review, and reproduction instructions all
pass. Otherwise it is explicitly preliminary or blocked with the failed gate named.

## Multi-step run contract

The evaluation is a chain: freeze manifests; reproduce controls; train with recorded seed/config;
score raw outputs; independently audit leakage/scoring; run adversarial/routing/fallback tests;
compare cost and regression deltas; decide `route`, `abstain`, `escalate`, or `reject`.

Each step hands its manifest or result path to the next worker. A later step may not silently recreate
an earlier dataset or treat a missing artifact as zero. Failed or blocked steps remain explicit and
cannot be reported as a model result.

## Required artifact bundle

`runs/<run-id>/` contains `manifest.json`, `config.json`, `environment.txt`, `predictions.jsonl`,
`scores.json`, `slices.tsv`, `calibration.tsv`, `routing.tsv`, `adversarial.tsv`, `cost.tsv`, and
`decision.md`. The decision names the model actually served, its coverage, fallback, and exact next
action. This bundle is the hand-off object for mesh integration and independent review.
