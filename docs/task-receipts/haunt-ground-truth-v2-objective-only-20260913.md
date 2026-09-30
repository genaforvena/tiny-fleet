# D04 score-blind ground-truth registration v2 (2026-09-13)

Task: `tinyfleet-drift-prerequisites-20260913/register-v2-scoreblind-ground-truth`

## Result

Registered an objective-only public-interface label subset for the three frozen repositories. The labels identify one documented public interface change per repository: Flask `Request.max_content_length`, Requests `HTTPAdapter.get_connection_with_tls_context`, and Pydantic `FieldInfo.default_factory_takes_validated_data`. Each row binds exact snapshot commits and SHA256 hashes of the old/new source files and release-note source. Flask and Pydantic rows also bind the relevant native test source and test name; the Requests row makes no test-specific assertion because the frozen test tree has no named test for the API migration.

No second reviewers were invented. The registration retains the two-reviewer requirement for semantic comparisons and sets `semantic_generalization: false`. It has no `behavior_change` or `dependency_change` labels, reports no model scores, and makes no cross-repository metric association. The unavailable main semantic labels remain withheld pending two independent blinded reviewers.

## Evidence and verification

- Registration: `runs/drift-validation-v2/registration.json`, SHA256 `fef38fc39cdef05fdf2a1f916920b0bb70256ab70eaff6ada41df90ee0bc85fb`.
- Score-blind labels: `runs/drift-validation-v2/labels.jsonl`, SHA256 `51c2c0cb4c1976c4e5a4e013bb28d0d2e5b1e9cef8bf8be5e7693c40189a7b72`.
- Versioned unit map: `runs/drift-validation-v2/unit-map.json`, SHA256 `4e06420d52012230ca9dc755de246256e83e28a1ff9bd83711390c10bd694380`; the validator checks that every label unit, source path, and public symbol matches this map.
- Validation: `runs/drift-validation-v2/validation.json` (SHA256 `5d949126e8f590576e24585518d7dc33a04f91d995c7f49cf667bc0047cf0c48`) reports preliminary status, three units across three repositories, all three `interface_change`, zero reviewed units, and no semantic generalization. Validation command: `.venv/bin/python scripts/drift_validate.py --run-dir runs/drift-validation-v2` (exit 0); captured stdout SHA256 `2c33a861367012d7fe10d47a14338369d5b8d65841e2536ab23148030fd6b8aa`.
- D04 tests: `.venv/bin/python scripts/test_drift_validate.py` (7 passed, exit 0); captured output SHA256 `504fd3299a5deac557266695f21195fd5b1a8554b3dd7e897e38b99c4e7b8429`. The suite also mutates the unit-map file and confirms validation refuses its hash mismatch. Test-first check failed on the new objective-only cases before validator changes, then passed after implementation.
- The six source archive hashes and the full six-snapshot native test outcomes remain in `docs/task-receipts/haunt-behavioral-preflight-v2-20260913.md` and `runs/behavioral-preflight-v2/`.

Independent D04-V review is still required. The generative gate remains blocked by the missing arm-specific model/adapter and verified scorer path. This artifact does not satisfy all preconditions for the original analysis step.
