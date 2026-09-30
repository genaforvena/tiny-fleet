# Confirmatory-v1 behavioral gate closure — one exact snapshot remains blocked

Task: `tinyfleet-confirmatory-v1-gate-closure-20260913/clean-paired-behavioral-preflight`

Verdict: **BLOCKED-TEST. Five snapshots now pass in recorded environments; HTTPX new still has
one reproducible unclosed async-generator warning under the frozen source and warning policy. No
comparison, model inference, labels, score, or matrix was run.**

## Binding

The exact sample registration remains `runs/drift-confirmatory-v1/registration.json`, SHA-256
`f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`. Its original behavioral
bundle is `runs/behavioral-preflight-confirmatory-v1-python311/results.json`, SHA-256
`39e7c1c3b42f0f08a77686b5bc3693720295a9d8bb777696c3daa98217ff57a6`. The six source archives
remain those registered by that file. The retries below alter environment packages or runtime
only; no archive, extracted source file, test, warning filter, or label was edited.

## Paired outcomes

| Repository snapshot | Recorded environment change | Outcome |
|---|---|---|
| HTTPX old | Python 3.11.13 image `python@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1`; Click 8.2.1, which satisfies the source's `click==8.*` constraint | **PASS** — 704 passed |
| HTTPX new | Same Python 3.11.13 image and Click 8.2.1 | **BLOCKED-TEST** — 1,416 passed, one skipped, one failed: `tests/test_timeouts.py::test_write_timeout[trio]` |
| attrs old | Original Python 3.11.13 registered environment | **PASS** — 1,235 passed, five skipped, one xfailed |
| attrs new | Python 3.11.13; mypy 1.13.0, within the snapshot's `mypy>=1.11.1` range | **PASS** — 1,420 passed, seven skipped, one xfailed |
| pytest old | Python 3.11.13; attrs 22.2.0, Pygments 2.13.0, pluggy 1.0.0, each within the snapshot's declared test ranges | **PASS** — 3,260 passed, 109 skipped, 11 xfailed |
| pytest new | Python 3.11.13; attrs 24.3.0, Pygments 2.18.0, pluggy 1.5.0, each within the snapshot's declared test ranges | **PASS** — 3,627 passed, 114 skipped, 11 xfailed, one xpassed |

The targeted 15 pytest-new cases that failed against current 2026 dependencies pass with those
release-compatible package versions, and the full suite then passes. The corresponding pytest-old
full-suite failures also disappeared with versions contemporary with that snapshot. These are
dependency-environment corrections; the source and test archives stayed unchanged.

## Remaining HTTPX-new failure

The project promotes warnings to errors. On the timeout test's Trio path, the retained stack trace
reports `httpx._content.ByteStream.__aiter__` being garbage-collected before exhaustion; Trio emits
a `ResourceWarning`, and pytest surfaces it as `PytestUnraisableExceptionWarning`. Click 8.2.1
removes the separate Click deprecation failure but not this warning. The same timeout case reproduced
under Python 3.12.3 and after an isolated Trio 0.28.0 change; no source, test, or warning-policy
workaround was applied. The Python 3.12 full-suite exploration also encountered a file-permission
failure because that extracted source tree was root-owned, so it is diagnostic only and is not counted
as a passing run.

This exact archived sample therefore cannot yet satisfy the clean behavioral gate. A passing gate
requires all six suites to pass with retained runtime/dependency provenance and full logs. Keep the
sample frozen and this step blocked until a supported environment passes the HTTPX-new test without
editing the snapshot, its tests, or warning policy, or until a separately frozen and independently
verified sample supersedes it. Do not infer that the one failure is a null behavioral result.

## Retained evidence

All files below are under `runs/` and their hashes are included so the result can be replayed without
trusting this summary:

- `runs/behavioral-preflight-confirmatory-v1-python311/retry-pinned-click/httpx-old/pytest.log` —
  SHA-256 `41133e82f9970e6968ddc6c30768e0797102584da96bda9d048a6bdb9c70bbd7`; environment freeze
  `.../httpx-old/freeze.txt` — SHA-256
  `911c6480090a8fc2ea092d5209538759865e5a836b065865153b062781bfb2be`.
- `runs/behavioral-preflight-confirmatory-v1-python311/retry-pinned-click/httpx-new-copy/pytest.log` —
  SHA-256 `f06a332f74e7adae9bdfa218bc10b0a3001cd9a86993b17645b3b20dd901a5e8`; environment freeze
  `.../httpx-new-copy/freeze.txt` — SHA-256
  `64e5ff683db28c221b94f779b40230c096922c5d7c4f212af2eb37b4f6d6bed8`.
- `runs/behavioral-preflight-confirmatory-v1-python311/retry-pinned-click/attrs-new-mypy113/full-pytest.log`
  — SHA-256 `b379f4420df90229e999bd50de352c6d3f9d1d5f7508e2218e03424c8bb2bed5`; environment freeze
  — SHA-256 `1bc79a150b7573d52cef54693aad36ec638d2e357982a42353345d1564951682`.
- `runs/behavioral-preflight-confirmatory-v1-python311/retry-pinned-click/pytest-old-supported/pytest.log`
  — SHA-256 `3305d19a4797372ee83511bb54cd984c1dc5079b15ca11647157620f94e90e5d`; environment freeze
  — SHA-256 `66fd2c197e685637a27a688c08369d41a78069c78373f80d4d9b2ac9e3c6063c`.
- `runs/behavioral-preflight-confirmatory-v1-python311/retry-pinned-click/pytest-new-supported/pytest.log`
  — SHA-256 `071a1b9be2dfc371de1ce47981a002dec164212ef513ce8f18d5587c52df3860`; environment freeze
  — SHA-256 `e72978d1158cb12826bae11a71b6650cfb31733a9271b88c6532002d4b26d274`.
- The Python 3.12 full exploratory log and freeze are
  `runs/behavioral-preflight-confirmatory-v1-py312/httpx-new/full-pytest.log` (SHA-256
  `08cc32d5099dcafdb5365f59d6535d2e48ee25f8022cca0e96b4323d2cd0771a`) and
  `.../full-freeze.txt` (SHA-256
  `1038e80150053496bdf3a1640f20af46465ebc20042fcf4183cb62815592dfe2`). The Trio 0.28.0 targeted
  reproduction is `runs/behavioral-preflight-confirmatory-v1-py312/httpx-new-trio028/pytest.log`
  (SHA-256 `6b2204cd10f328f7d9ccb4ae50755da63ab69f1892969e31951aae719dfacf4f`) with freeze SHA-256
  `6caa3d1e10e7704f5031f0d21676540da290db65ae1195abbd7e8ac811718990`.

The next independent task may prepare sample-bound corpora and adapters, but the independent verifier
must leave the behavioral gate blocked and the matrix closed while this exact HTTPX-new failure
remains.
