# A00 verification receipt — FAIL

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `6e394e48e65fb07e8ad495c0bd900cd51a2998c7`
- Verification receipt base revision: `b9166d34f69e7b812955a8d6b58dea88ebd5b620`
- UTC: `2026-09-08`
- Result: **FAIL — gate remains open.**

## Independent checkout and commands

The submitted source revision was checked out detached at
`/tmp/tinyfleet-a00v-worktree.rg6cDw`. All verifier outputs are in the new
temporary directory `/tmp/tinyfleet-a00v-output.QINSln`; no author run
directory was replayed or modified.

1. The declared command first exited `127` because a fresh worktree has no
   `.venv`. That captured stderr is
   `/tmp/tinyfleet-a00v-output.QINSln/test-pass.txt`, SHA-256
   `48bb8abdd3d09a167f1d4a72e8173232d89c48cf54e873c3e6d7916f462e7837`.
   I then exposed the already-installed interpreter to the isolated checkout
   through its local `.venv` symlink and reran the exact command.
2. `rtk proxy .venv/bin/python scripts/test_application_screen.py` exited `0`.
   Output: `/tmp/tinyfleet-a00v-output.QINSln/test-restored-pass.txt`;
   SHA-256 `85078c38fa46ea226ab5b345e21b84ed9e378963fbb552f8ad0bf4bf16ad6a25`.
3. `rtk proxy .venv/bin/python scripts/application_screen.py --registry runs/applications/registry.json --validate`
   exited `0`. Output:
   `/tmp/tinyfleet-a00v-output.QINSln/validate-pass.txt`; SHA-256
   `9c3ec54de3f528c086d07902bb4901f32e0b14b4eec795d2ba80bdffde181532`.
   It reported ten applications and `status: valid`.
4. Deliberate isolated mutation: changed the validator's load-bearing
   `gpu_minutes != 30` condition to `gpu_minutes != 31`. The test command
   exited `1`, including failures of the registry and no-go validation paths.
   Output: `/tmp/tinyfleet-a00v-output.QINSln/mutation-fail.txt`; SHA-256
   `52cb60c6126f110d4c5e5a4262215d705a995818377eda489a08526e33311187`.
   The source was restored, after which the exact test command exited `0`.

## Failed acceptance predicates

1. A00 requires exact **data-license** contracts. Each registry application
   supplies only `source.url` and `source.license`; several values explicitly
   defer model/data licensing until a later run. There is no `data_license`
   field and `validate_registry` does not require one. Thus the registry does
   not freeze the required data contract before scoring.
2. The implementation receipt claims the test-output SHA-256 is
   `85078c38fa46ea226ab5b345e21b84ed9e378963fbb552f8adbf4bf16ad6a25`.
   Independent execution twice produced
   `85078c38fa46ea226ab5b345e21b84ed9e378963fbb552f8ad0bf4bf16ad6a25`.
   The receipt hash is therefore incorrect, even though the test exits zero.

The ten IDs, baseline/gate/cost fields, exact 299/598 arithmetic, offline
validator behavior, and mutation sensitivity were independently observed; they
do not cure the missing data-license contract or inaccurate receipt hash.

## Exact next action

`haunt` must submit a corrected commit that adds and validates an explicit
per-application data-license field (with tests), corrects the implementation
receipt hash, and preserves the offline/reproducible contract. Then `vpn`
resumes this same gate against that commit and repeats the independent checks.
