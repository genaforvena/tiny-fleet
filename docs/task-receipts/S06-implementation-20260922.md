# S06 implementation receipt — typed BLOCKED/capability

Result: `BLOCKED/capability` (2026-09-22T09:44:00Z)

- Task: `tinyfleet-publication-science-20260908/run-paired-replications`
- Actor: `tiny-fleet`
- Repository: `/home/mesh-home/tiny-fleet`
- Registration: `runs/fleet-study-v1/registration.json`
- Source revision: `19e31fe` (guarded `--resume`), `31159d2` (S06 verification receipt)

## Exact blocking reason

The live matrix died twice with exit `137` (SIGKILL) under host RAM exhaustion.
At the kills: 28.1/32 GiB used, swap fully exhausted (`8191/8191` MiB), and only
~3.9 GiB available. The runner process itself reached ~3.2 GiB RSS, which the
host could not absorb alongside the resident mesh consumers (mesh-voice-clone
3.3 GiB, mesh-room-gigaam 1.7 GiB, llama-server, and several omp/mind processes).

A compounding defect was mine: the first launch was backgrounded and, when it
appeared stalled, I relaunched it without first confirming the original had
exited. Two `run_study_matrix.py` processes then ran concurrently against the
same `--run-root`. The older orphan (1.87 GiB, 34m45s elapsed) was stopped; no
shared mesh consumer was touched.

## Run-root integrity

Both processes were writing the same root, so the bundle was re-audited after
the duplicate was stopped. `_row_complete` reports exactly the pre-run state,
and file sizes match the earlier inventory:

- `seed-17/base/base/predictions-base.jsonl` 249,047 B — 400 records, complete
- `seed-17/prompt_only/prompt-only/predictions-prompt-only.jsonl` 525,420 B — 400 records, complete
- `seed-17/pooled_adapter/pooled-lora/predictions-pooled-lora.jsonl` 366,386 B — 400 records, complete
- `seed-17/simple_router/specialist__toy_passage_ppl/predictions-...jsonl` 43,120 B — incomplete, no summary

No file was corrupted or truncated by the concurrent writers, and the 1,200
complete records are preserved. No seed-29 or seed-43 rows exist yet.

## Capability fix delivered (not blocked)

The original S06 blocker — the runner refusing any non-empty run root with no
resume path — is fixed and tested:

- `19e31fe` `feat: add guarded resume for the immutable fleet-study matrix`
- `scripts/test_run_study_matrix.py`: 13 tests, exit 0, including
  `test_resume_keeps_complete_rows_and_refuses_foreign_entries`, which asserts a
  complete row is byte-identical after `--resume` and that foreign entries abort.
- `31159d2` closes the 2026-09-11 typed block: the CLI, run-root handling,
  five-arm execution path, raw prediction writer, and resource capture are all
  present; `--plan-only` renders the frozen 15-row matrix at exit 0.

## Commands and exit codes

```text
rtk proxy .venv/bin/python scripts/run_study_matrix.py \
  --registration runs/fleet-study-v1/registration.json \
  --run-root runs/fleet-study-v1 --resume
exit=137 (SIGKILL, host RAM exhaustion)
```

```text
rtk proxy .venv/bin/python scripts/test_run_study_matrix.py
exit=0; tests=13
```

## Exact retry command

Only after host RAM recovers above ~10 GiB available and swap drains:

```bash
cd /home/mesh-home/tiny-fleet && rtk proxy .venv/bin/python scripts/run_study_matrix.py \
  --registration runs/fleet-study-v1/registration.json \
  --run-root runs/fleet-study-v1 --resume
```

`--resume` keeps the three complete seed-17 arms verbatim and runs only the
missing rows, so no collected evidence is re-spent. This block is a resource
result, not a scientific one; no arm, seed, or metric has been selected or
removed.
