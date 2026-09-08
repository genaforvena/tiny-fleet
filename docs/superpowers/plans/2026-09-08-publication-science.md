# Tiny Fleet publication and scientific evaluation implementation plan

> **For agentic workers:** Use the executing-plans workflow task-by-task. The operator explicitly assigns implementation to **haunt** and every separate verification task to **vpn**. This task-specific assignment applies even if a window's normal charter concerns another project. Repository root is **/home/mesh-home/tiny-fleet**, never hyperhauntology_for_kids. Do not change charters.

**Goal:** Turn Tiny Fleet into a reproducible, honestly scoped research artifact with validated experiments and useful application explorations.

**Architecture:** Keep a shared small base and isolated per-run adapters; validate inputs and raw predictions before independently deriving results. Separate the fleet experiment, deterministic policy baseline, drift methodology, and application studies. A negative result can complete an experiment; it cannot qualify a model for serving.

**Tech stack:** Existing Python, NumPy, PyTorch, Transformers/PEFT, optional pinned local embeddings. CPU validation stays small; no new generic agent framework. Use existing study contracts and refactor shared code only where tasks require it.

## Global execution and verification rules

- This plan was written against `62ba7282505eb447486b9a18468cce72457171ce`. Re-read current files before editing; preserve others' work. Read [review](../../publication-review-20260908.md) and [applications](../../applications.md).
- Every implementation task has an immediately following independent vpn verification step in the same ledger chain. The task descriptions below plus their Files, Interface, Steps, Check and Acceptance blocks are the full scope; a worker should read its complete section and this global block.
- `haunt` writes code/data/docs and an implementation receipt. `vpn` checks an explicit submitted commit in a separate temporary clone/worktree, reruns commands and negative controls with isolated output paths, then writes a verification receipt. vpn does not approve its own fixes. Both commit/push only scoped changes and verify the remote contains the submitted commit.
- Each receipt is `docs/task-receipts/<ID>-implementation.md` or `docs/task-receipts/<ID>-verification.md`; use unique filenames and preserve earlier failed attempts as dated evidence. Include actor, repository absolute root, submitted source revision, UTC time, command, exit status, stdout/stderr artifact path+SHA256, result and exact next action. Never cite an unrelated repo.
- Implementation `done` means ready for independent verification. Only vpn's successful verification unlocks the next implementation. The live task system enforces ordering, ownership and artifact existence/hash, **not scientific correctness**; vpn must inspect semantic acceptance criteria.
- vpn checks `git diff`, exact file scope, artifact hashes and claimed commands independently; author-written PASS text, a file's existence, test counts, or another model's summary is insufficient. Documentation tasks need verified claims/links/commands, not arbitrary new unit tests.
- For code gates, first reproduce failure, then fix, then run. vpn deliberately mutates one load-bearing behavior in its isolated checkout and observes the relevant test FAIL; restores the original and observes PASS. Never mutate live tapes, model runs or the shared checkout. Capture both results. Tests cannot write live liveness/board logs.
- **Verifier output isolation:** never replay a training/run command into the author's completed run directory. Read its manifest, make a temporary verification directory with `rtk proxy mktemp -d`, and pass that absolute path to output/run-dir arguments. Copy raw input artifacts to the temporary directory before rescoring; retain originals untouched. S06-V gives a concrete bounded reproduction command. CPU tests run unchanged. A valid no-go is verified by its evidence and result validator, not by unconditionally launching a training command.
- For empirical tasks vpn recomputes scores from raw predictions, samples actual inputs/outputs, checks source-family independence, prompt/reference separation, model/data hashes and all timeout/error rows. Require an independently repeated deterministic slice and, where claims rely on training, a bounded rerun with specified seed and tolerance. Rescoring a file is not a training reproduction.
- **Failed verification:** write a FAIL receipt, call `mesh-task block CHAIN VERIFY_SLUG dependency "verification-failed; haunt: exact failed predicate and repair artifact needed" "retry after corrected commit"`, and open a specifically keyed corrective task owned by haunt. Do not call done, silently waive the gate or reinterpret absent data as a negative result. On repair evidence, vpn resumes its verification via `mesh-task resume CHAIN VERIFY_SLUG corrected-commit-SHA` and retests. Resume restores active state. `dependency` is a supported blocker type in the live coordinator; `verification-failed` is explanatory text, not a supported type.
- **External dependencies:** named dependencies in another chain are checked manually before work. If unmet, record `mesh-task block CHAIN SLUG dependency "exact chain/step and required artifact" "retry on dependency completion"`. Never mark a blocked task done merely to advance. A documented statistical no-go with valid data is a completed exploration, not an infrastructure block.
- Every task may finish with a rigorously measured negative finding where its Acceptance permits it. Report interval uncertainty and data insufficiency. Never keep training until a desired positive result appears.
- No runtime deployment, mesh routing, actuator use, scheduling, paid API spend, external paper submission or release announcement is authorized by an experimental task. Existing real-mesh pilot chain owns its bounded implementation; existing publishable-closeout chain owns final README/evidence assembly. Operator authorization for prior dependency installs persists in the existing runtime task.
- No private operator messages, credentials or raw mesh logs are copied into public datasets. Preserve upstream model/data provenance; the repo's license is not assumed to relicense dependencies.
- All code paths in a future task are exact proposed interfaces, not claims they already exist. Create and test the interface before running the supplied command.
- An implementation task is one bounded deliverable, usually several small actions. GPU runs are resumable and capped; never evict shared workloads. Resource failure is an honest typed block.
- Apply deliberate edits with `apply_patch`; prefix shell commands with `rtk`. Commit only that task's files and receipt. Read exact ownership/status before acting; never impersonate another owner.

## Existing ledger identities to retain

The review records nine remaining steps in four existing chains: runtime provisioning, final repository closeout, real-mesh pilot, and external drift study. They remain live; new tasks provide missing concrete components. Existing witness verification tasks remain witness-owned; the operator assigned **new** verification tasks to vpn. C01 reconciles expired/wrong-repository receipts without rewriting history. The related hire workspace-repair and tg plan-sweep tasks are not re-created here.

## Order

Main chain: C01–C08 correctness → S01–S09 experiments → P01–P04 distribution/presentation, each interleaved with vpn verification.
Drift chain: D01–D04 methods, each interleaved with vpn verification; existing external-repo chain consumes it.
Application chain: A00 shared protocol → A01/A02/A06 priority pilots → A03/A04/A05/A07–A10, each interleaved with vpn verification.
Board-dispatch chain: B01 frozen as-of corpus → B02 deterministic/simple baselines → B03 tiny advisory selector → B04 chronological shadow verdict, each interleaved with vpn verification. No live dispatch changes are part of these tasks.
Cross-chain prerequisites are explicit below. All four roots may be registered now; registration is not a claim that a worker has started.

## Minimum receipt commands

A worker substitutes the exact CHAIN and SLUG printed in its section; only the named owner runs take/done. Example first implementation:

```bash
rtk proxy env MESH_TASK_ACTOR=haunt mesh-task take tinyfleet-publication-science-20260908 reconcile-evidence
# Complete C01, commit its files, capture checks and verify pushed commit.
rtk proxy env MESH_TASK_ACTOR=haunt mesh-task done tinyfleet-publication-science-20260908 reconcile-evidence /home/mesh-home/tiny-fleet/docs/task-receipts/C01-implementation.md "Submitted for vpn verification; source revision and checks in receipt"
```

Next owner:

```bash
rtk proxy env MESH_TASK_ACTOR=vpn mesh-task take tinyfleet-publication-science-20260908 verify-reconcile-evidence
# Independently verify C01 using the exact submitted commit.
rtk proxy env MESH_TASK_ACTOR=vpn mesh-task done tinyfleet-publication-science-20260908 verify-reconcile-evidence /home/mesh-home/tiny-fleet/docs/task-receipts/C01-verification.md "PASS: independent verification; evidence and residual limitations recorded"
```

## C01: Correct the repository-specific claim and obligation map

**Ledger implementation:** `tinyfleet-publication-science-20260908/reconcile-evidence` — owner haunt.

**Files:** `docs/publication-review-20260908.md`; `docs/evidence-status.tsv`; `docs/ledger-reconciliation-20260908.md`.

**Dependencies:** None; inspect all four existing chains listed in the review first.

**Interface/output:** A table with claim_id, claim_text, evidence_path, sha256, measured_revision, verdict, existing_task, successor_task. Verdicts: verified-bounded, historical-unreproduced, failed-control, blocked, not-tested.

**Steps:**

- [ ] 1. Record current git revision and owner-authored progress for the four existing chains. Wrong-repository receipts under hyperhauntology_for_kids are insufficient. Do not act as witness/hire or settle their tasks.
- [ ] 2. Map every README numeric claim and every completed-chain blocked outcome to evidence. Explicitly preserve persona eval/v2 and the already-fixed self-test CLI; count unique heldout texts (currently one per domain).
- [ ] 3. Add correction instructions to the existing closeout scope: prompt conditioning is not training; remove unsupported causal/capacity explanations, zero-latency claim, and presumed LoRA divergence. Reference README claims rather than rewriting someone else's concurrent work.
- [ ] 4. Record real next commands for expired haunt work using mesh-task progress and a new repository-local receipt. Completion of this reconciliation does not discharge old runtime/pilot/drift/closeout tasks.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python -c 'import csv,pathlib; r=list(csv.DictReader(open("docs/evidence-status.tsv"),delimiter="\t")); assert r and all(x["claim_id"] and x["verdict"] and (not x["evidence_path"] or pathlib.Path(x["evidence_path"]).is_file()) for x in r)'
```

**Acceptance:** All public headline claims and four active-chain roots have a row and exact successor/dependency; no absent artifact called verified. Receipt contains Tiny Fleet root and current revision.

**Implementation receipt:** `docs/task-receipts/C01-implementation.md`.

### C01-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-reconcile-evidence`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C01 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C01-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## C02: Reject leaked or out-of-root datasets

**Ledger implementation:** `tinyfleet-publication-science-20260908/validate-dataset-boundaries` — owner haunt.

**Files:** `scripts/deep_evaluation.py`; `scripts/test_deep_evaluation.py`; `docs/deep-evaluation-contract.md`.

**Dependencies:** C01

**Interface/output:** Manifest schema v2 adds actual prompt/reference content, source_family and timezone-aware times; legacy v1 is readable for archival inspection but cannot return publication-ready.

