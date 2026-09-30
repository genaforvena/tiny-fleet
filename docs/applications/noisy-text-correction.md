# A08 domain OCR/typing correction with protected fields

Status: `INCONCLUSIVE`, offline baseline screen, 2026-09-09. This is a
reproducible exploration artifact, not a deployment or model-benefit claim.

The CC0-1.0 synthetic manifest expands to 12 development, 20 validation, and
120 heldout documents. Heldout source families are independent and disjoint
from validation, with 60 English and 60 Russian documents. Each document has
one protected ticket identifier that must remain unchanged.

The matched deterministic baselines are identity and dictionary/edit-distance
correction. On the 120 heldout documents, identity has mean CER `0.042258`
and the dictionary baseline has mean CER `0.000000`, a 100% observed relative
reduction. Both preserve all 120 protected identifiers; measured protected
field corruption is `0.0%`. These finite synthetic results do not establish
generalization: source-family intervals are not estimable for the singleton
families in this screen, so the verdict remains `INCONCLUSIVE`.

ByT5-small is recorded as the primary feasibility precedent
([paper](https://arxiv.org/abs/2105.13626)) only. The ByT5-small and 360M LoRA
arms are unavailable until C02-C08 and S01-S05 are independently verified.
The pilot was not run: there is no justified headroom over the deterministic
baseline, and no GPU or paid API cost was incurred. No adapter is wired into
live routing.

Run the contract and baseline checks with:

```text
rtk proxy .venv/bin/python scripts/test_app_noisy_text_correction.py
rtk proxy .venv/bin/python scripts/applications/noisy_text_correction.py --phase baseline --run-dir runs/applications/noisy-text-correction/baseline-20260909
```

The raw JSONL and summary are stored under
`runs/applications/noisy-text-correction/baseline-20260909/`.
