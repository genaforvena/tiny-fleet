# C05 implementation receipt — correct causal loss

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Source revision: `dca2d10cabcb2da8e07270ba19bb29eccbadb6a1`
- Result: **PASS — ready for independent `vpn` verification**

## Scoped changes

- Added `scripts/loss_metrics.py` with `masked_labels(input_ids, attention_mask)`,
  shifted-target `summed_nll(logits, labels)`, and target-count-weighted
  `aggregate_perplexity`.
- Updated `scripts/train_eval.py` and `scripts/persona_code.py` to mask padding,
  score only `labels[:, 1:]`, and aggregate by scored target count.
- Persona evaluation now records per-case `nll_sum`, `target_count`, and truncation
  counts; historical numerical tables and old adapters are unchanged.
- Added `scripts/test_loss_metrics.py` covering manual NLL, padding-ID/logit
  invariance, one-token examples, and the old input-length weighting failure.

## Verification

Test-first sequence: the new test initially failed against the old tree because
`scripts/loss_metrics.py` was absent (`ModuleNotFoundError`). After implementation,
the exact task check passed:

```text
Command: rtk proxy .venv/bin/python scripts/test_loss_metrics.py
Exit: 0
Output artifact: /tmp/tinyfleet-c05-test-20260911.txt
SHA-256: 56e03afda220e7ba78bbcecf9a2e53a0149cfc3e311fa10bbd01b25e8e5ba671
Output: Ran 4 tests ... OK
```

Additional checks:

```text
rtk proxy .venv/bin/python -m compileall -q scripts/loss_metrics.py scripts/train_eval.py scripts/persona_code.py
Exit: 0

rtk proxy .venv/bin/python scripts/persona_code.py self-test --manifest runs/persona-code/manifest.json
Exit: 0; output: self-test: ok

rtk git diff --check
Exit: 0
```

No fresh model training or corrected empirical table was run. Corrected scores are
pending the separately scoped S06 run, as required by the plan. The source commit
is not yet pushed at receipt creation; the owner will verify remote ancestry before
settling C05.

Next action: independent `vpn` verification at
`tinyfleet-publication-science-20260908/verify-correct-causal-loss`.