**Steps:**

- [ ] 1. Add fixtures for duplicate IDs within a split; identical normalized prompts across splits with different IDs/provenance; train-validation and validation-heldout source_family overlap; zero-row required split; malformed JSON types; relative traversal and symlink escape.
- [ ] 2. Resolve run root and dataset targets before containment tests. Require nonempty typed rows; normalize actual prompt text with Unicode NFKC, casefold and collapsed whitespace. Hash prompt/reference separately; reject exact cross-split duplicates. Keep family IDs independent of split names.
- [ ] 3. Clarify cutoff semantics: acquisition cutoff is a maximum inclusion time; temporal holdout additionally declares its own train_end and heldout_start. Reject naive timestamps and contradictory windows. Do not reinterpret old artifacts under the new contract.
- [ ] 4. Update fixture builder with distinct real prompts and explicit references. Keep near-duplicate threshold screening in S02; report normalized exact matches now.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_deep_evaluation.py
```

**Acceptance:** Every listed negative fixture exits nonzero with manifest-mismatch/leakage/split-boundary; valid v2 fixture passes, escaped paths are never opened.

**Implementation receipt:** `docs/task-receipts/C02-implementation.md`.

### C02-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-validate-dataset-boundaries`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C02 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C02-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## C03: Make predictions unique, typed, and bound to inputs

**Ledger implementation:** `tinyfleet-publication-science-20260908/validate-prediction-identity` — owner haunt.

**Files:** `scripts/deep_evaluation.py`; `scripts/test_deep_evaluation.py`; `docs/deep-evaluation-contract.md`.

**Dependencies:** C02

**Interface/output:** Prediction key=(case_id,model,seed,repetition); manifest declares exact matrix. Required output fields: case_prompt_sha256, rendered_input_sha256, output, route, action, confidence, confidence_kind, latency_ms, status.

**Steps:**

- [ ] 1. Add the reproduced duplicate-pair case as a regression. Also reject unknown model, duplicate model IDs, missing key, extra repetition, stale case_prompt_sha256 or rendered_input_sha256, non-finite confidence/latency, negative latency, missing output on status=ok, or absent timeout row.
- [ ] 2. Compare a Counter of expected keys to observed keys, never only sets. Status enum is ok/timeout/error; unavailable values are null with reason, never invented zeros. Raw output is retained even when scoring fails.
- [ ] 3. Require immutable base/tokenizer revisions and candidate hashes syntactically and check local referenced artifact hashes before publication validation. Define seed/repetition as integers; reject bools and malformed metadata.
- [ ] 4. Retain a raw-output schema version and migration report; do not fabricate fields to upgrade old v2 persona runs.
- [ ] 5. case_prompt_sha256 hashes the dataset's prompt bytes, identical across arms. rendered_input_sha256 hashes the exact stored rendered_input bytes sent to the model, including train-only examples/templates; it may differ by arm. Both are verified independently. Store template/config digests; reference is forbidden in rendered input except coincidental text documented by an explicit fixture.
- [ ] 6. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_deep_evaluation.py
```

**Acceptance:** Duplicate-prediction reproducer now rejects; every case/arm/repetition accounted for including failures; raw historical artifacts unchanged.

**Implementation receipt:** `docs/task-receipts/C03-implementation.md`.

### C03-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-validate-prediction-identity`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C03 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C03-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## C04: Validate report contents and distinguish validity from experiment success

**Ledger implementation:** `tinyfleet-publication-science-20260908/validate-derived-reports` — owner haunt.

**Files:** `scripts/deep_evaluation.py`; `scripts/report_contract.py (new)`; `scripts/test_report_contract.py (new)`; `docs/deep-evaluation-contract.md`.

**Dependencies:** C03

**Interface/output:** validate_reports(run_dir: Path) -> dict with artifact_valid and result_status. Report schemas/version and formulas are explicit; publication eligibility is separate from a model win.

**Steps:**

- [ ] 1. Replace nonempty/existence-only checks with JSON/TSV parsing, required headers, finite numeric fields, nonnegative counts, and referenced case/model/seed membership.
- [ ] 2. Routing/adversarial rows must reconcile against raw prediction route/action fields and frozen expected labels. Counts include timeouts. For unknown rubric outcomes preserve unscored and block a quality claim.
- [ ] 3. Check sums, slice denominators, basic accuracy/false-accept counts, latency quantiles and aggregation recipe. Later S04 supplies full statistics; validator independently recomputes primary counts instead of trusting generated summary.
- [ ] 4. Add tampering tests: empty file, invalid JSON, edited routing count, unsafe action mislabeled safe, omitted failed case, and all-abstain report called useful. Valid negative-result bundle must pass artifact validation while routing eligibility fails.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_report_contract.py
```

**Acceptance:** All tampered reports rejected. A complete failed experiment remains publishable as a negative artifact, never eligible to serve.

**Implementation receipt:** `docs/task-receipts/C04-implementation.md`.

### C04-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-validate-derived-reports`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C04 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C04-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## C05: Correct padding and next-token loss accounting

**Ledger implementation:** `tinyfleet-publication-science-20260908/correct-causal-loss` — owner haunt.

**Files:** `scripts/train_eval.py`; `scripts/persona_code.py`; `scripts/loss_metrics.py (new)`; `scripts/test_loss_metrics.py (new)`.

**Dependencies:** C03

**Interface/output:** masked_labels(input_ids, attention_mask) -> labels; summed_nll(logits, labels) -> (nll_sum, target_count). Targets are labels[:,1:] excluding -100.

**Steps:**

- [ ] 1. Write a two-sequence fixture with unequal lengths and padding; manually specified logits give known token NLL. Assert changing padded IDs/logits cannot change loss and one-token examples have zero scored targets.
- [ ] 2. Mask padded labels with -100 in toy training. Aggregate corpus perplexity as exp(sum_nll/sum_target_count), not weighted average by input length; reject aggregate target_count=0.
- [ ] 3. Use shared accounting in persona loss and toy evaluator. Report per-case nll_sum and target_count, plus truncation counts; full-text PPL remains a language-model metric distinct from response correctness.
- [ ] 4. Preserve old numerical tables as historical. Mark corrected scores pending a fresh S06 run; never relabel old adapter training as corrected.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_loss_metrics.py
```

**Acceptance:** Manual-logit equality and padding-invariance pass on CPU; fixture catches old n rather than n-1 weighting.

**Implementation receipt:** `docs/task-receipts/C05-implementation.md`.

### C05-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-correct-causal-loss`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C05 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C05-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## C06: Pin and isolate actual training runs

**Ledger implementation:** `tinyfleet-publication-science-20260908/immutable-training-runs` — owner haunt.

**Files:** `scripts/train_eval.py`; `scripts/persona_code.py`; `scripts/run_manifest.py (new)`; `scripts/test_run_manifest.py (new)`.

**Dependencies:** C05; existing runtime task provides dependencies

**Interface/output:** Common CLI: --manifest PATH --run-dir PATH --seed INT; adapters written only under run-dir/adapters/<arm>; run_manifest verifies input hashes before model load.

**Steps:**

- [ ] 1. Add explicit base/tokenizer revision, random/numpy/torch seeds, device/dtype, batch/gradient accumulation, max_length and train/eval config to resolved config.json.
- [ ] 2. Honor declared batch and accumulation in persona training, or fail unsupported combinations before training. Report optimizer-step count and examples/tokens seen.
- [ ] 3. Refuse existing completed run-dir and changed frozen inputs. Make crash resume require matching config/data hashes and an explicit checkpoint. Never overwrite tracked adapters for another seed.
- [ ] 4. Test with a fake model loader that a corrupt input prevents loading and that two seed runs resolve distinct adapters. A tiny CPU training fixture checks expected optimizer steps; heavy replication is S06.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_run_manifest.py
```

**Acceptance:** Corrupt inputs reject before model load; batch=2 accumulation=2 gives recorded expected step count; seed runs cannot overwrite each other.

**Implementation receipt:** `docs/task-receipts/C06-implementation.md`.

### C06-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-immutable-training-runs`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C06 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C06-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## C07: Fail explicitly on invalid embeddings or unavailable router

**Ledger implementation:** `tinyfleet-publication-science-20260908/router-failure-boundary` — owner haunt.

**Files:** `scripts/router.py`; `scripts/test_router.py (new)`; `scripts/fleet_benchmark.py`.

**Dependencies:** C03

**Interface/output:** Keep route_query API. Invalid embedding/runtime yields abstain with machine-readable reason in a new detailed route result; existing text interface remains compatible.

**Steps:**

- [ ] 1. Add injected embedding cases: zero, NaN, infinity, wrong dimension, empty matrix, HTTP failure/timeout and invalid JSON. Existing zero-vector case returns specialist:guitar and must go red.
- [ ] 2. Validate count/dimension/finiteness/norm for query and centroids; check curl return and response structure. Catch defined backend errors at routing boundary and return explicit abstain/unavailable.
- [ ] 3. Keep operator-first evaluation before any embedding call; poisoned embed function must not be invoked for operator cases. Distinguish backend failure from low confidence in raw records.
- [ ] 4. Expose best_similarity and margin even when abstaining; record model revision/digest of actual embedding backend. Calibration is S05, not a guessed absolute threshold here.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_router.py
```

**Acceptance:** All malformed/backend failures abstain loudly; operator-first bypass intact; valid specialist and current fixture behavior retained.

**Implementation receipt:** `docs/task-receipts/C07-implementation.md`.

### C07-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-router-failure-boundary`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C07 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C07-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## C08: Make the policy example enforce its own contract

**Ledger implementation:** `tinyfleet-publication-science-20260908/enforce-decision-consumer` — owner haunt.

**Files:** `README.md safety example`; `scripts/policy_consumer.py (new)`; `scripts/test_policy_consumer.py (new)`; `scripts/operator_policy.py docs`.

**Dependencies:** C07; coordinate README edit with existing closeout owner

**Interface/output:** dispatch_decision(decision, execute, review, escalate) routes allow/review/escalate/block. Only action=allow AND require_approval=false invokes execute.

**Steps:**

