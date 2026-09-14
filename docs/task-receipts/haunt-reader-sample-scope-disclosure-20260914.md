# Reader sample-scope disclosure — 2026-09-14

Task: `chat-review-confirmatory-v1-sample-scope-disclosure-20260914/amend-reader-report`.

The reader conclusions now state that the six HTTPX/attrs/pytest snapshots are a distinct frozen
sample (`runs/drift-confirmatory-v1/registration.json`), separate from the protocol-v1 registered
Flask/Requests/Pydantic sample in `02-external-sample-v2/sample-manifest.json`. The report states
that the HTTPX/attrs/pytest run does not replace or amend the registered study, limits its available
result to descriptive generative evidence, and keeps publication blocked pending a versioned
protocol/registration update or a compliant run on the registered sample.

Evidence SHA-256:

- Amended reader report: `6c057173db798c1a310fd877be1477658d2ee9e436d73b372f91962e87831666`
- Distinct HTTPX/attrs/pytest registration: `f21f4b9afcce8146d4f67cc78c0f1041bcd467676ac3a5aad812476a6cbc60e8`
- Protocol-v1 Flask/Requests/Pydantic manifest: `07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59`
- Protocol text: `76b62091b80109bfd8fd0002882b2b297a2fdb0cfff14f7347bbedb529b97466`
- Generation registration still records `status=blocked-before-generation` and
  `comparison_authorized=false`: `157fb3351366e656760ff17bb1a1379607fcc8d14fdc3a83037dbc338c265de7`

Verification passed: `git diff --check` on the report; a targeted validator confirmed the two
registrations name the expected disjoint repository sets, the report includes the sample distinction
and blocked generative-only scope, and all cited report links resolve. The pre-existing edits to
`README.md` and `scripts/study_runner.py` were left untouched.
