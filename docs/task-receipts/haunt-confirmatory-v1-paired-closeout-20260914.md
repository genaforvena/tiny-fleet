# Confirmatory-v1 paired gate closeout — 2026-09-14

Task: `tinyfleet-drift-confirmatory-prerequisites-20260913/final-gate-audit-and-fresh-task`

## Result

The six-snapshot behavioral gate now has a passing outcome for both snapshots of all three
repositories. The machine-readable closeout is
`runs/behavioral-preflight-confirmatory-v1-paired-closeout-20260914.json` (SHA-256
`fd36f832d08601ba21debc3735bc8f6489a33a0d4415ba91485850de1c1800f5`). It preserves the original
Python 3.11 bundle and records the accepted supported retry, complete test-log digest, full
environment-freeze digest, and source archive digest for each outcome.

| Repository | Old | New |
|---|---|---|
| attrs | PASS — 1,235 passed, 5 skipped, 1 xfailed | PASS — 1,420 passed, 7 skipped, 1 xfailed |
| HTTPX | PASS — 704 passed with Click 8.2.1 | PASS — 1,417 passed, 1 skipped with AnyIO 4.9.0 + Trio 0.26.1 |
| pytest | PASS — 3,260 passed, 109 skipped, 11 xfailed | PASS — 3,627 passed, 114 skipped, 11 xfailed, 1 xpassed |

All accepted test logs report no failures. The original preflight bundle remains unchanged as the
diagnostic record of the earlier dependency failures; the paired closeout supersedes only its
behavioral verdicts using retained supported-environment retries. No source, test, or warning-policy
file was modified.

## Generation registration repair

`runs/drift-confirmatory-v1/adapter-registration.json` is bound by SHA-256
`aca4c62e360b92d27223707f86a340d471113bcfb9042658426e121be47cfc6a` and points to six trained
confirmatory adapters. I independently recomputed every adapter-tree digest and bound each path and
digest in both the generation registration's adapter table and its six prompt rows. The six corpus
manifest, train, and validation bindings were also refreshed from their sample-bound manifests.

The live runner additionally rejected the registration because `scorer.digest` was absent. The
registered scorer source hash equals the SHA-256 of `scripts/drift_score.py`, so that exact hash is
now bound as `scorer.digest`; the embedding-model digest remains its separate registered value.
The resulting `generative-registration.json` SHA-256 is
`157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`.

Verification performed:

- `validate_v2_manifest()` accepted all six prompt rows; each adapter-tree digest recomputed to its
  registration, and all six corpus manifests exist.
- `python3 scripts/test_drift_generate.py`: 6 tests passed.
- All six source archive digests equal their frozen sample-registration values.
- No model inference, generation, scoring, comparison, or matrix was run. The registration remains
  `blocked-before-generation` and `comparison_authorized` remains false.

## Remaining gate

The independent step owner must publish a current gate-level PASS over the exact behavioral-closeout
and generation-registration hashes above. The earlier PASS was scoped to the prior blocked evidence
and does not satisfy this check. The original final-gate audit remains unresumed until that current
PASS exists.