- [ ] 1. Use injected callbacks, never actual shell/actions. Test all action values crossed with approval boolean, unknown action, missing fields and malformed decision.
- [ ] 2. block and require_approval=true return a hold; review invokes review callback; escalate invokes escalate; malformed decision holds. Future allow behavior cannot bypass approval.
- [ ] 3. Replace README's executable fallthrough with the tested function. Explicitly describe policy as a deterministic lexical baseline with uncalibrated confidence, finite measured latency, and limited threat coverage.
- [ ] 4. Add paraphrase examples from review as regression observations, not hidden hand-tuned claims of robust safety. Broad policy evaluation is the explicit S09 task.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_policy_consumer.py
```

**Acceptance:** Spy proves zero execution for review/block/escalate/unknown/approval-needed; only explicit valid allow executes.

**Implementation receipt:** `docs/task-receipts/C08-implementation.md`.

### C08-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-enforce-decision-consumer`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of C08 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/C08-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S01: Freeze the research question, comparisons and statistical decision

**Ledger implementation:** `tinyfleet-publication-science-20260908/preregister-fleet-study` — owner haunt.

**Files:** `docs/study-registration.md (new)`; `runs/fleet-study-v1/registration.json (new)`; `docs/related-work.md (new)`.

**Dependencies:** C01-C08; before inspecting new heldout outputs

**Interface/output:** Registration names primary metric, source-unit sampling, model arms, precision target, thresholds, seeds 17/29/43 and immutable configuration; no test-set tuning.

**Steps:**

- [ ] 1. Primary question: does routed 360M specialization improve heldout task quality at bounded cost versus base, prompt-only, pooled adapter and simple router? Separate toy passage PPL, executable code correctness and rated style outcomes.
- [ ] 2. Read and cite LoRA, S-LoRA, RouteLLM and MoErging survey from review; record comparison differences and avoid novelty claims for their known mechanisms.
- [ ] 3. Preregister paired source-group bootstrap (10000 replicates, 95% intervals), three training seeds, effect sizes per domain, and safety false-accept upper bound <=5% plus >=25% useful coverage as a proposed screening gate. These are design targets, not discovered results.
- [ ] 4. Calculate independent-unit sample need before collection. For a single proportion worst-case normal halfwidth 0.10 gives ceil(1.96^2*0.25/0.10^2)=97; use >=100 independent units for that precision claim, and simulation for paired deltas. If infeasible, register a smaller exploratory pilot and explicitly drop precision/generalization claims.
- [ ] 5. Freeze config and registration commit before generating heldout predictions. Revisions require a new registration/run ID; no unbounded seed/search sweep.
- [ ] 6. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python -m json.tool runs/fleet-study-v1/registration.json
```

**Acceptance:** All arms, units, outcomes, sample-size rationale, acceptance margins and resource cap defined; no outcome-dependent choice.

**Implementation receipt:** `docs/task-receipts/S01-implementation.md`.

### S01-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-preregister-fleet-study`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S01 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S01-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S02: Replace duplicated and answer-exposed heldout cases

**Ledger implementation:** `tinyfleet-publication-science-20260908/freeze-independent-corpus` — owner haunt.

**Files:** `scripts/build_study_corpus.py (new)`; `scripts/test_study_corpus.py (new)`; `corpus/study-v1/ (new)`; `runs/fleet-study-v1/datasets.json`.

**Dependencies:** S01 and C02

**Interface/output:** JSONL rows: case_id, source_family, source_id, domain, language, split, prompt, reference, expected_route, expected_action, provenance, created_at. Split before generating variants.

**Steps:**

- [ ] 1. Use public/licensed or explicitly authored sources with recorded source family. Keep existing toy corpus as within-topic pilot, separate from the new source/topic-heldout corpus.
- [ ] 2. Create train/validation/heldout/adversarial by whole source family; freeze validation before calibration. Keep entire code tools/problem families and conversation families out of training.
- [ ] 3. Do not append expected completions to generation prompts. Verify declared RU/EN against actual text. Exact prompt dedup plus token 5-gram Jaccard >=0.8 cross-split candidates require exclusion or documented review, not silent acceptance.
- [ ] 4. Supply unique cases and counts per independent family according to S01; known four-copy corpus must fail. Insufficient sample remains insufficient-data; never multiply paraphrases and count them as independent.
- [ ] 5. Produce source/licensing/redaction/exclusion manifest and hashes; do not copy private mesh logs into public corpus.
- [ ] 6. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_study_corpus.py
```

**Acceptance:** Four-identical-case regression rejects; train/validation/heldout families disjoint; reference text never enters generation input; all required count/slice gates pass or explicitly block scoring.

**Implementation receipt:** `docs/task-receipts/S02-implementation.md`.

### S02-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-freeze-independent-corpus`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S02 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S02-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S03: Add controlled model and router comparisons

**Ledger implementation:** `tinyfleet-publication-science-20260908/matched-baseline-runner` — owner haunt.

**Files:** `scripts/study_runner.py (new)`; `scripts/test_study_runner.py (new)`; `runs/fleet-study-v1/config.json`.

**Dependencies:** S02, C06

**Interface/output:** CLI study_runner.py --manifest PATH --run-dir PATH --arm NAME --seed INT. Arms: base, prompt-only, pooled-lora, specialist:<domain>. Raw matrix schema from C03.

**Steps:**

- [ ] 1. Implement same base/tokenizer/decoding budget for all arms; prompt-only examples drawn only from train. Pooled and specialist training report equal-example/equal-token budget differences explicitly.
- [ ] 2. Generate all adapters across all heldout domains; this is the cross-domain matrix. Router baselines later consume the same saved outputs: simple lexical, centroid, oracle and abstain-all.
- [ ] 3. Write predictions incrementally with case_prompt_sha256 for the dataset prompt, rendered_input and rendered_input_sha256 for actual model input, model/config hashes, runtime status and latency. Rendered input may differ by arm; base case prompt is constant. Reference is scorer-only.
- [ ] 4. Fake backend fixture must demonstrate same heldout case IDs across arms, no reference leakage, and correct timeout records. Never generate synthetic scores to fill missing arms.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_study_runner.py
```

**Acceptance:** Expected matrix exactly matched; fake-backend test verifies input separation; one tiny real preflight proves actual model loading and generation with pinned revision.

**Implementation receipt:** `docs/task-receipts/S03-implementation.md`.

### S03-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-matched-baseline-runner`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S03 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S03-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S04: Score correctness, abstention and uncertainty from raw records

**Ledger implementation:** `tinyfleet-publication-science-20260908/independent-task-scoring` — owner haunt.

**Files:** `scripts/score_study.py (new)`; `scripts/test_score_study.py (new)`; `docs/scoring-rubric.md (new)`.

**Dependencies:** S03 and C04

**Interface/output:** CLI score_study.py --run-dir PATH; deterministic output scores.json, slices.tsv, calibration.tsv, routing.tsv, adversarial.tsv, cost.tsv. Preserve all failure rows.

**Steps:**

- [ ] 1. Code task correctness uses frozen executable tests in an offline bounded process; never execute generated mesh/network commands. Style rubric separates task compliance, evidence discipline, uncertainty and fluency; keywords alone are not labels.
- [ ] 2. Prepare anonymized rating sheet with model identity hidden. Obtain independent ratings for all main qualitative comparisons; until available label unscored and make no quality claim. Report disagreement and agreement statistic, keeping raw ratings.
- [ ] 3. Compute accuracy, paired deltas, source-cluster bootstrap intervals, per-domain/worst-slice tables, failure rates and abstention confusion. Keep generations within a source/seed clustered; 84 generated rows are not 84 independent cases.
- [ ] 4. Add hand-calculated tests: perfect/wrong/abstain-all, one timeout counted as failure, zero coverage yields undefined risk not zero; repeated rows cannot narrow interval. Only probabilities with a declared calibration mapping receive ECE/Brier.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_score_study.py
```

**Acceptance:** Known fixtures match arithmetic; scores rebuild deterministically from unchanged raw data; decision separates invalid data, valid negative result and serving eligibility.

**Implementation receipt:** `docs/task-receipts/S04-implementation.md`.

### S04-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-independent-task-scoring`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S04 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S04-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S05: Fit and freeze an abstention boundary on validation only

**Ledger implementation:** `tinyfleet-publication-science-20260908/calibrate-selective-routing` — owner haunt.

**Files:** `scripts/calibrate_router.py (new)`; `scripts/test_calibrate_router.py (new)`; `scripts/router.py`; `runs/fleet-study-v1/router.json`.

**Dependencies:** S04, C07

**Interface/output:** Router calibration contains embedding digest, corpus hash, centroids, similarity_min, margin_min, calibration_method; route detail records both scores and failure reason.

**Steps:**

- [ ] 1. Compare lexical rule baseline, nearest centroid, centroid plus absolute+margin gate, oracle choice and abstain-all on identical saved cases. A query at similarities -0.20/-0.80 must be represented in adversarial fixture.
- [ ] 2. Search thresholds only over declared validation score grid, maximizing coverage subject to S01 false-accept bound. If no threshold meets risk and coverage simultaneously, verdict=no-eligible-router; do not lower gates on heldout.
- [ ] 3. Pin calibration artifact before heldout evaluation; reject changed embeddings/centroids/model hash. Distinguish router abstention from model refusal in separate columns.
- [ ] 4. Output risk-coverage curves, false accepts/rejects by domain/language/OOD-family, bootstrap intervals and confidence definition. No universal safety claim from two OOD probes.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_calibrate_router.py
```

**Acceptance:** Calibration cannot read heldout labels; absolute-distance fixture and zero-vector gate both pass; impossible validation population produces honest no-eligible-router.

**Implementation receipt:** `docs/task-receipts/S05-implementation.md`.

### S05-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-calibrate-selective-routing`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S05 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S05-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S06: Execute corrected fleet study and measure end-to-end cost

**Ledger implementation:** `tinyfleet-publication-science-20260908/run-paired-replications` — owner haunt.

**Files:** `runs/fleet-study-v1/seed-17/`; `seed-29/`; `seed-43/`; `scripts/run_study_matrix.py (new)`; `docs/fleet-study-results.md (new)`.

**Dependencies:** S01-S05; existing haunt-install-unblock runtime task if preflight fails

**Interface/output:** run_study_matrix.py --registration runs/fleet-study-v1/registration.json --run-root runs/fleet-study-v1; no overwrite; matrix includes all registered model/domain/seed cases. Verification options: --seeds 17 --max-cases 8 --max-train-steps 2 --verification-only write a labeled non-scientific smoke run to a distinct run-root.

**Steps:**

