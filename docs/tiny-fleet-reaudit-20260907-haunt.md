# Tiny Fleet re-audit — haunt step artifact

Date: 2026-09-07 21:12 UTC
Chain: `tinyfleet-reaudit-20260907/reaudit-tinyfleet-full-scope`
Owner: `haunt`

## Fresh work

The persona/code evaluator contract was repaired and rerun from the pinned
manifest in `runs/persona-code/manifest.json`:

- `self-test --manifest` now validates the pinned base revision, corpus paths,
  row counts, and SHA-256 values.
- `eval-all.json` is now schema `persona-code.eval/v2` and records the manifest
  SHA-256, per-case held-out outputs/scores/rubric fields, and per-case
  adversarial outputs/actions.
- The run produced 24 held-out predictions (3 models × 2 domains × 4 cases)
  and 84 adversarial predictions (3 models × 2 domains × 14 cases).

## Result

The evaluation is not an acceptance claim. All 84 adversarial cases were
expected to abstain and the generated-output heuristic classified **0/84** as
abstentions. This is a failed safety control and leaves persona/code routing
blocked. The held-out output artifact is evidence of measurement only; it does
not establish specialist quality or generalisation.

## Verification

Passed:

```text
.venv/bin/python scripts/test_persona_code.py       persona-code tests: 2/2
.venv/bin/python scripts/persona_code.py self-test --manifest runs/persona-code/manifest.json
.venv/bin/python -m py_compile scripts/persona_code.py scripts/test_persona_code.py
```

The independent repository checks remain the prior audit evidence; this step
does not reclassify them or alter routing. The next witness step must inspect
this artifact, the JSON run output, and the failed 0/84 abstention control.
