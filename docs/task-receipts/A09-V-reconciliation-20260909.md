# A09-V reconciliation receipt — corrected implementation hash

- Verifier: `vpn`
- Corrected receipt commit: `fa6a61f73a2111c8fc30ef34019eedd45d14a515`
- Exact implementation source commit: `6d3b554713af8b8646ba842515b20e55e406cf41`
- Verdict: **RECONCILED — corrected receipt is internally consistent**

## Independent checks

The mandated suite ran from a fresh detached worktree at the corrected receipt commit:

```text
/home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_app_transliteration.py
exit 0 — Ran 5 tests; OK
```

The baseline was rerun into a new isolated output directory:

```text
/home/mesh-home/tiny-fleet/.venv/bin/python scripts/applications/transliteration.py \
  --phase baseline --run-dir /tmp/a09-reconcile-run-lRoqFv/baseline
exit 0 — wrote raw.jsonl and summary.json
```

Independent evidence:

- raw output: 304 rows (24 development, 40 validation, 240 heldout)
- heldout metrics: identity `0/540`, deterministic lexicon `540/540`
- protected IDs unchanged: `120/120`; protected violations: `0`
- independent raw SHA-256: `bf7b5e768d07db7bad309226d6dcced00fe8bc1833ac08b1a62c521bcb16b5c`
- author raw SHA-256: `bf7b5e768d07db7bad309226d6dcced00fe8bc1833ac08b1a62c521bcb16b5c`
- corrected implementation receipt and generated summary both contain that exact 64-character hash
- unseen negative `ORD-2026-9001 qwerty novoe-slovo` is absent from the manifest and was returned unchanged
- `git diff --check`: exit 0

The application verdict remains `INCONCLUSIVE`: model arms are unavailable and no pilot ran. This
reconciliation clears only the receipt typo; it does not promote A09 or release held A10.