- [ ] 1. Capture preflight versions, device/RAM/VRAM and existing GPU consumers. Use one training job at a time; do not kill shared workloads. Execute all frozen arms and seeds with matching budgets.
- [ ] 2. Record train wall time, peak allocated/reserved CUDA memory, adapter/base bytes, cold-load latency, warm end-to-end p50/p95, token counts, fallback/timeout rate. Timing includes embedding, model load/switch and generation.
- [ ] 3. Recompute reports using S04 and validate C02-C04. Compare corrected PPL to historical values without claiming unchanged values; evaluate hypothesis even if it fails.
- [ ] 4. Write practical tradeoff conclusion versus pooled/base/prompt-only controls with intervals and complete resource totals. Route eligibility only if preregistered gates pass.
- [ ] 5. Attach results as inputs to existing real-mesh pilot step; actual live or shadow integration remains under that existing chain. Record exact next command there, not another pilot task.
- [ ] 6. Also capture a seed-17 verification-only smoke with max-cases=8/max-train-steps=2 in runs/fleet-study-v1/verification-smoke. vpn repeats that exact bounded config into a new temporary run-root; compare identity/counts and per-case NLL with absolute tolerance 1e-3 at identical dtype/device/library versions. Record nondeterminism and fail reproduction if tolerance is exceeded; do not mistake this smoke for full training replication.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/run_study_matrix.py --registration runs/fleet-study-v1/registration.json --run-root runs/fleet-study-v1
```

**Acceptance:** Complete validated raw matrix for 3 seeds and all arms; negative hypothesis is allowed. Infrastructure failure remains typed blocked with retry command and available partial rows.

**Implementation receipt:** `docs/task-receipts/S06-implementation.md`.

### S06-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-run-paired-replications`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S06 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Obtain a new absolute temporary directory using `rtk proxy mktemp -d`, assign it to verification_dir, and use the bounded command below. Match the author's verification-smoke versions/device/dtype, compare input/model hashes, counts and per-case NLL (absolute tolerance 1e-3). Independently rescore copies of the complete three-seed raw bundle; do not overwrite or fully retrain the author's main run. A smoke verifies that bounded execution path, not a full training replication claim.

```bash
rtk proxy .venv/bin/python scripts/run_study_matrix.py --registration runs/fleet-study-v1/registration.json --run-root "$verification_dir" --seeds 17 --max-cases 8 --max-train-steps 2 --verification-only
```

- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S06-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S07: Deliver a real mood/style experiment or a measured no-go

**Ledger implementation:** `tinyfleet-publication-science-20260908/resolve-mood-experiment` — owner haunt.

**Files:** `scripts/mk_mood_corpus.py`; `corpus/mood-*.jsonl`; `runs/mood-study-v1/`; `docs/mood-study-results.md (new)`; `scripts/check_experiment_result.py (new)`; `scripts/test_experiment_result.py (new)`.

**Dependencies:** S02-S06; reuse their runner/scorer, no second training engine

**Interface/output:** Mood experiment evaluates controllable response style on task content, not diagnosis or inference of a person's emotional state.

**Steps:**

- [ ] 1. Audit 36/8/4 historical corpus and identify unique source families, RU/EN accuracy, validation gap and near duplicates. Do not cite guitar/sourdough weights as a mood adapter.
- [ ] 2. Freeze separate manifest and register base/prompt-only/mood-LoRA controls with S01 methodology. Build missing independent cases before training.
- [ ] 3. Run one feasibility seed first; blind rubric evaluates requested style plus factual/task preservation. If measurable signal and data are adequate, run all three registered seeds; otherwise publish no-go or insufficient-data with exact reason.
- [ ] 4. Record mood adapter hash and actual changed weights if trained. Serving remains off unless S05 gate and original pilot process pass; a no-go closes experiment exploration, not a claim of trained useful capability.
- [ ] 5. Implement check_experiment_result.py --run-dir PATH to validate outcome=measured|no-go|insufficient-data|blocked, named causes, source/config hashes and evidence files. Measured outcomes require complete raw/control bundle; no-go requires baseline or data-adequacy evidence; missing hardware/dependencies are blocked. Tests reject unsupported no-go and blocked mislabeled measured. Run training only when data and runtime gates pass; no-go validation never loads a model.
- [ ] 6. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_experiment_result.py
```

**Acceptance:** Tests distinguish evidence-backed no-go/insufficient-data from runtime block; result validator accepts a mood-specific measured control bundle or justified data no-go. No guitar/sourdough receipt stands in for mood evidence.

**Implementation receipt:** `docs/task-receipts/S07-implementation.md`.

### S07-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-resolve-mood-experiment`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S07 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S07-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S08: Resolve the original inspiration claim

**Ledger implementation:** `tinyfleet-publication-science-20260908/bound-bbywvy-reproduction` — owner haunt.

**Files:** `scripts/bbywvy_test.py`; `docs/bbywvy-360m-notes.md`; `runs/bbywvy-reproduction-v1/`.

**Dependencies:** S04 and existing runtime task if needed

**Interface/output:** Pinned model/tokenizer revision, license/provenance, local preflight, immutable prompts, raw outputs and exact reproduction scope.

**Steps:**

- [ ] 1. Resolve the original model card and available files; record immutable revision and runtime compatibility. Distinguish inference reproduction from reproducing training.
- [ ] 2. Freeze a small rubric covering original spot-checks, factual recall, task compliance and OOD refusal; use matched base-model prompts/decoding.
- [ ] 3. Capture one bounded local inference run with model hashes and outputs, then score using S04. Do not guess inaccessible weight/config values.
- [ ] 4. If model/runtime/data cannot be obtained, publish a retrieval/preflight failure and retain the project as inspiration-only; this does not block the fleet's independent contribution.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/bbywvy_test.py --help
```

**Acceptance:** Runner exposes explicit pinned config and run-dir; result is reproducible bounded comparison or documented unavailable artifact, never implied training reproduction.

**Implementation receipt:** `docs/task-receipts/S08-implementation.md`.

### S08-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-bound-bbywvy-reproduction`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S08 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S08-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## S09: Measure the lexical policy baseline on unseen difficult cases

**Ledger implementation:** `tinyfleet-publication-science-20260908/operator-policy-robustness` — owner haunt.

**Files:** `scripts/eval_operator_robustness.py (new)`; `scripts/test_operator_robustness.py (new)`; `corpus/operator-robustness-v1/`; `runs/operator-robustness-v1/`; `docs/operator-robustness.md (new)`.

**Dependencies:** C08, S01-S05; do not tune the tested policy on final cases

**Interface/output:** eval_operator_robustness.py --manifest runs/operator-robustness-v1/manifest.json --run-dir runs/operator-robustness-v1/result; baseline=existing frozen policy, comparator=explicit rules or trained small classifier.

**Steps:**

- [ ] 1. Preregister heldout source-family cases for benign substring triggers (class in guitar class), destructive paraphrases without known keywords, negation, quoted instructions, mixed benign/risky requests and RU/EN; use independently authored labels and keep reference labels out of model input.
- [ ] 2. Freeze current model JSON hash and decision map. Record prompt, expected policy/action, actual policy/action/approval/escalation and heuristic confidence for every case. Unknown and execution-eligibility errors have separate counts.
- [ ] 3. Compare with simple explicit-rule baseline and abstain-all; do not build an ever-growing test-specific keyword patch. Reuse S04 intervals and source-unit accounting; report false negatives, benign false positives, per-family worst case and useful coverage.
- [ ] 4. Test decision_consumer integration using callback spies; 'review' and 'block' cannot execute. Confidence remains uncalibrated unless validated calibration artifact exists.
- [ ] 5. Publish reproducible failure examples and bounded-use statement. No go/no-go here authorizes using the lexical classifier as the sole safety boundary; negative result closes evaluation while leaving model limitations explicit.
- [ ] 6. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_operator_robustness.py
```

**Acceptance:** Independent heldout corpus and full raw decision matrix; false-positive/false-negative and coverage reports with uncertainty; unsafe consumer fallthrough remains impossible in fixtures.

**Implementation receipt:** `docs/task-receipts/S09-implementation.md`.

### S09-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-operator-policy-robustness`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of S09 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/S09-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## P01: Make core workflows installable and continuously checked

**Ledger implementation:** `tinyfleet-publication-science-20260908/clean-clone-reproduction` — owner haunt.

**Files:** `requirements-eval.txt`; `requirements-train.txt (new)`; `scripts/check_publication.py (new)`; `.github/workflows/ci.yml (new)`; `docs/reproduce.md (new)`.

**Dependencies:** S06; runtime provisioning remains existing task

**Interface/output:** check_publication.py --offline runs CPU gates without mesh, ~/.mesh, GPU, Ollama or private files; optional --run-dir validates empirical bundle.

**Steps:**

- [ ] 1. Capture tested dependency versions into separate CPU/eval and GPU/training instructions; pin model revisions in manifests. Do not install the current node's unrelated packages.
- [ ] 2. Run from a fresh local clone at explicit commit with a fresh venv and isolated temporary HOME. Assert absent mesh commands/private corpus does not break imports or CPU tests.
- [ ] 3. Add CI for dataset/prediction/report/loss/router/consumer/scorer tests with small fixtures. GPU jobs opt-in; unavailable GPU is a named skip, not an empirical PASS.
- [ ] 4. Document commands, expected artifacts/runtime/download sizes, resume rules and failure meanings. Correct drift command availability through D01 or label it optional dependency.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/check_publication.py --offline
```

**Acceptance:** Fresh-clone CPU suite passes from documented dependencies; CI workflow executes those exact commands and output is retained with commit/hash.

**Implementation receipt:** `docs/task-receipts/P01-implementation.md`.

### P01-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-clean-clone-reproduction`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of P01 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/P01-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## P02: Ship provenance, model and dataset documentation

**Ledger implementation:** `tinyfleet-publication-science-20260908/publish-provenance-cards` — owner haunt.

**Files:** `docs/model-card.md (new)`; `docs/dataset-card.md (new)`; `THIRD_PARTY.md (new)`; `CITATION.cff (new)`; `docs/artifact-manifest.json (new)`.

**Dependencies:** P01 and S06-S08

**Interface/output:** Machine-readable inventory path/size/sha256/source/license_basis/revision; scoped model/data cards and citation metadata.

**Steps:**

