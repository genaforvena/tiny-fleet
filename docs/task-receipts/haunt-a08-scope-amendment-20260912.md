# Owner scope amendment: Tiny Fleet correction result

- Date: 2026-09-12 UTC
- Owner: `haunt`
- Parent: `haunt-install-unblock-20260907/install-and-retry-tinyfleet`
- Resolver: `unblock/haunt/62c0662129fa8ee9/resolve`
- Decision: amend this task's dictionary-result criterion to the frozen synthetic A08 fixture only.

## Amended claim and closure criterion

This task may close on the exact, case-sensitive baseline result for the frozen, CC0,
synthetic-only A08 correction fixture: the dictionary baseline produced 120/120 exact heldout
outputs (mean CER 0; protected fields unchanged in 120/120), while the identity baseline produced
0/120 exact outputs. The closure claim is limited to those fixture outputs and the pinned
replacement implementation.

The verdict remains **`INCONCLUSIVE` for broader correction behavior**. The fixture contains only
five synthetic substitutions, source-family uncertainty is not estimable, and the ByT5/LoRA arms
are unavailable. This result does not establish general dictionary quality, natural-language
correction behavior, or BbyWVY dictionary behavior. The separate six-case BbyWVY smoke proves
runtime loading and non-empty generation only; its script has no dictionary arm. Do not combine
the smoke and A08 result into a BbyWVY dictionary claim.

The broader BbyWVY dictionary question is outside this amended task's closure criterion and remains
unproven. It requires a separate BbyWVY-compatible dictionary arm and declared comparison before
any claim about that behavior.

## Frozen evidence

The selected manifest is
`runs/operator-selected-dictionary-v1/input-manifest.json` (SHA-256
`9081dd78b28ed94b501016698cd6d5347095a5ea079730bf888123c3ec2e1e08`). It pins the CC0
synthetic-only A08 dictionary at source commit
`ed7fa28fb2b010f0cd1294b6df36bf53a5d21396`, languages `en` and `ru`, exact case-sensitive
Python `str.replace` without Unicode normalization or case folding, and the 152-row materialized
corpus at `runs/operator-selected-dictionary-v1/corpus.jsonl` (SHA-256
`81a41340c0c01555a536e9aa30b3b2b72b1dd9ae48908014fd0f58192515dcd3`).

The measured baseline output is
`runs/operator-selected-dictionary-v1/result/raw.jsonl` (SHA-256
`555f1ab7808d5d01324c770e58fc594b48ea17ff55364d6a4214e4aed8b988fd`). The separate cached-model
smoke is `runs/operator-selected-dictionary-v1/bbywvy-smoke.txt` (SHA-256
`f64847a15bc68114b0d369200a0173d3f37e8a76c13fe499d93f9854eb4cffc6`). Full input selection and
measurement method are in
`docs/task-receipts/adint-operator-authorized-dictionary-input-20260912.md`.

## Verification performed for this amendment

- Recomputed the manifest, corpus, raw result, and BbyWVY smoke SHA-256 values above.
- Confirmed the frozen corpus has 152 rows.
- Ran `rtk proxy .venv/bin/python scripts/test_app_noisy_text_correction.py`; all five tests passed.
- Confirmed the owner resume gate had been refused while this resolver still carried the stale
  `operator-input` block. The frozen input exists, so that block is now cleared by the amended
  criterion rather than by another operator response.

Parent task completion is limited to the amended A08 criterion above. The A08 `INCONCLUSIVE` limit
and the unmeasured BbyWVY dictionary claim remain explicit in this receipt and in the task result.
