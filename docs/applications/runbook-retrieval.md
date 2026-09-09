# A04 local cited runbook retrieval

Status: bounded BM25 baseline screen, `NO_GO_BASELINE_DOMINANT`.

This offline study uses generated CC0-1.0 manual paragraphs with frozen manual
source families. Heldout cases contain 100 answerable queries and 60
unanswerable near-match queries. The baseline returns up to five paragraph IDs;
an empty list is the explicit no-answer result. A citation is accepted only when
it is a paragraph in that case's manual, and citation existence is not treated as
support for an unanswerable query.

BM25 retrieved the supported paragraph for every answerable heldout query and
returned no citations for all 60 no-answer queries. The exact one-sided 95%
upper bound on no-answer false acceptance is `1 - 0.05**(1/60) = 4.87%`, meeting
the preregistered <=5% boundary. The simple baseline therefore leaves no
justified headroom for a model pilot; EmbeddingGemma is recorded as a pinned
candidate but was not downloaded or scored because C02-C08 and S01-S05 remain
unverified. Peak RAM is `null` because no resident model was used; CPU latency is
recorded in the run summary.

Reproduce with:

```bash
rtk proxy .venv/bin/python scripts/test_app_runbook_retrieval.py
rtk proxy .venv/bin/python scripts/applications/runbook_retrieval.py --phase baseline --run-dir runs/applications/runbook-retrieval
```
