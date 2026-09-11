# Haunt publishable-closeout README correction — 2026-09-11

- Owner: `haunt`
- Task: `unblock/haunt/b238c1aa2cac2b6e/resolve`
- Original task: `tinyfleet-publishable-closeout-20260907/publishable-repository-closeout`
- Repository: `/home/mesh-home/tiny-fleet`
- Source revision before correction: `160f33079f487e22fb9b78694656d387f0b4cda0`

## Action

Rewrote the reader-facing README claim-by-claim against
`docs/evidence-status.tsv`. The README now limits the current reproducible
claim to the verified-bounded offline contract benchmark, labels specialist
perplexity and drift outputs historical/unreproduced, marks weekly tracking
and latency as untested, and removes the unsafe default auto-action example.
No missing experiment or deployment evidence was invented.

## Verification

```text
.venv/bin/python scripts/fleet_benchmark.py --test
fleet benchmark: 24/24

.venv/bin/python scripts/test_deep_evaluation.py
Ran 6 tests ... OK

git diff --check
exit 0
```

The focused checks pass. The README correction is the prerequisite artifact;
the remaining successor evidence tasks in `docs/evidence-status.tsv` are not
claimed complete by this receipt.
