# Tiny Fleet: merit, publication readiness, and ledger review

Review date: 2026-09-08 UTC. Repository: https://github.com/genaforvena/tiny-fleet.
Inspected revision: `62ba7282505eb447486b9a18468cce72457171ce`.
Requested by operator; reviewer/ledger author: tg. All newly created implementation tasks belong to haunt; each has a separate independent verification task owned by vpn, as explicitly requested. Application exploration and architectural-drift tasks are included.

## Assessment

**Worth pursuing, as a bounded empirical study and reproducible engineering artifact. Not yet evidence for the README's stronger scientific claims.**

The strongest question is: on a single consumer GPU, when does routing among genuinely fine-tuned 360M specialists improve held-out task quality per unit latency/memory over a base model, a pooled adapter, prompt/retrieval conditioning, and simple routing rules? Report where this fails as well as where it succeeds. An honest negative result on abstention or specialization can have research value.

Three projects currently share one README: a toy LoRA fleet, a deterministic operator-policy selector, and a codebase-drift experiment. Give each its own claim and evidence boundary. The first is the clearest primary paper/artifact; drift needs a separate validation study. A term-frequency change or cosine between differently prompted outputs is not architectural ground truth.

Novelty is not “multiple LoRAs plus a router.” Prior work includes [LoRA](https://arxiv.org/abs/2106.09685), [S-LoRA](https://arxiv.org/abs/2311.03285), and [RouteLLM](https://arxiv.org/abs/2406.18665); the [MoErging survey](https://arxiv.org/abs/2408.07057) maps specialist reuse and routing. These primary sources were checked during this review. My proposed contribution is an empirical evaluation at very small scale, with explicit abstention, independent-source tests, cost accounting, and reproducible negative results. This is a research direction, not a demonstrated novelty or acceptance claim.

## Findings, in repair order

| Severity | Evidence at inspected revision | Consequence | New task |
|---|---|---|---|
| High | `scripts/deep_evaluation.py:112-143`: cases overwritten in dict, prediction pairs collapsed into a set; “text” comparison serializes metadata fields excluding actual text | Duplicate predictions and leaked text can pass; existing six passing tests do not establish study validity | C02, C03 |
| High | `scripts/deep_evaluation.py:77-79`: reports checked for existence only | Empty/forged routing, adversarial and aggregate reports can be accepted | C04 |
| High | `scripts/deep_evaluation.py:95-98`: lexical relative-path check without resolving traversal/symlinks | Claimed run containment is not enforced | C02 |
| High | `scripts/router.py:77-88`: zero-vector division, no finite-value or absolute similarity gate | NaN margin can fall through to specialist; relative margin alone can select a specialist when both scores are low | C07, S05 |
| High | `README.md` safety example executes the review action if require_approval is false; `operator_policy.py` emits such review decisions | Example contradicts the documented review-before-execution rule | C08 |
| High | `scripts/train_eval.py:66-67,88-91`; `scripts/persona_code.py:154-165` | Training labels include padding in toy trainer; perplexity uses input length rather than predicted-token count | C05 |
| High | `runs/persona-code/eval-all.json`, `docs/tiny-fleet-reaudit-20260907-haunt.md` | 84 adversarial predictions, zero classified abstentions. This is a failed heuristic control, not a calibrated estimate of universal unsafe behavior | S04-S06 |
| High | README: “trained” drift models, “Yes…striking”, semantic interpretations of cosine, predicted greater divergence from true LoRA | Contradicts the later pinned conclusions which support descriptive structural change only | Existing closeout + C01 |
| Medium | `scripts/train_eval.py` mutable base ID/no explicit seed; persona trainer writes fixed adapter paths despite run-dir | Old results can be overwritten; repeatability and adapter-to-run identity incomplete | C06 |
| High | `scripts/persona_code.py:90,104,221,236`: split-derived source IDs, four identical heldout texts per domain, generation receives reference completion | Artificial independence, inaccurate RU/EN metadata and answer exposure invalidate the apparent heldout task-quality evidence | S01-S04 |
| Medium | README structural command points to absent `scripts/mesh-tiny-fleet`; runtime/most drift tooling is in lte-workstation | A clean public clone cannot run the advertised workflow | D01, P01 |
| Medium | `tinyfleet-specialists` mood training/verification receipts cite guitar/sourdough adapters; no mood adapter in current repo | Ledger completion does not establish the named mood experiment | S07 |
| Medium | Original BbyWVY work remains notes/spot-checks | Do not imply reproduced training or established equivalence | S08 |
| Medium | `requirements-eval.txt` is only numpy floor; no clean-clone CI or complete run environment lock | Local successful execution is not outsider reproducibility | P01 |

The reviewed drift bundle explicitly states that it does **not** support semantic, conceptual, behavioral, generative, architectural, or cross-repository findings:
`docs/tiny-fleet-artifacts-20260907/architecture-drift/04-conclusions/conclusions.md`.
The admitted sample changes from 3 to 5 paths; that bounded observation must not be conflated with the older full-tree vocabulary headline.

## Fresh verification

Executed from this repository on 2026-09-08 using its existing .venv, all exit 0:

```bash
rtk proxy .venv/bin/python scripts/fleet_benchmark.py --test
rtk proxy .venv/bin/python scripts/operator_policy.py --test
rtk proxy .venv/bin/python scripts/test_deep_evaluation.py
rtk proxy .venv/bin/python scripts/test_persona_code.py
rtk proxy .venv/bin/python scripts/persona_code.py self-test --manifest runs/persona-code/manifest.json
```

Observed: fleet 24/24 fixture/inventory checks; policy 41/41 heldout, 14/14 adversarial, 8/8 structured decisions plus precedence mutation; deep-eval 6 tests; persona-code 2/2; manifest self-test OK. These are contract checks, not new GPU training, live router evaluation, or scientific replication. This turn changes review/plan/evidence files only.

Independently reproduced two failures with temporary/in-memory fixtures: appending a duplicate prediction returns `ACCEPT`; injecting an all-zero embedding returns `specialist:guitar`. Counting actual corpus text confirms persona heldout=4 rows/1 unique text and code heldout=4 rows/1 unique text. These observed failures override any inference that the green fixture suite guarantees validity.

## Remaining live ledger work before adding this plan

Read both chain JSON and `mesh-task status`, and compared `mesh-promises --json` at 00:16:56Z. Nine unfinished steps remain across these four direct chains:

| Existing chain | Actual state | Remaining owners/work | Treatment |
|---|---|---|---|
| `haunt-install-unblock-20260907` | active; lease expired 2026-09-07 23:34:14Z | haunt: install-and-retry-tinyfleet | Keep identity; use for actual dependency provisioning |
| `tinyfleet-publishable-closeout-20260907` | active; same expired lease | haunt: publishable-repository-closeout | Keep identity; owns README correction and final evidence-index assembly |
| `tinyfleet-real-mesh-pilot-20260907` | first step active, expired 23:34:40Z; two open | haunt: select/implement; witness: verify-and-report | Keep identity; consume S06 evidence, execute shadow pilot under original task |
| `tinyfleet-architecture-drift-review-20260907` | all four open | haunt: external sample/run/conclusions; witness: critical review | Keep identity; owns >=3 external repositories and actual comparative study |

The promises view contains all four current obligations, owner haunt. “active” with an expired lease and a repost is not evidence of current execution.

Additional related ledger obligations: `design-audit-task-sweep-20260907/plans-tiny-fleet-expansion` remains open, owner tg; `ba260907-05-workspace/repair` is open, owner hire, and explicitly addresses wrong-repository receipts. These are coordination tasks, not additional specialist experiments.

Completed chains: `tinyfleet-specialists`, `tinyfleet-drift-methodology`, `tinyfleet-architecture-drift-completion`, `tinyfleet-reaudit-20260907`. Their completion means that steps delivered artifacts, including blocked/negative outcomes; it does not mean all scientific promises succeeded. Successor work is now explicitly named.

The board at 2026-09-07T23:04:57Z cites an unrelated `hyperhauntology_for_kids` artifact for Tiny Fleet closeout; TG later called that recovery successful. That receipt does not prove Tiny Fleet progress. C01 requires a correct-repository reconciliation without rewriting old evidence or impersonating another owner.

## Implementation package

Detailed small-worker contracts: [publication implementation plan](superpowers/plans/2026-09-08-publication-science.md).
New chain plans: [publication](plans/publication-science-20260908.tsv), [drift methods](plans/drift-science-20260908.tsv), [applications](plans/applications-20260908.tsv), [board dispatch](plans/board-dispatch-20260908.tsv).
There are **80 new ledger steps**: 40 haunt implementation/exploration tasks and 40 interleaved independent vpn verification tasks. Implementation scope: 8 correctness, 9 experimental (including adversarial operator-policy evaluation), 4 presentation/reproducibility, 4 drift-method, 11 application-protocol/pilot, and 4 board-dispatch study tasks. Existing tasks above are dependencies, not duplicates. No implementation task is claimed complete by this review. See [application hypotheses and cited precedents](applications.md).

The operator specifically proposed board dispatch. This is a plausible high-value task for free-text intent/suitability classification. B01–B04 compare a tiny adviser against current rules, linear classification and embeddings on source/time-isolated cases, then replay decisions in shadow. Explicit ownership, eligibility, leases, dependencies, duplicate prevention and retry rules remain deterministic. A model suggestion cannot release a lease or change task state. Historical owner acceptance/completion times are not causally inferable from offline replay.

vpn is present in the live tmux roster. Its ordinary networking charter is not modified: the operator explicitly assigned these repository verification tasks to it. Existing witness-owned gates remain unchanged. Every new implementation submits to a vpn gate before its successor is released. Failed verification blocks progress and names a corrective haunt task; a valid negative scientific result can pass verification without qualifying for deployment.

The release may honestly present a negative or preliminary result. A stronger usefulness claim requires the paired experiment, uncertainty, resource comparison and original pilot gate. A cross-repository architectural claim additionally requires independent labels and the existing external-study/witness gate. Uploading a paper or publishing a release is not evidence that either claim is true.