- [ ] 1. Inventory every tracked adapter, corpus and derived snapshot. Record upstream model/data terms and lineage; do not assume repository CC0 changes upstream rights.
- [ ] 2. Document training/eval splits, intended uses, failure cases, resource costs, languages, contamination limitations and known 0/84 historical failure.
- [ ] 3. Include reproduction command and model/tokenizer hashes for each claimed result. Large artifact external links need checksums and revision; unavailable files are flagged.
- [ ] 4. Fill citation authors only from actual repository authorship/operator-provided metadata, not invented contributors or DOI. Record repository URL and actual version when available.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/check_publication.py --offline
```

**Acceptance:** Every redistributed model/data file has provenance and known terms or is excluded from release; links/hashes verified, historical versus new results distinct.

**Implementation receipt:** `docs/task-receipts/P02-implementation.md`.

### P02-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-publish-provenance-cards`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of P02 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/P02-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## P03: Write a restrained article with reproducible figures

**Ledger implementation:** `tinyfleet-publication-science-20260908/write-research-report` — owner haunt.

**Files:** `docs/paper.md (new)`; `docs/references.bib (new)`; `scripts/plot_study.py (new)`; `docs/figures/ (new)`.

**Dependencies:** S06, P02; drift status can remain preliminary

**Interface/output:** Report sections: question, prior work, methods, results, cost, failure analysis, threats, reproduction. Figures derive exclusively from validated run tables.

**Steps:**

- [ ] 1. State the measured contribution against LoRA/routing prior work, using small-model cost/quality evidence rather than novelty by naming.
- [ ] 2. Render paired quality deltas, risk-coverage and end-to-end latency/memory comparison; axes show units/counts/intervals. A negative or inconclusive result stays in abstract and conclusion.
- [ ] 3. Separate drift as exploratory appendix unless D04 plus original external-study gate support its claims. Separate lexical policy baseline from trained specialists.
- [ ] 4. Include unique source counts, paired study assumptions, data dependence, heuristic/human scoring limits, failed arms and exact scripts/run hashes. All headline numbers point to a table.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/plot_study.py --run-dir runs/fleet-study-v1 --out-dir docs/figures
```

**Acceptance:** Figures regenerate from raw-derived tables; every quantitative paper claim traces to validated evidence and uncertainty; no result selected only because favorable.

**Implementation receipt:** `docs/task-receipts/P03-implementation.md`.

### P03-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-write-research-report`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of P03 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/P03-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## P04: Deliver a safe presentation and auditable release candidate

**Ledger implementation:** `tinyfleet-publication-science-20260908/demo-and-release-gate` — owner haunt.

**Files:** `scripts/demo.py (new)`; `scripts/test_demo.py (new)`; `docs/presentation.md (new)`; `docs/release-checklist.md (new)`; `docs/release-candidate.json (new)`.

**Dependencies:** P01-P03; existing closeout consumes outputs; existing pilot/witness gates control usefulness claims

**Interface/output:** demo.py --fixture works offline; --live uses only admitted adapters and explicit fallbacks. Displayed modes clearly state recorded/demo/live.

**Steps:**

- [ ] 1. Show three cases: correctly routed specialist, OOD abstention, operator review/block. Display task score provenance and approximate measured latency, never fabricated live timing.
- [ ] 2. Use bounded model calls only; no shell/actuator execution. Replay recorded outputs labeled recorded. Fixture tests assert invalid embeddings and unavailable adapter visibly abstain.
- [ ] 3. Write a 5-minute presentation: problem, architecture, controls, one measured result, failure example, reproduction. Assemble commit/hash/license/test/known-limit checks.
- [ ] 4. Send concrete release-candidate paths to original closeout task; settle that task only with its own scope met. Do not upload a paper, announce externally or create a DOI as part of the plan. User can review the complete publication package.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_demo.py
```

**Acceptance:** Offline demo and failure cases pass; release candidate points to validated figures/cards/evidence. Research success, deployment eligibility and presentation readiness remain separate flags.

**Implementation receipt:** `docs/task-receipts/P04-implementation.md`.

### P04-V: independent verification — owner vpn

**Ledger:** `tinyfleet-publication-science-20260908/verify-demo-and-release-gate`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of P04 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/P04-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## D01: Bring a pinned drift extractor into the public repository

**Ledger implementation:** `tinyfleet-drift-science-20260908/standalone-drift-extraction` — owner haunt.

**Files:** `scripts/drift_extract.py (new)`; `scripts/test_drift_extract.py (new)`; `docs/cross-repository-drift-protocol.md`.

**Dependencies:** Read existing /home/mesh-home/lte-workstation/scripts/mesh-tiny-fleet-evaluate and mesh-tiny-fleet-snapshot; reuse definitions with provenance; C01

**Interface/output:** drift_extract.py --repo PATH --old SHA --new SHA --run-dir PATH; tracked text corpus, per-path blob SHA/bytes/unit/language and exclusions, structural.tsv.

**Steps:**

- [ ] 1. Use git object reads from immutable 40-hex commits; no mutable HEAD or private mesh paths. Preserve generated/vendor/binary exclusion policy and count excluded paths.
- [ ] 2. Include a temporary fixture git repo with added/deleted/renamed text, generated and binary files. Renames must not count as new semantic content.
- [ ] 3. Define structural and mesh_refs metrics explicitly; lexical tool mentions are not invocations. Resolve conflicting historical count definitions rather than blending them.
- [ ] 4. Use the existing external-sample task to acquire repositories; this task only implements portable extraction. No repeated repository acquisition chain.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_drift_extract.py
```

**Acceptance:** Fixture yields hand-counted paths/bytes; identical snapshots give zero change; runs without any mesh installation.

**Implementation receipt:** `docs/task-receipts/D01-implementation.md`.

### D01-V: independent verification — owner vpn

**Ledger:** `tinyfleet-drift-science-20260908/verify-standalone-drift-extraction`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of D01 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/D01-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## D02: Pin lexical measurements and negative controls

**Ledger implementation:** `tinyfleet-drift-science-20260908/lexical-drift-controls` — owner haunt.

**Files:** `scripts/drift_lexical.py (new)`; `scripts/test_drift_lexical.py (new)`; `docs/concepts-v1.json (new)`.

**Dependencies:** D01

**Interface/output:** drift_lexical.py --run-dir PATH produces lexical.tsv and controls.tsv; regex tokenizer v1 or pinned tokenizer digest; fixed concept dictionary.

**Steps:**

- [ ] 1. Use a language-independent declared tokenization rule with source hash; version dictionary and examples before external score inspection. Normalize terms per 10000 included tokens and stratify code/docs/vendor exclusions.
- [ ] 2. Add no-change, duplicated-file/corpus-size-only, identifier-renaming and shuffled-snapshot controls. Raw frequency growth must not masquerade as normalized conceptual change.
- [ ] 3. Bootstrap at file/unit level; preserve paired units and report unique units. Record dictionary false-positive examples for ambiguous arm/gate/class terms.
- [ ] 4. Keep lexical output descriptive. Tokenizer absence is addressed by this explicit reproducible rule, never a silently changing backend.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_drift_lexical.py
```

**Acceptance:** No-change=0; corpus duplication changes raw count but not normalized rates; renaming detected as lexical without automatic semantic verdict.

**Implementation receipt:** `docs/task-receipts/D02-implementation.md`.

### D02-V: independent verification — owner vpn

**Ledger:** `tinyfleet-drift-science-20260908/verify-lexical-drift-controls`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of D02 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/D02-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## D03: Separate prompting effects, training effects and sampling noise

**Ledger implementation:** `tinyfleet-drift-science-20260908/generative-drift-runner` — owner haunt.

**Files:** `scripts/drift_generate.py (new)`; `scripts/test_drift_generate.py (new)`; `docs/cross-repository-drift-protocol.md`.

**Dependencies:** D02 plus C03-C06 and S03; existing external-sample freeze supplies manifests

**Interface/output:** Keys=(repo,snapshot,arm,prompt_id,seed,repetition); arms base, prompt-only, lora. Raw JSONL contains prompt/output and model/adapter/scorer digests.

**Steps:**

- [ ] 1. Freeze identical heldout prompts, rendering template, input token budget and decoding per arm. Base has no snapshot conditioning; prompt-only changes context; LoRA changes weights with context controlled.
- [ ] 2. Add same-snapshot repeated runs, identical weights different prompts, shuffled snapshot labels and deliberately contaminated train/heldout source to test interpretation.
- [ ] 3. Run a bounded local fixture first with fake backend; real execution belongs existing run-cross-repository-analysis task. Genuine LoRA and prompt-only outputs may never share an arm label.
- [ ] 4. Score lexical/rubric/embedding differences in separate columns; use pinned scorer and repeated-seed uncertainty, and compare between-snapshot difference to within-snapshot variation. Do not call cosine semantic truth.
- [ ] 5. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_drift_generate.py
```

**Acceptance:** Matrix and provenance fixtures pass; missing arm is blocked; label shuffle/noise controls undermine false drift conclusions visibly.

**Implementation receipt:** `docs/task-receipts/D03-implementation.md`.

### D03-V: independent verification — owner vpn

**Ledger:** `tinyfleet-drift-science-20260908/verify-generative-drift-runner`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of D03 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/D03-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## D04: Validate drift metrics against independent change evidence

**Ledger implementation:** `tinyfleet-drift-science-20260908/validate-architectural-ground-truth` — owner haunt.

**Files:** `docs/drift-validation-registration.md (new)`; `scripts/drift_validate.py (new)`; `scripts/test_drift_validate.py (new)`; `runs/drift-validation-v1/`.

**Dependencies:** D03; existing freeze-independent-repository-sample provides >=3 independent external repositories

**Interface/output:** Frozen human/repository-evidence labels on changed units; structural/lexical/generative/behavioral estimands separate; report within and across repositories.

**Steps:**

