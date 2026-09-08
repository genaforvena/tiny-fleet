# A01 implementation receipt — command-intents

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `20ac800b237eddef5bb618ca8a63028794b49062`
- UTC: `2026-09-08`
- Result: **READY FOR INDEPENDENT VPN VERIFICATION**

## Scope and result

This commit adds the offline-only parser/scorer, frozen CC0 command corpus,
deterministic baseline raw rows, registration/no-go document, and contract tests.
The parser only emits the ten declared read-only functions or `unknown`; it
performs no OS, model, network, or routing operation. The optional FunctionGemma
revision is explicitly unavailable because gated credentials are absent. No
model arm was attempted because C02–C08 and S01–S05 are not verified.

The baseline has exact heldout accuracy 120/120 and 0/50 unknown false accepts,
but its one-sided 95% false-accept upper bound is 5.8155%, so it does not clear
the preregistered <=1% rare-error gate. With no observed deterministic-baseline
headroom and insufficient rare-error evidence, the bounded verdict is
`NO_GO_BASELINE_DOMINANT`; no pilot or deployment was run.

## Commands and artifacts

```text
rtk proxy .venv/bin/python scripts/applications/build_command_intent_corpus.py
exit 0
rtk proxy .venv/bin/python scripts/applications/command_intents.py --phase baseline --run-dir runs/applications/command-intents/baseline-20260908 --manifest corpus/applications/command-intents/manifest.json
exit 0
rtk proxy .venv/bin/python scripts/test_app_command_intents.py
exit 0 (7 tests)
```

- `docs/task-receipts/A01-check-20260908.txt` — stdout/stderr, SHA-256 `d1b72ce42cfd1df4c3900549070f8ce83790347381b130ae4da60eb03a876483`
- `runs/applications/command-intents/baseline-20260908/regex-grammar-raw.jsonl` — SHA-256 `260b45ad1e2435aaae91cb4e7bf1d3d688c16394a9393ea5f7c6464327bf7aff`
- `runs/applications/command-intents/baseline-20260908/summary.json` — SHA-256 `b7c501c2858831d65236bf9c76aadd750eb26ff0ec519139a838907ae9b71f5f`

`git diff --check` exited 0 before the source commit.

## Exact next action

VPN checks out `20ac800b237eddef5bb618ca8a63028794b49062` in isolation, reruns
the test and baseline into a new temporary directory, recomputes the summary,
inspects source-family splits and raw rows, and adds an unseen negative case.
It must record PASS, FAIL, or BLOCKED in `A01-verification.md`; it must not
score into the author run directory.
