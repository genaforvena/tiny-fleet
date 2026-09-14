# Reader registration-status correction — 2026-09-14

Task: `chat-review-confirmatory-v1-registration-status-disclosure-20260914/correct-registration-status-wording`.

The reader conclusions now report the frozen generation registration's exact value,
`status=frozen_pending_independent_verification`, and retain
`comparison_authorized=false`. The comparison remains publication-blocked pending resolution of
the independent-verification and authorization state. The registration and raw data were not
modified. The earlier [sample-scope receipt](haunt-reader-sample-scope-disclosure-20260914.md)
remains untouched.

Evidence SHA-256:

- Corrected [reader conclusions](../confirmatory-v1-reader-conclusions-20260914.md):
  `a376c97beb40ca5ed8718abe223045ad47c6bcfdb1317081dea0cffb5191e54d`
- Frozen [generation registration](../../runs/drift-confirmatory-v1/registration.json):
  `f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`

Focused validation passed: the registration JSON has the stated status and false authorization
flag; the reader report matches both values, retains its blocked/generative-only scope, and every
relative Markdown link resolves. `git diff --check` passed for the report correction and this
receipt.
