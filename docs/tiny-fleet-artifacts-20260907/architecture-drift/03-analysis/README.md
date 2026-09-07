# Comparable architecture-drift analysis: frozen external sample

Status: **PRELIMINARY / STRUCTURAL ONLY; declared runtime arms blocked**  
Run date: 2026-09-07  
Study: `tinyfleet-architecture-drift-completion`

This artifact analyzes only the frozen `sample-manifest.json` from
`02-external-sample/`. It does not select new revisions, copy source, or promote a
single-repository comparison to a cross-repository finding.

## Inputs

- repository: `/home/mesh-home/lte-workstation`
- old commit: `2dc867eed5d128beeb69ca2e818f291ab76ea895`
- new commit: `82c096be8bffc04aa56867c12d6292134f338662`
- sample manifest SHA-256: `c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`
- inclusion: the four registered changed shell/test paths plus `LICENSE`

## Result vector

| estimand | status | result |
|---|---|---|
| structural | PASS / descriptive | 3 to 5 files, 274,906 to 284,322 bytes, 3 to 5 units; 2 additions and 2 modifications |
| lexical/concept | BLOCKED | no pinned tokenizer or versioned concept dictionary is in the frozen sample |
| behavioral | BLOCKED | no clean pinned runtime and paired test artifacts are available |
| generative | BLOCKED | prompts, seeds, model digests, scorer revision, and raw outputs are unavailable |

Structural change is descriptive only. It is not evidence of semantic, behavioral, or
architectural drift by itself. No `NULL`, cross-repository conclusion, or fine-tuning claim
is warranted.

## Files

- `run-config.json`: immutable input binding and analysis rules.
- `raw-input.json`: manifest hash and extracted manifest rows used as input.
- `structural.tsv`: measured per-snapshot structural summaries and deltas.
- `lexical.tsv`, `behavioral.tsv`, `generative.tsv`: explicit blocked states.
- `decision.md`: fail-closed decision and exact next action.
