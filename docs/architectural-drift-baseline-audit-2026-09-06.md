# Architectural Drift Report baseline audit

Date: 2026-09-06
Source report: `docs/tiny-fleet-drift-report.md`
Source commit: `4e87f2e`

## Reproduction evidence

The report's v1 ref resolves to commit `5475816081b26a0f9aebb92da844493b19304eef`, dated
2026-06-15. The extracted cache at `~/.mesh/tiny-fleet/` contains 232 v1 files and 1,439 v2
files, matching the report's file counts. Its recorded v2 snapshot is commit `a8b73e01`, dated
2026-09-03, rather than a moving `HEAD`; this is a reproducible anchor for the next run.

The cached structural record reproduces v2 total size (29,541.0 KB), average size (20.5 KB),
vocabulary (88,724), extension counts, and the listed concept counts. No generated comparison
results are present under `~/.mesh/tiny-fleet/results/`, so the reported three cosine values,
0.4946 average, 0.5054 drift score, and qwen capacity comparison are not independently
reproducible from the retained bundle.

## Method findings

1. `scripts/mesh-tiny-fleet` uses Ollama Modelfiles with version-specific system prompts and
few-shot examples; it does not fine-tune weights. The report correctly labels this limitation.
2. The structural extractor is implemented in `scripts/mesh-tiny-fleet-snapshot`, but its
`mesh_refs` metric sums a fixed allowlist of tool names. The cached v2 value is 4,020 while the
report claims 30,326 references; that claim is therefore not reproduced by the shipped extractor
and must be corrected or given a separate counting definition.
3. The current comparison uses token Jaccard, bigram overlap, and term-frequency cosine in the
script; it does not establish that an embedding model produced the report's cosine table. The
embedding backend, prompt set, raw outputs, model revisions, seeds, and confidence intervals are
absent from the retained results.
4. The report's interpretation conflates at least vocabulary drift, structural growth, and
generative response divergence. These must become separate measures with controls before a single
architectural-drift verdict is publishable.

## Decision and next gates

The report is a valuable methodology candidate and a useful hypothesis, but the headline score is
not yet a publishable measured result. The active `tinyfleet-drift-methodology` chain now covers:

- audited snapshot/provenance and every reported number;
- an improved cross-repository protocol with leakage, controls, calibration, uncertainty, and
  license-safe corpus construction;
- a tested evaluator and negative controls;
- a frozen cross-repo study with prompt-only versus genuine fine-tuning arms where dependencies
  permit;
- independent `witness` review of freshness, reproducibility, interpretation, usability, and
  publishability; and
- final synthesis only after those artifacts exist, with blocked dependencies stated explicitly.

Until those gates pass, the report must be presented as a preliminary analysis, not as evidence of
a validated general architectural-drift measurement.
