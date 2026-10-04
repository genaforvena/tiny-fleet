# Architectural drift: execution and completion plan

Status, 2026-10-04: **in progress; full four-estimand study not complete**. The
latest Docs dashboard reports all nine full-bundle requirements incomplete and
research status UNKNOWN; execution inputs READY is availability only. This does
not negate the separately accepted, bounded LTE pilot controls criterion. See
the [evidence ledger](evidence-status.tsv) for the sample-specific distinction
and requirement-level records.
Completion owner: **genome**. Independent acceptance: **witness**, not the author.
Durable resident task: `tiny-fleet-architectural-drift-completion-20260930`.
This is an execution roadmap for the existing [protocol](cross-repository-drift-protocol.md),
not an amendment to frozen samples, registrations, budgets, or publication gates.

## Question and fixed scope

Which structural, lexical, behavioral, and generative changes between pinned snapshots
are reproducible? Report these as four separate estimands, never one semantic-drift score.
A negative or inconclusive result is a valid result. A blocked arm remains open with an
exact missing prerequisite and retry condition; a plan or fixture pass does not complete it.

The registered external sample is
[`02-external-sample-v2/sample-manifest.json`](tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json):

| Repository | Old release / commit | New release / commit |
|---|---|---|
| Flask | 2.2.2 / `a1c478bc93d3dc018a6e7a1ba3cf5409553c9df3` | 3.1.0 / `ab8149664182b662453a563161aa89013c806dc9` |
| Requests | v2.28.1 / `4d394574f5555a8ddcc38f707e0c9f57f55d9a3b` | v2.32.3 / `0e322af87745eff34caffe4df68456ebc20d9068` |
| Pydantic | v1.10.4 / `63c683d9fc7b494bf81e964f97ec2f9b78b8e09d` | v2.10.4 / `5bd3a6507b749fcd4833173fba88b3690ff77170` |

The local tiny-fleet structural comparison is a tooling check, not an external sample.
The separate HTTPX/attrs/pytest confirmatory-v1 run does **not** replace these projects.
Its [reader conclusions](confirmatory-v1-reader-conclusions-20260914.md) retain a
descriptive generative result and explicitly unresolved comparison authorization.

## Run now: verify inputs without starting inference

Prerequisites: Python 3, this worktree, and the six previously acquired archives.
These archives are local run inputs, not guaranteed to exist in a fresh clone.
If absent, acquire the exact registered commits using the manifest's acquisition rule,
recreate its `git archive --format=tar` bytes, and verify hashes before use. Do not pick
new tags or silently substitute a different sample.

Run from the repository root:

```bash
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

registry = Path('docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json')
sample = json.loads(registry.read_text())
root = Path('runs/behavioral-preflight-v3-python311/source-archives')
for repo in sample['repositories']:
    for snapshot in repo['snapshots']:
        path = root / f"{repo['repo_id']}-{snapshot['label']}.tar"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != snapshot['archive']['sha256']:
            raise SystemExit(f'hash mismatch: {path}')
        print(repo['repo_id'], snapshot['label'], snapshot['commit'], digest, 'PASS')
PY
```

Acceptance: all six archives match their registered SHA256; any absent or changed input
fails the command. On 2026-09-30, all six matched. This proves byte identity, not scientific
acceptance, license-filtered extraction, native behavior, or permission to run the matrix.

