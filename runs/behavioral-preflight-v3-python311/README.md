# Behavioral snapshot preflight v3

This bundle replays the six source-pinned test suites in the frozen external sample. It is a
compatibility preflight only; it produces no comparison score, behavioral label, or finding.

The run used `python:3.11.13-slim-bookworm` at image digest
`sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1` and ran
`python -m pytest -q tests` sequentially in separate virtual environments. Full logs, effective
environment freezes, source archives, original environment captures, and the runner are retained
here. Source archives match the frozen manifest hashes listed in `results.json`.

To replay in the same pinned image, mount this bundle at `/study` and the captured source
archives at `/study/source-archives`. Extract each archive to `/study/work/<suite>`. For
`requests-new`, replace `tests/certs/mtls/client/client.pem` with
`/study/overlays/requests-new-client.pem`; this is a public test-fixture certificate signed by the
snapshot's own test CA, regenerated because the frozen fixture had expired. Mount
`environment-captures/` read-only at `/freeze`, then run:

```sh
python /study/run_matrix.py
```

The runner applies the recorded dependency compatibility overrides, writes complete test output
and resolved freezes, and exits nonzero if any suite fails. The pristine Requests-new source is
available in its source archive; the certificate is the only source-tree overlay. No source file,
test assertion, warning policy, or test output was edited or suppressed.
