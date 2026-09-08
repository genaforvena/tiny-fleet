# Application hypotheses for tiny specialist models

Status: exploration portfolio, registered 2026-09-08. **None of the benefits below has been measured in Tiny Fleet yet.**
Implementation owner: haunt. Independent verification: vpn after each task.
[Executable task plan](superpowers/plans/2026-09-08-publication-science.md), sections A00–A10.
[Live-ledger input](plans/applications-20260908.tsv).

## A00 frozen screening contract

The machine-readable registry is `runs/applications/registry.json`; it is the
single pre-scoring record of each application’s input/output schema, explicit
baseline competitors, metric, gate, source provenance, resource ceiling, state
and run hashes. Validate it offline with:

```bash
rtk proxy .venv/bin/python scripts/application_screen.py \
  --registry runs/applications/registry.json --validate
```

The shared harness does not load a model, call a network, execute an operating
system command, or score a live run. Later task modules must expose
`predict_baseline(case) -> dict` and `score_case(case, prediction) -> dict`,
while retaining raw outputs and explicit unavailable reasons. A source family
is the independence unit: duplicate families cannot increase the denominator.
Missing values are null plus a reason, never zero; a score is a probability
only when calibrated. The exact one-sided 95% upper bound after zero failures is
`1 - 0.05**(1/n)`: 299 independent units are required for a 1% bound and 598
for 0.5%. A no-go or inconclusive result is a valid terminal screening result.

## Why explore this

Tiny models are most credible where the input domain is bounded, the output is short or structured, correctness can be checked, and abstention has a safe downstream meaning. A 360M causal LM is only one candidate: an encoder, byte-level sequence model, parser or linear classifier may be the better instrument. The experiments must allow that outcome.

The fleet hypothesis is separate: even if a tiny model wins one task, routed specialists must beat a matched pooled adapter or simple selector after embedding, adapter-loading and fallback costs are included. Neither parameter count nor a lower passage perplexity establishes user value.

Prioritize command interpretation, extraction and queue routing because their decisions are easy to score. Reuse one runner, immutable manifests and source-family splits; avoid a separate framework for every application.

## Portfolio

