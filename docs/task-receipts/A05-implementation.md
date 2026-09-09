# A05 implementation receipt — duplicate issue detection

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `6fb49c8a3ef88dd9a6e3124c7913a7265a960641`
- UTC: `2026-09-09`
- Scope: `scripts/applications/duplicate_incidents.py`, `scripts/test_app_duplicate_incidents.py`, `corpus/applications/duplicate-incidents/`, `runs/applications/duplicate-incidents/`, `docs/applications/duplicate-incidents.md`, `docs/task-receipts/A05-check-20260909.txt`
- Primary precedent: <https://deepmind.google/models/gemma/embeddinggemma/>; model card <https://huggingface.co/google/embeddinggemma-300m>

## Result

READY FOR INDEPENDENT VPN VERIFICATION. The implementation adds a frozen
CC0-1.0 synthetic incident-family/time-period split, 120 independent heldout
cases (100 positive matches and 20 explicit no-match cases), a hard-negative
candidate in each positive case, typed abstention, and deterministic
normalized-hash, character 3-gram cosine, and BM25 baselines. Raw JSONL
predictions and a summary preserve candidate-retrieval recall, pair precision
and recall, false acceptance, abstention coverage, latency, and source-family
unit. Malformed, unknown-candidate, duplicate-candidate, cross-split and
inconsistent-abstention inputs are rejected.

EmbeddingGemma is pinned as a feasibility precedent at
`google/embeddinggemma-300m`, revision
`57c266a740f537b4dc058e1b0cda161fd15afa75`, under Gemma Terms of Use. Its
gated weights were not downloaded. all-MiniLM and model arms are explicitly
unavailable until C02-C08 and S01-S05 verification completes; no model score,
pilot or deployment was run.

The deterministic result is `INCONCLUSIVE`: normalized hashing has pair
precision 1.00, pair recall 0.80, candidate-retrieval recall 1.00 and 33.3%
abstention; character n-gram and BM25 each have pair precision 0.8333 and
falsely accept all 20 no-match cases. The preregistered model gate is therefore
not evaluated and no scientific model benefit is claimed.

## Verification performed

```text
rtk proxy .venv/bin/python scripts/test_app_duplicate_incidents.py — exit 0 (6 tests)
rtk proxy .venv/bin/python scripts/applications/duplicate_incidents.py --phase baseline --run-dir runs/applications/duplicate-incidents — exit 0
rtk proxy .venv/bin/python scripts/application_screen.py --registry runs/applications/registry.json --validate — exit 0
git diff --check — exit 0
```

Check output: `docs/task-receipts/A05-check-20260909.txt`, SHA-256
`4b1f0be4c49f6f7b42d9fecb4e7359d1ba782c7497336d6d5dd17e67e9095865`.

Artifact SHA-256 values before commit:

- `corpus/applications/duplicate-incidents/manifest.json` — `333182515d1011a50749c32d941d7da7e3b2a32bab2e3675567e5ab3aa208aff`
- `runs/applications/duplicate-incidents/bm25-raw.jsonl` — `fae2c57bbe3e49e6ae69379bf5d609bd72d9cd1677392280793cd61d72e5f116`
- `runs/applications/duplicate-incidents/character-ngram-raw.jsonl` — `0e032154eeac9f234efa48a35cecc6e38e6713e9df0abc9dbf13e1a46bc97683`
- `runs/applications/duplicate-incidents/normalized-hash-raw.jsonl` — `ddf34d546572020a1e89118973c55a679c30067ae9a29736cd7d32701d29221d`
- `runs/applications/duplicate-incidents/summary.json` — `081346815da1b858d66983257ab45e9da30fa63d6d96f2bcb8f98876ce626603`

## Exact next action

VPN must inspect the submitted commit in an isolated checkout, rerun the test
and baseline into a new temporary directory, recompute counts/hashes, mutate
one load-bearing abstention or candidate-validation behavior to observe FAIL
then restore PASS, and inspect an unseen hard negative before writing
`A05-verification.md`.
