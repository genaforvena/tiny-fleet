# Local structural-drift experiment

Status: **preliminary, descriptive only**. No behavioral, semantic, or generative drift claim.

Pinned tiny-fleet commits: old `4e87f2ee3644f53e2a9665195b9d6ddb933aa1d8`, new `b23fbf708b954cbf5462ebcd2d7ef50036a3fb1d`. The extractor reads immutable Git blobs, not the dirty working tree. `manifest.json` records 12 → 306 included text paths, 82,150 → 1,454,580 included bytes, 294 added paths, four changed paths, zero deleted paths, and zero identical-blob renames. Python modules grew 6 → 79, but the single static local import edge persisted without addition or removal; neither snapshot had a Python parse failure. Excluded path counts are 13 → 467; generated run/corpus/adapter paths are excluded, but source, configuration, tests, and documentation share the included denominator. `structural.tsv` gives the old/new counts and path deltas; `old-files.tsv`, `new-files.tsv`, and the two Python edge tables preserve the observed inputs.

`python-edge-delta.tsv` retains a header-only zero-delta result for this
pair. `old-python-edges.tsv` and `new-python-edges.tsv` each name the same
`scripts/router.py` → `scripts/operator_policy.py` static import. Endpoint
hashes for any nonzero delta are selected from the corresponding old/new
included inventory; the positive regression creates immutable Git commits
with one added and one removed local edge and checks both hashes.

Controls: `identity-control/manifest.json` compares the new commit with itself and reports zero path and edge deltas; `scripts/test_drift_extract.py` exercises changed-in-place content, duplicate identical-blob rename matching, exclusions, local import additions, and identity. `scripts/test_drift_edge_delta.py` exercises one added and one removed edge, snapshot-specific endpoint hashes, external import exclusion, parse-failure disclosure, repeat byte identity, and a header-only identical-snapshot delta. The larger path/byte counts establish repository growth under the stated filter, not architectural meaning. No repository-native behavior, independent external sample, leakage validation, model output, or generalization result was produced by this run. The registered cross-repository and confirmatory studies retain their separate gates.

Reproduce with the commands in `README.md` under “Reproduce the structural slice”. The exact next scientific step is a pinned external-repository corpus with repository-specific license/secret filtering and unit maps, then paired native behavioral checks; this local manifest cannot be promoted to that gate.