| Task | Application and bounded output | Primary precedent (feasibility, not our result) | Baseline | Proposed screening gate |
|---|---|---|---|---|
| A01 | Offline read-only command interpretation: Parse 10 declared read-only intents into {function,arguments} or unknown; simulator only, no OS calls. | [FunctionGemma 270M](https://ai.google.dev/gemma/docs/mobile-actions) | regex/grammar; TF-IDF linear intent classifier; base 360M; FunctionGemma as optional pinned comparator | exact function+argument accuracy >=95%; OOD false-accept one-sided 95% upper bound <=1%; >=5 percentage-point paired gain over strongest simple baseline |
| A02 | Ticket text to evidence-backed JSON: Extract product/version/issue/requested_action and exact evidence spans; absent values null. | [NuExtract-tiny](https://huggingface.co/numind/NuExtract-tiny) | regex+dictionary; base 360M; pinned NuExtract-tiny | field precision >=95%, recall >=90%, unsupported-field rate <=1%; paired improvement or documented cost advantage over baseline |
| A03 | Normalize logs without inventing diagnoses: Extract component/error_code/operation/timestamp/evidence_span; no root-cause field. | [NuExtract authors; transfer hypothesis](https://huggingface.co/numind/NuExtract-tiny) | existing regex/template parser; base 360M; extraction adapter | >=5-point exact-record gain on heldout applications; known-format degradation <=1 point; unsupported-field rate <=1% |
| A04 | Local cited runbook retrieval with no-answer handling: Retrieve up to five paragraph IDs from frozen public manuals; return no-answer when support is absent. Generation optional and separately scored. | [EmbeddingGemma 300M](https://deepmind.google/models/gemma/embeddinggemma/) | BM25; current all-MiniLM; pinned EmbeddingGemma; optional 360M query rewrite | Recall@5 >=5 points above strongest simple baseline; no-answer false acceptance <=5%; publish CPU/RAM tradeoff |
| A05 | Duplicate issue detection with an abstain result: Match ticket to same-incident ID or none; do not equate shared symptoms with shared incident. | [EmbeddingGemma; application hypothesis](https://deepmind.google/models/gemma/embeddinggemma/) | normalized hashing; character n-gram cosine; BM25; all-MiniLM | pair precision >=95% and recall gain >=5 points over baseline at matched precision; report candidate-retrieval recall separately |
| A06 | Small-model queue routing versus linear classification: Route to 8 fixed support queues plus unknown; preserve operator-first gate when used in fleet. | [EmbeddingGemma; application hypothesis](https://deepmind.google/models/gemma/embeddinggemma/) | TF-IDF logistic regression; nearest centroid; base 360M; LoRA classifier | macro-F1 >=3-point gain OR noninferiority within 1 point with >=20% measured latency/RAM benefit; OOD false acceptance <=5% |
| A07 | PII highlighting with explicit residual-risk reporting: Find character spans for declared PII types in synthetic/public licensed documents; human-review suggestions only. | [GLiNER2-PII preprint](https://arxiv.org/abs/2605.09973) | regex; existing NER; pinned small span extractor; optional tiny-fleet tagger | per-critical-type recall >=99%, precision >=90%, exact offsets correct; any insufficient type remains insufficient-data |
| A08 | Domain OCR/typing correction with protected fields: Correct one frozen document domain while preserving numbers, IDs, paths and already-correct text. | [ByT5 paper](https://arxiv.org/abs/2105.13626) | identity transform; dictionary/edit-distance; pinned ByT5-small; 360M LoRA | >=20% relative character-error reduction vs strongest baseline; clean-field corruption <=0.5%; protected fields unchanged |
| A09 | One bounded transliteration/diacritic-restoration task: Select one language/alphabet transformation; protect literal IDs and exact-copy spans; unknown names may abstain. | [ByT5 paper](https://arxiv.org/abs/2105.13626) | deterministic transliterator plus lexicon; pinned ByT5-small; base and LoRA | >=5-point exact-word gain on unseen word/name families with protected spans unchanged; report ambiguous references separately |
| A10 | Natural-language actions in a deterministic toy world: Emit typed commands to an in-memory grid simulator; single and two-action compositions, unknown means no state change. | [FunctionGemma TinyGarden](https://deepmind.google/models/gemma/functiongemma/) | hand grammar; base 360M; pinned FunctionGemma; tiny-fleet adapter | single-action final-state success >=95%, heldout two-action >=85%; invalid/OOD commands leave state unchanged; report gain over grammar |

The gates are **proposed experimental choices**, not numbers attributed to the cited models or universal guarantees. Freeze them before looking at test outcomes. “>=5-point gain” means percentage points for a bounded accuracy/recall scale. Compare paired source units; record uncertainty and treat an interval crossing a decision boundary as inconclusive.

## Exploration budget and stopping

A00 registers all inputs and budgets. Start with a simple baseline and corpus adequacy check; use a single seed-17 adapter only if there is measurable headroom. Initial ceiling: 30 GPU minutes per application, one GPU job at a time, plus explicitly recorded CPU and labeling time. This is a bounded screening budget, not a promise that every study fits it.

A no-go requires evidence: baseline already meets target at lower cost, model fails a prespecified quality/safety boundary, or independent data cannot be acquired. An unavailable runtime is an infrastructure block, not evidence that the idea has no merit. Selected candidates receive a separately frozen three-seed confirmation using reserved cases; new heldout data is required after tuning on a pilot result.

Low observed failure rate is not automatically a tight guarantee. For zero observed failures in n independent cases, the exact one-sided 95% upper binomial bound is `1 - 0.05**(1/n)`: at least 299 zero-failure cases are needed for a <=1% bound, and 598 for <=0.5%. This arithmetic assumes independent units; paraphrases or all pairs of the same incidents do not create that independence.

## Boundaries that make the results useful

- Command and game experiments emit typed values into an in-memory simulator; no OS, network or actuator execution.
- Extraction requires supporting spans and null for missing values. Invalid JSON, fabricated fields and timeouts count as failures.
- Retrieval reports support and no-answer behavior separately from fluent answer generation.
- PII work is reviewed highlighting on synthetic/public licensed data, not a claim of complete anonymization.
- Correction/transliteration must protect numbers, identifiers and already-correct text.
- Corpus source, license, privacy checks, model revisions, peak memory, cold/warm latency and errors are part of every result.
- Negative findings remain public artifacts. No adapter is enabled in the mesh by an exploration result; use the existing pilot and independent verification gate.

## Board dispatch: operator-prioritized application

The operator asked whether tiny models fit board dispatch. Yes: interpreting an unowned free-text task and ranking eligible specialists is a plausible bounded classification problem. Test it against the actual current rules, TF-IDF classification and embedding centroids; many explicit-owner tasks already have a deterministic answer and should not inflate model accuracy.

Four additional implementation tasks, each followed by vpn verification, are registered in [board-dispatch plan](plans/board-dispatch-20260908.tsv), sections B01–B04 of the execution plan: frozen as-of-state corpus, simple baselines, constrained tiny adviser, and chronological offline/shadow evaluation. This is an application hypothesis, not a deployed capability.

The model proposes task class and ranked eligible IDs or abstains. The deterministic system enforces explicit owner, whitelist, lease, dependencies, retry policy and duplicate prevention. It never asks the model whether to ignore these constraints. Malformed recommendations remain visible even when the guard rejects them. Replay cannot establish actual acceptance or task-completion gains; those need a later real shadow pilot.

The proposed screen requires a >=5-point suitable-owner accuracy gain with positive paired-interval lower bound, >=25% useful coverage, zero final constraint violations, and <=250ms p95 CPU advisory latency on named hardware. Cost and raw invalid proposals are reported. If simple rules win, the result is a useful no-go for adding tiny inference to this path.

## Architectural drift

Drift is a separate hypothesis: does a model-derived change signal track independently evidenced architecture/behavior change beyond text-size or vocabulary changes? The D01–D04 tasks cover portable extraction, lexical controls, generative controls and independently labeled validation. The existing external-repository ledger chain owns sampling at least three independent repositories and the actual comparative run. Cosmetic changes, same-snapshot variance and label shuffling are mandatory controls. A good lexical detector may still fail as an architectural detector; that distinction is itself reportable.

## Evidence consulted

Primary sources above were opened during the review on 2026-09-08. FunctionGemma documents a 270M function-calling model and an offline specialization workflow; NuExtract-tiny is an author-published extraction model; EmbeddingGemma is a small retrieval model; ByT5 studies byte-level sequence modeling; GLiNER2-PII is a PII extraction preprint. Their task-specific results and hardware configurations are not transferable Tiny Fleet measurements. Resolve and pin actual model versions, licenses and runtimes when a task begins.
