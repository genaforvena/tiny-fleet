# A08-V verification receipt — noisy-text-correction

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Audited source revision: `ed7fa28fb2b010f0cd1294b6df36bf53a5d21396`
- Verification checkout: detached isolated worktree `/tmp/tiny-fleet-a08-verify-20260909` at `325a3b6391fc8e90ea345efec3093bdc2cb2ba51`
- UTC: `2026-09-09`
- Audit mode: isolated read/execute verification; no VPN, route, DNS, firewall, WireGuard, or exit-node changes

## Result

**PASS** for the A08-V verification gate. The implementation's scientific verdict remains
`INCONCLUSIVE`, exactly as declared: deterministic baselines are measured, but model arms are
unavailable and source-family uncertainty intervals are not estimable for singleton synthetic
families. A09 and later remain held.

## Fresh independent commands

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_app_noisy_text_correction.py
exit 0 — Ran 5 tests; OK

rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/applications/noisy_text_correction.py \
  --phase baseline --run-dir /tmp/a08-independent-GlpXrn/baseline
exit 0 — wrote raw.jsonl and summary.json

rtk git diff --check
exit 0 — clean isolated checkout after mutation restoration
```

The independent raw artifact SHA-256 is
`555f1ab7808d5d01324c770e58fc594b48ea17ff55364d6a4214e4aed8b988fd`, matching the implementation
receipt. The manifest SHA-256 is
`17879f42f885b18ed5e0638a6620ff745200ddb79d9a3004a20fa22933ea0997`.
The regenerated summary is semantically equivalent; its byte hash differs from the author's
because it embeds the isolated run path and fresh latency.

## Independent recomputation

The raw JSONL contains 304 rows: 152 documents × 2 baselines, split as 24 development, 40
validation, and 240 heldout rows. The heldout denominator is 120 independent source families,
with 60 English and 60 Russian documents; validation has 20 disjoint documents. Recomputed
heldout results are:

```text
identity CER mean                 0.042258360054970225
dictionary/edit-distance CER mean 0.0
relative reduction vs identity    1.0
identity exact                    0/120
dictionary exact                 120/120
protected unchanged              120/120 for both baselines
protected violations             0
```

The output records `INCONCLUSIVE`, unavailable ByT5-small and 360M LoRA arms, zero GPU minutes,
and zero paid API calls. No deployment or live-routing change was made.

## Counterexample and mutation checks

An unseen input containing `servise qwerty` and protected ID `ORD-2026-9001` was not in the
dictionary and was returned unchanged (exit 0); this is an OOD negative case, not a usefulness
claim.

In the isolated checkout, changing the dictionary corrector's return to the uncorrected input
made the contract suite fail 1 test (4 passed, 1 failed, exit 1). The source was restored and the
fresh 5-test suite passed (exit 0).

## Residual limitations and next action

This PASS accepts only the frozen A08 acceptance contract. It does not establish production
generalization, neural-model benefit, or deployment safety. The next action is coordinator
reconciliation of this receipt; A09 must remain held until released by the task chain.
