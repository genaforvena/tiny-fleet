# Cross-repository architectural-drift protocol

Status: protocol v1, pilot registration 2026-09-06

This protocol measures architectural change across repositories without treating one
repository's vocabulary, tooling, or prompt as a universal definition of drift. It was
written after the baseline audit found that the earlier tiny-fleet report mixed structural,
lexical, and generative claims and retained neither the generative bundle nor a reproducible
definition of `mesh_refs`.

## Claim and estimands

Register the claim before inspecting the comparison score:

> Between two pinned snapshots of each repository, which structural, lexical, behavioral,
> and generative changes are reproducible, and which transfer across repositories?

Report four estimands separately:

1. **Structural change**: file/byte/type counts and the repository's declared architectural
   units (for example tools, packages, routes, or modules).
2. **Lexical/concept change**: token and concept-frequency deltas, normalized by corpus size
   and stratified by path class; never call this semantic drift by itself.
3. **Behavioral change**: paired outcomes from repository-native tests, static checks, and
   deterministic probes run against both snapshots.
4. **Generative change**: paired model outputs for frozen prompts, scored with a pinned,
   versioned scorer and reported with raw outputs, seeds, model revisions, and uncertainty.

The headline is a vector of these estimands, not one average. A missing arm is `blocked`, not
zero. A comparison is publishable only if its data and runtime gates pass.

## Repository and snapshot selection

Select at least two materially different repositories before analysis. Record for each:

| field | requirement |
|---|---|
| repository identity | canonical local path or URL, license, and commit graph provenance |
| snapshots | immutable commit IDs, timestamps, parent IDs, and selection rule |
| comparison window | why the pair represents an architectural change rather than a release artifact |
| inclusion policy | tracked files included, generated/vendor/secrets excluded with counts |
| unit map | how files map to tools, packages, modules, or other repository-native units |
| runtime | interpreter/compiler, dependencies, model/scorer revisions, OS, and hardware |

Use a release/tag pair when available; otherwise use two commits selected by a preregistered
time or commit-distance rule. Never use `HEAD` in a frozen report. A later run may add a new
snapshot pair, but it does not rewrite an earlier result.

## License-safe corpus construction

Build the corpus from files allowed by the repository license and the study's redistribution
policy. Store hashes and metadata for excluded material, not copied proprietary content. Apply
the same path, binary, generated-file, vendored-dependency, and secret filters at every snapshot.
Keep the raw extraction manifest beside the run:

```json
{
  "schema": "cross-repo-drift.corpus/v1",
  "repo_id": "tiny-fleet",
  "snapshot": "4e87f2ee3644f53e2a9665195b9d6ddb933aa1d8",
  "files": 0,
  "bytes": 0,
  "included_sha256": "...",
  "excluded": {"generated": 0, "vendor": 0, "binary": 0, "secret": 0}
}
```

The zeros above are schema placeholders only; a real run must replace them with measured
values or fail validation. Each included row has `path`, `language`, `unit_id`, `blob_sha256`,
`bytes`, `commit_time`, and `license_basis`.

## Leakage and split controls

Split before normalization or tokenization. Keep train/calibration/heldout/adversarial data
disjoint by source, path/unit, and time where those fields exist. Run exact-hash and
near-duplicate checks across all boundaries. A generated file copied from an earlier snapshot
must not become an independent held-out example. Freeze the split manifest and cutoff before
running a model or scorer.

For cross-repository claims, repository identity is a grouping variable: never let the same
unit or copied fixture appear in the training side of one repository and the held-out side of
another. Report within-repository and cross-repository results separately; two repos do not
constitute broad generalisation by themselves.

## Structural and lexical measurements

Compute the same language-agnostic metrics for every snapshot: included files, bytes, median
and p95 file size, extensions/languages, unit count, and changed-path counts. Add a
repository-native metric only with its parser and definition recorded. For example,
`mesh_refs` must state whether it counts lexical tool-name matches, parsed invocations, or
something else; the count is not comparable across definitions.

Token metrics use a pinned tokenizer and report vocabulary size, normalized term frequency,
top additions/removals, and bootstrap intervals over units. Concepts are an explicit versioned
dictionary with false-positive/false-negative examples. Structural and lexical outputs are
descriptive; neither is evidence that behavior or meaning changed.

## Behavioral and generative arms

