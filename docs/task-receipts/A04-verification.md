# A04 independent verification receipt — local cited runbook retrieval

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Source commit verified: `e00b532c5a60ae5e25d7a6362daaf98018daa68b`
- Verification checkout: detached worktree at `/tmp/tinyfleet-a04-verify.LomLKW`
- UTC: `2026-09-09`
- Verdict: **PASS** for the A04 acceptance predicates

## Scope and source inspection

The submitted commit contains exactly the seven A04 files: the BM25 implementation,
its five-test contract suite, the manifest, documentation, and baseline run outputs.
The implementation is offline and deterministic: no model download, network call,
generation, training, or deployment path is used. The CLI exposes `baseline`, while
`pilot` and `score` fail closed because their dependencies are not verified.

The manifest declares CC0-1.0 data, 162 unique manual families, and 162 cases:
160 heldout, 1 development, and 1 validation. The 160 heldout cases comprise 100
answerable and 60 unanswerable cases; no source family crosses splits.

## Independent verification

All commands ran from the detached verification checkout. Artifact-producing output
was written to the fresh directory `/tmp/tinyfleet-a04-run.p7sYm3`, not the submitted
`runs/` directory.

```text
rtk proxy python3 scripts/test_app_runbook_retrieval.py — exit 0 (5 tests)
rtk proxy python3 scripts/applications/runbook_retrieval.py --phase baseline --run-dir /tmp/tinyfleet-a04-run.p7sYm3 — exit 0
git diff --check — exit 0
```

The independently recomputed heldout counts are: 160 total, 100 answerable,
60 unanswerable, 100/100 Recall@5 hits, and 0/60 false accepts. The fresh baseline
reported `NO_GO_BASELINE_DOMINANT`, recall `1.0`, false-accept rate `0.0`, and the
one-sided 95% upper bound `0.04870291331009746` (4.8703%), below the preregistered
5% limit. The raw output hash is stable and matches the implementation receipt.

```text
ccea4572ffa535a36ec41774d4c16769c4c7291026af96f5fdeba70c920beefa  corpus/applications/runbook-retrieval/manifest.json
199639828a2927b77e01513253da2e0c04ff9c9f2c6ca71094a02fd5583b07d7  /tmp/tinyfleet-a04-run.p7sYm3/bm25-raw.jsonl
8c0a0665f7e4eff40cee1b0de161a9c7f6f54806ab7ca90ab95d0106023d5b04  /tmp/tinyfleet-a04-run.p7sYm3/summary.json
```

## Red gate and unseen negative

In the isolated checkout, the load-bearing retrieval predicate was mutated from
`score > 0` to `score >= 0`. The test suite went red with exit 1 and exactly two
failures: the explicit no-answer test retrieved `p-1`, and the baseline verdict
became `INCONCLUSIVE`. The predicate was restored; the same five-test suite then
returned exit 0.

An unseen unsupported query, `quantum entanglement failure`, against paragraphs
about service restart and health returned `paragraph_ids: []` and passed an explicit
empty-result assertion.

## Residual limitations

This PASS is limited to the stated A04 acceptance predicates. The fixtures are
generated frozen manual paragraphs, the model arms remain unavailable because C02-C08
and S01-S05 are unverified, peak RAM is unmeasured (`null`), and no live routing or
deployment capability is claimed.

## Remote containment

The verified source commit equals `origin/master`:

```text
e00b532c5a60ae5e25d7a6362daaf98018daa68b
```
