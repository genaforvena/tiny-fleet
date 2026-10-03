# Documentation

Start with the [project README](../README.md) for the research question, current evidence, and offline checks. Use the [evidence ledger](evidence-status.tsv) to distinguish measured findings from open requirements. This index groups reader documentation separately from proposals and historical records; a page's presence does not establish scientific acceptance.

## Research results and execution

| Document | Purpose |
|---|---|
| [Architectural drift execution](architectural-drift-execution.md) | Required four-estimand work, reproduction steps, and open acceptance criteria |
| [Terminology-drift result](tiny-fleet-drift-report.md) | Measured exploratory result, costs, limits, and reproduction |
| [Confirmatory-v1 conclusions](confirmatory-v1-reader-conclusions-20260914.md) | Separate experiment's descriptive findings and unresolved scope |
| [Fleet study gaps](study-gap-analysis.md) | Independence, provenance, and evaluation gaps |
| [BbyWVY notes](bbywvy-360m-notes.md) | Background on the motivating narrow-model experiment |

## Protocols, evaluation, and reproduction

| Document | Purpose |
|---|---|
| [Cross-repository drift protocol](cross-repository-drift-protocol.md) | Structural, lexical, behavioral, and generative estimands |
| [Fleet study registration](study-registration.md) | Paired study design and acceptance requirements |
| [Evaluation methodology](evaluation-methodology.md) | Evaluation approach and limitations |
| [Deep evaluation contract](deep-evaluation-contract.md) | Dataset and output integrity checks |
| [Scoring rubric](scoring-rubric.md) | Scoring definitions |
| [Drift registration](drift-validation-registration.md) and [v2](drift-validation-registration-v2.md) | Versioned validation designs; retain their distinct scopes |
| [Generative-v2 runner contract](drift-generative-v2-runner-contract.md) | Runner and artifact requirements |
| [Concept dictionary](concepts-v1.json) | Versioned lexical definitions |
| [Frozen research artifacts](tiny-fleet-artifacts-20260907/) | Sample manifests, protocols, and supporting records; preserve paths and bytes |

## Proposals and research context

These documents describe designs or possible uses. Read their stated status before treating them as implemented or validated.

- [Applications overview](applications.md) and [application proposals](applications/).
- [Mishe transfer design](mishe-transfer.md) and [board dispatch study](board-dispatch-study.md).
- [Persona and code plan](persona-and-code-plan-2026-09-07.md).
- [Related work](related-work.md).
- [Tiny-fleet and Mishe context](mesh.md).

## Historical audits and records

These records preserve prior observations and decisions. Use the project README and evidence ledger for current conclusions; historical receipts do not substitute for current acceptance.

| Group | Records |
|---|---|
| September 6 baseline and evaluation audits | [Architecture baseline](architectural-drift-baseline-audit-2026-09-06.md), [repository audit](audit-current-repo-2026-09-06.md), [method review](review-eval-method-2026-09-06.md), [validator verification](deep-evaluation-validator-verification-2026-09-06.md), [mood corpus](mood-corpus-2026-09-06.md) |
| September 7 reaudits | [Full reaudit](full-reaudit-20260907.md), [additional reaudit](tiny-fleet-reaudit-20260907-haunt.md) |
| September 8 ledger and publication review | [Ledger reconciliation](ledger-reconciliation-20260908.md), [ledger registration](ledger-registration-20260908.json), [publication review](publication-review-20260908.md), [review verification](review-verification-20260908.md) |
| Task receipts | [Historical receipt guide](task-receipts/README.md) |
| Older implementation plans | [Tabular plans](plans/) and [workflow plans](superpowers/plans/) |

## Keeping this documentation useful

The resident Docs role maintains this tree and the root README. Keep reader entry points, methods, results, and historical context distinct. Update links with any move or consolidation and preserve frozen evidence. Local wake notes, chat, plans, handoffs, and operational checks belong in the ignored `.mishe-tauftauf/` site; add public documentation when it helps a reader understand or reproduce the project.
