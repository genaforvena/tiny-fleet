# A02 independent verification receipt — ticket-extraction

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Owner receipt commit inspected: `97c5c050d742558b250754ebd196c6e9be0904c8`
- Exact source commit verified: `69e3eb46c7b381c278262449e0d47cb352ed928a`
- Verification checkout: fresh detached isolated worktree at `/tmp/a02-v-independent.R3BSnA`
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

The captured output artifact is `/tmp/a02-v-env-independent-output.txt` with SHA-256
`11368724ca80274a0952b4d98492b0d021a3f9b66a3b992f11bdf258fb3a4978`.
The owner receipt's recorded SHA-256 was
`8f6e7b7b6aebc3b82242e30dd18dbfd679232a717da7e6d634084059c0061f27`; the byte-level
difference is the non-deterministic unittest duration (`0.010s` versus `0.006s`).

## Independent evidence

- `git rev-parse HEAD` in the verification checkout: `69e3eb46c7b381c278262449e0d47cb352ed928a`
- `.venv/bin/python --version`: `Python 3.12.3`
- Acceptance result: 7 tests passed, 0 failures, process exit `0`
- No `python3` fallback was used.

