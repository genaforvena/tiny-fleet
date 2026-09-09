# A09 bounded transliteration and diacritic restoration

Status: `INCONCLUSIVE`, offline baseline screen, 2026-09-09. This is a
reproducible exploration artifact, not a deployment or model-benefit claim.

The CC0-1.0 synthetic manifest freezes Russian Latin/Cyrillic word
transformation with exact ticket IDs protected. It expands to 12 development,
20 validation, and 120 heldout documents: 60 `ru-latn` and 60 `ru-cyrl`
heldout documents, each from an independent source family. Unknown words are
left unchanged (abstention), and protected `ORD-YYYY-NNNN` tokens are never
rewritten.

Matched baselines are identity and a deterministic transliterator plus frozen
lexicon. On heldout words excluding protected IDs, identity scored 0/540 exact
words, while the lexicon scored 540/540, an observed 1.0 exact-word gain.
Protected IDs were unchanged in 120/120 lexicon outputs. No ambiguous heldout
references were present in this frozen screen (`ambiguous_n=0`). The finite
synthetic result does not establish generalization: source-family intervals
are not estimable for singleton synthetic families, so the verdict remains
`INCONCLUSIVE`.

ByT5-small is recorded as the feasibility precedent
([paper](https://arxiv.org/abs/2105.13626)) only. ByT5-small, base 360M, and
360M LoRA arms are unavailable pending independent C02-C08 and S01-S05
verification. No pilot ran, no GPU or paid API cost was incurred, and no live
routing was changed.

Run the checks with:

```text
rtk proxy .venv/bin/python scripts/test_app_transliteration.py
rtk proxy .venv/bin/python scripts/applications/transliteration.py --phase baseline --run-dir runs/applications/transliteration/baseline-20260909
```

Raw JSONL and summary artifacts are under
`runs/applications/transliteration/baseline-20260909/`.
