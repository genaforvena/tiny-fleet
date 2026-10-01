# tiny-fleet: small models as predictive-compression drift instruments

**Can a small language model act as a predictive code-length meter for repository change?**

At the objective level, yes: an autoregressive model's token log-loss is its
ideal predictive code length (in bits, `-log2 p(token | context)`), and an
arithmetic coder can turn that predictive distribution into a lossless code.
Comparing held-out code lengths for models fitted to two repository snapshots
can therefore measure a distribution/timepoint signal. It does **not** establish
semantic understanding or explain why code changed. Nor is an adapter literally
a compressed repository: real archive compression must also pay for the model,
adapter, tokenizer/decoder and framing.

The prediction/compression equivalence is established adjacent work; see
[Language Modeling Is Compression (ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/file/3cbf627fa24fb6cb576e04e689b9428b-Paper-Conference.pdf).
Diachronic language-model methods also exist for meaning-shift tasks, including
[TempoWiC social-media models (EvoNLP 2022)](https://aclanthology.org/2022.evonlp-1.6/).
Those are neighboring areas, not the exact repository-specific measurement
tested here; this README makes no novelty claim.

**LTE-workstation:** the [2026-09-03 historical report](docs/tiny-fleet-drift-report.md)
did not validate a fine-tuned compression meter. Its Ollama Modelfiles changed
prompts and few-shot examples; LoRA was listed as future work. It used a 135M
Ollama model; the pilot below fits a separate, pinned 360M base. The later
Flask/Requests/Pydantic LoRA study was a different sample and says nothing about
LTE history. The direct two-timepoint LTE measurement and its limitations are
reported below.

Fleet deployment, routers and the other applications below are historical
experiments, not the project's goal. The inspiration was the narrowly fitted
[BbyWVY-360m](https://huggingface.co/StarpowerTechnology/BbyWVY-360m);
[the original notes](docs/bbywvy-360m-notes.md) remain available.

We treat models as **measuring instruments, not authorities**. A different
held-out loss is a distributional signal, not evidence that a model understands
architectural change. Negative results count.

## LTE-workstation two-timepoint pilot

This is the direct test of the historical LTE claim, not a reuse of the
Flask/Requests/Pydantic sample below. It compares LTE-workstation history at
`5475816081b26a0f9aebb92da844493b19304eef` (2026-06-15) and
`a8b73e01b55d06f8ae3bed8f438c7ea36c902e63` (2026-09-03). The filtered,
UTF-8 text inventory contains 31 old files (201,592 bytes) and 589 new files
(5,186,335 bytes); binary, private, and unregistered paths are excluded.

The same pinned 360M SmolLM2-Instruct base is fitted separately on each
snapshot with LoRA (rank 8, alpha 16), seeds 17/29/43, 4,096 training tokens
per fit, fresh AdamW optimizers, and 19 passes over the fixed sample.

The shared-host run uses CPU/fp32, one thread and non-reentrant activation
checkpointing under `mesh-heavy-run 3072`'s cgroup memory cap; the runner also
enforces a six-hour wall limit.
Each snapshot also has 4,096 validation tokens. The path/exact-blob component split
keeps versions of a path and duplicate content out of different splits.

The first prepare-only hash split had four changed but zero unchanged test
paths. Before any LTE-source model outputs, the frozen plan was amended to put
the unique byte-identical common file with the lowest `SHA256(path)` into test;
its deterministic, deliberately selected control is not a random sample.
The source-held-out test has four changed paired paths and one byte-identical
common-file control; each side uses at most 512 model input IDs (511
next-token targets).

All four changed test units are Markdown; this pilot therefore measures a
repository-documentation signal, not a held-out executable-code change.

The primary measure is crossed held-out negative log-likelihood in nats per
token (`bits/token = nats/token ÷ ln 2`), compared against the shared base
model, snapshot-specific training unigram, and unchanged-source control.
Each 512-ID prefix uses its first ID as context and scores 511 next tokens;
the reported metric is token-level only, not a full-snippet bits-per-byte
rate. Expected tape denominators are 180 LoRA, 10 base, 20 unigram likelihood
rows, and 132 training rows. Only aggregate measurements belong in Git; raw
source, token IDs, inventories, checkpoints and tapes stay in the ignored local
research site. No generations or human semantic labels are part of this pilot.

### Measured LTE result

The strict analyzer completed with no errors: 210/210 likelihood rows and
132/132 training rows. The sequential CPU run took 17,583 s (4.88 h); peak
process RSS was 2.71 GiB under the 3,072 MB cgroup cap. The score table gives
mean token-weighted NLL over four changed held-out documents, averaged across
three LoRA seeds; pass 0 is the shared unadapted base.

A two-way crossover counts a seed only if the old adapter has lower NLL on
old text and the new adapter has lower NLL on new text.

| Checkpoint | Old fit on old text | New fit on old text | Old fit on new text | New fit on new text | Same-seed two-way crossovers |
|---|---:|---:|---:|---:|---:|
| Pass 0 (base) | 3.2995 | 3.2995 | 3.2209 | 3.2209 | — |
| 4 additional passes | 3.2326 | 3.2501 | 3.1548 | 3.1735 | 0/3 |
| 19 additional passes | 3.7369 | 3.8190 | 3.5855 | 3.8038 | 0/3 |

At both fitted checkpoints, the old-snapshot adapter has lower NLL than the
new-snapshot adapter on both timepoints for all three matched seeds. At pass
19, both adapters also score worse than the shared base on the changed test
documents. The byte-identical control has equal scores across its old/new
labels, as expected.

Mean across the three seeds, train/validation diagnostic NLL (pass 0 → 4 → 19):

| Fit snapshot | Train NLL | Validation NLL |
|---|---|---|
| Old | 3.678 → 3.453 → 1.472 | 3.420 → 3.368 → 4.028 |
| New | 3.346 → 3.151 → 1.477 | 3.711 → 3.642 → 4.340 |

The late training-loss drop with a sharp validation-loss rise is consistent
with overfitting this small fixed sample; it does not produce a new-timepoint
preference. This LTE pilot therefore gives no evidence that the measured
compressibility signal identifies emergent terminology. All four changed
held-out units are Markdown, so there is no held-out executable-code result.

This result is limited to one repository, two selected snapshots, four changed
test units, one unchanged unit, one model/tokenizer, and a small training
budget. Pretraining contamination is unknown. Predictive NLL is not semantic
correctness; it cannot explain why terms or software changed. Model, adapter,
tokenizer and decoder costs are excluded.

### Reproduce the LTE measurement

The LTE history and pinned model cache are local inputs, not bundled with this
repository. Use a new private run directory outside the tracked worktree:

```bash
LTE_REPO=/path/to/lte-workstation
umask 077
mkdir -p "$HOME/.local/state"
PRIVATE_ROOT=$(mktemp -d "$HOME/.local/state/tiny-fleet-lte.XXXXXXXX")
RUN_DIR="$PRIVATE_ROOT/run"

.venv/bin/python scripts/lte_snapshot_compression.py --prepare \
  --repository "$LTE_REPO" \
  --old-revision 5475816081b26a0f9aebb92da844493b19304eef \
  --new-revision a8b73e01b55d06f8ae3bed8f438c7ea36c902e63 \
  --run-dir "$RUN_DIR"

# On the shared host, this enforces the registered 3072 MB cgroup cap.
mesh-heavy-run 3072 -- .venv/bin/python scripts/lte_snapshot_compression.py \
  --run --run-dir "$RUN_DIR"
.venv/bin/python scripts/lte_snapshot_compression.py --analyze --run-dir "$RUN_DIR"
```

Preparation copies raw source and token IDs into `RUN_DIR`; keep it private and
never commit it. The runner refuses a run directory inside the source repository
or an unignored Git worktree path. Before running, use the CPU dependency install
and pinned-revision download in the separate Flask/Requests/Pydantic setup section
below; both experiments use this exact 360M model revision. Execution is offline.
The runner verifies the effective process cgroup limit and refuses execution
unless it can prove a cap of at most 3,072 MB; outside the shared host, provide
an equivalent Linux cgroup limit.

## Earlier, separate LoRA overfitting study

The experiment uses the same pinned
[SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)
base and six existing old/new code-snapshot LoRAs: Flask, Requests and Pydantic.
The original adapters received one bounded training epoch; they are the
**adaptation baseline**, not evidence of deliberate overtraining.

Each adapter is fitted repeatedly on a frozen 4,096-token training subset,
with checkpoints after **4 and 19 additional passes**. These are not 5/20
full-corpus epochs: the historical optimizer is unavailable, so continuation
uses a fresh optimizer. Training, validation and source-held-out losses show
whether repeated fitting actually overfits and whether that helps the detector.

| Measurement | What it checks |
|---|---|
| Old/new adapter likelihood on excluded source modules | Whether the weights distinguish held-out snapshots |
| Token-unigram and training-context prompt-only baselines | Whether fitting adds value over cheaper alternatives |
| Terminology/concept probes | Whether output changes align with observed source vocabulary. Base and LoRA arms are prompted with no source text; the prompt-only arm deliberately receives 512 tokens of *training* context, so it is not source-free |
| Repeated identical-model probes | Reproducibility without a changed snapshot |
| Token-order shuffle and repository-label permutations | Sequence dependence and accidental directional alignment |
| Losses, failures, empty/capped outputs and elapsed cost | Memorization, deterioration and operational usefulness |

The held-out modules are excluded from both snapshots' train/validation sets.
Prompt-only controls receive training text, never the held-out target.
There are only **three repository pairs**, with one held-out module per snapshot
and one training seed. The Requests held-out excerpt is byte-identical across
snapshots: it is an unchanged-source control, not a third changed module.
Generation seeds are not independent training replicas. Pretraining contamination
and human semantic accuracy remain unknown. With only two changed source units,
the exact sign-permutation test has a positive-tail floor of 1/4; this experiment
cannot establish a general statistical superiority claim.

### Measured prospective result

The frozen six-adapter run completed with all **132 likelihood, 201 generation,
132 training rows and 12 continued checkpoints** validated; all tape rows were
successful, with no execution failures or empty outputs. It used 12,397.6 model
wall-seconds (3 h 26 min 38 s) and peaked at 4.09 GiB RSS.

| Stage | LoRA changed-pair accuracy | Base | Training-context prompt-only | Unigram |
|---|---:|---:|---:|---:|
| Original adapters | 0.75 | 0.50 | 0.75 | 0.75 |
| 4 additional passes | 0.75 | 0.50 | 0.75 | 0.75 |
| 19 additional passes | 0.50 | 0.50 | 0.75 | 0.75 |

The changed-pair denominator is only Flask and Pydantic; Requests is byte-identical and remains a negative control.
For the LoRA diagonal-preference statistic (not classifier accuracy), the
repeat19 one-sided repository-label sign-flip p-value was 0.25, the attainable
floor with two nonzero changed-pair units. This coarse two-unit calculation is
not inferential evidence, and LoRA did not beat base, prompt-only or unigram.
Token-shuffled repeat19 changed-pair accuracy was 0.25 for LoRA, 0.50 for
prompt-only and 0.75 for unigram; the shuffle preserves the scored-token multiset.

Selected-subset training loss fell in all six adapters, while held-out
self-loss rose in all six after repeat19. This is strong fitting/overfit
evidence, not a useful terminology-drift result. **195 of 201 generations hit
the 96-token cap**; the sole explicit identical-input decode repeat returned
identical raw output, but sampled decodes do not replicate training seeds.
Truncated lexical alignment is descriptive only; human semantic terminology
precision was not measured.

For the 16 repeat19 LoRA output-pairs on the two changed modules, all 32 raw
outputs were capped; 16/16 cosine alignments were defined, with mean
source/output delta cosine -0.0218 (range -0.1332 to 0.0718). Changed-source
term coverage ranged 1.52–10.95%. Prompt/decode rows are correlated repeated
probes, not 16 independent replications; low coverage and near-zero mixed-sign
cosines do not identify semantic correctness.
The pre-registered usefulness criterion therefore fails: these measurements
do not show that repeated fitting is a useful or reproducible terminology-drift instrument. The result is limited to three
purposively chosen repositories, two changed source units, one training seed,
and no human semantic labels; pretraining contamination remains unknown.

The source-bound raw run and strict complete analyzer output are retained in
the private local research site, not Git. Their receipt, tape hashes, the
prospective interpretation plan and independent result review are recorded in
the site's evidence artifacts.

### Reproduce the separate Flask/Requests/Pydantic study

The runner is CPU/fp32, cache-only, sequential and no-overwrite. It freezes
input/model/tokenizer/source hashes before execution, retains raw outputs and
failed attempts, and enforces a six-hour model-execution wall cap. It does not
evict GPU workloads, download models implicitly or amend older registrations.

`--prepare` records the repository revision it was prepared at, and `--run`
refuses to start if any bound input or implementing-source hash changed afterwards.
The completed measurement was prepared and source-bound to commit `9624641`.
Later revisions add this measured result, additional inference tests, and
reporting/runtime-verification fixes; they do not alter the frozen run or its
source-bound analyzer output.

```bash
python3 -m venv .venv
# Install a CPU torch wheel first if you do not need CUDA:
.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0
.venv/bin/python -m pip install -r requirements-model-drift.txt

# If the pinned base is not cached, explicitly download it once:
.venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="HuggingFaceTB/SmolLM2-360M-Instruct",
    revision="a10cc1512eabd3dde888204e902eca88bddb4951",
    allow_patterns=["*.json", "*.safetensors", "*.model"],
)
PY
# Runner calls below are offline; use unused directories.
# Smoke performs an actual model update without changing original weights.
.venv/bin/python scripts/model_terminology_drift.py --smoke --run-dir /tmp/model-drift-smoke
.venv/bin/python scripts/model_terminology_drift.py --prepare --run-dir /tmp/model-drift-study
.venv/bin/python scripts/model_terminology_drift.py --run --run-dir /tmp/model-drift-study
.venv/bin/python scripts/analyze_model_terminology_drift.py --run-dir /tmp/model-drift-study --output /tmp/model-drift-analysis.json
```

The Flask/Requests/Pydantic study is a separate prospective exploratory
experiment, not a repaired or renamed LTE-history replication. Its historical
results and failed/partial runs are preserved; they cannot settle the LTE claim.

<details>
<summary>Historical fleet experiments, applications and earlier research plans</summary>

## Historical fleet conclusions — 2026-09-30

**Specialization improved reference likelihood on the toy passage task, but did
not establish useful generation, routing superiority, or deployment safety.**
These are interim exploratory measurements of saved seed-17 checkpoints, not
the registered three-training-seed replication.

Four completed CPU/fp32 arms contain **3,200 validated outputs**, 800 per arm:
100 cases in each of four domains in each held-out/adversarial split. This is
the original four-arm publication snapshot, not the final stopped-run inventory.
The operator subsequently stopped the fleet jobs to prioritize model drift;
completed and partial evidence was retained without restarting either study.

| Execution arm | Held-out passage reference PPL (100 cases) ↓ | Code expressions passing fixed fixtures (200 cases) | Empty outputs / 800 | 256-token cap hits / 800 | Whole-arm minutes |
|---|---:|---:|---:|---:|---:|
| Base | 3.841820 | 0 / 200 | 264 | 438 | 96.51 |
| Prompt-only | 4.187572 | 0 / 200 | 393 | 314 | 83.32 |
| Pooled LoRA | 2.551908 | 0 / 200 | 0 | 800 | 146.11 |
| Passage specialist | 2.283509 | 0 / 200 | 0 | 619 | 137.90 |

The passage specialist's reference PPL is **40.56% below base** and **10.52%
below pooled** on these fixed template cases. Lower PPL is not a generated-answer
quality score: repetition and capped completions persist, and every code output
in these four arms fails expression parsing. No output-prefix stripping or
favorable line extraction was used. All four arms have zero recorded model
runtime/likelihood failures; unsuccessful task outputs remain in the denominator.

Authored template variants are not independent substantive source families.
Saved adapters do not establish independent training seeds 17/29/43 or complete
historical resource accounting. Style is **UNSCORED** without independent human
ratings. Safety/route false-accept risk and useful coverage are **UNMEASURED**:
canary-refusal explanations are not observed router decisions. Off-domain
reference likelihood is auxiliary, not code correctness, style quality, or
harmfulness. Wall times include loading/overhead and are not controlled latency
benchmarks; memory is cumulative process high-water, not adapter overhead.

### Inspect the measured evidence

The [aggregate result snapshot](runs/checkpoint-panel-interim-20260930/analysis.json)
contains all 32 arm/split/domain metric rows, costs, raw-tape hashes, input-protocol
binding and limitations. Its SHA256 is
`5bc3bc1cd3e8a1972c6ff111cdff6cf85c707184e3ccfd57cf610506f7716d87`.
Analysis revision: `659222052f0c340a653fbac6e23e3dc72192cc28`;
protocol revision: `0c271da49d6c4354fefb153158fe45751e4cb05a`.
An independent resident witness checked hashes and accepted only this partial
interpretation, not full-study completion.

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
p = Path("runs/checkpoint-panel-interim-20260930/analysis.json")
assert hashlib.sha256(p.read_bytes()).hexdigest() == "5bc3bc1cd3e8a1972c6ff111cdff6cf85c707184e3ccfd57cf610506f7716d87"
r = json.loads(p.read_text())
assert r["validated_rows"] == 3200
for m in r["metrics"]:
    if m["split"] == "heldout" and m["domain"] == "toy_passage_ppl":
        print(m["arm"], m["cases"], m["conditional_ppl"])
PY
```

This inspects the published summary; it does not rerun model inference. Raw
checkpoint tapes and local protocol dependencies are not bundled here, so a
fresh clone cannot independently reproduce the model run from this summary.

### Historical completion plan and distribution — superseded as current priority

| Workstream | Execution owner | Required experiments / acceptance | Current prerequisite |
|---|---|---|---|
| Existing exploratory CPU panel | genome; witness reviews | Finish seven arms / 5,600 outputs; validate exact inputs, raw hashes, all denominators, code fixtures and costs; preserve failures | Running evaluator and event-driven finalizer; no restart or decoding changes |
| Original frozen fleet study | genome; discover audits provenance | Reconcile training seeds and cumulative budgets, source dependence and missing route tapes; retain negative/inconclusive findings | Do not silently repair a frozen design by replacing corpus or adapters |
| Separate fleet v2 replication | genome; discover audits source families; senses checks bindings | Freeze reviewed corpus/router/source; pooled plus four specialists × training seeds 17/29/43; compare base, prompt-only, pooled, candidate and metadata routing; validate 7,500 prescribed exports, paired source-group contrasts, risk and coverage | Independent **human sandbox review** before freeze/training; then one training job at a time, at most 15 trainings, 12 cumulative GPU-hours / 24 model-execution wall-hours |
| Blinded style scoring | Two independent human raters; witness accepts | Randomized blinded 1–5 sheets, independence attestations, agreement and missingness analysis | Real rating sheets; automated/self-ratings cannot substitute |
| Architectural drift | genome; discover handles source/license/unit inventory; witness accepts | Registered Flask/Requests/Pydantic old/new snapshots: structural, lexical, paired native behavior, 162-record gated generative matrix; identity/shuffle/leak/missing-artifact controls | Archive measurement path, pinned paired probes, complete reviewed execution manifest and resource admission |
| Publication | genome author; independent witness/reviewer | README conclusions, claim-specific limitations, reproducible evidence and commands, exact-revision review, GitHub delivery and exact-commit CI status | Partial publication is not scientific completion; missing required arms stay open |

This historical plan is not a claim that either fleet experiment completed.
The separate v2 study was later approved and frozen; five training admissions
completed and one was interrupted when the operator stopped the jobs.
No full v2 evaluation or routed superiority result was established.
Old resource ledgers and all completed/partial artifacts remain preserved.

The Mishe operational-transfer proposal is a separate shadow study, not evidence
of a deployed fleet; any operational trial needs its own registration and
authorization. Full research remains **open** through required experiments,
human gates, independent acceptance and reviewed delivery. Negative results are
valid conclusions; missing evidence is not a passing result.

## Historical material — not current scientific acceptance

The older narrative below is retained for provenance. Its affirmative fleet and
semantic-drift claims, training-cost guarantees and deployment descriptions have
not been established by the current controlled research and must not override
the conclusions and limitations above.

## Start here: evidence and study status

| Work | What is supported | What remains open |
|---|---|---|
| Offline fleet contract | **24/24** fixture checks: 14 adversarial operator cases, four routing cases, two adapter inventory checks, four safety decisions | Not live routing accuracy, model quality, or deployment safety |
| Operator policy | **41/41** synthetic held-out cases, **14/14** adversarial cases, **8/8** structured decisions | Lexical coverage and uncalibrated confidence; no robust real-world safety claim |
| Local structural drift | Immutable Git-object extraction and an identical-commit control | Descriptive path/byte/static-import changes only; no semantic inference |
| Registered fleet study | Frozen paired-comparison design and a reproducible overlap audit | Independent source units, training provenance/budgets, actual held-out routing, blinded style ratings and scientific acceptance |
| Architectural drift study | Frozen external sample and working measurement/inference components | Full four-estimand execution, controls, authorization reconciliation and independent acceptance; completion task remains open |
| Mishe transfer | Prospective shadow-evaluation design | No executed operational trial or production model change |

[The evidence ledger](docs/evidence-status.tsv) records claim-specific verdicts
and measured revisions. Historical values are not silently promoted by a new
fixture pass. See the [fleet registration](docs/study-registration.md),
[study gap analysis](docs/study-gap-analysis.md), and
[Mishe transfer design](docs/mishe-transfer.md) for requirements and limitations.

## Quick start: offline checks

Run from the repository root. Use an isolated environment on systems with
PEP 668-managed Python:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-eval.txt
.venv/bin/python scripts/fleet_benchmark.py --test
.venv/bin/python scripts/operator_policy.py --test
.venv/bin/python scripts/test_policy_consumer.py
```

Expected results: `fleet benchmark: 24/24`, `held-out policy: 41/41`,
`adversarial: 14/14`, `safety decisions: 8/8`, and `policy consumer: 4/4`.
The fleet fixture uses synthetic routing inputs and checks available specialist
weights; it does not run live model inference. These commands require no GPU,
Ollama server, or model download. Installing dependencies may require network
access. All counts describe bounded repository fixtures, not generalization.

## Architectural drift study

**Planned, assigned, and started; not complete.**
[The execution and completion plan](docs/architectural-drift-execution.md)
provides frozen inputs, runnable preflight/reproduction commands, dependency-ordered
work, acceptance gates, blockers and retry rules. **Genome owns completion;
witness owns independent acceptance.** The resident obligation is
`tiny-fleet-architectural-drift-completion-20260930`, kept open through report
review and delivery, not closed by writing this plan.

The [cross-repository protocol](docs/cross-repository-drift-protocol.md) requires
four distinct estimands:

1. **Structural:** paths, bytes, native units and dependency structure.
2. **Lexical:** normalized token/concept frequencies, stratified by path class.
3. **Behavioral:** common paired native probes in pinned environments.
4. **Generative:** frozen paired outputs for base, prompt-only and genuine LoRA
   arms, with pinned scoring, costs, controls and uncertainty.

The registered external sample is **Flask, Requests and Pydantic**, with six
immutable snapshots in the
[sample manifest](docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json).
The separate HTTPX/attrs/pytest run is
[descriptive generative evidence](docs/confirmatory-v1-reader-conclusions-20260914.md),
not a replacement registered sample or a publishable four-estimand result.

### Completion sequence

| Stage | Required outcome |
|---|---|
| Input/gate reconciliation — next resident step | Verify six archive hashes; bind model, excerpts, adapters and scorer; reconcile current review, blind-order and execution authorization |
| External structural/lexical measurement | Measure all six registered snapshots with license/exclusion accounting, frozen unit maps and lexical definitions |
| Paired native behavior | Resolve pinned environments and measure common old/new probes; suite pass counts alone are not drift |
| Generative execution | Independently approve a complete v2 manifest and resource admission before running the 162-record real-model matrix |
| Controls and interpretation | Retain raw failures, costs, paired scores, intervals, shuffled-label/leak/missing-artifact controls and per-arm decisions |
| Independent review and delivery | Reviewed four-estimand report, evidence-ledger/README update and recorded delivery; blocked required arms remain open |

On 2026-09-30, the six available external archives matched their registered
SHA256 values. The local structural comparison and identical-commit control
also ran successfully. Full-study gaps remain: archive-capable measurement and
bundle validation, paired behavioral estimates, a complete admissible generative
manifest/matrix, and independent scientific acceptance. The proposed
`cross-repo-drift` orchestration CLI is **not implemented**; do not treat its
protocol examples as runnable commands. The execution plan assigns these gaps
rather than hiding them behind a placeholder runner or a promised result/date.

### Reproduce the local structural slice

This standard-library path needs Python 3, Git and the two commit objects. Use a
fresh output directory: the extractor itself does not protect an existing run
from overwrite. This shell snippet creates separate comparison/control outputs:

```bash
RUN=$(mktemp -d /tmp/tiny-fleet-drift.XXXXXX)
OLD=4e87f2ee3644f53e2a9665195b9d6ddb933aa1d8
NEW=b23fbf708b954cbf5462ebcd2d7ef50036a3fb1d
python3 scripts/drift_extract.py --repo . --old "$OLD" --new "$NEW" \
  --run-dir "$RUN/comparison"
python3 scripts/drift_lexical.py --run-dir "$RUN/comparison"
python3 scripts/drift_extract.py --repo . --old "$NEW" --new "$NEW" \
  --run-dir "$RUN/identity-control"
python3 scripts/drift_lexical.py --run-dir "$RUN/identity-control"
printf 'Results: %s\n' "$RUN"
```

The pinned comparison measures **12 → 306 included text paths** and
**82,150 → 1,454,580 bytes**: 294 added paths, four changed paths, no removed
paths or identical-blob renames. Python modules grow 6 → 79; the measured local
import edge stays at one, with zero edge churn. The identical-commit control has
zero path/edge deltas and zero lexical concept delta.

Read `manifest.json`, `structural.tsv`, `python-edge-delta.tsv` and both file
inventories together. Edge rows bind source/target paths to their side's blob
SHA256. The extractor reads Git objects, not the working tree; it excludes
`generated`, `vendor`, `node_modules`, `runs`, `adapters`, `corpus`, binary or
invalid UTF-8 blobs, and gitlinks. Exclusions and Python parse failures remain
explicit. Static local Python imports are **not runtime dependencies**; dynamic
imports and non-Python dependencies are unobserved. Documentation is included,
so path growth alone does not identify architecture change. The lexical tool
records tokenizer/dictionary hashes; its counts are not semantic ground truth.

The optional [local artifact sink](scripts/drift_result.py) publishes a keyed
bundle atomically and verifies repeated publication without overwriting ambiguous
or changed results. Inspect `python3 scripts/drift_result.py --help` and run
`python3 scripts/test_drift_result.py` before adopting it. Local bundle idempotence
does not imply exactly-once inference, task completion or external delivery.

Earlier LTE vocabulary/cosine headlines and weekly `mesh-*` tracking are
historical or unverified. Their [historical report](docs/tiny-fleet-drift-report.md)
and [baseline audit](docs/architectural-drift-baseline-audit-2026-09-06.md) are
retained for provenance, not as current architectural or semantic findings.

## Operator policy: bounded middleware, not an LLM safety oracle

`models/operator-policy.json` contains lexical feature weights, precedence rules
and safe response templates. It runs deterministically without a GPU; confidence
is uncalibrated and latency is finite. It does not execute tools or prove that a
prompt is safe. Applications must retain their own authorization boundary.

```python
from scripts.operator_policy import load_model, respond, safety_decision
from scripts.policy_consumer import dispatch_decision

policy = load_model()
print(respond("A probe failed and returned zero.", policy))
decision = safety_decision("Delete the database from the only active session.", policy)
result = dispatch_decision(
    decision,
    execute=lambda d: "would execute an independently authorized action",
    review=lambda d: "queued for human review",
    escalate=lambda d: "queued for a specialist or human",
)
assert result == {"status": "held", "reason": "blocked"}
```

The callbacks above are inert examples, not approval or real execution.
`dispatch_decision` rejects malformed decisions and holds `block` decisions.
Only valid `allow` with `require_approval=False` calls `execute`; `review` and
`escalate` call their corresponding callbacks, never `execute`. The current
operator classes do not emit `allow`. Queueing a review is not permission to
perform the proposed action.

The centroid router checks the operator policy first, then selects a specialist
only above its coded margin threshold (`0.10`); otherwise it abstains. Live
centroid construction requires Ollama with `all-minilm`. The offline fixture
result is not an accuracy estimate for that live path.

## Model experiments and historical results

The original toy setup uses 60 synthesized passages per domain (48 train / 12
test), LoRA rank 16 on attention/MLP projections, five epochs and learning rate
`2e-4`. The previously reported guitar/sourdough perplexities are historical,
not reproduced findings at this revision:

| Model | Guitar test | Sourdough test |
|---|---:|---:|
| Base | 18.2 | 19.4 |
| Guitar LoRA | 11.5 | 15.5 |
| Sourdough LoRA | 13.8 | 12.2 |

Do not infer a routing win, generalization, training cost guarantee, or larger
semantic drift from these values. Specialization and fallback quality require
controlled measurement, not an asserted rule about small models.

The [registered fleet study](docs/study-registration.md) compares base,
prompt-only, pooled LoRA and routed specialists on identical cases, with grouped
uncertainty, safety coverage and resource accounting. Its frozen design and
budgets are separate from exploratory checkpoint measurements.
[The gap analysis](docs/study-gap-analysis.md) documents measured template
sharedness; distinct case IDs do not establish independent source units.

Live experiments are **opt-in**, not part of quick start:

- `scripts/mkcorpus.py` needs a local Ollama teacher and writes toy corpora;
  do not run it over frozen study inputs.
- `scripts/train_eval.py train` needs PyTorch/Transformers/PEFT and GPU capacity;
  registered training additionally requires its manifest/run-dir/seed inputs.
  Preserve prior adapters/runs and reconcile budgets before any training.
- `scripts/train_eval.py eval` loads the base and saved toy adapters on CUDA.
- `scripts/router.py` and `scripts/fleet_benchmark.py --live-router` require a
  running Ollama server and the `all-minilm` embedding model.

No unrelated GPU workload should be evicted to reproduce this repository.
Model caches, compatible dependency versions, admission and measured costs must
be recorded by the specific experiment; a bare package-install line is not an
immutable scientific environment.

## Evaluation contracts and layout

```text
scripts/operator_policy.py       deterministic policy train/eval and decisions
scripts/policy_consumer.py       callback dispatch with explicit execution boundary
scripts/router.py               operator-first centroid routing and abstention
scripts/fleet_benchmark.py       offline fixture / optional live-router checks
scripts/train_eval.py            toy LoRA training and perplexity evaluation
scripts/audit_study_independence.py  hash-bound all-domain overlap diagnostic
scripts/drift_extract.py         immutable Git-object structural measurement
scripts/drift_lexical.py         descriptive lexical measurements and controls
scripts/drift_generate.py        fixture and real-model versioned generative paths
scripts/drift_result.py          opt-in local bundle publication/reconciliation
corpus/                         toy/operator and registered study inputs
models/operator-policy.json     tracked policy artifact
adapters/                       local/checkpoint-dependent LoRA artifacts
runs/                           frozen registrations, outputs and decisions
docs/                           protocols, evidence, receipts and conclusions
```

Validate run integrity before interpreting scores:

```bash
python3 scripts/test_deep_evaluation.py
# Replace this path with an existing complete run, not an empty new directory:
python3 scripts/deep_evaluation.py --run-dir /path/to/complete-run
```

[The deep-evaluation contract](docs/deep-evaluation-contract.md) checks dataset
hashes/counts, split boundaries, required artifacts and prediction cardinality.
It rejects leakage, missing artifacts and inconsistent provenance; passing is
an integrity gate, not proof of scientific validity or deployment readiness.

## Further reading

- [Architectural drift execution and completion](docs/architectural-drift-execution.md)
- [Cross-repository drift protocol](docs/cross-repository-drift-protocol.md)
- [Confirmatory-v1 scope and reader conclusions](docs/confirmatory-v1-reader-conclusions-20260914.md)
- [Fleet study registration](docs/study-registration.md)
- [Measured study gaps](docs/study-gap-analysis.md)
- [Mishe shadow-transfer design](docs/mishe-transfer.md)
- [Claim-specific evidence ledger](docs/evidence-status.tsv)

License: [CC0 1.0 Universal](LICENSE). This project's dedication does not
relicense third-party models, repository snapshots or datasets; retain their
own license and redistribution requirements.

</details>
