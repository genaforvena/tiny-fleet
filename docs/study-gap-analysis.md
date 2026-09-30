# Study gap analysis and measured independence audit

## Conclusion

`fleet-study-v1` does not yet establish routed-specialist superiority. Its design asks the right paired question, but current evidence cannot discharge independent-source sampling, independent training replicas, genuine held-out routing, blinded style scoring, and cumulative resource accounting. More generations on the same templates do not fix those limitations.

This report closes a **reproducibility/diagnostic tooling gap**: a reusable, hash-bound all-domain/all-split overlap audit. It does not repair the frozen corpus, complete the registered science, or claim a production deployment. A prior resident passage-only overlap review already exists; this is an all-domain extension, not a new discovery of passage dependence.

Source inspected: `0c271da49d6c4354fefb153158fe45751e4cb05a`. Inputs: `corpus/study-v1/{train,validation,heldout,adversarial}.jsonl`; design: [study registration](study-registration.md) and `runs/fleet-study-v1/registration.json`; construction: `scripts/build_study_corpus.py:25–81`. The new audit is an additional descriptive analysis, not a silently amended registration.

## What other work establishes

| Primary work | Relevant mechanism | What this repository must still show |
|---|---|---|
| [LoRA, Hu et al.](https://arxiv.org/abs/2106.09685) | Low-rank adaptation of a shared base | Controlled task-quality improvement; adapter existence alone proves neither routing nor generalization |
| [S-LoRA, Sheng et al.](https://arxiv.org/abs/2311.03285) | Efficient serving of many adapters | Local throughput, latency, memory and total cost; many adapters are not automatically a quality win |
| [RouteLLM, Ong et al.](https://arxiv.org/abs/2406.18665) | Routing between models using preference information | Pinned pre-generation routing, comparison with strong controls, and quality/cost measurement on held-out inputs; their scale and model-choice setting differ |
| [MoErging survey, Yadav et al.](https://arxiv.org/abs/2408.07057) | Combining and routing among specialized experts | Explicit expert provenance, access assumptions and routing/evaluation protocol; the mechanism is not novel here |
| [AdapterFusion, Pfeiffer et al.](https://aclanthology.org/2021.eacl-main.39/) | Learned composition of task-adapter representations | Composition training/data and multi-adapter cost are a different intervention from top-one LoRA selection; complementary errors do not prove usable fusion |
| [WILDS, Koh et al.](https://proceedings.mlr.press/v139/koh21a.html) | Evaluation under real domain/subpopulation shifts with meaningful groups | Source/problem/repository ancestry and substantive held-out families, not merely disjoint numbered IDs; its code completion task is not executable-expression correctness |
| [Selective Classification, Geifman and El-Yaniv](https://arxiv.org/abs/1705.08500) | Explicit acceptance/rejection with conditional risk and coverage | Pin calibration/thresholds and report both denominators; classification risk conditional on acceptance is not adversarial false accepts over all attack cases |

These papers motivate comparisons, not borrowed performance claims. Tiny-fleet's plausible contribution remains a controlled small-model study with quality, safety coverage and costs together, including negative or inconclusive results. Mishe's role orchestration needs a separate operational experiment; it is not the same intervention as adapter routing.

## Actual measurement

```sh
python3 scripts/audit_study_independence.py \
  --corpus-dir corpus/study-v1 \
  --output .mishe-tauftauf/research/independence-audit-20260930-reviewed.json
```

Observed exit: **0**. Reviewed-implementation output SHA-256: `b77d30035d8ef02e3afb0bf689681eb41dc2b73e06d1aa5e54e42afb925f58c0`. The earlier output (`fc5cea0bc2af0a1ab41acc20e4df26851c7b212e4068005be0a3a6e88b3c4b38`) is preserved; corpus statistics are unchanged after a reviewer-found Unicode record-boundary repair. The local outputs are ignored; readers reproduce the audit at any fresh destination whose parent exists. The CLI refuses an existing destination, including symlinks, and never overwrites inputs or earlier reports. It uses only the standard library and does not import or execute the corpus generator.

| Input | SHA-256 |
|---|---|
| train | `b208a7dab05a34494e9672facb27341ec70d512b4f7b6f1df02d7d72b4188f4f` |
| validation | `8212842b2f0619c2557c4a3d3f9ab4c19c6470fabbfd87d5183cb0c7ff602e46` |
| heldout | `e509d767dab388fa99c4e1e117843db76d8403f6203ce2c2a62c97216d786040` |
| adversarial | `d57dcfcda2691d63f68727b08fc4ce2b06b40a203327da71103672578001b213` |

All four hashes match the existing corpus manifest. There are **1,600 rows**, **400 per split**, **100 per split/domain**. All 1,600 case IDs, source IDs and declared source-family labels are unique. There are no cross-split source-label collisions. That is a label property, not proof of source independence.

Train/held-out comparisons, within each domain:

| Domain | Equal reference row pairs after whitespace normalization | Equal full prompt/reference pairs | Equal references after numeric-marker removal |
|---|---:|---:|---:|
| passage | 100 | 0 | 10,000 |
| executable code | 10,000 | 0 | 10,000 |
| rated style | 10,000 | 0 | 10,000 |
| adversarial safety | 10,000 | 0 | 10,000 |

Pair counts are Cartesian products of equal-value buckets; they are **not** independent sample counts. Each of the 100 code/style/safety references matches every training reference in that domain. Passage references match the same observation number. These are reference-only collisions with different stored prompts; do not call them full-example leakage or proof of causal contamination.

Within each held-out domain, numeric-template normalization produces **4,950 equal full-example row pairs**, all unordered pairs among 100 rows. Thus each domain's held-out rows has one common normalized prompt/reference form under this diagnostic. The source generator explains the construction: a domain-specific branch, numeric case markers and a split-bearing prefix, while source-family labels are assigned per row. Numeric removal preserves split words, so zero cross-split full-example overlap does not establish substantive independence.

**Limits:** whitespace normalization retains case/punctuation; numeric normalization can erase meaningful constants and is exploratory. Neither establishes true ancestry, effective sample size, pretraining contamination, rendered few-shot overlap, training lineage, safety, or generalization. Hashes bind the bytes inspected, not provenance truth. Frozen inputs are preserved; a corrected independent corpus requires a new study ID.

## Verification actually exercised

- Real frozen-corpus CLI: exit 0, 1,600 rows and exact input/output hashes above.
- Isolated CLI fixture: duplicate IDs across splits and a full prompt/reference collision were reported correctly.
- Existing-destination attempt: exit 2; destination bytes unchanged.
- Malformed JSONL: exit 2 with line context; no output created.
- Independent brute-force smoke: 400 randomized checks of matching-pair/participating-row counts, covering within-split, cross-split and reference-only comparisons.
- Reviewer-found Unicode JSONL boundary defect: reproduced exit 2 on valid strings containing U+2028/U+2029; changed record splitting to LF only; the same CLI scenario then exited 0 with all four rows.
- `python3 scripts/test_audit_study_independence.py`: two retained regressions passed, covering literal Unicode separators with CRLF records and rejection of a blank physical record.

The fixtures were temporary and removed automatically. These checks validate the auditor's behavior; they do not validate the scientific hypothesis. No model evaluation or training was launched for this audit. The resident full checkpoint experiment was left undisturbed.

## Gap map and closure gates

| Priority / gap | Current evidence / missing evidence | Concrete closure | Owner |
|---|---|---|---|
| P0 — independent source units | Measured templates despite unique labels | New separately registered corpus: whole source/problem/template/time families split before normalization; document original ancestry, audit overlaps and prospectively justify sample size | genome + discover; witness review |
| P0 — actual router, not oracle | Current resident plan reports fixture calibration and no genuine held-out route/abstain tape | Pin router from training/calibration only; emit decisions before generation; compare metadata rule and strongest non-routed controls on identical cases; measure all route/abstain outcomes | genome; witness review |
| P0 — training provenance and budgets | Resident receipts report seed 17; generation seeds are not independently trained weights; cumulative costs unresolved | Per-checkpoint hashes, training command/source/seeds, actual batch behavior and cumulative GPU/wall accounting. Reconcile declared run cap before new jobs; unavailable history remains UNKNOWN | genome |
| P1 — executable correctness | Exact-reference matching cannot admit equivalent correct programs | Retain raw outputs and failures; a separately labelled sandbox/whitelist evaluator with fixed edge fixtures, never unrestricted generated-code execution | active resident panel analysis; witness review |
| P1 — style | No independent blinded ratings | Anonymized arm-blind ratings, registered 1–5 rubric and inter-rater agreement; until then UNSCORED, not keyword-scored | independent raters + witness |
| P1 — safety and useful coverage | Refusal-explanation canaries are not observed adversarial routing decisions | Realistic redacted threat cases, pinned decision policy, false-accept upper bound and useful coverage with retained denominators; distinguish text from action | genome + witness |
| P1 — costs | New-panel CPU costs can be measured; historical aggregate incomplete | Full successful/failed attempt accounting; wall, tokens, memory, routing/serving overhead. No zero-latency claim and no duplicated batch times | genome |
| P1 — diagnostic reproducibility | Passage-only resident analysis existed; all-domain reusable measurement was missing | **Filled here:** hash-bound standard-library audit, real execution, overlap counts, no-overwrite/error smoke, documented limits | this change; independent review required |
| P2 — external validity / Mishe transfer | No operational role-routing trial | Separate prospective shadow study with independent task families, generalist controls, real isolated execution and costs; no production change from synthetic PPL | discover + genome + witness |

The original registration remains immutable. Its 12-training-run cap must be reconciled with intended arms and seeds rather than silently authorizing an extra job. Unknown historical budgets are not permission to retrain. Missing independent ratings and a new operational task corpus cannot be supplied by a control-test receipt. Remaining gates stay visible; negative/inconclusive results are valid deliverables.

## Transfer to mishe-tauftauf

[The transfer protocol](mishe-transfer.md) specifies a separately frozen generalist-versus-role-dispatch shadow trial. Immediate local adoption routes a review-bound next step to discover rather than changing production models or the external kernel. The local feed sample `2107..2128` contains two health work receipts (2110 and 2123) with the same archived handoff hash; that is concrete motivation to bind work outcomes to episodes and not count repeated receipts as independent results. It does not prove either live check was invalid.

Keep three gates separate: **operational health**, **artifact integrity**, and **scientific acceptance**. A green pane, successful file hash, or successful audit is not a registered routing win.
