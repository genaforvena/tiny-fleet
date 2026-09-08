# A02 implementation receipt — ticket-extraction

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-08`
- Result: **READY FOR INDEPENDENT VPN VERIFICATION**

## Scope and result

This scoped change adds the offline extractor/scorer, deterministic CC0
screening manifest, baseline raw outputs and summary, documentation, and
contract tests. It extracts four nullable fields and exact evidence spans;
contradictory labels abstain, absent values remain null, and quoted prompt
injection is ignored. No model or deployment path is enabled.

The 100-case heldout baseline scores 400/400 fields and 100/100 exact-span
cases, with 0 unsupported fields and a 0.7461% one-sided 95% upper bound.
Because the baseline has no observed headroom and the neural prerequisites are
unverified, the result is the justified bounded verdict
`NO_GO_BASELINE_DOMINANT`; it is not a neural comparison.

## Commands and artifacts

```text
rtk proxy .venv/bin/python scripts/applications/build_ticket_corpus.py
exit 0
rtk proxy .venv/bin/python scripts/test_app_ticket_extraction.py
exit 0 (7 tests)
rtk proxy .venv/bin/python scripts/applications/ticket_extraction.py --phase baseline --run-dir runs/applications/ticket-extraction/baseline-20260908
exit 0
git diff --check
exit 0
```

The captured check output is `docs/task-receipts/A02-check-20260908.txt`.
SHA-256: `97cbab94bff09f1fe36f3f5b84f42a159f51356e5f54ccbceb8700007b198797`.
The source manifest is `corpus/applications/ticket-extraction/manifest.json`.
SHA-256: `7b539de4d1d123ae3975cbbcc70192965f852cca15e46e6f5ecea5ac80a9f866`.
The baseline artifacts are under
`runs/applications/ticket-extraction/baseline-20260908/`.

- `regex-dictionary-raw.jsonl` SHA-256: `bf76823764f36a0a94351aee9dcbbd76161cca320fcad4084bb09cb9535650b3`
- `summary.json` SHA-256: `0837c47a02e3a3255268e2c7d584d71e01dc89e1f693c2a8ec0efb5fbf29cf3c`

## Exact next action

VPN checks out the submitted commit in isolation, reruns the test and baseline
into a new temporary directory, recomputes all counts/hashes, and tests unseen
negative cases. It must write `A02-verification.md` and settle the paired
verification task only on an independent PASS.
