# A06 independent verification receipt — support-routing

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Exact source commit verified: `c74f863fb99ccd9c7566ff8c7607512c8b5d4652`
- Submitted implementation revision: `370d7f233f7413197081f80b1dcb7a75ea5cf4ca`
- Verification checkout: fresh detached isolated worktree at `/tmp/tiny-fleet-a06-verify-20260909`
- Environment: interpreter `/home/mesh-home/tiny-fleet/.venv/bin/python`, Python 3.12.3
- Verdict: **PASS**

## Acceptance verification

The mandated contract test was run independently from the detached checkout:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_app_support_routing.py
exit 0
Ran 5 tests in 0.047s
OK
```

The independent baseline was written to a new temporary directory, not the author's run:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/applications/support_routing.py \
  --phase baseline --run-dir /tmp/a06-final-independent-5UeSf0/baseline
exit 0
```

Independent recomputation from the two raw JSONL files produced:

```text
heldout_n=140 known_n=80 ood_n=60 heldout_families=140
tfidf_macro_f1=0.6611169467787115
tfidf_ood_false_accept_n=0
tfidf_ood_false_accept_upper_95=0.04870291331009746
verdict=NO_GO_BASELINE_DOMINANT
```

The unseen negative cases `weather forecast for tomorrow`, `write a poem about my vacation`,
and `erase all records` all returned `unknown`; an unseen ambiguous `invoice password` centroid
case also returned `unknown`.

The mutation gate was exercised by changing the abstention threshold in the isolated source. The
same test command then failed one assertion (`NO_GO_BASELINE_DOMINANT` became `INCONCLUSIVE`,
exit 1), proving the check observes load-bearing behavior. The source was restored and the clean
5-test run above passed afterward.

## Stable artifact hashes

Recomputed stable hashes match the implementation receipt:

```text
manifest.json                         0a56497d645cb715aa3338ffa59af3417cf62db055df036bc6eaa509e555d87a
tfidf-logistic-raw.jsonl               8cb740e53e27da5defaedf814f739a58d4d0e97e464306c7ccd214d2b92112b7
nearest-centroid-raw.jsonl             85978bebdf857da2cbd1522c7e6c07b1706e463d2fb0f170069eafb4a795d1d8
author summary.json                    df23715ea7ff102b9df43df5da2d205513c5564a6ce764c1113fe51ec78f3009
independent raw outputs: identical stable hashes
```

The independently regenerated `summary.json` is not byte-identical because it embeds the new
temporary run path and measured latency; its semantic metrics and verdict match exactly. The
independent evidence files are retained at `/tmp/a06-final-independent-5UeSf0/` with aggregate
SHA-256 `7a290b055282942ab541bf60b9a17af9a62b2062ad3c97a7e61291f66b4ae67d` for the recomputation
record, and test output SHA-256 `29a534a82f702590098b6740b600c5526e4ccfd3bd2feb5368a2886076b53b3c`.

## Residual limitations

This PASS accepts the frozen A06 acceptance contract only. The model arms remain unavailable until
C02–C08 and S01–S05 are independently verified; no neural pilot or live routing deployment was
run. The baseline is a locally authored synthetic CC0 corpus, so these results do not establish
production usefulness or safety.
