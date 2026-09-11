# Deep-evaluation contract

Status: design gate for `tinyfleet-specialists/design-deep-evals`  
Version: `2`  
Owner: `tinyfleet-specialists`

This contract turns `docs/evaluation-methodology.md` into a frozen hand-off between corpus
freezing, model evaluation, and mesh review. A run is publishable only when every required artifact
exists, hashes resolve, and the negative controls fail closed.

## Frozen manifest

`runs/<run-id>/manifest.json` is immutable after the first scoring step. It must contain:

```json
{
  "schema": "tiny-fleet.deep-eval.manifest/v2",
  "run_id": "2026-09-06-guitar-001",
  "git_commit": "<40-hex commit>",
  "base_model": {"id": "<pinned model id>", "revision": "<immutable revision>"},
  "candidate": {"id": "<adapter or model id>", "revision": "<sha256>"},
  "controls": ["base", "reference"],
  "seed": 17,
  "prediction_matrix": {"models": ["base", "reference", "<adapter or model id>"], "seeds": [17], "repetitions": [0]},
  "raw_output_schema": "tiny-fleet.predictions/v1",
  "migration_report": {"status": "none"},
  "rendering": {"template_sha256": "<64-hex>", "config_sha256": "<64-hex>"},
  "config_sha256": "<64-hex sha256>",
  "created_at": "2026-09-06T00:00:00Z",
  "cutoff": "2026-08-01T00:00:00Z",
  "temporal": {"train_end": "2026-07-01T00:00:00Z", "heldout_start": "2026-07-15T00:00:00Z"},
  "datasets": {
    "train": {"path": "corpus/guitar-train.jsonl", "rows": 0, "sha256": "<64-hex>"},
    "validation": {"path": "corpus/guitar-validation.jsonl", "rows": 0, "sha256": "<64-hex>"},
    "heldout": {"path": "corpus/guitar-heldout.jsonl", "rows": 0, "sha256": "<64-hex>"},
    "adversarial": {"path": "corpus/guitar-adversarial.jsonl", "rows": 0, "sha256": "<64-hex>"}
  },
  "slices": ["domain", "language", "source_id", "created_at_bucket", "expected_route"],
  "evaluation": {"bootstrap_replicates": 10000, "confidence": 0.95}
}
```

The example uses placeholders intentionally; a real manifest must replace every `<...>` value and
must report positive row counts. `git_commit`, model revision, seed, cutoff, and all dataset hashes
are required for reproduction. Dataset paths are repository-relative and may not point outside the
run's declared source snapshot.

Each JSONL row must have these fields, with `split` matching its manifest dataset:

```json
{
  "case_id": "guitar-000001",
  "source_id": "source-2026-07-book-03",
  "created_at": "2026-07-12T14:00:00Z",
  "domain": "guitar",
  "language": "en",
  "split": "heldout",
  "expected_route": "specialist:guitar",
  "expected_action": "answer",
  "prompt": "What chord is this?",
  "reference": "The answer text",
  "source_family": "book-03",
  "provenance": {"kind": "licensed|synthetic|internal", "source": "...", "redacted": true}
}
```

`case_id` must be unique within each split. `prompt` and `reference` are actual typed strings;
prompt leakage is checked after Unicode NFKC, case-folding, and collapsed whitespace. `source_family`
is independent of split names and may not overlap train/validation or validation/heldout. All paths
are resolved before containment checks, so symlink escapes are rejected without opening the target.
Timestamps must be timezone-aware; `cutoff` is a maximum inclusion time, while `train_end` and
`heldout_start` define the temporal holdout window. Version 1 remains readable only for archival
inspection and is never publication-ready.

## Report bundle

The scorer writes these exact files under the same run directory:

| File | Required content | Gate |
|---|---|---|
| `config.json` | resolved training/scoring arguments | hash matches manifest |
| `environment.txt` | Python, package, OS, GPU/model runtime versions | non-empty and captured before scoring |
| `predictions.jsonl` | one raw prediction per case/model, including confidence and latency | row count equals manifest cases × models |
| `scores.json` | aggregate score, bootstrap interval, paired deltas, worst case | no aggregate without paired rows |
| `slices.tsv` | score, count, interval for every declared slice | every non-empty slice present |
| `calibration.tsv` | reliability bins, ECE, Brier, selective risk | bins sum to prediction count |
| `routing.tsv` | route confusion, abstain/escalate counts, margin distribution | operator-first cases included |
| `adversarial.tsv` | expected action, actual action, forbidden-output result | zero unreviewed failures |
| `cost.tsv` | p50/p95 latency, peak memory, cold start, fallback/timeout | units and sample count present |
| `decision.md` | route/abstain/escalate/reject, coverage, fallback, next exact action | cites all above artifacts |

Raw predictions are append-only inputs. Scores and decision files are derived in a separate,
deterministic pass; editing a prediction requires a new run id and new manifest hash.

Each prediction has the key `(case_id, model, seed, repetition)` and must include the dataset
prompt hash, the exact rendered-input text and hash, output, route, action, confidence and its
declared kind, latency, and status. The manifest's prediction matrix is authoritative; duplicate,
unknown, missing, or extra keys are rejected. Status is `ok`, `timeout`, or `error`; failed rows
retain raw output when available and use null for unavailable confidence/latency values with an
explicit reason. Prompt and rendered-input hashes are checked independently, and references may
not be placed in rendered input without an explicit fixture justification.

## Deliberate negative controls

The validator/test harness must execute these fixtures on every contract change:

1. **Leakage control:** duplicate a held-out `case_id` into train and duplicate a normalized text
   across train/heldout. Expected result: `REJECT leakage` naming both IDs and the boundary; never
   silently de-duplicate or continue scoring.
2. **Source/time control:** place the same `source_id` in train and heldout, then place a heldout
   row after the manifest cutoff. Expected result: `REJECT split-boundary` with source and cutoff.
3. **Missing-artifact control:** remove each required report file in turn, including
   `predictions.jsonl` and `environment.txt`. Expected result: `REJECT missing-artifact <path>`;
   missing is not zero and cannot produce a decision.
4. **Hash/count control:** alter one byte or row after freezing. Expected result:
   `REJECT manifest-mismatch` with expected and observed hash/count.
5. **Orphan-prediction control:** add a prediction for an unknown `case_id` or omit one expected
   model/case pair. Expected result: `REJECT prediction-cardinality` before aggregate scores.
6. **Boundary controls:** duplicate an ID within a split, overlap a `source_family` across adjacent
   splits, use a malformed typed field, leave a required split empty, and point a dataset through a
   symlink outside the run root. Expected results are stable `manifest-mismatch`, `split-boundary`,
   or `leakage` rejections; the escaped target is never opened.

Negative controls are successful only when they fail closed with a stable error category and a
non-zero process exit. A green contract test therefore includes both valid-fixture acceptance and
all five intentional rejection cases.

## Gate sequence

Freeze manifests and hashes; reproduce base/reference controls; train with recorded configuration;
write raw predictions; independently validate leakage and artifacts; compute scores, slices,
calibration, routing, adversarial, and cost tables; then write the decision. A later step consumes
the earlier path and hash and may not regenerate missing inputs. Until this bundle exists, the
current offline `24/24` benchmark remains a contract smoke test, not a specialist result.

## Next implementation step

Implement a dependency-free validator with `--manifest` and `--run-dir`, using the rejection
categories above, and add its valid-fixture plus five negative-control cases to the offline test
path before `mood-corpus` creates new RU/EN data.
