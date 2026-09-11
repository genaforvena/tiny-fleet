# D02 implementation receipt

- Actor: haunt
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `1da5e3c39a80cc29296cef8ffc6df6c8c113e5ab` (parent of the scoped implementation commit)
- UTC: 2026-09-11
- Scope: `scripts/drift_lexical.py`, `scripts/test_drift_lexical.py`, `docs/concepts-v1.json`

## Result

Implemented `drift_lexical.py --run-dir PATH`. It consumes D01's immutable extraction artifacts,
uses the declared Unicode word-regex tokenizer, records the dictionary SHA-256, reports rates per
10,000 included tokens, and stratifies `all`, `code`, `docs`, and `vendor` rows. `controls.tsv`
records no-change, duplication, rename, and shuffled-snapshot controls. Lexical output is
descriptive: rename is marked `LEXICAL_ONLY`, with no semantic conclusion.

## Verification

1. `rtk proxy .venv/bin/python scripts/test_drift_lexical.py` — exit 0, 5 tests OK.
   Captured stdout/stderr: `/tmp/tiny-fleet-D02-test-20260911.txt`
   SHA-256: `4e8428cdb3a17ca8a8f72ad5cdc0635500dcadac0c540be6472d07e84d6647e2`
2. Production CLI on D01 artifacts from immutable snapshots `220b2aa29c877c37134e5c4b4ee3343f1b2f69f3`
   and `1da5e3c39a80cc29296cef8ffc6df6c8c113e5ab` completed with exit 0.
   Output directory: `/tmp/tiny-fleet-d02-run.qe3v3V`
   `lexical.tsv` SHA-256: `580b6e8f0300bf4a87b435e464f0c16ae44e3afa7a24a072fd86ed480144e36d`
   `controls.tsv` SHA-256: `2f5867e1a2b438703fa9c6b0212efbf1c89be12cd269a3ef34e396bca9c9bd54`
   CLI JSON SHA-256: `6c4d9daa469e95bc09dd8f7e580692f306737ae9f3859790f4ab0f61f9d871c9`

## Next action

Submit this scoped commit to the independent VPN verification gate. VPN must rerun the test in an
isolated output directory, inspect the TSV artifacts, and apply its required mutation/negative case.
