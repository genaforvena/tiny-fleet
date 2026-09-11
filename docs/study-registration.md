# Fleet study registration

Study ID: `fleet-study-v1`. Frozen design: `runs/fleet-study-v1/registration.json`.
This document records the question and decision before held-out predictions are generated.

## Question and comparisons

Does routed specialization of the shared `HuggingFaceTB/SmolLM2-360M-Instruct` 360M base improve
held-out task quality at bounded cost? The candidate is compared on identical cases with the base,
domain prompt-only conditioning, one pooled LoRA adapter, and a simple deterministic router. The
candidate must not be credited for a router that was tuned after seeing held-out outputs.

The primary comparisons are paired within independent source groups and are reported separately for
toy passage perplexity, executable code correctness, and blinded rated style. The study also reports
adversarial false-accept rate and useful routing coverage as a safety screen.

## Frozen design

- Base revision: `a10cc1512eabd3dde888204e902eca88bddb4951`.
- Adapter: LoRA, rank 16, alpha 32, dropout 0.05, seven declared projection modules, max length 256,
  batch 2, learning rate 0.0002, five epochs.
- Training seeds: 17, 29, and 43; one training job at a time; maximum 12 GPU-hours and 24 wall-hours.
- Minimum independent units: 100 each for passage, code, style, and adversarial safety. Whole source,
  file/problem, and time families are split before normalization.
- Paired source-group bootstrap: 10,000 replicates and 95% intervals. Missing or invalid outputs stay
  in the raw tape and denominator; they are not silently scored as zero or success.

The proposed screening margins are a relative passage-perplexity reduction of at least 10%, a code
accuracy gain of at least 5 percentage points, and a style gain of at least 0.25 points, each with a
paired 95% lower bound above zero against the best prespecified non-routed arm. Safety additionally
requires a one-sided 95% upper bound on adversarial false accepts of at most 5% and useful coverage of
at least 25%. These are design gates, not discovered results.

## Prior work and scope

LoRA establishes low-rank adaptation; S-LoRA addresses serving many adapters; RouteLLM studies
model routing; and MoErging surveys combining independently trained expert modules. This study does
not claim those mechanisms as novel. Its narrower contribution, if the gates pass, is a controlled
small-model comparison of pooled versus routed specialists under the same held-out source units,
with quality, safety coverage, and measured resource cost reported together.

The study is not a deployment claim. A negative or underpowered result remains the registered result,
and a resource-cap breach is reported rather than hidden by dropping a seed.
