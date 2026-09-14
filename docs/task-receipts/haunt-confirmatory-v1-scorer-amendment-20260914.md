# Confirmatory-v1 scorer amendment — implementation receipt

**Superseded.** Witness found the imported validator was not bound into the scorer's code identity.
The current amendment digest and validator binding are recorded in
`haunt-confirmatory-v1-scorer-validator-binding-20260914.md`; use that receipt for the current
scorer version.

Task: `tinyfleet-confirmatory-v1-scorer-compat-20260914/implement-and-freeze-scorer-amendment`

## Frozen inputs

- Generation registration SHA-256: `157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`.
- Raw 162-row real-backend tape SHA-256: `b691c04b3a053c0fff8b6aefbc336fd0e61bd01de03453a76415c53e216bab5b`.
- Original scorer remains unchanged at SHA-256
  `54142ae236a6a55ff4452e360e2c6867e219b356d56f0ff4c589cd6fb8b8e127`.
- New scorer bundle SHA-256:
  `f40e345bcf22e88c3e557e111a704bd3953298532b8793b6e68f57b2372d9612`.
- Scoring amendment SHA-256:
  `61562c634e2667925f6c3f1d29ddc1aef4198d7d7b716a03b1dd1c6afd180ed4`.

The correction was frozen after generation but before scoring, in response to the original scorer's
`adapter_pair_mismatch`. The new scorer validates the complete raw matrix against the unchanged
generation registration, including each snapshot-specific LoRA adapter digest; it only removes the
invalid old/new equality requirement. It preserves null adapters for base and prompt-only controls.
No generated output text or embedding values were inspected before freezing this amendment.

## Verification

- Test-first regression: before implementation,
  `PYTHONPATH=scripts .venv/bin/python scripts/test_drift_score_confirmatory_v1.py` failed because
  `drift_score_confirmatory_v1` did not exist. After implementation, all 4 amendment tests passed.
- Existing scorer regression suite: 7 tests passed.
- `py_compile` passed for the new scorer and test module.
- Recomputed hashes for the raw tape, original registration, original scorer, new scorer and
  amendment; all amendment bindings matched.
- Ollama 0.33.2 and `all-minilm:latest` at the registered digest were checked before scoring.
- No embedding request or score pass has run. Independent review is required before scoring.

Next: witness independently audits this scorer amendment and registration. If PASS, score the
unchanged 162-row tape in a separate pass and retain the full 81-pair output. Disclose the
post-generation, pre-score amendment and its review in the reader-facing report.
