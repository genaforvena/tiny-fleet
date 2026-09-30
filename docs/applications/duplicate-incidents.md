# A05 duplicate issue detection

Status: offline baseline screening, 2026-09-09. This is an application
hypothesis, not a measured Tiny Fleet model benefit.

The CC0-1.0 fixture in `corpus/applications/duplicate-incidents/manifest.json`
contains 132 synthetic incident records and 132 tickets. The 120 heldout cases
are 100 positive matches and 20 explicit no-match cases, each with a unique
ticket source family. Incident families and time periods are split by
development, validation and heldout partitions. Candidate lists include a
hard negative with the same broad service-error symptom; shared symptoms alone
never establish duplicate identity.

The baseline runner records raw predictions for normalized hashing,
character 3-gram cosine and BM25. It represents no match as
`{"incident_id": null, "abstain": true}` and retains candidate scores. It
rejects unknown candidates, inconsistent abstention, duplicate candidates,
malformed tickets and cross-split cases. all-MiniLM is recorded as unavailable
because the C02-C08 and S01-S05 verification gates are not complete; no model
score or pilot was run.

EmbeddingGemma is recorded as a feasibility precedent, not as our result:
[Google DeepMind describes it as a 308M-parameter on-device embedding model](https://deepmind.google/models/gemma/embeddinggemma/),
and the [Hugging Face model card](https://huggingface.co/google/embeddinggemma-300m)
identifies `google/embeddinggemma-300m`, Gemma Terms of Use and the pinned
revision `57c266a740f537b4dc058e1b0cda161fd15afa75`. Its gated weights were not
downloaded.

Run the deterministic screen with:

```text
rtk proxy .venv/bin/python scripts/test_app_duplicate_incidents.py
rtk proxy .venv/bin/python scripts/applications/duplicate_incidents.py --phase baseline --run-dir runs/applications/duplicate-incidents
```

The current baseline artifact is `INCONCLUSIVE`: normalized hashing has perfect
precision but abstains on paraphrases, while lexical baselines over-accept the
hard negatives. A `NO_GO_BASELINE_DOMINANT` result is reserved for a simple
baseline that meets pair precision >=95%, pair recall >=95% and false
acceptance <=5%; the model gate remains unevaluated. Any later model comparison must report pair precision and
recall gain at matched precision, candidate-retrieval recall, source-family
uncertainty, abstention coverage, and compute cost. No adapter is added to live
routing by this study.
