# Architecture-drift bundle and conclusions

Status: **PRELIMINARY / STRUCTURAL ONLY; three declared arms are blocked**

This bundle closes the packaging step for the frozen external sample. It does
not upgrade the Step 3 result into a semantic, behavioral, or generative
finding. The only supported statement is descriptive: the admitted sample
changed from three to five files and from 274,906 to 284,322 bytes between the
two pinned revisions, with two additions and two modifications.

## Inputs

- sample manifest: `../02-external-sample/sample-manifest.json`
- manifest SHA-256: `c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`
- analysis commit: `860b008` (`Run frozen external architecture drift analysis`)
- old revision: `2dc867eed5d128beeb69ca2e818f291ab76ea895`
- new revision: `82c096be8bffc04aa56867c12d6292134f338662`

## Bundle contents

- `repository-manifest.json` — the frozen sample binding and arm statuses.
- `cross-repository-report.md` — the comparison report, limited to the
  structural estimand.
- `conclusions.md` — the human-readable conclusion and non-conclusions.
- `limitations.md` — coverage loss and exact blockers.
- `verification-ledger.tsv` — commands and observed checks; 10 manifest rows,
  of which 8 carry blob/size/SHA-256 records and 2 are intentional absences.
- `checksums.sha256` — SHA-256 records for raw inputs and reports.
