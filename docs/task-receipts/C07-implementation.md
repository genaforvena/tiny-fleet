# C07 implementation receipt — router failure boundary

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: 2026-09-11
- Submitted source revision: `71e09b56fd0f6b86988cf53c577f64b9c7da8122`
- Scope: `scripts/router.py`, `scripts/test_router.py`

## Result

Implemented explicit abstention at the embedding/router boundary. Query and centroid
count/shape, finite-value, and non-zero-norm checks now reject malformed inputs. The
HTTP embedding backend checks curl status, timeout, JSON, response schema, and row
count. Route detail retains machine-readable `reason`, `best_similarity`, `margin`,
and embedding backend/model revision/digest fields. Operator-first evaluation remains
before centroid or embedding validation. The default revision/digest are explicitly
`unresolved` unless supplied by `TINY_FLEET_EMBEDDING_REVISION` and
`TINY_FLEET_EMBEDDING_DIGEST`; no backend identity was fabricated.

The new test suite covers zero, NaN, infinity, wrong dimension, empty matrix, invalid
centroid, HTTP timeout/failure, invalid JSON, operator bypass, and valid specialist
routing. The original zero-vector regression was red before implementation, then
green after it.

## Verification

Commands were run from the repository root through the pinned environment:

```text
rtk proxy .venv/bin/python scripts/test_router.py       # exit 0; 7 tests OK
rtk proxy .venv/bin/python scripts/fleet_benchmark.py --test  # exit 0; 24/24
rtk proxy .venv/bin/python -m compileall -q scripts/router.py scripts/test_router.py # exit 0
git diff --check                                      # exit 0
```

Captured stdout/stderr artifacts from the exact checks:

- `/tmp/tiny-fleet-c07-test-router.txt` — SHA256
  `e586fc0f3bb2a05f4c80f07d1b4c6171e830592f6c7aaf70d4af3b0aa3ebd072`
- `/tmp/tiny-fleet-c07-fleet-test.txt` — SHA256
  `9b278027e97aa3c0299d3242beba62227bd884ada4d1fdcd83d1f18fe2040193`

Observed exact result: `Ran 7 tests ... OK`; fleet benchmark reported operator
adversarial `14/14`, router contract `4/4`, specialist inventory `2/2`, safety
decisions `4/4`, and fleet benchmark `24/24`.

## Next action

Ready for independent `vpn` verification of C07, including isolated mutation/recovery
and the C07-V acceptance predicates. This implementation does not submit or settle
the verification gate.
