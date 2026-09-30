# Confirmatory-v1 generative matrix progress — 2026-09-14

Task: `tinyfleet-confirmatory-v1-comparison-20260914/execute-confirmatory-v1-generative-matrix`

At 2026-09-14T10:55:51Z the registered real-backend generation command remained active as PID
3942700 (`scripts/drift_generate.py`, v2 registration, CPU device). Process age was 30m27s,
CPU time 2h24m34s across worker threads, RSS 6.27 GiB, state `Rl`. The runner buffers records
and writes the matrix only after the complete 162-row set validates, so no partial output exists.

The frozen registration and paired behavioral closeout still match the task's exact SHA-256 values:

- `runs/drift-confirmatory-v1/generative-registration.json`:
  `157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`
- `runs/behavioral-preflight-confirmatory-v1-paired-closeout-20260914.json`:
  `fd36f832d08601ba21debc3735bc8f6489a33a0d4415ba91485850de1c1800f5`

The independent VPN receipt is PASS at
`docs/task-receipts/vpn-confirmatory-v1-independent-gate-verification-20260914.md`.
The current v2 generator validates the manifest but has no `comparison_authorized` hard-stop;
therefore the task's conditional stop was not triggered. The registered embedding model is present
locally at its pinned digest (`all-minilm:latest`,
`1b226e2802dbb772b5fc32a58f103ca1804ef7501331012de126ab22f67475ef`).

Next action: wait on PID 3942700 until exit; if successful, validate the 162-row raw tape and its
runtime/provenance fields, hash it, then run the deterministic embedding scorer in a separate
process. If generation exits unsuccessfully, retain the exact process error and leave the matrix
unscored; retry only from the task's stated prerequisite/event.

## Checkpoint 2026-09-14T11:12:04Z

PID 3942700 is still active after 46m39s wall time and 3h47m08s cumulative CPU, at 486% CPU and
7.58 GiB RSS (`Rl`). The two frozen gate hashes above were rechecked unchanged. The output directory
is still absent because the runner commits records only after the full matrix validates; no failure
or partial tape has been observed.

Next update: recheck PID 3942700 by 2026-09-14T11:30:00Z. On exit, validate and hash the complete
raw tape before starting the separate scorer; on failure, record the precise error and retry event.

## Checkpoint 2026-09-14T11:56:40Z

The generation process exited 0 with all 162 rows. The raw tape SHA-256 is
`b691c04b3a053c0fff8b6aefbc336fd0e61bd01de03453a76415c53e216bab5b`; full v2 provenance
validation returned `ACCEPT`, all 162 records were successful, and no frozen gate hash changed.
The pinned scorer failed before any embedding request with `adapter_pair_mismatch`; witness then
returned FAIL because the first scorer amendment omitted its imported generation validator from the
verified source bundle and the files were uncommitted.

A follow-up now binds the validator digest to both the amendment and frozen runner registration, and
adds a mutation regression. The amended scorer suite passes 5 tests; the original scorer suite passes
7 tests. The amendment remains pre-score and the raw tape has not been scored. Next: commit and push
only the scoped raw run, scorer, amendment, tests and receipts; witness must then publish fresh PASS
before any embedding request. Recheck by 2026-09-14T12:10:00Z.
