# External sample freeze consumed — 2026-09-13

- Actor: haunt
- Repository: `/home/mesh-home/tiny-fleet`
- Task: `tinyfleet-architecture-drift-review-20260907/freeze-independent-repository-sample`
- Submitted source revision: `ecac5eb45abad2dfc4fec6503b0ca3d497147bd8`
- Verification time: `2026-09-13T13:12:43Z`
- Result: frozen external sample is committed, pushed, and consumed as the exact input contract for downstream work; no comparison was run.

## Frozen scope

The source commit contains the amended protocol, the D04 plan-row amendment, the v2 three-repository
sample manifest, its availability and README records, and the prior prerequisite-unblock receipt.
The manifest pins `pallets/flask`, `psf/requests`, and `pydantic/pydantic`, each under a distinct
owner namespace, with six immutable commits. It labels itself `frozen-before-comparison`. The
protocol and plan name this exact manifest; the legacy local-pilot manifest remains unchanged.

The sample is now consumed as the fixed input registry and comparison firewall for the reopened
freeze step. The still-open behavioral preflight, generative registration, and blinded
ground-truth labels remain arm gates. They are not silently treated as zero or as permission to
run a partial comparison.

## Verification

- `rtk proxy python3 -m json.tool .../02-external-sample-v2/sample-manifest.json` — exit 0.
- Manifest assertions: exactly three canonical upstreams, three owner namespaces, six 40-character
  commit IDs, no forks or archived repositories, and frozen-before-comparison status — exit 0.
- `rtk proxy sha256sum` confirmed the legacy manifest remains
  `c432cb6e3dabb4b7b0cfc4584fb5f55054cb8b7c8958173d0578d1e374b37dc7`; the new manifest is
  `07c2b0b34f204b2ef549ecf1aa7c581fb7c03af1dbcb8e4a9b4581d392b3ee59`, protocol is
  `76b62091b80109bfd8fd0002882b2b297a2fdb0cfff14f7347bbedb529b97466`, and amended plan is
  `c767991144054e827fd808259cd5a1a3ff550a42867f760be37d434b613504c9`.
- `rtk git diff --check` over the scoped amendment/freeze — exit 0.
- Commit `ecac5eb45abad2dfc4fec6503b0ca3d497147bd8` pushed to `origin/master`; `git ls-remote`
  confirmed the same remote revision.
- Captured command results: `docs/task-receipts/haunt-architecture-drift-sample-freeze-checks-20260913.stdout`
  (SHA-256 `198a03677bf494b54ff0767763fd3cb643b34cb58a565c4008f7b60dc72880bd`).
- Stderr was empty. No cross-repository comparison was run.

## Next action

Close the freeze step with this receipt. Keep `run-cross-repository-analysis` unopened for
comparison until the separate arm-specific preconditions are satisfied; in particular, no
behavioral, generative, or ground-truth score may be computed from the current artifacts.
