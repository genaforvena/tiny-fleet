# Confirmatory-v1 comparison: reader conclusions

**Classification: blocked as a publishable four-estimand comparison.** The run supports a
descriptive result for its generative arm only. Structural and lexical outputs are absent, and the
behavioral artifact is a compatibility gate rather than a paired behavior estimate.

The sample contains three external projects and six pinned release snapshots: HTTPX 0.23.1→0.28.1,
attrs 22.2.0→24.3.0, and pytest 7.2.0→8.3.4. The frozen registrations and raw evidence are under
[`runs/drift-confirmatory-v1/`](../runs/drift-confirmatory-v1/).

**Sample scope.** These HTTPX/attrs/pytest snapshots are a distinct frozen sample recorded in
[`runs/drift-confirmatory-v1/registration.json`](../runs/drift-confirmatory-v1/registration.json).
They are not the registered external sample in [protocol v1](cross-repository-drift-protocol.md):
its [`02-external-sample-v2` manifest](tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json)
pins Flask, Requests, and Pydantic. The HTTPX/attrs/pytest run does not replace or amend that
registered study. Its available result remains descriptive and generative-only; publication of the
registered comparison remains blocked until a versioned protocol/registration update admits this
sample or a compliant run uses the registered Flask/Requests/Pydantic sample.

| Estimand | Evidence and conclusion |
|---|---|
| Structural | **Blocked / not measured.** This run has no structural summary of file, byte, type, or unit changes. |
| Lexical / concept | **Blocked / not measured.** No token-frequency or concept-dictionary result is present. The three objective interface labels are examples, not a lexical estimate or semantic ground truth. |
| Behavioral | **Gate passed; change not estimated.** All six suites passed: attrs 1,235 old / 1,420 new; HTTPX 704 / 1,417; pytest 3,260 / 3,627. These are different suites and, for HTTPX, supported dependency environments; pass-count differences do not measure behavioral drift. |
| Generative | **Complete, descriptive only.** All 162 registered generations succeeded; the scorer produced 81 unique old/new pairs, 27 per arm. |

The generative arm compares embedding cosine between old- and new-snapshot outputs. The base arm
uses no repository excerpt; its paired output hashes matched in all 27 pairs, as expected for this
unconditioned control. The other two arms use either the snapshot excerpt or its
snapshot-specific LoRA adapter.

| Arm | Pairs | Mean cosine | Observed range |
|---|---:|---:|---:|
| Base | 27 | 1.000 | 1.000–1.000 |
| Prompt-only | 27 | 0.481 | 0.035–0.785 |
| LoRA | 27 | 0.782 | 0.267–1.000 |

LoRA similarity exceeded prompt-only similarity in each sampled project (attrs 0.770 vs 0.583;
HTTPX 0.729 vs 0.500; pytest 0.847 vs 0.362; nine pairs per arm and project). This describes
output similarity for the pinned `HuggingFaceTB/SmolLM2-360M-Instruct@a10cc151` model, one prompt
per snapshot, three seeds, and three repetitions. Cosine is not semantic correctness, and these
values do not establish that either conditioning arm better represents a project's architecture.
No inferential interval is reported; the pairs are clustered within only three projects, so no
generalization to repositories at large is supported.

Two limits materially narrow the result. First, deterministic held-out excerpt selection happened
after the objective-label freeze. The selector was label-content-blind, so this is a chronology
limitation rather than evidence of label leakage; it is still not a pre-label excerpt freeze.
Second, the frozen generation registration records
`status=frozen_pending_independent_verification` and `comparison_authorized=false`. The sample is
frozen pending independent verification, and this registration does not authorize comparisons. The
execution receipt records that the assigned task proceeded because the runner did not hard-stop on
this flag. Resolve the independent-verification and authorization state before treating the
comparison as publishable.

The evidence is in the [matrix receipt](task-receipts/haunt-confirmatory-v1-generative-matrix-20260914.md),
[behavioral gate receipt](task-receipts/haunt-confirmatory-v1-paired-closeout-20260914.md), and
[final gate audit](task-receipts/haunt-confirmatory-v1-final-gate-audit-20260914.md). A publishable
cross-repository conclusion still needs the registered structural and lexical measurements, a
paired behavioral outcome arm, a `controls.tsv` with the protocol's required negative-control
results, uncertainty intervals, and independent review of this interpretation.
