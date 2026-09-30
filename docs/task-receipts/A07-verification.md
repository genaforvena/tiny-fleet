# A07-V verification receipt — independent vpn audit

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Audited revision: `b7caf0d4765f3a202d251656fbaa52def91ba25b`
- UTC: `2026-09-09`
- Audit mode: detached isolated git worktree; no VPN, route, DNS, firewall, WireGuard, or exit-node changes

## Result

PASS for the A07-V verification gate. The baseline's scientific verdict remains
`INCONCLUSIVE` as declared by A07: all finite point estimates are perfect, but
the Wilson 95% recall lower bound is `0.886483`, below the preregistered `0.99`
threshold. This is not evidence of complete anonymization and does not promote
the unavailable model arm.

## Evidence

The pinned checkout reran the contract suite with system Python because the
untracked source `.venv` is not present in an isolated worktree:

```text
python3 scripts/test_app_redaction_assistance.py — exit 0 (5 tests)
python3 scripts/applications/redaction_assistance.py --phase baseline \
  --run-dir <temporary-audit-run> \
  --manifest corpus/applications/redaction-assistance/manifest.json — exit 0
git diff --check — exit 0
clean restored checkout — confirmed
```

Independent manifest expansion reported:

```json
{"formats":["csv","log","markdown","plain"],"heldout_documents":120,"languages":["en","ru"],"source_families":120,"types":["account_id","email","name","phone"]}
```

Recomputed artifact hashes matched the submitted receipt for the manifest and
raw predictions:

```text
c13695a68ddee326bf1e312a9ac776a3ccd0b436bb41a9574809161af95cc4d2  corpus/applications/redaction-assistance/manifest.json
b9eec6416a1dfbc0caae9da431e0c43ecf03ef557f0228915f621da69d9eae31  regex-raw.jsonl
```

The generated summary was semantically identical (`INCONCLUSIVE`, 120 heldout,
30 gold and 30 predicted per type, exact offsets, Wilson lower bound
`0.886483`); its byte hash is expected to differ because it contains the
temporary absolute raw-output path and measured latency.

## Mutation and OOD checks

The Russian branch of the name matcher was removed in the isolated checkout.
The multilingual exact-offset test then failed with exit 1. Restoring the
branch returned the complete five-test suite to exit 0.

An unseen OOD document containing `Имя: Алина Петрова` and obfuscated
`a.lina [at] example dot org` produced one name span and no email span. This
is consistent with the receipt's residual risks around unseen spellings and
obfuscation; it is not a production or private-data claim.

## Exact next action

A07-V is verified. No further vpn action is required; the next owner may consume
this receipt for the A07 gate transition.
