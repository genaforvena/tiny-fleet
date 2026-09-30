# D04-V independent ground-truth verification (2026-09-13)

Status: **PASS, scoped to the three objective interface labels.** This receipt verifies the frozen D04 objective-only subset; it does not authorize semantic generalization or a model-score comparison.

## Frozen inputs and independent checkout

- Reviewed detached checkout at Tiny Fleet commit `518dc571248fec4948662e2917c5996ceaee9a1c` (`Register score-blind objective drift labels v2`), isolated from unrelated edits in the shared Tiny Fleet checkout.
- Registration: `runs/drift-validation-v2/registration.json`, SHA256 `fef38fc39cdef05fdf2a1f916920b0bb70256ab70eaff6ada41df90ee0bc85fb`.
- Labels: `runs/drift-validation-v2/labels.jsonl`, SHA256 `51c2c0cb4c1976c4e5a4e013bb28d0d2e5b1e9cef8bf8be5e7693c40189a7b72`.
- Unit map: `runs/drift-validation-v2/unit-map.json`, SHA256 `4e06420d52012230ca9dc755de246256e83e28a1ff9bd83711390c10bd694380`.
- Frozen sample manifest hash independently recomputed as `07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59`, matching the registration.

## Evidence and scope checks

- Independently fetched every registered old/new source file, release-note file, and optional native-test source from the stated upstream repository and immutable commit. All 11 recorded SHA256 values matched. The release-note entries were also located in the upstream files: Flask 3.1.0 `CHANGES.rst`, Requests 2.32.2 `HISTORY.md`, and Pydantic 2.10.3 `HISTORY.md`.
- The changed symbols are supported by the immutable source pairs: Flask changes `Request.max_content_length` from a read-only config view to a per-request configurable property; Requests adds `HTTPAdapter.get_connection_with_tls_context` and deprecates the old subclass hook; Pydantic adds `FieldInfo.default_factory_takes_validated_data`. Flask and Pydantic named test references exist in the independently hashed test files. Requests makes no test-specific claim, consistent with its absent test fields.
- Label coverage is exactly 3 units across the 3 registered repositories, one selected interface unit each, with all 3 labeled `interface_change`. The unit map explicitly says this is not exhaustive module labeling. These source-backed labels are not fixture-only; they support only the named interface changes.
- No row contains a model score, drift score, prediction, or score field. Registration sets `score_reveal: false` and `model_scores_allowed: false`; semantic generalization is false. This verifies the stored artifact is score-free, not any person's unrecorded access history.
- Reviewer/adjudication state is correctly withheld: zero reviewed units, no reviewer identities or labels, and no adjudication claims. The validator independently reproduces `reviewed_units: 0` and `semantic_generalization: false`; this is not a two-reviewer semantic ground truth.
- There are no cosmetic or no-change control rows in this subset. The validator's guard rejects a cosmetic/no-change unit labeled as an architectural change, and `test_cosmetic_and_no_change_cannot_be_architecture_change` passes. Therefore the guard is verified as a code invariant, but cosmetic discrimination is not measured by this dataset.
- In the isolated checkout, `python3 scripts/test_drift_validate.py` passed all 7 tests. `python3 scripts/drift_validate.py --run-dir runs/drift-validation-v2` independently reproduced the hashes, 3/3 repository coverage, 3 interface labels, 0 reviewed units, and preliminary status.

## Disposition

Accept only the three source-backed objective interface labels for the stated D04 subset. Keep semantic labels and semantic generalization withheld until two independent reviewers exist. Keep cosmetic/no-change discrimination, blocked behavioral arms, and the generative arm outside this PASS; no cross-repository association or comparison run is authorized by this receipt.
