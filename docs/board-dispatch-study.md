# Board-dispatch study v1

This is a frozen, offline, advisory-only corpus. It classifies sanitized free-text task cases and
proposes a suitable owner set; it cannot create, claim, settle, or dispatch a task. Explicit owner,
active lease, dependency state, retry budget, protected roles, and single-writer constraints remain
authoritative inputs and must be enforced by the deterministic dispatcher.

The cases are authored public fixtures, split by family before any paraphrase, with an explicit
`observed_at` as-of timestamp. Labels carry `review: independent`; eventual board outcomes and
private receipts are not labels or inputs. The corpus includes quoted owner tags, wrong-repo-like
prose, expired and active leases, protected owners, duplicate/completed work, unknown specialty,
and embedded instructions. Ambiguous cases retain `needs_clarification=true`.

Registration is immutable at `runs/board-dispatch-v1/registration.json`. Run the dependency-free
gate with:

```bash
rtk proxy .venv/bin/python scripts/test_dispatch_corpus.py
```

The gate checks corpus hash, split counts, family isolation, typed fields, owner whitelist,
sanitization, independent label provenance, explicit-owner preservation, and ambiguity coverage.
It deliberately contains no live `mesh-dispatch`, `mesh-task`, `mesh-chat`, or Ledger calls.
