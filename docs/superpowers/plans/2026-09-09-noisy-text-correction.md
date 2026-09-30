# Noisy Text Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline, reproducible A08 domain-text correction screen that measures deterministic baselines while preserving protected fields and honestly gates unavailable model arms.

**Architecture:** A frozen CC0 synthetic manifest expands to development, validation, and heldout source families. A pure correction/scoring module runs identity and dictionary/edit-distance baselines, writes raw JSONL and a summary, and refuses pilot/score phases until model dependencies are independently verified. Protected spans are extracted from the clean reference and must remain byte-for-byte unchanged.

**Tech Stack:** Python 3 standard library, JSON/JSONL artifacts, unittest, no network or paid APIs.

## Global Constraints

- Hold out source documents before noise generation; real publicly licensed noise is not available, so the corpus is explicitly synthetic CC0.
- Minimum screening set is 100 independent heldout units plus disjoint validation; source families may not cross splits.
- Baselines are identity and dictionary/edit-distance; ByT5-small and 360M LoRA are recorded as unavailable until dependency gates pass.
- Pilot cap is 30 GPU minutes and one model job; no pilot is justified unless baseline headroom and labeled data justify it.
- Go/no-go requires >=20% relative CER reduction, clean-field corruption <=0.5%, and unchanged protected fields; unmeasurable bounds are INCONCLUSIVE.
- No adapter is added to live routing.

### Task 1: Contract tests and frozen manifest

**Files:**
- Create: `scripts/test_app_noisy_text_correction.py`
- Create: `corpus/applications/noisy-text-correction/manifest.json`

- [ ] Write tests for exact correction, protected-field preservation, missing/OOD/malformed input, split independence, and raw/summary artifacts.
- [ ] Run `rtk proxy .venv/bin/python scripts/test_app_noisy_text_correction.py`; expected initial import failure because the implementation module does not exist.
- [ ] Add the manifest with 12 development, 20 validation, and 120 heldout synthetic documents across independent source families.

### Task 2: Minimal deterministic implementation

**Files:**
- Create: `scripts/applications/noisy_text_correction.py`

- [ ] Implement manifest validation, protected-span extraction, identity and edit-distance correction, CER/protected-integrity scoring, and baseline artifact output.
- [ ] Keep ByT5-small and 360M LoRA explicitly unavailable; reject non-baseline phases with a visible error.
- [ ] Run the focused test file and exact CLI check until green.

### Task 3: Documentation and receipt

**Files:**
- Create: `docs/applications/noisy-text-correction.md`
- Create: `docs/task-receipts/A08-implementation.md`
- Create: `runs/applications/noisy-text-correction/baseline-20260909/` artifacts via the CLI

- [ ] Record the ByT5 precedent, corpus provenance, baseline counts, protected-field results, uncertainty, cost, and INCONCLUSIVE/NO-GO verdict.
- [ ] Hash the raw output and receipt, run scoped verification, commit only A08 files, push, and verify remote ancestry.
