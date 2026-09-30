# HTTPX Trio timeout blocker resolution — 2026-09-14

Task: `unblock/haunt/c2b458c5951d307d/resolve`

## Diagnosis

The resolver was live and open. The parent `tinyfleet-confirmatory-v1-gate-closure-20260913`
remained blocked only because HTTPX-new's `tests/test_timeouts.py::test_write_timeout[trio]`
emitted `ResourceWarning: Async generator 'httpx._content.ByteStream.__aiter__' was garbage
collected before it had been exhausted`; pytest promoted Trio's finalizer warning to an
unraisable-exception failure under the frozen project's `filterwarnings = ["error", ...]` policy.
The source and test were unchanged.

Trio 0.27.0 (the prior Python 3.11 retry), Trio 0.28.0 (the prior Python 3.12 retry), and Trio
0.32.0 with AnyIO 4.15.1 all reproduced the warning. Trio 0.26.2 cleared it, but was below
AnyIO 4.15.1's declared Trio-extra minimum, so that result was not accepted. The supported
combination AnyIO 4.9.0 + Trio 0.26.1 passed. AnyIO 4.9.0's installed metadata declares
`Requires-Dist: trio>=0.26.1; extra == "trio"`.

The AnyIO 4.15.1 + Trio 0.32.0 diagnostic is retained at
`runs/behavioral-preflight-confirmatory-v1-py312/httpx-new-trio032/` (targeted failure log,
runtime, requirements, and full environment freeze).

## Accepted retry

The accepted run uses the frozen HTTPX-new source and tests copied byte-for-byte to a writable
trial directory, CPython 3.12.3 (supported by this snapshot), AnyIO 4.9.0, Trio 0.26.1, Click
8.2.1, pytest 8.3.4, and the retained dependency set in `freeze.txt`. Only AnyIO and Trio differ
from the previous HTTPX-new retry's frozen dependency list. The source's warning configuration
was not changed; pytest's cache was directed outside the source tree. The copy was compared to
the frozen extraction before running; after the run, the only differences were generated
`__pycache__` bytecode files.

- Targeted `test_write_timeout[trio]`: **1 passed** — `runs/behavioral-preflight-confirmatory-v1-py312/httpx-new-anyio49-trio0261/targeted-pytest.log`
- Full HTTPX-new suite: **1,417 passed, 1 skipped** — `runs/behavioral-preflight-confirmatory-v1-py312/httpx-new-anyio49-trio0261/full-pytest.log`
- Environment: `runs/behavioral-preflight-confirmatory-v1-py312/httpx-new-anyio49-trio0261/freeze.txt`, `python-version.txt`, and `requirements.freeze.txt`
- Frozen `tests/test_timeouts.py` SHA-256: `5d31587a56a902b22a26b36f27f3410cac6b855c92376dc465eb86f9dc8b5eae`
- Frozen `pyproject.toml` (including warning policy) SHA-256: `df6ead82c82909bacc1f54fa0de8edc52dab17742d548d41c284506e3c05706f`
- Targeted log SHA-256: `4237eb8d30ab4e25d028ca343d50bfba364b7f76a907b73390b9601a16e46fe1`
- Full-suite log SHA-256: `6a77147fb35f9fe2345b13a03584fd0e8d60dfa8a6166170879098ace7f34423`
- Complete freeze SHA-256: `4e3fdafd78d5e1d76c754c26e811336d9b544bb52a779e36c7b240abb86d7a7e`

This resolves the stated HTTPX-new warning prerequisite. The parent clean-paired-preflight step
has been resumed so its owner can record the six-snapshot gate outcome. This receipt does not
claim independent gate verification or authorize a comparison/matrix run; those gates remain
closed until their own evidence passes.
