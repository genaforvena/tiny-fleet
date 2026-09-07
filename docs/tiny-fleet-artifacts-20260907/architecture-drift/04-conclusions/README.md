# Architecture-drift bundle and conclusions

Status: **PRELIMINARY / STRUCTURAL PLUS REPOSITORY-NATIVE SMOKE; three declared gates remain blocked**

This bundle closes the packaging step for the frozen external sample. It does
not upgrade the Step 3 result into a semantic, behavioral, or generative
finding. The only supported statement is descriptive: the admitted sample
changed from three to five files and from 274,906 to 284,322 bytes between the
two pinned revisions, with two additions and two modifications.

## Inputs

- sample manifest: `../02-external-sample/sample-manifest.json`
- manifest SHA-256: `c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`
- analysis commit: `860b008` (`Run frozen external architecture drift analysis`)
- analysis-input refresh: `a2ac5d5` (`docs: capture frozen architecture drift analysis inputs`)
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

## Supply decision

No missing arm is synthesized from the host. The next admissible run must provide a separately
pinned runtime and either an old-snapshot-equivalent board test or a preregistered comparable
replacement; lexical and generative arms remain blocked until their tokenizer/dictionary and
prompt/seed/model/scorer/raw-output records exist. Any continuation must retain manifest hash
`c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7` and commits `2dc867e` and
`82c096b`.
