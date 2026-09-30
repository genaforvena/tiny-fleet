# Confirmatory-v1 behavioral preflight

Compatibility preflight for the six frozen HTTPX, attrs, and pytest snapshots. This bundle does
not compare versions or repositories and produces no model score, label, or inference. The source
archives are read-only mounts; their observed hashes are recorded against the frozen registration
in `results.json`.

Runtime: `python@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1`,
`linux/amd64`, Python 3.11.13. Each snapshot has an isolated virtual environment. Installs follow
the snapshot's own test requirements (`requirements.txt`, `.[tests]`, `.[testing]`, or `.[dev]`)
and the resulting complete `pip freeze --all` is retained under `environments/`. The upstream
requirements leave some transitive dependencies unconstrained; the captured freeze is the exact
resolved environment for each run.

Committed install and pytest logs use deterministic gzip (`*.log.gz`) so the raw test output's
intentional trailing whitespace remains byte-for-byte preserved without being normalized by Git.
Decompress a log with `gzip -dc path.log.gz`; `results.json` hashes the uncompressed bytes.

Replay the initial six attempts with `bash run_matrix.sh`. The runner verifies the frozen source
archives indirectly through the registered archive hashes recorded in `results.json`, extracts
each into an isolated work directory, installs its test dependencies, then runs
`python -m pytest -q`. Full install and test logs are under `install/` and `pytest/`. Do not use
the generated `work/` or `venvs/` directories as source evidence; they are disposable run state.

The initial pytest-old/new installs could not infer the release version because GitHub source
archives do not contain `.git`. `retry_setup.sh` records the source's own tox version environment
variable (`SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PYTEST`) and puts each venv's `bin` directory on
`PATH`, as tox does. `attrs-new` is also rerun with the venv `PATH` so its mypy tests can locate
the installed console script. Retry logs, freezes, and outcomes are under `retries/`; the initial
attempts remain preserved separately.

## Outcomes

| Repository | Old | New |
|---|---|---|
| HTTPX | **BLOCKED-TEST** — 703 passed; one Click deprecation warning is an error. | **BLOCKED-TEST** — 1,415 passed, one skipped; two warning-related failures. |
| attrs | **PASS** — 1,235 passed, five skipped, one xfailed. | **BLOCKED-TEST** — 1,387 passed, seven skipped, one xfailed; 33 mypy-backed failures remain with venv `PATH` corrected. |
| pytest | **BLOCKED-TEST** — corrected setup ran 3,228 tests: 32 failed, 109 skipped, 11 xfailed. | **BLOCKED-TEST** — corrected setup ran 3,617 tests: 10 failed, 114 skipped, 11 xfailed, one xpassed. |

The HTTPX outputs include the complete warnings and tracebacks. The pytest corrected runs use the
frozen snapshot versions `7.2.0` and `8.3.4` from the registration's tags, supplied only to
setuptools-scm for building the extracted source. No test, warning policy, or frozen archive was
edited. Every archive's observed SHA-256 matches the registration. No repository pair has two
passing snapshots in this environment, so this receipt does not authorize a behavioral comparison.
