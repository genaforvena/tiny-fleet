# A09 implementation receipt: transliteration

Result: `INCONCLUSIVE` deterministic baseline exploration, ready for
independent A09-V.

## Scope

- Task: `tinyfleet-applications-20260908/transliteration`
- Source revision: `6d3b554713af8b8646ba842515b20e55e406cf41` (`feat: add A09 transliteration baseline`)
- Sources: `scripts/applications/transliteration.py`,
  `scripts/test_app_transliteration.py`
- Corpus: `corpus/applications/transliteration/manifest.json`
- Documentation: `docs/applications/transliteration.md`
- Run: `runs/applications/transliteration/baseline-20260909/`

## Verification

```text
rtk proxy .venv/bin/python scripts/test_app_transliteration.py
```

Exit code: `0`; 5 tests passed. Tests cover known-word rewriting and literal
ID preservation, unknown/OOD abstention, malformed input, protected-span
scoring, ambiguity reporting, split independence, and artifact creation.

```text
rtk proxy .venv/bin/python scripts/applications/transliteration.py --phase baseline --run-dir runs/applications/transliteration/baseline-20260909
```

Exit code: `0`; raw JSONL and summary were written. Raw output SHA-256:
`bf7b5e768d07db7bad309226d6dcced00fe8bc1833ac08b1a62c521bcb16b5c`. Heldout count is 120 with 540 scored non-protected words
per baseline. Identity exact rate is `0/540`; deterministic lexicon exact rate
is `540/540`; protected IDs are unchanged `120/120`.

The declared verdict is `INCONCLUSIVE`: model arms are unavailable pending
C02-C08 and S01-S05, and source-family uncertainty intervals are not estimable
for singleton synthetic families. Pilot cost is zero GPU minutes and zero
paid API calls. No deployment or live-routing change was made.

## Independent verification handoff

The next ledger step is VPN-owned:
`tinyfleet-applications-20260908/verify-transliteration`. VPN must rerun the
check in isolated output paths, inspect artifacts, recompute counts/hashes,
and include an unseen negative case. A09-V and A10 remain held until the
coordinator releases them.
