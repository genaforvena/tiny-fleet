# Confirmatory-v1 behavioral preflight — 2026-09-13

Task: `tinyfleet-confirmatory-v1-arm-gates-20260913/preflight-six-confirmatory-snapshots`

Verdict: **PREFLIGHT COMPLETE; behavioral gate remains blocked for comparison.** All six
registered source snapshots were checked and their test outcomes captured. Only attrs-old passed;
the other five suite outcomes are blocked in this pinned environment. No source version
comparison, label use, model inference, score, or matrix run occurred.

## Binding and runtime

The test bundle is `runs/behavioral-preflight-confirmatory-v1-python311/`. Its `results.json`
binds to `runs/drift-confirmatory-v1/registration.json` SHA-256
`f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`. All six observed source
archive hashes equal the exact per-snapshot hashes in that registration.

Every suite ran in its own virtual environment under the pinned image
`python@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1`
(`linux/amd64`, CPython 3.11.13). Snapshot-declared test requirements were installed without
editing source, tests, or warning policy. Each complete resolved `pip freeze --all`, runtime
version, install log, pytest log, source hash, and log/freeze digest is retained in the bundle.
Some upstream transitive requirements are unbounded; the frozen environment files are the exact
versions used by these runs.

## Outcomes

| Repository | Old snapshot | New snapshot |
|---|---|---|
| HTTPX | **BLOCKED-TEST** — 703 passed, one failed because a Click deprecation warning is promoted to an error. | **BLOCKED-TEST** — 1,415 passed, one skipped, two warning-related failures (Click deprecation and an unraisable async-generator `ResourceWarning`). |
| attrs | **PASS** — 1,235 passed, five skipped, one xfailed. | **BLOCKED-TEST** — after correcting venv `PATH`, 1,387 passed, seven skipped, one xfailed, 33 mypy-backed failures. |
| pytest | **BLOCKED-TEST** — after supplying its registered source version and venv `PATH`, 3,228 passed, 32 failed, 109 skipped, 11 xfailed, one warning. | **BLOCKED-TEST** — after the same setup correction, 3,617 passed, 10 failed, 114 skipped, 11 xfailed, one xpassed. |

The first pytest attempts failed before collection because GitHub source archives omit `.git` and
setuptools-scm could not infer the version. The retry used the corresponding frozen release
versions, `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTEST=7.2.0` and `8.3.4`, as named by the
snapshots' tox configuration. The first attrs-new run omitted the venv's `bin` on `PATH`; its
retry corrected that standard tox environment detail, after which the remaining mypy failures
were visible. Initial and corrected logs remain separate; the machine-readable final outcome and
all hashes are in `results.json`.

## Gate consequence

The receipt is complete as a compatibility preflight, not a clean behavioral gate. No project pair
has both suites passing under this shared pinned runtime, so the confirmatory matrix remains
unauthorized. Retry only after the recorded dependency/tool compatibility blockers are resolved
without changing frozen source, tests, warning policy, or labels. Independent gate verification
may audit these exact receipts and report the gate honestly; it must not infer or compare versions.