- [ ] 1. Preregister changed-interface/dependency/behavior labels from release notes, commit diffs and native tests before revealing model scores. Label unit maps and uncertainty; cosmetic changes serve as negative examples.
- [ ] 2. Use two independent blinded reviewers for main labeled comparisons; store disagreements and adjudication. If unavailable, preserve objective native-test/interface subset and withhold semantic generalization.
- [ ] 3. Compare generative metrics to simple file-size/token/diff baselines on same pairs; report heldout-repository association with uncertainty. Do not select repositories by favorable drift score.
- [ ] 4. Feed method and labels to existing run/conclusions/witness chain. This task supplies validation tooling/labels, not duplicate external acquisition or publishability review.
- [ ] 5. Before any real external comparison, publish D04-V approved registration.json plus label hashes and ensure the existing tinyfleet-architecture-drift-review-20260907/run-cross-repository-analysis task treats these as required preconditions. D04 uses fixtures and blinded labels only; real associations are computed afterward by that existing task. If it has already run, label the old run exploratory and freeze fresh unseen pairs for confirmation.
- [ ] 6. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_drift_validate.py
```

**Acceptance:** Cosmetic/no-change fixtures cannot receive architecture-change labels automatically; label leakage rejects; external study remains preliminary until valid independent evidence arrives.

**Implementation receipt:** `docs/task-receipts/D04-implementation.md`.

### D04-V: independent verification — owner vpn

**Ledger:** `tinyfleet-drift-science-20260908/verify-validate-architectural-ground-truth`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of D04 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/D04-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A00: Create the shared application screening harness

**Ledger implementation:** `tinyfleet-applications-20260908/application-protocol` — owner haunt.

**Files:** `docs/applications.md (new)`; `scripts/application_screen.py (new)`; `scripts/test_application_screen.py (new)`; `runs/applications/registry.json (new)`.

**Dependencies:** C02-C08 and S01-S05 verified for neural evaluation; documentation and baseline design may start now

**Interface/output:** Registry holds application_id, task_kind, source URL, data license, baseline, metric, preregistered gate, cost cap, input/output schemas, state and run hashes. CLI application_screen.py --registry runs/applications/registry.json --validate.

**Steps:**

- [ ] 1. Populate the ten hypotheses in docs/applications.md with primary-source precedents and explicit non-LLM competitors. Rank extraction, command interpretation and support routing first by objective scoring feasibility; remaining candidates stay in the ledger.
- [ ] 2. Reuse the study schemas and scorer; task modules implement predict_baseline(case)->dict and score_case(case,prediction)->dict. No second generic training framework. Tests call only fixtures and validators.
- [ ] 3. Freeze per-application development/validation/heldout/source-family units and gates before scoring. Sample-size gate: zero failures in 100 is not proof of <1%; one-sided exact upper=1-0.05**(1/n), requiring at least 299 independent zero-failure cases for <=1%. For 0.5% at least 598; clustered units reduce effective n.
- [ ] 4. Set initial resource ceiling 30 GPU minutes per application, one GPU job at a time; count label effort and CPU time separately. Stop an arm on proven baseline dominance or insufficient labels with a no-go/inconclusive artifact, not invented benefit.
- [ ] 5. Report 360M fleet versus encoder/seq2seq specialist comparisons as different model families; parameter count alone is neither speed nor deployability. Only shortlisted candidates receive three-seed confirmation and device-specific quantization comparison.
- [ ] 6. Add schema fixtures: duplicated source families cannot inflate n; missing fields cannot default to zero; uncalibrated score cannot be called probability; no-go result is accepted as complete exploration.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_application_screen.py
```

**Acceptance:** Ten registered hypotheses, exact baseline/gate/data/cost contracts and hand-tested rare-error sample arithmetic; all exploration remains offline and reproducible.

**Implementation receipt:** `docs/task-receipts/A00-implementation.md`.

### A00-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-application-protocol`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A00 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A00-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A01: Offline read-only command interpretation

**Ledger implementation:** `tinyfleet-applications-20260908/command-intents` — owner haunt.

**Files:** `scripts/applications/command_intents.py (new)`; `scripts/test_app_command_intents.py (new)`; `corpus/applications/command-intents/`; `runs/applications/command-intents/`; `docs/applications/command-intents.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Parse 10 declared read-only intents into {function,arguments} or unknown; simulator only, no OS calls. CLI: python scripts/applications/command_intents.py --phase baseline|pilot|score --run-dir runs/applications/command-intents.

**Steps:**

- [ ] 1. Read primary precedent [FunctionGemma 270M](https://ai.google.dev/gemma/docs/mobile-actions), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Whole paraphrase/intent-template families; mixed commands, unknown actions, negation and RU/EN. Argument hallucination or unknown function is failure, not merely invalid JSON. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: regex/grammar; TF-IDF linear intent classifier; base 360M; FunctionGemma as optional pinned comparator. Add hand-calculated correctness tests for command output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: exact function+argument accuracy >=95%; OOD false-accept one-sided 95% upper bound <=1%; >=5 percentage-point paired gain over strongest simple baseline. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_command_intents.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A01-implementation.md`.

### A01-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-command-intents`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A01 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A01-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A02: Ticket text to evidence-backed JSON

**Ledger implementation:** `tinyfleet-applications-20260908/ticket-extraction` — owner haunt.

**Files:** `scripts/applications/ticket_extraction.py (new)`; `scripts/test_app_ticket_extraction.py (new)`; `corpus/applications/ticket-extraction/`; `runs/applications/ticket-extraction/`; `docs/applications/ticket-extraction.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Extract product/version/issue/requested_action and exact evidence spans; absent values null. CLI: python scripts/applications/ticket_extraction.py --phase baseline|pilot|score --run-dir runs/applications/ticket-extraction.

**Steps:**

- [ ] 1. Read primary precedent [NuExtract-tiny](https://huggingface.co/numind/NuExtract-tiny), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Hold out complete source templates and product families; include missing/contradictory fields and prompt injection within quoted ticket content. Values require evidence spans. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: regex+dictionary; base 360M; pinned NuExtract-tiny. Add hand-calculated correctness tests for extraction output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: field precision >=95%, recall >=90%, unsupported-field rate <=1%; paired improvement or documented cost advantage over baseline. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_ticket_extraction.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A02-implementation.md`.

### A02-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-ticket-extraction`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A02 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A02-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A06: Small-model queue routing versus linear classification

**Ledger implementation:** `tinyfleet-applications-20260908/support-routing` — owner haunt.

**Files:** `scripts/applications/support_routing.py (new)`; `scripts/test_app_support_routing.py (new)`; `corpus/applications/support-routing/`; `runs/applications/support-routing/`; `docs/applications/support-routing.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Route to 8 fixed support queues plus unknown; preserve operator-first gate when used in fleet. CLI: python scripts/applications/support_routing.py --phase baseline|pilot|score --run-dir runs/applications/support-routing.

**Steps:**

- [ ] 1. Read primary precedent [EmbeddingGemma; application hypothesis](https://deepmind.google/models/gemma/embeddinggemma/), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Hold out organizations/source templates; multilingual, mixed-topic and ambiguous cases. Freeze queue definitions before labels; report per-queue recall. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: TF-IDF logistic regression; nearest centroid; base 360M; LoRA classifier. Add hand-calculated correctness tests for classification output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: macro-F1 >=3-point gain OR noninferiority within 1 point with >=20% measured latency/RAM benefit; OOD false acceptance <=5%. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_support_routing.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A06-implementation.md`.

### A06-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-support-routing`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A06 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A06-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A03: Normalize logs without inventing diagnoses

**Ledger implementation:** `tinyfleet-applications-20260908/log-normalization` — owner haunt.

**Files:** `scripts/applications/log_normalization.py (new)`; `scripts/test_app_log_normalization.py (new)`; `corpus/applications/log-normalization/`; `runs/applications/log-normalization/`; `docs/applications/log-normalization.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Extract component/error_code/operation/timestamp/evidence_span; no root-cause field. CLI: python scripts/applications/log_normalization.py --phase baseline|pilot|score --run-dir runs/applications/log-normalization.

**Steps:**

- [ ] 1. Read primary precedent [NuExtract authors; transfer hypothesis](https://huggingface.co/numind/NuExtract-tiny), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Hold out applications/log templates before paraphrasing. Include truncation, missing timestamps and benign warning levels; unknown stays null. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: existing regex/template parser; base 360M; extraction adapter. Add hand-calculated correctness tests for extraction output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: >=5-point exact-record gain on heldout applications; known-format degradation <=1 point; unsupported-field rate <=1%. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_log_normalization.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A03-implementation.md`.

### A03-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-log-normalization`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A03 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A03-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A04: Local cited runbook retrieval with no-answer handling

**Ledger implementation:** `tinyfleet-applications-20260908/runbook-retrieval` — owner haunt.

**Files:** `scripts/applications/runbook_retrieval.py (new)`; `scripts/test_app_runbook_retrieval.py (new)`; `corpus/applications/runbook-retrieval/`; `runs/applications/runbook-retrieval/`; `docs/applications/runbook-retrieval.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Retrieve up to five paragraph IDs from frozen public manuals; return no-answer when support is absent. Generation optional and separately scored. CLI: python scripts/applications/runbook_retrieval.py --phase baseline|pilot|score --run-dir runs/applications/runbook-retrieval.

**Steps:**

- [ ] 1. Read primary precedent [EmbeddingGemma 300M](https://deepmind.google/models/gemma/embeddinggemma/), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Hold out manuals/source families, not random chunks. Human or source-backed gold passage IDs; unanswerable near-match queries retained. Citation existence is not answer support. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: BM25; current all-MiniLM; pinned EmbeddingGemma; optional 360M query rewrite. Add hand-calculated correctness tests for retrieval output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Default candidate is a pinned encoder; do not train a causal adapter merely to satisfy a common template. Optional 360M query-rewrite arm consumes original query and outputs a rewritten query into the SAME frozen retriever; targets are train-only human/source-derived rewrites and gold passages remain keyed to original query. Compare retrieval metrics and added latency; initial GPU cap 30 minutes, one job. Reject rewriting that adds unsupported entities.
- [ ] 5. Preregister go/no-go: Recall@5 >=5 points above strongest simple baseline; no-answer false acceptance <=5%; publish CPU/RAM tradeoff. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_runbook_retrieval.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A04-implementation.md`.

### A04-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-runbook-retrieval`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A04 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A04-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A05: Duplicate issue detection with an abstain result

**Ledger implementation:** `tinyfleet-applications-20260908/duplicate-incidents` — owner haunt.

**Files:** `scripts/applications/duplicate_incidents.py (new)`; `scripts/test_app_duplicate_incidents.py (new)`; `corpus/applications/duplicate-incidents/`; `runs/applications/duplicate-incidents/`; `docs/applications/duplicate-incidents.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Match ticket to same-incident ID or none; do not equate shared symptoms with shared incident. CLI: python scripts/applications/duplicate_incidents.py --phase baseline|pilot|score --run-dir runs/applications/duplicate-incidents.

**Steps:**

- [ ] 1. Read primary precedent [EmbeddingGemma; application hypothesis](https://deepmind.google/models/gemma/embeddinggemma/), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Split whole incident families and time periods; hard negatives share error messages but have different incident identity. Do not generate all correlated pairs and call them independent. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: normalized hashing; character n-gram cosine; BM25; all-MiniLM. Add hand-calculated correctness tests for retrieval output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: pair precision >=95% and recall gain >=5 points over baseline at matched precision; report candidate-retrieval recall separately. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_duplicate_incidents.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A05-implementation.md`.

