# Tiny Fleet full re-audit — 2026-09-07

## Verdict

The repository is not fully complete. The core toy loop and the bounded operator policy are
working, and real LoRA adapters exist for the original toy domains plus persona/code. The
acceptance boundary is still open because several declared directions have only plans, summary
counts, or blocked artifacts rather than end-to-end evidence.

## Evidence checked

From `/home/mesh-home/tiny-fleet` at `38c8c3e6074048263208a92f3eee219e7d326854` (also
`origin/master`):

| Direction | Current evidence | Verdict |
|---|---|---|
| Original guitar/sourdough specialist loop | `scripts/fleet_benchmark.py --test`, 24/24; real adapter files and hashes | PASS for toy contract |
| Operator policy | `scripts/operator_policy.py --test`: held-out 41/41, adversarial 14/14, safety 8/8, mutation pass | PASS for bounded offline contract |
| Deep-evaluation contract | `scripts/test_deep_evaluation.py`: 6 tests; independent review confirms fail-closed artifact/leakage checks | PASS for validator scope; not a full study |
| Mood corpus / mood specialist | redacted mood train/heldout/adversarial files exist, but no mood adapter or complete mood benchmark artifact is present | OPEN |
| Persona/code corpus | manifest and redacted splits exist: 12/10 train rows, 4 heldout, 14 adversarial per domain | PRELIMINARY; too small for the declared claims |
| Persona/code LoRA | pinned SmolLM2-360M revision and two adapter directories; train/eval JSON says complete | REAL TRAINING ARTIFACT |
| Persona/code evaluation | held-out perplexity matrix exists, but adversarial rows are only reported as counts; no raw predictions, rubric, abstention decisions, repeated seeds, or prompt-only control | OPEN |
| Persona/code runner contract | `persona_code.py self-test` works only without `--manifest`, while the plan's command includes that option | CONTRACT BUG |
| Specialist routing/wiring | offline router covers guitar/sourdough; no verified persona/code or mood live route in this repository | OPEN |
| Architectural drift structural arm | frozen sample, structural outputs, pinned runtime and bounded behavioral smoke are checked and pushed | PASS / PRELIMINARY |
| Architectural drift lexical/concept arm | no pinned tokenizer, normalization contract, or versioned dictionary in the frozen bundle | BLOCKED |
| Architectural drift generative arm | no frozen prompts/seeds/scorer/model digests/raw outputs/uncertainty bundle | BLOCKED |
| BbyWVY-360M reproduction | notes exist; no reproducible model/runtime run bundle | OPEN |

## Verification run

The following commands were run fresh on 2026-09-07:

```text
.venv/bin/python scripts/fleet_benchmark.py --test       PASS (24/24)
.venv/bin/python scripts/test_deep_evaluation.py          PASS (6 tests)
.venv/bin/python scripts/operator_policy.py --test        PASS (41/41, 14/14, 8/8, mutation)
.venv/bin/python scripts/persona_code.py self-test         PASS (without manifest argument)
```

The repository was clean before this audit and `HEAD == origin/master` at the observed revision.

## Required closure order

1. Fix and test the persona/code runner contract; make evaluation emit raw held-out and
   adversarial predictions, rubric decisions, cardinality, and hashes.
2. Run repeated-seed base/persona/code and prompt-only controls, then obtain an independent
   witness result before routing either specialist.
3. Either train/evaluate the mood adapter with the same artifact contract or explicitly close the
   mood promise as blocked with the missing dependency/input named.
4. Build the real routing path for only verified specialists and test fallback/abstention on the
   live caller.
5. For architectural drift, preserve the existing preliminary result and add the pinned lexical
   and generative inputs; never promote the old headline cosine table without raw records.
6. Reproduce BbyWVY-360M only if the model/runtime can be pinned; otherwise keep the explicit
   blocked artifact rather than treating notes as completion.

No routing or substrate wiring was changed by this audit.
