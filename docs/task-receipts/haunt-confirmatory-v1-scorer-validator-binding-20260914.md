# Confirmatory-v1 scorer validator binding — 2026-09-14

Task: `tinyfleet-confirmatory-v1-scorer-binding-fix-20260914/bind-validator-and-land-scorer-amendment`

## Witness finding addressed

Witness's first review correctly found that the amended scorer imported
`scripts/drift_generate.py::validate_v2_records` without including that dependency in its verified
code identity. The scorer bundle now hashes all three executable sources: the raw-record validator,
the pinned embedding/provenance helper, and the amended scorer. Before any embedding request,
`verify_amendment()` also requires the live validator digest to equal both the amendment's digest and
the frozen generation registration's `runner.source_sha256`.

A mutation regression changes the registration's validator digest and asserts rejection with
`validator_registration_mismatch`. The test passed after failing before this binding existed.

## Frozen evidence

- Generation registration SHA-256:
  `157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`.
- Raw tape SHA-256:
  `b691c04b3a053c0fff8b6aefbc336fd0e61bd01de03453a76415c53e216bab5b`.
- Generation validator SHA-256:
  `adc416a6e5d47b464c82b13d07b1cfffd0cd5e03c6a45a9f7772e51cfe4632c7`.
- Original scorer dependency SHA-256:
  `54142ae236a6a55ff4452e360e2c6867e219b356d56f0ff4c589cd6fb8b8e127`.
- Amended scorer SHA-256:
  `f5f01e9620c6073f3128b8c15a26a5e87bbebfcd1e08de6de510094f7b9c9114`.
- Three-source scorer bundle SHA-256:
  `f824ce755e1e7168ba302f961a4519e6878f677b2efd5618357f6abf768dba14`.
- Scoring amendment SHA-256:
  `f92f9acf77c18d629bb2f5b9ebbbfc34c609dd38a6e6bb9b61fdb8796b8e8eb7`.

## Verification

- The amended scorer test suite passed: 5 tests, including all registered old/new snapshot-specific
  adapter pairs and rejection of a changed validator binding.
- The original scorer regression suite passed: 7 tests.
- `py_compile` passed for the amended scorer and its tests.
- The frozen generation registration, original scorer, validator, and raw tape remain unchanged.
- No output text or embedding values were inspected; no score pass or embedding request was run.

The scorer amendment must be independently re-reviewed against these updated digests before scoring.
After PASS, run only the unchanged raw tape through the amended scorer in a separate deterministic
pass. The amendment remains post-generation/pre-score and must be disclosed with the review verdict.
