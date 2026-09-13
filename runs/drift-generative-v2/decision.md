# External-snapshot generative arm — registration status

Status: **BLOCKED BEFORE GENERATION**.

The pinned sample, base model revision, prompt template, decoding, seed schedule and candidate
embedding model are recorded in `registration.json`. The exact model/runtime, source references,
and resource observation are in `environment.txt`. The registration deliberately has no output or
score rows.

The verified D03 runner is a fixture matrix runner. Its production CLI uses `FakeBackend` unless
another backend is injected in-process; its record schema applies one input across all arms and
records one model digest without an adapter digest. It therefore cannot represent this study's
base / snapshot-context / six snapshot-specific LoRA arms honestly. No snapshot-specific adapters,
held-out excerpt hashes, or deterministic scorer implementation are frozen yet. Existing unrelated
LoRA adapters are excluded.

Retry only after the four exact blockers in `registration.json` have artifacts. Then run the
complete paired matrix with raw outputs and scores. This record leaves the generative arm blocked;
it is not a negative result and does not authorize the cross-repository comparison.
