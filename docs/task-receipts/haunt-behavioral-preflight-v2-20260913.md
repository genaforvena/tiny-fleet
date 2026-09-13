# Behavioral snapshot preflight v2 (2026-09-13)

Task: `tinyfleet-drift-prerequisites-20260913/preflight-v2-behavioral-snapshots`

Mind: `haunt`

Source: frozen sample `docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json` (SHA256 `07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59`)

Host interpreter: CPython 3.12.3; each snapshot ran in its own venv. Complete `pip freeze` captures and pytest logs are under `runs/behavioral-preflight-v2/`.

The frozen source archive hashes were independently checked against the manifest before testing:

| Project | Snapshot | Commit | Source archive SHA256 |
|---|---|---|---|
| Flask | old | `a1c478bc93d3dc018a6e7a1ba3cf5409553c9df3` | `9cab061d3c8b1fcc156b1ebb247d0a6caa73864fb096e1ebcdb369d2b3fbaefc` |
| Flask | new | `ab8149664182b662453a563161aa89013c806dc9` | `1ab1e67fb5c9e05d226e3cd94734e46009e012b269e29794f29151ef341feb06` |
| Requests | old | `4d394574f5555a8ddcc38f707e0c9f57f55d9a3b` | `5b95d48511eaaad22b4bfe0ba42d12dcce08c97fb587aa9cfd17dab0399868b9` |
| Requests | new | `0e322af87745eff34caffe4df68456ebc20d9068` | `02db3918a45a7707a9eba6e240a7d3cde2ad5be23fc293dbe218d263662453dd` |
| Pydantic | old | `63c683d9fc7b494bf81e964f97ec2f9b78b8e09d` | `d47f96f734030506f57bf3868314f2e3ccfcf34be323422a4ac645eb99c04585` |
| Pydantic | new | `5bd3a6507b749fcd4833173fba88b3690ff77170` | `d8c26a1987494e70b3ee903a19ed7a75d37ea907358ed124d1567b7fa63b2df4` |

## Outcomes

| Project | Old snapshot | New snapshot |
|---|---|---|
| Flask | **Blocked before collection** (pytest exit 4): Python 3.12 emits `DeprecationWarning: ast.Str is deprecated` while importing the snapshot's test configuration under its warnings-as-errors policy. | **Pass**: 490 passed, 2 skipped (exit 0). |
| Requests | **Blocked in two HTTPS tests** (577 passed, 13 skipped, 1 xfailed): `test_pyopenssl_redirect` and `test_auth_is_stripped_on_http_downgrade`; the `pytest-httpbin` fixture calls removed `ssl.wrap_socket`, so the test server fails and TLS assertions error. | **Blocked in one HTTPS test** (589 passed, 15 skipped, 1 xfailed): `test_different_connection_pool_for_mtls_settings` fails because its fixture certificate is expired (`SSLV3_ALERT_CERTIFICATE_EXPIRED`). |
| Pydantic | **Blocked before collection**: Python 3.12's `ast.Str` deprecation is raised as an error while the pinned Hypothesis version is imported from `tests/conftest.py`. | **Pass**: 5,135 passed, 954 skipped, 17 xfailed (exit 0). |

Requests was first run concurrently in the old/new environments; its test helper uses a shared `/tmp/test_utils.py` extraction path, so those first logs are not used as evidence. Both final runs were sequential and used distinct `TMPDIR` roots. The old snapshot still has the independent `ssl.wrap_socket` fixture failure; the new snapshot's zip-extraction test passes in isolation. The final logs in the artifact are those isolated runs.

## Interpretation and limits

This is a behavioral **preflight**, not a score or a comparison result. All six frozen commits were tested. Three full suites pass; three old/new arms remain blocked by Python 3.12 compatibility in the historical test dependencies/fixtures. No failing test was edited, no warning was suppressed, no output was used as a model label, and no behavioral difference is attributed to a snapshot unless both sides of that project's pair can run. Do not infer an empty-test result or turn these compatibility failures into performance scores. Keep only the affected arms blocked while sourcing an appropriate historical runtime or independently repairing/reproducing the test harness.

The prerequisite generation registration remains separately blocked (see `docs/task-receipts/haunt-generative-v2-preregistration-blocked-20260913.md`): it lacks the arm-specific adapters, source excerpt hashes, and deterministic scorer needed for a valid generative run. This preflight does not clear that gate.

## Commands and evidence

Commands were `pytest -q tests` from each exact source snapshot in its isolated venv. Dependency declarations came from each snapshot: Flask `requirements/tests.txt` plus its snapshot-specific minimal test requirements; Requests `requirements-dev.txt`; Pydantic's pinned old `tests/requirements-testing.txt` and new committed `uv.lock` dev group. Each environment freeze is retained with its SHA256 verifiable from the captured file. Source archive checks, package versions, complete test output, and test exit results are retained in `runs/behavioral-preflight-v2/`.

Full pytest log SHA256:

| Log | SHA256 |
|---|---|
| `pytest/flask-old.log` | `d3978c1d90bea52a683118880860372da212283f288df9142e57bf3fe85de4bc` |
| `pytest/flask-new.log` | `fc6dd5818752e522ee02c1d56d825f06f384d5a60d450dd1bee99dfa8fd0a08a` |
| `pytest/requests-old.log` | `38a118762db132dfb5a0f8ae1aa1967c3dd107c3b038fe22df2c89b0efd333b0` |
| `pytest/requests-new.log` | `ecc19b8f778fe182feb85bccf04103c89efe1734406bbf6a38edec8b06084066` |
| `pytest/pydantic-old.log` | `2e56adec695cdf3f6d3c2aa0c7cf1e5061ca0cf33195307aede901701f371d5f` |
| `pytest/pydantic-new.log` | `100258894a36f322230c79cc920c324e9d69c24431136ae1d02a85f5f46c92d2` |
