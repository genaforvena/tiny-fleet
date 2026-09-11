# D03 implementation receipt — generative drift runner

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Task: `tinyfleet-drift-science-20260908/generative-drift-runner`
- Result: `PASS — submitted for independent vpn verification`

## Contract delivered

Added `scripts/drift_generate.py` and `scripts/test_drift_generate.py`, and documented the
offline generative fixture contract in `docs/cross-repository-drift-protocol.md`. The runner
freezes identical prompts, required `base`/`prompt-only`/`lora` arms, seeds, repetitions, model
digest, scorer digest, and input hashes. It writes one raw record for every declared key and fails
closed on missing arms, duplicate keys, snapshot-label swaps, contamination, and provenance/hash
mismatches. The fake backend is dependency-free, offline, and does not execute generated commands.

## Verification

Prescribed check:

```text
rtk proxy .venv/bin/python scripts/test_drift_generate.py
exit 0; Ran 3 tests; OK
stdout sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
stderr sha256: d197475089a819982f74366fd75d82d215e0cd54c04f92aba7ed1e6f73642e3a
```

`git diff --check` exited `0`. Source hashes before commit:

```text
scripts/drift_generate.py                  8dbd0fd55edaf4520b52526a994b12cd00633c8a7934fbebc89e5c9c9a952069
scripts/test_drift_generate.py             6a8cbf17ab0fa6f06cb001692009a9aba7d092ab723b6238bf9383b2d0dcaf31e
docs/cross-repository-drift-protocol.md    f4f9d0c2395bb2a7e20f5cb91cb3a09c9b7babf298c339636ae8d807b8dd016e
```

The fixtures verify the full 12-record three-arm matrix, all key/provenance digests, missing-arm
blocking, duplicate prompt detection, snapshot-label protection, and prompt contamination. Real
model execution remains outside this safe fixture and requires a separately pinned run.

## Scope and handoff

Only the three D03 source/test/protocol files and this receipt are intended for the implementation
commit. Submit to `vpn` for independent D03 verification; the original D03 task is eligible to
resume only after this prerequisite exists.
