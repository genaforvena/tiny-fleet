# Haunt receipt: final v2 gate audit — analysis remains blocked

Task: `tinyfleet-drift-prerequisites-20260913/final-v2-gate-audit-and-recovery`.

I reread the behavioral preflight, frozen generation registration, v2 runner/excerpt/scorer and
adapter receipts, objective D04 registration, and the independent D04-V receipt. I did not recover
`tinyfleet-architecture-drift-review-20260907/run-cross-repository-analysis` and ran no comparison.
The frozen protocol's behavioral and generative gates are not all evidenced.

**Behavioral gate — BLOCKED.** The six-snapshot preflight has two passing suites (Flask new and
Pydantic new) and four blocked arms: Flask old and Pydantic old fail before test collection on
Python 3.12 `ast.Str` deprecation under warnings-as-errors; Requests old has two HTTPS-fixture
failures because `pytest-httpbin` calls removed `ssl.wrap_socket`; Requests new has one mTLS test
failure caused by its expired fixture certificate. The raw logs are under
`runs/behavioral-preflight-v2/pytest/`. The preflight receipt's earlier prose said three pass and
three blocked, contradicting its own table and logs; that count is corrected in the current
receipt. Retry only after the affected four snapshot arms have valid, source-pinned historical
runtimes or independently reproduced compatible test fixtures, with complete logs and paired
old/new coverage.

**Generative gate — BLOCKED.** The original frozen `registration.json` remains byte-for-byte
unchanged (SHA256 `df8c67e0c2f4dd31fc673b8af1438d6c3496f79d90a436521b945a304d44fe02`) and still
contains null excerpt hashes, null scorer code revision, and null adapter map. Separate registered
artifacts now exist for the six excerpts, scorer, and six trained adapters; adapter registration
SHA256 is `3896fd9fd5df55775caf37fc6432d420ce97658967a8b7a3cce42b2c97671db7`. But the independent
v2 execution-artifact verification step is still active with owner vpn, and no complete assembled
162-record manifest or raw output tape exists. Retry after vpn posts a passing exact-hash
verification receipt; then build the manifest only from those verified frozen artifacts before
any inference.

**Ground-truth gate — PASS, narrow objective subset only.** The v2 registration, labels, and
validation hashes are `fef38fc39cdef05fdf2a1f916920b0bb70256ab70eaff6ada41df90ee0bc85fb`,
`51c2c0cb4c1976c4e5a4e013bb28d0d2e5b1e9cef8bf8be5e7693c40189a7b72`, and
`5d949126e8f590576e24585518d7dc33a04f91d995c7f49cf667bc0047cf0c48`. VPN's independent receipt
(`vpn-ground-truth-v2-independent-verification-20260913.md`, SHA256
`eaa78c63c40c26f3b1a071b68919411e5bd004a81200b1c0658f881bcc989e0e`) accepts three
source-backed interface labels only. It records zero semantic units reviewed, no semantic
generalization, and no cosmetic/no-change controls. Do not use these objective labels as semantic
ground truth or a substitute for missing behavioral outcomes. A future semantic comparison still
needs two independent blinded reviewers and control labels.

**Ordering limitation — OPEN.** The objective labels were frozen and a generic model smoke ran
before the six excerpts were selected. The selector did not access labels or scores, but neither
the label verifier nor this audit can certify unrecorded access history or restore strict temporal
blindness. A retry for confirmatory interpretation needs a newly frozen unseen sample with its
labels independently frozen before inference, or an independent review that explicitly resolves
this exact ordering limitation.

**Next events:** resolve the four behavioral snapshot blockers; receive vpn's v2 execution-artifact
verification receipt; create the exact verified generation manifest; resolve the sample ordering
limitation; then re-run this gate audit. Only if those gates pass may the original analysis task be
recovered. Until then, retain the typed blocker and do not compare.
