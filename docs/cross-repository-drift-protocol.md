# Cross-repository architectural-drift protocol

Status: protocol v1, portable extractor registered 2026-09-11

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

For the registered architectural-drift study, freeze at least **three independent external
repositories** before analysis. The study's own repository (`tiny-fleet`) is not an external
repository. The earlier two-repository local pilot and its `lte-workstation` sample are retained
as historical artifacts; they do not satisfy or count toward this external-repository gate. Record
for each external repository:

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

The dependency-free `scripts/drift_extract.py` is the pinned corpus extractor. Invoke it with
`--repo PATH --old <40-hex> --new <40-hex> --run-dir PATH`; it reads only `git ls-tree` and
`git cat-file` objects, never mutable `HEAD` or a private mesh installation. It writes
`old-files.tsv`, `new-files.tsv`, `old-corpus.txt`, `new-corpus.txt`, `structural.tsv`, and
`manifest.json`. Paths containing `generated`, `vendor`, or `node_modules`, binary blobs, and
malformed UTF-8 are retained as excluded metadata and counted, never copied into the corpus.
Renames are identified by equal blob hashes and are not counted as added semantic content.
`units` means newline count; `mesh_refs` means executable-position `mesh-*` tokens only, not
ordinary documentation mentions. Identical commit inputs must produce zero path delta.

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

## Historical local pilot and registered external sample

The earlier two-repository pilot is retained for historical reproducibility only: `tiny-fleet`
(`4e87f2e` on 2026-09-03, with its new commit to be frozen by that pilot's own runner) and
`lte-workstation` (`2dc867eed5d128beeb69ca2e818f291ab76ea895` to
`82c096be8bffc04aa56867c12d6292134f338662`). The original
`02-external-sample/sample-manifest.json` is not edited by this amendment. Neither local repository
counts toward the separate requirement for three independent external repositories.

For that requirement, freeze and use all three entries in
`02-external-sample-v2/sample-manifest.json`: `pallets/flask`, `psf/requests`, and
`pydantic/pydantic`. The manifest defines the stable-tag cutoff rule, commit IDs, license evidence,
snapshot windows, inclusion policy, and canonical archive SHA-256 for every pinned snapshot. It is
the sole input registry for the external sample; do not substitute `HEAD`, add repositories, or
change a pair after examining comparison results. A required unavailable input blocks only its
declared arm and must be named in the run decision.

## Reproduction command contract

The eventual runner accepts explicit paths and commits and writes only inside a new run directory:

```bash
cross-repo-drift register --run-dir runs/<run-id> \
  --repo flask=/path/to/flask@ab8149664182b662453a563161aa89013c806dc9 \
  --repo requests=/path/to/requests@0e322af87745eff34caffe4df68456ebc20d9068 \
  --repo pydantic=/path/to/pydantic@5bd3a6507b749fcd4833173fba88b3690ff77170
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

## Offline generative fixture runner

`scripts/drift_generate.py` is the bounded fixture runner for the generative arm. Its frozen
manifest names repository/snapshot/prompt identity, the three required arms (`base`, `prompt-only`,
`lora`), seeds, repetitions, model digest, and scorer digest. It writes one raw
`generative.jsonl` record for every `(repo, snapshot, arm, prompt_id, seed, repetition)` key and
validates input hashes and provenance before accepting the matrix. Missing arms, duplicate keys,
snapshot-label swaps, and prompt contamination fail closed. The default fixture backend is
dependency-free and does not execute generated commands or access the network; real inference is
an explicitly separate, pinned run.
