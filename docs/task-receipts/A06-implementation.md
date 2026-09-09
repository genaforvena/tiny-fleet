# A06 implementation receipt — support-routing

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Source revision: recorded after commit below
- UTC: `2026-09-09`
- Scope: `scripts/applications/support_routing.py`, `scripts/test_app_support_routing.py`, `corpus/applications/support-routing/`, `runs/applications/support-routing/`, `docs/applications/support-routing.md`, `docs/task-receipts/A06-check-20260909.txt`
- Primary precedent: <https://deepmind.google/models/gemma/embeddinggemma/>

## Result

READY FOR INDEPENDENT VPN VERIFICATION. This implementation adds the frozen
CC0 synthetic corpus, eight-queue-plus-unknown contract, TF-IDF logistic and
nearest-centroid baselines, raw output files, summary, documentation, and
contract tests. The model arms remain explicitly unavailable because C02–C08
and S01–S05 are not independently verified.

The heldout baseline contains 140 independent source-family units, including 60
OOD units. TF-IDF macro-F1 on known queues is 0.6611169468; nearest-centroid
macro-F1 is 0.6492121849. TF-IDF has 0/60 OOD false accepts with exact one-sided
95% upper bound 0.0487029133, so the preregistered 5% OOD gate is met by the
simple baseline. The bounded verdict is `NO_GO_BASELINE_DOMINANT`; no pilot or
deployment was run.

## Commands and artifacts

```text
rtk proxy .venv/bin/python scripts/test_app_support_routing.py
exit 0 (5 tests)
rtk proxy .venv/bin/python scripts/applications/support_routing.py --phase baseline --run-dir runs/applications/support-routing
exit 0
git diff --check
exit 0
```

Check output: `docs/task-receipts/A06-check-20260909.txt`, SHA-256
`2ad38f3d3816d9c90da9095985213ea9bf03c494c193094b1ba3bc466f8ab7e4`.

Artifact SHA-256 values before commit:

- `corpus/applications/support-routing/manifest.json` — `0a56497d645cb715aa3338ffa59af3417cf62db055df036bc6eaa509e555d87a`
- `runs/applications/support-routing/tfidf-logistic-raw.jsonl` — `8cb740e53e27da5defaedf814f739a58d4d0e97e464306c7ccd214d2b92112b7`
- `runs/applications/support-routing/nearest-centroid-raw.jsonl` — `85978bebdf857da2cbd1522c7e6c07b1706e463d2fb0f170069eafb4a795d1d8`
- `runs/applications/support-routing/summary.json` — `df23715ea7ff102b9df43df5da2d205513c5564a6ce764c1113fe51ec78f3009`

## Exact next action

VPN must inspect this submitted commit in an isolated checkout, rerun the test
and baseline into a new temporary directory, recompute the result and hashes,
mutate one load-bearing behavior to observe FAIL then restore PASS, and inspect
an unseen negative case before writing `A06-verification.md`.