The [README structural reproduction](../README.md#architectural-drift-study) is also
runnable now. The pinned comparison was rerun on 2026-09-30: 12 → 306 included paths,
82,150 → 1,454,580 bytes, 294 added paths, four changed paths, no deleted paths or
identical-blob renames, and no local Python import-edge churn. An identical-commit
control returned zero structural and lexical deltas. This is not a new external finding.

## Ordered work and acceptance gates

Steps may proceed independently where inputs permit; do not start generation while its
gates remain blocked. Genome retains ownership through delivery. Discover can supply
source/license/unit-map investigations; senses can supply deterministic gate checks.
Neither infrastructure health nor artifact hashes substitute for witness acceptance.

| Step | Owner | Execution / deliverable | Acceptance and next action |
|---|---|---|---|
| 1. Reconcile frozen inputs and gates | genome | Verify six archives above; bind sample, excerpts, adapter trees, scorer and model revisions to a source-bound inventory. Reconcile current receipts against `runs/drift-generative-v2/decision.md`, including exact artifact review and excerpt/label chronology. | Six archive hashes pass; discrepancies and authorization state explicit. Witness reviews exact bytes, not a historical role name. This is the next resident step. |
| 2. Complete external structural/lexical measurement | genome; discover assists | Reuse extractor and lexical definitions to build an archive-capable measurement path for all six snapshots, with identical license/secret/vendor filters, excluded metadata, frozen native unit maps, tokenizer and concept dictionary hashes. Save per-project inventories and deltas in a fresh run. | All six snapshots measured; unit-level uncertainty and documentation/source strata reported. Identity, rename, duplication and shuffled-label controls exercise the actual path. Current Git-object extractor alone does not supply archive ingestion or all protocol gates. |
| 3. Measure paired native behavior | genome | Reconcile six pinned dependency/runtime preflights; repair supported environments without changing source snapshots. Freeze common deterministic probes and expected old/new outcomes before comparison; save command, exit, duration and stdout/stderr hashes per snapshot. | Paired outcomes, not differences in test-suite pass counts. Missing environments remain failed preflights with precise retry conditions; no empty passing arm. |
| 4. Freeze admissible generative execution | genome + witness gate | Bind six excerpt rows, six adapter tree hashes, immutable base revision, prompt template, scorer content/model digests, decoding, seeds and repetitions into a complete v2 manifest. Independently dispose of blind-order limitations and reconcile actual resource admission/caps. | Exact artifact review, behavioral prerequisites and explicit execution authorization recorded. Preserve initial registration. Exploratory-only evidence cannot silently become confirmatory; a required unseen sample needs a separately versioned freeze before outputs. |
| 5. Generate and score | genome | After step 4 passes, run real v2 inference using the command below; retain successful and failed records and measured wall/token/memory costs. Score separately with the pinned scorer and retain paired scores, per-project slices and intervals. | 162 unique registered records (3 projects × 2 snapshots × 3 arms × 3 seeds × 3 repetitions); 81 old/new pairs. Base, prompt-only and genuine LoRA remain distinct. Inference seeds are not independently trained adapters; cosine is not semantic correctness. |
| 6. Validate controls and interpret | genome; witness independently reviews | Assemble protocol bundle: registration/environment, corpus manifest, splits, structural/lexical/behavioral tables, raw generations, scores, `controls.tsv`, and `decision.md`. Exercise shuffled labels, intentional leakage and missing-artifact refusal. | Every declared artifact and control checked. Publishable only if all declared arms pass; otherwise report preliminary/blocked with exact omissions. Preserve negative results and failed attempts. |
| 7. Deliver reader-facing result | genome after witness PASS | Update README, conclusions and evidence ledger with measured revision and bound artifacts; independent review; commit/push only owned paths and record SHA/outcome. | Reviewed report and reproducible commands delivered. Do not close the study task merely because the plan, tests or structural pilot pass. CI acceptance, if required, needs a successful run for the pushed SHA. |

## Existing commands versus missing orchestration

These are real implementation checks, not experiments:

```bash
python3 scripts/test_drift_extract.py
python3 scripts/test_drift_edge_delta.py
python3 scripts/test_drift_lexical.py
python3 scripts/test_drift_generate.py
python3 scripts/test_drift_validate.py
python3 scripts/test_drift_score_confirmatory_v1.py
```

After step 4's independent gates pass, the existing real-model CLI is:

```bash
# Supply the independently approved v2 manifest and a NEW output directory.
.venv/bin/python scripts/drift_generate.py \
  --manifest /path/to/approved-v2-manifest.json \
  --run-dir /path/to/new-run --device cpu
```

This is conditional, not a launch instruction for the current blocked registration.
The backend needs locally cached pinned Transformers weights/tokenizer, PEFT adapters and
compatible dependencies. V2 refuses fake output. Do not retrain, overwrite prior runs,
evict unrelated workloads, or extend frozen budgets to make the command pass.

`cross-repo-drift register/corpus/split/measure/validate` in protocol v1 is a **proposed
interface, not an installed executable**. Steps 2 and 6 own the missing ingestion and
full-bundle validation work; existing scripts are components, not a completed end-to-end
runner. This roadmap is executable as staged work, not a claim that the full study is
already runnable with one command.

## Progress, retries, and completion

The resident plant keeps the task and source-bound artifacts under ignored
`.mishe-tauftauf/`; reader-facing requirements stay in this document. Each bounded step
must record inputs/revision, command/exit, actual outcome, limits and the next owner.
Use an actionable next step while ready; if blocked, record the exact prerequisite and
retry event. Do not repeatedly audit unchanged blockers instead of doing available work.

No completion date is claimed before runtime, resource and independent-review gates
are reconciled. The completion obligation remains open until the four-estimand report
and independent disposition are delivered; unresolved required arms stay visibly blocked.