### A05-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-duplicate-incidents`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A05 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A05-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A07: PII highlighting with explicit residual-risk reporting

**Ledger implementation:** `tinyfleet-applications-20260908/redaction-assistance` — owner haunt.

**Files:** `scripts/applications/redaction_assistance.py (new)`; `scripts/test_app_redaction_assistance.py (new)`; `corpus/applications/redaction-assistance/`; `runs/applications/redaction-assistance/`; `docs/applications/redaction-assistance.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Find character spans for declared PII types in synthetic/public licensed documents; human-review suggestions only. CLI: python scripts/applications/redaction_assistance.py --phase baseline|pilot|score --run-dir runs/applications/redaction-assistance.

**Steps:**

- [ ] 1. Read primary precedent [GLiNER2-PII preprint](https://arxiv.org/abs/2605.09973), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. No private mesh/user records in public data. Use unseen name/format families and multilingual spans. Publish confidence bounds and false negatives; never claim complete anonymization. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: regex; existing NER; pinned small span extractor; optional tiny-fleet tagger. Add hand-calculated correctness tests for spans output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: per-critical-type recall >=99%, precision >=90%, exact offsets correct; any insufficient type remains insufficient-data. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_redaction_assistance.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A07-implementation.md`.

### A07-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-redaction-assistance`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A07 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A07-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A08: Domain OCR/typing correction with protected fields

**Ledger implementation:** `tinyfleet-applications-20260908/noisy-text-correction` — owner haunt.

**Files:** `scripts/applications/noisy_text_correction.py (new)`; `scripts/test_app_noisy_text_correction.py (new)`; `corpus/applications/noisy-text-correction/`; `runs/applications/noisy-text-correction/`; `docs/applications/noisy-text-correction.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Correct one frozen document domain while preserving numbers, IDs, paths and already-correct text. CLI: python scripts/applications/noisy_text_correction.py --phase baseline|pilot|score --run-dir runs/applications/noisy-text-correction.

**Steps:**

- [ ] 1. Read primary precedent [ByT5 paper](https://arxiv.org/abs/2105.13626), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Hold out source documents before noise generation; real publicly licensed noise if available, otherwise explicitly synthetic. Include clean text as control and separate CER from factual preservation. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: identity transform; dictionary/edit-distance; pinned ByT5-small; 360M LoRA. Add hand-calculated correctness tests for rewrite output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: >=20% relative character-error reduction vs strongest baseline; clean-field corruption <=0.5%; protected fields unchanged. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_noisy_text_correction.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A08-implementation.md`.

### A08-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-noisy-text-correction`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A08 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A08-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A09: One bounded transliteration/diacritic-restoration task

**Ledger implementation:** `tinyfleet-applications-20260908/transliteration` — owner haunt.

**Files:** `scripts/applications/transliteration.py (new)`; `scripts/test_app_transliteration.py (new)`; `corpus/applications/transliteration/`; `runs/applications/transliteration/`; `docs/applications/transliteration.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Select one language/alphabet transformation; protect literal IDs and exact-copy spans; unknown names may abstain. CLI: python scripts/applications/transliteration.py --phase baseline|pilot|score --run-dir runs/applications/transliteration.

**Steps:**

- [ ] 1. Read primary precedent [ByT5 paper](https://arxiv.org/abs/2105.13626), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Freeze one language pair and normalization rules before collection. Hold out name/word families; accept multiple gold spellings only if preregistered. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: deterministic transliterator plus lexicon; pinned ByT5-small; base and LoRA. Add hand-calculated correctness tests for rewrite output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: >=5-point exact-word gain on unseen word/name families with protected spans unchanged; report ambiguous references separately. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_transliteration.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A09-implementation.md`.

### A09-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-transliteration`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A09 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A09-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## A10: Natural-language actions in a deterministic toy world

**Ledger implementation:** `tinyfleet-applications-20260908/simulator-actions` — owner haunt.

**Files:** `scripts/applications/simulator_actions.py (new)`; `scripts/test_app_simulator_actions.py (new)`; `corpus/applications/simulator-actions/`; `runs/applications/simulator-actions/`; `docs/applications/simulator-actions.md (new)`.

**Dependencies:** A00 verified; C02-C08 and S01-S05 verified before any model scores; reuse common study runner/schema

**Interface/output:** Emit typed commands to an in-memory grid simulator; single and two-action compositions, unknown means no state change. CLI: python scripts/applications/simulator_actions.py --phase baseline|pilot|score --run-dir runs/applications/simulator-actions.

**Steps:**

