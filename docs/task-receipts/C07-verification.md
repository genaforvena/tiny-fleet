# C07-V verification receipt — router failure boundary

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11T18:29:17Z`
- Submitted source revision: `71e09b56fd0f6b86988cf53c577f64b9c7da8122`
- Implementation receipt SHA-256: `580b13780feaf3bc24fcc5650716e3791611fecf11863eec0288e3b3ef469e47`
- Verification checkout: `/tmp/tiny-fleet-c07-v-CnD1qY/repo`

## Scope and independent checks

The submitted source commit changes only `scripts/router.py` and
`scripts/test_router.py`, matching the C07 scope. The verification checkout was
clean at the submitted revision; the repository's pinned interpreter was invoked
from `/home/mesh-home/tiny-fleet/.venv/bin/python` because `.venv` is untracked
and is not present in a plain clone. No live run directory or board log was used.

| Check | Exit | Output artifact | SHA-256 |
|---|---:|---|---|
| `.venv/bin/python scripts/test_router.py` | 0 | `/tmp/tiny-fleet-c07-v-CnD1qY/restored-router.stdout` | `670a39115e7523a8984e4842e16547cb2094b03fad392b037b4b9dc8b2656e62` |
| `.venv/bin/python scripts/fleet_benchmark.py --test` | 0 | `/tmp/tiny-fleet-c07-v-CnD1qY/restored-fleet.stdout` | `9b278027e97aa3c0299d3242beba62227bd884ada4d1fdcd83d1f18fe2040193` |
| `.venv/bin/python -m compileall -q scripts/router.py scripts/test_router.py` | 0 | `/tmp/tiny-fleet-c07-v-CnD1qY/restored-compile.stdout` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `git diff --check` | 0 | `/tmp/tiny-fleet-c07-v-CnD1qY/restored-diffcheck.stdout` | `e3b0c44298fc1c1499d66772fb053253bc5c1b882d40a71d5d5697af8aea2d` |

Observed independently: router `Ran 7 tests ... OK`; fleet benchmark
reported operator adversarial `14/14`, router contract `4/4`, specialist
inventory `2/2`, safety decisions `4/4`, and fleet benchmark `24/24`.

## Mutation and counterexample evidence

The zero-norm rejection predicate was mutated in the isolated checkout from
equality to an impossible negative comparison. The router suite exited 1 and
failed `test_zero_query_embedding_abstains_with_machine_readable_reason`,
observing `invalid_similarity` instead of `invalid_embedding_norm`.

Mutation output: `/tmp/tiny-fleet-c07-v-CnD1qY/mutated-router.stdout`,
SHA-256 `3f73ba916d7d5796e9c5bb157fdd66e2dbc950bea0a438a8b8373cc1766a4e6c`.
The original predicate was restored before the passing checks above.

Additional independent negative cases not present in the implementation receipt's
positive examples passed: malformed backend JSON schema returned
`embedding_response_schema`, and a valid JSON response with the wrong row count
returned `embedding_response_shape`; both returned route `abstain`.

Counterexample output: `/tmp/tiny-fleet-c07-v-CnD1qY/counterexample.stdout`,
SHA-256 `6f5e4be967fb7a4916b4292481bc4211ca953844d8f85df6ec456d481b3f3a47`.

## Result and next action

**PASS.** C07 acceptance is met: malformed embeddings and backend failures
abstain with machine-readable reasons, operator-first bypass remains intact, and
valid specialist routing plus current fleet behavior are retained. This receipt
does not claim calibrated accuracy, deployment safety, or backend availability.

Next action: settle
`tinyfleet-publication-science-20260908/verify-router-failure-boundary` as
PASS; the coordinator may then release C08 implementation.
