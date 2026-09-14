# Confirmatory-v1 independent gate verification — 2026-09-14

Task: `tinyfleet-confirmatory-v1-gate-closure-20260913/independently-verify-closed-gates`

## Verdict

**PASS** for both requested gates, against source commit `a31f1ba3922ed5484c685a8ed77d9fe0283f87d3`.

The exact pushed artifacts were present in that commit and matched the requested SHA-256 values:

- `runs/behavioral-preflight-confirmatory-v1-paired-closeout-20260914.json`: `fd36f832d08601ba21debc3735bc8f6489a33a0d4415ba91485850de1c1800f5`
- `runs/drift-confirmatory-v1/generative-registration.json`: `157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`
- `docs/task-receipts/haunt-confirmatory-v1-paired-closeout-20260914.md` names those same hashes and scopes the closeout to those gates.

## Independent checks

- The behavioral closeout contains exactly one outcome for each old/new snapshot of attrs, HTTPX, and pytest. All six have `verdict=PASS` and `test_exit=0`.
- Recomputed every referenced test-log content digest (including decompression for retained `.gz` logs), retained-log digest where supplied, full environment-freeze digest, and source-archive digest. All match the closeout; each source archive also matches its frozen registration digest.
- The closeout's initial-results digest and its binding to the requested generation-registration hash match.
- `validate_v2_manifest()` accepted all six prompt rows. Recomputed all six adapter-tree digests and confirmed the prompt, adapter-registration, and generation-registration bindings. Verified the six corpus source archives, train/validation files, corpus manifests, sample-registration hash, held-out ledger, and objective-label ledger against their recorded digests.
- The registration remains `blocked-before-generation`, has `comparison_authorized=false`, and declares 162 expected records. No generation, inference, scoring, or comparison was invoked for this review.

The prior corpus/adapter preflight receipt was reviewed as context; this verdict relies on the exact closeout and registration artifacts and the independent checks above.
