# Dictionary-input resolver refresh — 2026-09-14

Task: `unblock/haunt/2e1cbcd2f8380a3b/resolve`

The resolver was still blocked with retry text requiring a fresh dependency preflight and the
source/path/hash. Its named parent step `haunt-install-unblock-20260907/install-and-retry-tinyfleet`
is already `DONE`, with scope amendment
`docs/task-receipts/haunt-a08-scope-amendment-20260912.md`. That amendment records the operator's
selection and narrows closure to the synthetic A08 dictionary fixture. The broader BbyWVY
dictionary arm remains unproven and is not included in that completed task.

## Rechecked input and replay

The selected manifest at `runs/operator-selected-dictionary-v1/input-manifest.json` has SHA-256
`9081dd78b28ed94b501016698cd6d5347095a5ea079730bf888123c3ec2e1e08`. It records the operator
selection: `corpus/applications/noisy-text-correction/manifest.json` at commit
`ed7fa28fb2b010f0cd1294b6df36bf53a5d21396`, CC0-1.0, synthetic-only; languages `en` and `ru`;
exact case-sensitive `str.replace` without normalization, case-folding, or tokenization; and
corpus `runs/operator-selected-dictionary-v1/corpus.jsonl` (152 rows). Recomputed hashes:

- source manifest: `17879f42f885b18ed5e0638a6620ff745200ddb79d9a3004a20fa22933ea0997`
- implementation `scripts/applications/noisy_text_correction.py`:
  `69330b7803f0844198c84f07d54cc89e822d4df9abc63ddfb58b6c3c921c60db`
- materialized corpus: `81a41340c0c01555a536e9aa30b3b2b72b1dd9ae48908014fd0f58192515dcd3`

Ran `scripts/test_app_noisy_text_correction.py`: **5 tests passed**. Replayed the dependency-free
baseline with:

```text
python3 scripts/applications/noisy_text_correction.py --phase baseline --run-dir runs/operator-selected-dictionary-v1/resolver-preflight-20260914 --manifest corpus/applications/noisy-text-correction/manifest.json
```

The fresh raw output SHA-256 is `555f1ab7808d5d01324c770e58fc594b48ea17ff55364d6a4214e4aed8b988fd`,
matching the frozen prior result byte-for-byte. Fresh summary:
`runs/operator-selected-dictionary-v1/resolver-preflight-20260914/summary.json` (SHA-256
`6107aec6c67aeb9397fcb623222b8d426f6d6491ef38f063d2ce7be5c9d15ad1`). The result remains
`INCONCLUSIVE` beyond the narrow A08 fixture because source-family uncertainty is not estimable.

The blocked resolver was resumed and closed against this preflight evidence. Its parent was not
resumed because it is already complete under the recorded A08-only scope amendment; no broader
BbyWVY dictionary claim is made.
