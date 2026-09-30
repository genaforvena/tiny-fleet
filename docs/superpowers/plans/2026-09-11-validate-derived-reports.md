# Validate Derived Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate every derived report against the frozen raw evaluation tape, rejecting tampering while accepting a complete negative experiment as a valid artifact.

**Architecture:** Keep raw prediction validation in `deep_evaluation.py` and add a dependency-free `report_contract.py` that parses each JSON/TSV/Markdown report, checks finite/nonnegative fields and membership, then recomputes primary counts from raw predictions. The test fixture exercises a valid failed run plus independent mutations of every report family.

**Tech Stack:** Python 3 standard library, `unittest`, JSON, TSV, SHA-256.

## Global Constraints

- Reports are derived artifacts; publication validity is separate from model or routing success.
- Missing, malformed, non-finite, negative, orphaned, or internally inconsistent reports reject with stable `REJECT report-*` categories.
- A complete failed experiment may return `artifact_valid=True` while `result_status` is `negative` and `routing_eligible=False`.
- No dependencies beyond the Python standard library.

### Task 1: Contract fixture and parser

**Files:**
- Create: `scripts/report_contract.py`
- Create: `scripts/test_report_contract.py`
- Modify: `docs/deep-evaluation-contract.md`

**Interfaces:**
- `validate_reports(run_dir: Path) -> dict` returns `{"artifact_valid": bool, "result_status": str, "routing_eligible": bool}` on acceptance and raises `ValidationError` on rejection.
- CLI accepts `--run-dir` and exits nonzero for rejected bundles.

- [ ] **Step 1: Write fixture tests first** for valid negative result, missing report, invalid JSON/TSV, edited counts, unsafe action, omitted failed case, and all-abstain usefulness claim.
- [ ] **Step 2: Run `rtk proxy .venv/bin/python scripts/test_report_contract.py` and observe the expected import/API failure.
- [ ] **Step 3: Implement the minimal parser, raw-count reconciliation, and stable CLI.
- [ ] **Step 4: Run the focused test and the existing deep-evaluation test.
- [ ] **Step 5: Update the contract document with report schemas and result-status separation.
- [ ] **Step 6: Run the exact C04 check and commit only scoped C04 files.
