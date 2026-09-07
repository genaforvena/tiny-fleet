# Frozen external-repository sample

Status: **frozen sample; analysis not run**  
Freeze date: 2026-09-07  
Study: `tinyfleet-architecture-drift-completion`

This directory freezes the bounded `lte-workstation` comparison sample required by
`docs/cross-repository-drift-protocol.md`. It does not claim an architectural-drift
finding.

## Selection

- Repository: `/home/mesh-home/lte-workstation`
- Public origin recorded in the repository metadata: `github.com/genaforvena/lte-workstation`
- License evidence: `LICENSE`, CC0 1.0 Universal, present and unchanged in both snapshots
- Old snapshot: `2dc867eed5d128beeb69ca2e818f291ab76ea895`
- New snapshot: `82c096be8bffc04aa56867c12d6292134f338662`
- Selection rule: the complete set of tracked paths changed by the parent-to-child pilot
  window, restricted to text shell/test paths; retain `LICENSE` as the license basis.

The selected changed paths are `scripts/mesh-board`, `scripts/mesh-dispatch`,
`scripts/mesh-task`, and `scripts/test-mesh-board`. The two new paths are absent from the
old snapshot and are recorded as such in `sample-manifest.json`.

## Reproduction

Run from `/home/mesh-home/tiny-fleet`:

```bash
git -C /home/mesh-home/lte-workstation cat-file -e \
  2dc867eed5d128beeb69ca2e818f291ab76ea895^{commit}
git -C /home/mesh-home/lte-workstation cat-file -e \
  82c096be8bffc04aa56867c12d6292134f338662^{commit}
git -C /home/mesh-home/lte-workstation diff --name-status \
  2dc867eed5d128beeb69ca2e818f291ab76ea895 \
  82c096be8bffc04aa56867c12d6292134f338662
```

The manifest stores Git blob IDs, sizes, and SHA-256 hashes of each available selected
file at each snapshot. No source copy is redistributed in this freeze artifact; the
immutable source remains addressable in the local Git object database.

