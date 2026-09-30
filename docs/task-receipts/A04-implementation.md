# A04 implementation receipt — local cited runbook retrieval

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-09`
- Scope: `scripts/applications/runbook_retrieval.py`, `scripts/test_app_runbook_retrieval.py`, `corpus/applications/runbook-retrieval/manifest.json`, `runs/applications/runbook-retrieval/`, `docs/applications/runbook-retrieval.md`
- Primary precedent: <https://deepmind.google/models/gemma/embeddinggemma/>

## Result

READY FOR INDEPENDENT VPN VERIFICATION. This implementation is an offline,
deterministic BM25 baseline over frozen CC0-1.0 manual fixtures. It returns at
most five paragraph IDs and uses an empty list as explicit no-answer. A scorer
rejects duplicate, malformed, or out-of-manual citations. No model, network,
generation, training, or deployment was used.

The heldout screen contains 160 cases from disjoint manual/source families: 100
answerable and 60 unanswerable near matches. BM25 retrieved a gold paragraph
for 100/100 answerable cases (Recall@5 = 1.00), and falsely accepted 0/60
no-answer cases. The exact one-sided 95% upper bound is 4.8703%, below the
preregistered 5% limit. Since the strongest simple baseline already meets the
quality/no-answer boundary and C02-C08 plus S01-S05 are unverified, the result
is the evidence-backed `NO_GO_BASELINE_DOMINANT`; no model pilot was justified.

## Verification performed

```text
rtk proxy .venv/bin/python scripts/test_app_runbook_retrieval.py — exit 0 (5 tests)
rtk proxy .venv/bin/python scripts/applications/runbook_retrieval.py --phase baseline --run-dir runs/applications/runbook-retrieval — exit 0
rtk proxy .venv/bin/python scripts/application_screen.py --registry runs/applications/registry.json --validate — exit 0 (10 applications)
git diff --check — exit 0
```

The load-bearing no-answer predicate was mutated from `score > 0` to `score >= 0`:
the test suite went red (2 failures, including false no-answer retrieval and
loss of the no-go verdict), then the predicate was restored and the suite
returned exit 0.

Artifact SHA-256 values after the final baseline run:

- `corpus/applications/runbook-retrieval/manifest.json` — `ccea4572ffa535a36ec41774d4c16769c4c7291026af96f5fdeba70c920beefa`
- `runs/applications/runbook-retrieval/bm25-raw.jsonl` — `199639828a2927b77e01513253da2e0c04ff9c9f2c6ca71094a02fd5583b07d7`
- `runs/applications/runbook-retrieval/summary.json` — `b416a05d41cf8353ccb6fc04f43d797d388608e5931e20d0b16ef4888c84cbab`

## Exact next action

VPN must inspect this submitted commit in an isolated checkout, rerun the test
and baseline into a new temporary directory, recompute counts/hashes, mutate
the no-answer threshold to observe FAIL then restore PASS, and inspect an unseen
unsupported query before writing `A04-verification.md`.
