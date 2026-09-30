# A09 implementation receipt hash correction

Result: corrected and ready for VPN reconciliation.

## Root cause

The implementation receipt transcribed the raw artifact hash with one `b`
omitted after `...db`, producing a 63-character claim. The raw JSONL and
generated summary were not changed.

## Commands and evidence

```text
rtk sha256sum runs/applications/transliteration/baseline-20260909/raw.jsonl
```

Exit code: `0`; exact raw SHA-256:
`bf7b5e768d07dbb7bad309226d6dcced00fe8bc1833ac08b1a62c521bcb16b5c`
(64 hexadecimal characters).

```text
rtk rg -n 'bf7b|raw_sha256' docs/task-receipts/A09-implementation.md runs/applications/transliteration/baseline-20260909/summary.json
```

Exit code: `0`; the corrected implementation receipt and generated summary
now assert the same exact 64-character value. The independent A09-V receipt's
valid-hash assertion was corrected as well; its quoted old 63-character value
is retained only as the historical finding.

```text
rtk git diff --check
```

Exit code: `0`.

No metrics, raw outputs, model status, or dispatch state changed. A10 remains
held. VPN must reconcile A09-V from the corrected implementation receipt.
