# A02 independent verification receipt — ticket-extraction

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Owner receipt commit inspected: `97c5c050d742558b250754ebd196c6e9be0904c8`
- Exact source commit verified: `69e3eb46c7b381c278262449e0d47cb352ed928a`
- Verification checkout: fresh detached isolated worktree at `/tmp/a02-v-independent.fresh.bAoHpM`
- Environment: `.venv` symlinked to `/home/mesh-home/tiny-fleet/.venv`
- Interpreter: `/home/mesh-home/tiny-fleet/.venv/bin/python`
- Python: `3.12.3`
- Verdict: **PASS**

## Exact acceptance check

The mandated command was run from the fresh isolated checkout:

```text
rtk proxy .venv/bin/python scripts/test_app_ticket_extraction.py
test_absent_values_are_null (__main__.TicketExtractionTests.test_absent_values_are_null) ... ok
test_baseline_writes_raw_outputs_and_summary (__main__.TicketExtractionTests.test_baseline_writes_raw_outputs_and_summary) ... ok
test_contradiction_is_abstention (__main__.TicketExtractionTests.test_contradiction_is_abstention) ... ok
test_extracts_values_and_exact_spans (__main__.TicketExtractionTests.test_extracts_values_and_exact_spans) ... ok
test_malformed_input_is_valid_empty_record (__main__.TicketExtractionTests.test_malformed_input_is_valid_empty_record) ... ok
test_manifest_rejects_underpowered_screening (__main__.TicketExtractionTests.test_manifest_rejects_underpowered_screening) ... ok
test_prompt_injection_inside_ticket_is_not_evidence (__main__.TicketExtractionTests.test_prompt_injection_inside_ticket_is_not_evidence) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.010s

OK
exit 0
```

The fresh captured test output artifact is `/tmp/a02-v-fresh-test-output.txt` with SHA-256
`f78b0d29b727bcb529c8b31d3ac4c3bfc3da8bba25565a732463aef73636de92`.

The baseline was independently rerun into
`/tmp/a02-v-independent.fresh.bAoHpM/runs/a02-v-independent-baseline` and exited 0.
Its command output is `/tmp/a02-v-fresh-baseline-output.txt`, SHA-256
`91a9ce99df0156953cd995f9a3dce71aecffa87d24fb247f281e7dabaebfbfb2`.

The independent baseline reproduced the source raw output hash
`bf76823764f36a0a94351aee9dcbbd76161cca320fcad4084bb09cb9535650b3`.
Recomputed source hashes match the implementation receipt:

- manifest: `7b539de4d1d123ae3975cbbcc70192965f852cca15e46e6f5ecea5ac80a9f866`
- raw baseline: `bf76823764f36a0a94351aee9dcbbd76161cca320fcad4084bb09cb9535650b3`
- baseline summary: `0837c47a02e3a3255268e2c7d584d71e01dc89e1f693c2a8ec0efb5fbf29cf3c`

Recomputed predicates: 100 heldout cases from 100 distinct source families, 400/400
fields correct, 100/100 exact-span cases, and 0 unsupported fields. Recompute output is
`/tmp/a02-v-fresh-recompute-output.txt`, SHA-256
`58e1a7043b7933ca0a3edfd88669708ff7b83f51a3d95de2c99b4a1644749609`.

An unseen counterexample containing natural-language mentions but no labelled evidence
fields returned all four fields as null and no evidence spans. Output is
`/tmp/a02-v-fresh-negative-output.txt`, SHA-256
`6727f8a6e3bc416c9548e0a25ea2216d7641bcba1dbd394ead89687903c1a27a`.

## Independent evidence

- `git rev-parse HEAD` in the verification checkout: `69e3eb46c7b381c278262449e0d47cb352ed928a`
- `.venv/bin/python --version`: `Python 3.12.3`
- Acceptance result: 7 tests passed, 0 failures, process exit `0`
- No `python3` fallback was used.

## Residual limitation

The neural model arms remain unavailable because C02-C08 and S01-S05 are not verified.
The implementation's `NO_GO_BASELINE_DOMINANT` verdict is accepted as a bounded
baseline/no-go result, not as evidence of neural-model benefit.
