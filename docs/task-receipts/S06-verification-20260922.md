# S06 verification receipt — runner contract and bounded smoke

Result: `VERIFIED / IMPLEMENTATION-CLOSED` (2026-09-22T07:45:00Z)

- Task: `tinyfleet-publication-science-20260908/run-paired-replications`
- Actor: `tiny-fleet`
- Repository: `/home/mesh-home/tiny-fleet`
- Registration: `runs/fleet-study-v1/registration.json`

## Closed blocker

The 2026-09-11 typed `BLOCKED/dependency` recorded that `scripts/run_study_matrix.py`
exposed only `build_matrix` and had no CLI, no run-root handling, no backend
execution, and no raw prediction writer. That is no longer true: the module now
defines `main(argv)` with an argparse CLI, immutable-registration validation,
non-overwriting run-root handling, the frozen five-arm execution path
(`run_registered_arm`), raw per-case prediction tapes, and resource/timing
capture via `wait_for_gpu`.

## Verification performed

1. Plan-only validation of the frozen registration, exit 0, 15 rows
   (5 arms x seeds 17/29/43), no GPU consumed:

   ```text
   rtk proxy .venv/bin/python scripts/run_study_matrix.py \
     --registration runs/fleet-study-v1/registration.json \
     --run-root runs/fleet-study-v1 --plan-only
   exit=0; rows=15
   ```

2. Bounded verification-only smoke in an isolated run root, fake backend,
   exit 0:

   ```text
   rtk proxy .venv/bin/python scripts/run_study_matrix.py \
     --registration runs/fleet-study-v1/registration.json \
     --run-root runs/verification-s06-20260922 \
     --verification-only --max-cases 2 --max-train-steps 2
   exit=0; rows=15; prediction_tapes=15; files=46
   ```

   Summary artifact: `runs/verification-s06-20260922/smoke-summary.json`,
   schema `tiny-fleet.study-matrix-smoke/v1`,
   `verification_only=true`, `training_executed=false`.

3. Immutability guard exercised: the runner refused to write into the frozen
   study root (`refusing to overwrite non-empty run root:
   runs/fleet-study-v1`) because that root holds registration, corpus, and
   adapter inputs. The smoke therefore landed in
   `runs/verification-s06-20260922`, leaving the frozen registration and the
   `seed-17/` training artifacts untouched.

## Honest scope boundary

This receipt verifies the runner contract and the plumbing of every registered
arm. It is explicitly NOT a scientific result: no real training ran, no GPU was
consumed, and the fake backend produced placeholder predictions. It does not
satisfy `tinyfleet-publication-science-20260908/run-paired-replications` itself,
which still requires the live five-arm x three-seed matrix on the real backend
with the cached base model and GPU headroom.

## Exact next action

Re-run the resource preflight to confirm free VRAM, then execute the full
matrix with the real backend:

```bash
rtk proxy .venv/bin/python scripts/run_study_matrix.py \
  --registration runs/fleet-study-v1/registration.json \
  --run-root runs/fleet-study-v1
```

That run must capture all five frozen arms x seeds 17/29/43, raw rows,
resource/timing totals, validation, and a new implementation receipt. It must
not be reported as a study result until the real backend has executed every
row.
