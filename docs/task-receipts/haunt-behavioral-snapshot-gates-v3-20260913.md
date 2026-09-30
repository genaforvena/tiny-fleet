# Behavioral snapshot gates v3 (2026-09-13)

Task: `tinyfleet-drift-confirmatory-prerequisites-20260913/resolve-behavioral-snapshot-gates`

Mind: `haunt`

Frozen sample: `docs/tiny-fleet-artifacts-20260907/architecture-drift/02-external-sample-v2/sample-manifest.json`
SHA256: `07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59`

Artifact bundle: `runs/behavioral-preflight-v3-python311/`.
Machine-readable results and image/source pins: `runs/behavioral-preflight-v3-python311/results.json`.
Replay instructions: `runs/behavioral-preflight-v3-python311/README.md`.

## Outcome

All six frozen source snapshots now complete their test suites successfully under one pinned
Python 3.11.13 container image. Each used its own virtual environment and isolated temporary and
home directories; runs were sequential. The command was `python -m pytest -q tests`.

| Project | Snapshot | Result |
|---|---|---|
| Flask | 2.2.2 | 481 passed, 2 skipped |
| Flask | 3.1.0 | 490 passed, 2 skipped |
| Requests | 2.28.1 | 579 passed, 13 skipped, 1 xfailed |
| Requests | 2.32.3 | 590 passed, 15 skipped, 1 xfailed, 18 warnings |
| Pydantic | 1.10.4 | 2,441 passed, 93 skipped |
| Pydantic | 2.10.4 | 5,050 passed, 1,039 skipped, 17 xfailed |

All six pytest exit codes were 0. Skips, expected failures, and Requests-new warnings remain
visible and are retained in the full logs. This establishes that all six snapshot test arms can
run; it is not a comparison, score, behavioral label, or evidence about a model. Downstream
comparison remains gated on the separate preregistered label and generative prerequisites.

## Runtime and harness adjustments

The pinned image was `python:3.11.13-slim-bookworm`, digest
`sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1`. Every source archive
was checked against the frozen manifest SHA256 before execution and is retained in the bundle.
The source snapshots, test assertions, warning policy, and pytest output were not edited or
suppressed.

Three dependency compatibility overrides were used and are fully represented in the effective
requirements and freeze files:

- Flask-old used Werkzeug 2.2.2, Jinja2 3.1.2, and MarkupSafe 2.1.5 because the captured
  Werkzeug 2.0.0 pin was below that snapshot's declared minimum.
- Requests-new used greenlet 2.0.2 because captured greenlet 3.5.5 is incompatible with frozen
  httpbin 0.10.4 on Python versions below 3.12.
- Pydantic-old used mypy_extensions 0.4.3 because 1.1.0 emits a deprecation warning that this
  snapshot promotes to an error.

The Requests-new frozen client fixture certificate expired on 2026-03-13. In the external
extracted copy only, its public client certificate was regenerated from the snapshot's existing
client key/CSR and test CA. The replacement is at
`runs/behavioral-preflight-v3-python311/overlays/requests-new-client.pem`, SHA256
`1323192105e8111761fb80f9fda74d5c63a458595a582cea830130098eb10c2b`; it verifies for `sslclient`
against the snapshot test CA and is valid 2026-09-13 through 2028-09-12. No private key is included
in the artifact. This is a public test-fixture overlay, not a changed source assertion or disabled
TLS check.

## Evidence integrity

`results.json` records the six exact source archive SHA256s, container digest, test command,
effective environment freeze SHA256s, and full pytest log SHA256s. The logs are retained under
`runs/behavioral-preflight-v3-python311/pytest/`; full environment freezes are under
`environments/`; original captured pins and generated effective requirements are also included.
The receipt does not modify the frozen registration or prior preflight receipt.