Run repository-native checks in clean, pinned environments. Capture command, exit code, duration,
stdout/stderr hashes, and produced artifacts for each snapshot. A missing dependency is a
failed preflight with a named blocker, not a passing empty result.

The generative arm has three controls on identical frozen prompts:

- base model with no repository conditioning;
- prompt/retrieval conditioning without weight updates;
- genuine fine-tuning (LoRA/QLoRA or equivalent), when the pinned runtime supports it.

Prompt-only conditioning is a control and must never be labeled fine-tuning. Freeze prompt text,
decoding parameters, seed, model digest, adapter hash, and scorer version. Save one JSONL record
per `(repo, snapshot, arm, prompt_id, repetition)` containing the input hash, raw output, and
runtime metadata. Score in a separate deterministic pass with lexical, structural, rubric, and
embedding metrics as distinct columns. Embedding similarity is not a semantic ground truth.

Use repeated runs to estimate variance and bootstrap confidence intervals. Report paired deltas,
worst slice, and model-capacity sensitivity. A single cosine table without raw outputs,
embedding model revision, and repetition data is `unreproducible`.

## Minimum run bundle and gates

`runs/<run-id>/` must contain:

```text
registration.json       # claim, estimands, repos, snapshots, exclusions, preregistration
environment.txt         # OS, runtimes, dependencies, model/scorer digests, hardware
corpus/<repo>-<snap>.jsonl
corpus-manifest.json     # hashes, counts, units, license/exclusion accounting
splits.json              # cutoff, IDs, source/path/time and duplicate reports
structural.tsv
lexical.tsv
behavioral.tsv
generative.jsonl         # raw paired outputs, if the arm is available
scores.tsv               # deterministic scores and intervals
controls.tsv             # negative/control outcomes
decision.md              # pass, blocked, or preliminary with exact next action
```

The run fails closed when any of these are missing: immutable snapshot, corpus hash,
split/leakage report, control result, raw output for a generative claim, or environment record.
Negative controls must include a shuffled snapshot label, a deliberately leaked duplicate, and a
missing-artifact case; the gates must detect all three. The decision must distinguish:

- `publishable`: all declared arms and controls pass;
- `preliminary`: structural/lexical or behavioral evidence exists, but a declared arm is absent;
- `blocked`: a required artifact, dependency, provenance, or control failed.

## Registered pilot

The first pilot uses two materially different local repositories:

| repo | role | old snapshot | new snapshot | rationale |
|---|---|---|---|---|
| `tiny-fleet` | small-model evaluation and corpus tooling | `4e87f2e` (2026-09-03) | next preregistered commit after protocol review | evaluation/code/data mix; Python/JSONL |
| `lte-workstation` | distributed mesh substrate and shell tools | `2dc867e` (2026-09-06) | `82c096b` (2026-09-06) | operational shell/docs/tooling mix; materially different domain |

The table leaves the new `tiny-fleet` commit unclaimed until the pilot runner freezes it. The
protocol artifact records the observed commits so a runner can reject a moving target. The pilot
must not reuse the old report's June-vs-September pair as if it were a new result.

## Reproduction command contract

The eventual runner accepts explicit paths and commits and writes only inside a new run directory:

```bash
cross-repo-drift register --run-dir runs/<run-id> \
  --repo tiny-fleet=/path/to/tiny-fleet@<commit> \
  --repo lte-workstation=/path/to/lte-workstation@<commit>
cross-repo-drift corpus --run-dir runs/<run-id>
cross-repo-drift split --run-dir runs/<run-id>
cross-repo-drift measure --run-dir runs/<run-id> --arm structural,lexical,behavioral
cross-repo-drift validate --run-dir runs/<run-id>
```

Every subcommand must be resumable from its manifest, reject a changed commit or input hash,
and print the artifact path plus a non-zero failure category. The first implementation may
remain dependency-free for registration, corpus, split, and structural/lexical arms; model
execution is an optional arm whose unavailable runtime is recorded explicitly.

## Relation to the existing tiny-fleet contract

The run bundle extends `docs/deep-evaluation-contract.md`; it does not replace it. The existing
validator remains the gate for per-model train/validation/heldout/adversarial rows, while this
protocol adds repository identity, snapshot provenance, cross-repo split controls, and
cross-repo comparability. The baseline audit remains evidence about what the old report could
not prove, not a result produced by this protocol.
