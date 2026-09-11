# D01 implementation receipt — standalone drift extraction

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11T17:27:00Z`
- Scope: `scripts/drift_extract.py`, `scripts/test_drift_extract.py`,
  `docs/cross-repository-drift-protocol.md`

## Change

Added a dependency-free extractor accepting explicit repository path and immutable 40-hex old/new
commits. It reads Git objects directly, emits per-path blob hashes/bytes/units/language/status,
corpus and structural artifacts, counts generated/vendor/binary/encoding exclusions, identifies
renames by equal blob hash, and defines executable-position `mesh_refs` separately from prose.

## Verification

Command:

```text
rtk proxy .venv/bin/python scripts/test_drift_extract.py
```

- Exit: `0`
- Output artifact: `/tmp/d01-test.3LSdMH.txt`
- Output SHA-256: `1dce85386c40491a292edd4f2f827dc57e25ab900f0d9b7f5122e3df9e4a82cf`
- Result: `2 tests, OK`

The temporary fixture verifies hand-counted added/deleted/renamed text paths, generated/vendor/
binary exclusion accounting, corpus output, identical-snapshot zero delta, and operation using
only Git and Python. This is ready for independent `vpn` verification; it is not a D01-V result.

## Next action

Commit and push this scoped change, then submit
`tinyfleet-drift-science-20260908/verify-standalone-drift-extraction` to `vpn`.
