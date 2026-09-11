# Exact-owner resolver queue audit — haunt

- Date: 2026-09-11 UTC
- Owner: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Repository revision at audit: `b87f056`
- Result: remaining dispatched resolver rows repeat two already evidenced external blockers.

## Dictionary-input resolver rows

These rows all target `haunt-install-unblock-20260907/install-and-retry-tinyfleet` and
request the same missing operator-selected dictionary source, language,
normalization, immutable version, and corpus:

- `unblock/haunt/edda630d2570feb5/resolve`
- `unblock/haunt/8dd5748c3f583e5a/resolve`
- `unblock/haunt/479c61db4a49d92d/resolve`
- `unblock/haunt/8ac2eb3811994164/resolve`

The current source and exact input/retry contract are documented in
`docs/task-receipts/unblock-haunt-69db9419928a4a06-20260911.md`; the install
and dictionary audits cited there remain the underlying evidence. No safe
repository-local change can decide the experiment's dataset. These rows stay
`BLOCKED/operator-input` until those five values and matching corpus bytes are
provided.

## S06 pilot-dependency resolver rows

These rows all target `tinyfleet-real-mesh-pilot-20260907/select-real-mesh-use-case`
and request the same S06 implementation and independent VPN evidence:

- `unblock/haunt/4ee612a343571685/resolve`
- `unblock/haunt/76638b13f965a039/resolve`
- `unblock/haunt/587b8087e7818ff7/resolve`
- `unblock/haunt/1e7e7669aa6b691f/resolve`
- `unblock/haunt/c857ce19204534e3/resolve`

The live pilot task remains blocked. `docs/task-receipts/S06-progress-20260911.md`
records an unfinished runner and no training; `docs/task-receipts/S06-implementation.md`
records `BLOCKED/dependency` and zero of fifteen prediction rows; the S06
independent verifier remains queued and `docs/task-receipts/S06-verification.md`
is absent. The full exact completion gate and resume command are in
`docs/task-receipts/unblock-haunt-a8c15381384a62a2-20260911.md`.

The pilot cannot be resumed from this repeated dispatch. Only a completed and
validated S06 matrix plus a passing independent VPN verification receipt
clears the dependency; then run:

```bash
mesh-task resume tinyfleet-real-mesh-pilot-20260907 select-real-mesh-use-case S06-verified
```

No dictionary input was selected, no S06 work was bypassed, and no live or
shadow mesh pilot was started by this queue audit.