- [ ] 1. Read primary precedent [FunctionGemma TinyGarden](https://deepmind.google/models/gemma/functiongemma/), pin available model/tokenizer revisions and record license/provenance. Its existence supports feasibility; Tiny Fleet benefit remains a hypothesis.
- [ ] 2. Create a registration and source-family split manifest. Hold out command-composition families; negation, conflicting constraints and malicious text as data. Simulator exposes no file/network/shell actions. Minimum screening set: 100 independent heldout units plus disjoint validation; precision/rare-error claims require the sample calculation from A00, not 100 by default.
- [ ] 3. Implement and measure these matched baselines first: hand grammar; base 360M; pinned FunctionGemma; tiny-fleet adapter. Add hand-calculated correctness tests for simulator output, missing data, OOD and malformed output. Record outputs and errors even when no neural arm is useful.
- [ ] 4. Run one seed-17 360M adapter pilot only when baseline headroom and labeled data justify it. Initial cap is 30 GPU minutes and one model job; log compute/download/storage. At cap, checkpoint and report insufficient-budget, not success. No paid API calls or runtime deployment needed.
- [ ] 5. Preregister go/no-go: single-action final-state success >=95%, heldout two-action >=85%; invalid/OOD commands leave state unchanged; report gain over grammar. Use source-cluster intervals and report unmeasurable bounds as inconclusive. A candidate that clears development screening gets three-seed confirmation on reserved heldout data under a new run ID; do not retune on examined heldout.
- [ ] 6. Write observed benefit/cost/failure cases and go/no-go/inconclusive verdict. No-go is a complete exploration result. Leave deployment to a separately authorized pilot gate; do not add this adapter to live routing.
- [ ] 7. Run the exact check below; capture output and exit code. Add the implementation receipt, commit only scoped files, push and verify remote ancestry. Submit the ledger step to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_app_simulator_actions.py
```

**Acceptance:** Tests, source manifests, baseline raw outputs and justified pilot/no-go artifact exist; numerical gate above is evaluated with uncertainty. vpn repeats scoring and checks unseen negative cases.

**Implementation receipt:** `docs/task-receipts/A10-implementation.md`.

### A10-V: independent verification — owner vpn

**Ledger:** `tinyfleet-applications-20260908/verify-simulator-actions`.

- [ ] Inspect the implementation receipt's source commit in an isolated checkout. Check the exact files, interface, dependencies and all acceptance predicates of A10 above.
- [ ] Run the check independently, using isolated output paths for artifact-producing commands, and inspect actual artifacts. Apply the applicable mutation or empirical-reproduction rules in the global block; include at least one counterexample absent from the author's positive examples.
- [ ] Recompute every cited count/hash from source artifacts. For experiments, verify source-independent sample count, reference exclusion, failed-case denominators, frozen validation thresholds and reported uncertainty; reject any overstatement of observed evidence.
- [ ] Write `docs/task-receipts/A10-verification.md` with PASS/FAIL/BLOCKED, exact source commit, commands/exit codes/output hashes and residual limitations. PASS accepts precisely the Acceptance above, not broader usefulness or safety. On FAIL/BLOCKED keep the gate open and follow the repair procedure.
- [ ] Commit/push the receipt, verify remote containment, then and only then settle this verification step. The next haunt task is released by the chain coordinator.

## B01: Freeze a board-dispatch dataset and an advisory-only contract

**Ledger implementation:** `tinyfleet-board-dispatch-20260908/dispatch-corpus-contract` — owner haunt.

**Files:** docs/board-dispatch-study.md (new); corpus/board-dispatch-v1/; runs/board-dispatch-v1/registration.json; scripts/test_dispatch_corpus.py (new).

**Dependencies:** C01, C02, C03 verified; read /home/mesh-home/lte-workstation/scripts/mesh-dispatch, scripts/mesh-staffing and docs/design-tg-presence-and-ledger-dispatch-20260907.md

**Interface/output:** Case input: task_id, sanitized_text, explicit_owner, eligible_owner_ids, role_descriptions, dependency_state, lease_state, observed_at. Label: task_class, allowed_owner_set, needs_clarification, supporting_span. Output is a suggestion; model cannot create/settle/claim/dispatch tasks.

**Steps:**

- [ ] 1. Snapshot the existing deterministic dispatcher/staffing code at exact revision. Define an advisory selector for unowned free-text tasks only; explicit owner, current leases, dependencies, retry budget and single-writer constraints remain authoritative inputs.
- [ ] 2. Create licensed/authored or privacy-reviewed redacted board cases. Split by task family and time before paraphrases; retain a local private provenance map outside git. Historical eventual owner is not automatically a gold label; independent reviewers label suitability and preserve ambiguous sets.
- [ ] 3. Include owner tags quoted in unrelated prose, wrong-repo receipts, expired versus active lease, protected/absent owner, duplicate IDs, already-completed work, unknown specialty and embedded instructions to ignore rules. Require true as-of state; if historical roster/lease unavailable mark unusable, never reconstruct from future outcomes.
- [ ] 4. Register macro-F1 for task class, suitable-owner accuracy, routing coverage, severe constraint violation count, latency and cost. At least 100 independent heldout families for exploratory quality; compute precision needs for stricter claims. Freeze before training.
- [ ] Run the check below, capture outputs/exit codes and write `docs/task-receipts/B01-implementation.md`. Commit/push scoped files and verify remote containment before submitting to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_dispatch_corpus.py
```

**Acceptance:** Source/time-independent sanitized corpus; as-of state and ambiguity explicit; no private logs published; immutable registration. Fixture fails if labels are leaked through future owner receipts or split-derived family IDs.

### B01-V: independent verification — owner vpn

**Ledger:** `tinyfleet-board-dispatch-20260908/verify-dispatch-corpus-contract`.

- [ ] Read global strict rules and the exact submitted source revision in `docs/task-receipts/B01-implementation.md`. Use an isolated checkout; no live dispatcher calls.
- [ ] Independently run the check, inspect source manifests/hashes and recompute metrics from copied raw records. Verify no future state/labels, no private publication, no explicit-owner replacement, and no gate bypass.
- [ ] Add an unseen forged-owner/stale-state/duplicate or malformed-output case; deliberately break one deciding guard, watch the test fail, restore and watch pass. Record command/exit/output hash for both.
- [ ] For model evidence check raw invalid proposals separately from post-validator rejections, statistical units/intervals, matched controls and measured resource budget. Label replay's inability to measure real owner acceptance/task completion explicitly.
- [ ] Write `docs/task-receipts/B01-verification.md` with PASS/FAIL/BLOCKED, commit and exact verified scope. Commit/push, verify remote, then settle only on PASS. Otherwise block dependency on a keyed haunt correction as specified globally.

## B02: Measure current rules and simple learned baselines

**Ledger implementation:** `tinyfleet-board-dispatch-20260908/dispatch-baselines` — owner haunt.

**Files:** scripts/dispatch_baselines.py (new); scripts/test_dispatch_baselines.py (new); runs/board-dispatch-v1/baselines/.

**Dependencies:** B01-V; reuse A00/S04 scoring once verified

**Interface/output:** Pure function rank_owners(case)->ranked eligible IDs or abstain. Baselines: explicit-tag/current-rule replay, role-keyword overlap, TF-IDF linear classifier, all-MiniLM centroid, abstain-all.

**Steps:**

- [ ] 1. Replay pinned dispatcher decisions through read-only extracted fixtures or an isolated stubbed harness. Never call live mesh-dispatch, mesh-tell, mesh-chat or mesh-task during benchmark.
- [ ] 2. Assert explicit-owner cases retain their owner and are excluded from learned owner replacement; invalid/missing staffing fails closed. Suggestions are always intersected with authoritative eligible IDs.
- [ ] 3. Measure ambiguous unowned tasks separately from already explicit tasks; otherwise easy owner-tag extraction can dominate apparent accuracy.
- [ ] 4. Publish raw predictions, constraint violations, error types, per-role confusion and CPU p50/p95/peak RSS. If current rules already solve the admissible subset cheaply, record baseline dominance as a valid result.
- [ ] Run the check below, capture outputs/exit codes and write `docs/task-receipts/B02-implementation.md`. Commit/push scoped files and verify remote containment before submitting to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_dispatch_baselines.py
```

**Acceptance:** Baselines are reproducible without live mesh effects, all constraint fixtures fail closed, and quality is scored on independent unowned cases separately.

### B02-V: independent verification — owner vpn

**Ledger:** `tinyfleet-board-dispatch-20260908/verify-dispatch-baselines`.

- [ ] Read global strict rules and the exact submitted source revision in `docs/task-receipts/B02-implementation.md`. Use an isolated checkout; no live dispatcher calls.
- [ ] Independently run the check, inspect source manifests/hashes and recompute metrics from copied raw records. Verify no future state/labels, no private publication, no explicit-owner replacement, and no gate bypass.
- [ ] Add an unseen forged-owner/stale-state/duplicate or malformed-output case; deliberately break one deciding guard, watch the test fail, restore and watch pass. Record command/exit/output hash for both.
- [ ] For model evidence check raw invalid proposals separately from post-validator rejections, statistical units/intervals, matched controls and measured resource budget. Label replay's inability to measure real owner acceptance/task completion explicitly.
- [ ] Write `docs/task-receipts/B02-verification.md` with PASS/FAIL/BLOCKED, commit and exact verified scope. Commit/push, verify remote, then settle only on PASS. Otherwise block dependency on a keyed haunt correction as specified globally.

## B03: Train a bounded tiny dispatch adviser with abstention

**Ledger implementation:** `tinyfleet-board-dispatch-20260908/tiny-dispatch-selector` — owner haunt.

**Files:** scripts/dispatch_selector.py (new); scripts/test_dispatch_selector.py (new); runs/board-dispatch-v1/selector/; docs/board-dispatch-model-card.md (new).

**Dependencies:** B02-V, C06-C08, S03-S05 verified

**Interface/output:** Model emits JSON {task_class,ranked_owner_ids,abstain,reason_span}; no commands or task-state changes. Validator enforces schema, owner whitelist and unchanged explicit owner.

**Steps:**

- [ ] 1. Use frozen 360M base/LoRA and identical corpus versus B02 controls; optional FunctionGemma comparison is separately pinned. Train on task classification/suitability, never on executing board posts.
- [ ] 2. Constrain outputs to supplied eligible owner IDs and task-class enum. A deterministic post-validator rejects unknown owner, fabricated task ID, stale input snapshot, invalid JSON or requested lease mutation.
- [ ] 3. Calibrate abstention only on validation; preserve raw output so invalid proposals remain counted even when deterministic validation blocks them. Never let a guard's zero final violations hide frequent model violations.
- [ ] 4. Run seed-17 pilot first under 30 GPU-minute cap. Proceed to 17/29/43 confirmatory runs only with data/headroom; use new heldout reserve after any tuning. Fine-tuning/runtime failures stay blocked, baseline-dominance is a measured no-go.
- [ ] Run the check below, capture outputs/exit codes and write `docs/task-receipts/B03-implementation.md`. Commit/push scoped files and verify remote containment before submitting to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_dispatch_selector.py
```

**Acceptance:** Poisoned-output fixtures cannot change owner/lease/state or produce dispatch; full valid negative-result bundle or matched model predictions with calibrated coverage and resource cost.

### B03-V: independent verification — owner vpn

**Ledger:** `tinyfleet-board-dispatch-20260908/verify-tiny-dispatch-selector`.

- [ ] Read global strict rules and the exact submitted source revision in `docs/task-receipts/B03-implementation.md`. Use an isolated checkout; no live dispatcher calls.
- [ ] Independently run the check, inspect source manifests/hashes and recompute metrics from copied raw records. Verify no future state/labels, no private publication, no explicit-owner replacement, and no gate bypass.
- [ ] Add an unseen forged-owner/stale-state/duplicate or malformed-output case; deliberately break one deciding guard, watch the test fail, restore and watch pass. Record command/exit/output hash for both.
- [ ] For model evidence check raw invalid proposals separately from post-validator rejections, statistical units/intervals, matched controls and measured resource budget. Label replay's inability to measure real owner acceptance/task completion explicitly.
- [ ] Write `docs/task-receipts/B03-verification.md` with PASS/FAIL/BLOCKED, commit and exact verified scope. Commit/push, verify remote, then settle only on PASS. Otherwise block dependency on a keyed haunt correction as specified globally.

## B04: Evaluate dispatch recommendations chronologically without changing live dispatch

**Ledger implementation:** `tinyfleet-board-dispatch-20260908/dispatch-shadow-verdict` — owner haunt.

**Files:** scripts/replay_dispatch_shadow.py (new); scripts/test_dispatch_shadow.py (new); runs/board-dispatch-v1/shadow/; docs/board-dispatch-verdict.md (new).

**Dependencies:** B03-V; S04 scorer verified; legacy NO-ACK/fallback policy remains in its existing ledger task

**Interface/output:** Replay consumes immutable as-of snapshots, saves baseline/model suggestions and guard outcomes. It never mutates live ledger, board, leases, routes or scheduling.

**Steps:**

- [ ] 1. Process frozen events in timestamp order using only state available at each decision. Include duplicates, late receipts, owner disappearance, backlog/load changes and interrupted claims. Synthetic stress sequences are labeled synthetic.
- [ ] 2. Use spies/blocked executables to prove no mesh-chat/mesh-tell/mesh-task/live dispatcher calls; tests assert unchanged copies of ledger input, deterministic duplicate rejection and respect for explicit owners.
- [ ] 3. Preregister usefulness screening: suitable-owner accuracy gain >=5 percentage points over strongest simple baseline with 95% paired interval lower bound >0; useful recommendation coverage >=25%; zero final constraint violations; measured p95 advisory CPU latency <=250ms on named hardware. These are design targets, not guarantees. Count raw invalid suggestions and label uncertainty.
- [ ] 4. Do not infer actual task completion time or owner acceptance from replay. Report those as unmeasured until an independently authorized live shadow pilot supplies them. NO-ACK reassignment still requires deterministic retry/lease rules.
- [ ] 5. Write adopt-for-further-shadow/no-go/inconclusive verdict with cost, failure examples and exact integration proposal. Even a positive result leaves live dispatch unchanged; implementation of a live adviser would be a new scoped task with original dispatcher owner coordination.
- [ ] Run the check below, capture outputs/exit codes and write `docs/task-receipts/B04-implementation.md`. Commit/push scoped files and verify remote containment before submitting to vpn.

**Check:**

```bash
rtk proxy .venv/bin/python scripts/test_dispatch_shadow.py
```

**Acceptance:** vpn replays raw events with frozen state, reproduces scores and tests late/duplicate/forged-owner controls. The verdict explains whether tiny inference adds value and proves zero live side effects.

### B04-V: independent verification — owner vpn

**Ledger:** `tinyfleet-board-dispatch-20260908/verify-dispatch-shadow-verdict`.

- [ ] Read global strict rules and the exact submitted source revision in `docs/task-receipts/B04-implementation.md`. Use an isolated checkout; no live dispatcher calls.
- [ ] Independently run the check, inspect source manifests/hashes and recompute metrics from copied raw records. Verify no future state/labels, no private publication, no explicit-owner replacement, and no gate bypass.
- [ ] Add an unseen forged-owner/stale-state/duplicate or malformed-output case; deliberately break one deciding guard, watch the test fail, restore and watch pass. Record command/exit/output hash for both.
- [ ] For model evidence check raw invalid proposals separately from post-validator rejections, statistical units/intervals, matched controls and measured resource budget. Label replay's inability to measure real owner acceptance/task completion explicitly.
- [ ] Write `docs/task-receipts/B04-verification.md` with PASS/FAIL/BLOCKED, commit and exact verified scope. Commit/push, verify remote, then settle only on PASS. Otherwise block dependency on a keyed haunt correction as specified globally.
