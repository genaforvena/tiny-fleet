# D01-V verification receipt — standalone drift extraction

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Source commit: `1a4308477ba458c797a1d6c33bec5b4008d695ed`
- Verification UTC: `2026-09-11`
- Verdict: **PASS** for the D01 acceptance predicates

## Independent commands and evidence

The source commit was checked out in an independent local clone at
`/tmp/d01-vpn-HCzZpS/clone`. A package-free virtual environment was created with
`python3 -m venv --without-pip .venv`; no mesh package or repository dependency was installed.

1. `rtk proxy .venv/bin/python scripts/test_drift_extract.py`
   - exit `0`
   - output: `2 tests, OK`
   - output SHA-256: `d5e5f4429fcde9b4b5e2d53546b22b93de074aa4832492e23ec893dc73045daa`
2. CLI reproduction over immutable commits:
   `.venv/bin/python scripts/drift_extract.py --repo <clone> --old 1a4308477ba458c797a1d6c33bec5b4008d695ed --new ca47ca91774d26beb3b4efb2f007582257599254 --run-dir <fresh-dir>`
   - exit `0`
   - emitted `old-files.tsv`, `new-files.tsv`, both corpus files, `structural.tsv`, and `manifest.json`
   - manifest SHA-256: `eefbd05be2298f5d80679f98330f9aa1a35aa4cd9808eeccb16be62e6a14f025`
   - manifest reports old `207` included / `4` excluded / `2135146` bytes and new `213` included / `4` excluded / `2151008` bytes
3. Independent TSV recomputation with `awk` matched those included/excluded counts and byte totals exactly.
4. Identical snapshot CLI run with old=new `1a4308477ba458c797a1d6c33bec5b4008d695ed` returned exit `0` and delta:
   `added_text_paths=0`, `deleted_text_paths=0`, `renamed_text_paths=0`, `changed_text_paths=0`.
   - identical manifest SHA-256: `c3a9c489acc9ba3c902af831a1ffcf454f647c1441c960515d734725435ca38f`
5. Negative immutable-input case using `--old deadbeef` returned exit `1` with
   `ValueError: commit must be an immutable 40-hex object id`.

## Acceptance and limitation

The fixture hand-counts added/deleted/renamed text, generated/vendor/binary exclusions, corpus
membership, and identical-snapshot zero change; it passes without mesh installation. The
implementation receipt's claimed positive fixture was independently rerun, and the invalid
commit negative case was added. `structural.tsv` currently leaves its old/new columns blank for
delta metrics even though `manifest.json` and the per-file TSVs retain the measured values; this
is a presentation limitation outside the D01 acceptance predicate.

