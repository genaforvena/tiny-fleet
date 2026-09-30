# tiny-fleet

Can a shared **360M base model**, small specialist LoRA adapters, and a router
improve task quality at bounded cost?

This repository investigates that question using
[SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct),
toy guitar/sourdough specialists, an embedding-centroid router with abstention,
and a separate deterministic operator-policy baseline. It also studies changes
between pinned repository snapshots. **Neither routed-specialist superiority nor
semantic architectural drift is an established result here.**

The original inspiration was
[BbyWVY-360m](https://huggingface.co/StarpowerTechnology/BbyWVY-360m);
[behavior notes](docs/bbywvy-360m-notes.md) record the narrow-model experiment.

## Research conclusions — 2026-09-30

**Specialization improved reference likelihood on the toy passage task, but did
not establish useful generation, routing superiority, or deployment safety.**
These are interim exploratory measurements of saved seed-17 checkpoints, not
the registered three-training-seed replication.

Four completed CPU/fp32 arms contain **3,200 validated outputs**, 800 per arm:
100 cases in each of four domains in each held-out/adversarial split. Three
specialist arms are still running and are excluded from this snapshot.

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

### Completion plan and distribution

| Workstream | Execution owner | Required experiments / acceptance | Current prerequisite |
|---|---|---|---|
| Existing exploratory CPU panel | genome; witness reviews | Finish seven arms / 5,600 outputs; validate exact inputs, raw hashes, all denominators, code fixtures and costs; preserve failures | Running evaluator and event-driven finalizer; no restart or decoding changes |
| Original frozen fleet study | genome; discover audits provenance | Reconcile training seeds and cumulative budgets, source dependence and missing route tapes; retain negative/inconclusive findings | Do not silently repair a frozen design by replacing corpus or adapters |
| Separate fleet v2 replication | genome; discover audits source families; senses checks bindings | Freeze reviewed corpus/router/source; pooled plus four specialists × training seeds 17/29/43; compare base, prompt-only, pooled, candidate and metadata routing; validate 7,500 prescribed exports, paired source-group contrasts, risk and coverage | Independent **human sandbox review** before freeze/training; then one training job at a time, at most 15 trainings, 12 cumulative GPU-hours / 24 model-execution wall-hours |
| Blinded style scoring | Two independent human raters; witness accepts | Randomized blinded 1–5 sheets, independence attestations, agreement and missingness analysis | Real rating sheets; automated/self-ratings cannot substitute |
| Architectural drift | genome; discover handles source/license/unit inventory; witness accepts | Registered Flask/Requests/Pydantic old/new snapshots: structural, lexical, paired native behavior, 162-record gated generative matrix; identity/shuffle/leak/missing-artifact controls | Archive measurement path, pinned paired probes, complete reviewed execution manifest and resource admission |
| Publication | genome author; independent witness/reviewer | README conclusions, claim-specific limitations, reproducible evidence and commands, exact-revision review, GitHub delivery and exact-commit CI status | Partial publication is not scientific completion; missing required arms stay open |

The separate v2 corpus admission and validation-only router calibration are
complete locally, but its registration is **not frozen**, no v2 models have been
trained, and no held-out routed result exists. New v2 results must remain separate
from the original study and this exploratory panel. No unrelated GPU job may be
evicted and failed attempts must never reset the resource ledger.

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
