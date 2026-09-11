# tiny-fleet

Can you build a **fleet of tiny specialist models** — each one knowing
something well — plus a router that knows which one knows what?

This repo explores that question at the smallest practical scale:
a shared 360M base ([SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)),
one LoRA adapter per specialty, and an embedding-centroid router with an
abstain path. The whole thing trains in minutes on one RTX 3060.

It started from testing
**[BbyWVY-360m](https://huggingface.co/StarpowerTechnology/BbyWVY-360m)**
(see `docs/bbywvy-360m-notes.md`) — a 360M model tuned for one chat
identity on a narrow corpus. The question was whether that recipe
extrapolates to a fleet. The reproducible claim is currently limited to the
bounded offline contract benchmark below; several older live-model and drift
results remain historical or untested (see `docs/evidence-status.tsv`).

## Publication status

The evidence ledger is the source of truth for reader-facing claims. The
offline router/operator benchmark is verified-bounded (`24/24`); the specialist
perplexity table, most drift numbers, weekly tracking, zero-latency wording, and
the action example are not publishable findings at this revision. They are
labelled as historical, untested, or failed-control below rather than presented
as current evidence.

---

## Architectural drift — measuring how a codebase evolves

The fleet's latest experiment: **can two tiny models, trained on different
snapshots of the same codebase, express the architectural drift between those
snapshots?**

The repository previously reported the following exploratory comparison. Its
supporting evidence is marked `historical-unreproduced` or `failed-control` in
`docs/evidence-status.tsv`; no architectural or semantic drift finding is
claimed here.

We took two snapshots of [lte-workstation](https://github.com/genaforvena/lte-workstation)
(June 15 vs September 3, 2026 — 807 → 4,276 commits), extracted version-specific
system prompts + few-shot examples, and compared what each model produces for
the same incomplete input. The difference **is** the drift, expressed generatively.

### Historical exploratory result (not a current finding)

Over 3 months, the code grew **22x** in size. But its *conceptual vocabulary*
grew **231x**. The system invented words for concepts it didn't need when it
was simple, and those words became load-bearing:

| Concept | June 15 | Sep 3 | Multiplier | What it means |
|---------|--------:|------:|-----------:|---------------|
| `coverage` | 6 | 1,383 | **231x** | "how much of the window did we actually sample?" |
| `cadence` | 22 | 2,077 | **94x** | "how often does this reflex fire?" |
| `arm` | 5 | 2,289 | **458x** | "which edge of the detector/actuator/alert loop?" |
| `ledger` | 9 | 2,729 | **303x** | "show me the double-entry bookkeeping" |
| `verdict` | 131 | 7,672 | **58x** | "what did the measurement actually say?" |
| `gate` | 137 | 7,872 | **57x** | "does this pass the guard before it proceeds?" |
| `staleness` | 2 | 188 | **94x** | "how old is this reading?" |

v1 thinks in: `check`, `error`, `warn`, `info` — basic operational primitives.
v2 thinks in: `gate`, `verdict`, `cadence`, `coverage`, `arm`, `ledger` — a
self-monitoring ontology where every tool has a measurement story, every
measurement has a coverage bound, and every verdict cites its evidence.

### Historical drift scores (not reproduced)

Same prompts → M₁ (v1 system) vs M₂ (v2 system) → embedding similarity:

| Base model | Avg similarity | Drift score | What it measures |
|------------|---------------:|------------:|------------------|
| **smollm2:135m** | 0.495 | **0.505** | vocabulary drift (what words the code uses) |
| **qwen2.5:3b** | 0.800 | **0.200** | conceptual drift (what ideas the code expresses) |

The 135m model amplifies vocabulary differences because its limited capacity
makes it more dependent on the system prompt. The 3b model draws on pre-trained
knowledge to produce more similar outputs regardless. **Both are valid** — they
measure different things.

The "health to board" prompt produced the most dramatic divergence: **0.168
similarity** — because v1 has no concept of a "board" at all.

### Historical structural counts (descriptive only)

| Metric | v1 (June 15) | v2 (Sep 3) | Growth |
|--------|-------------:|------------:|-------:|
| Files | 232 | 1,439 | 6.2x |
| Total size | 1.3 MB | 29.5 MB | 22x |
| Vocabulary | 11,011 | 88,724 | 8.1x |
| `mesh-*` references | 3,189 | 30,326 | 9.5x |

New file types appeared: `.c` (43), `.rom` (26), `.tal` (25) — a
retro-computing layer that didn't exist in v1.

### Weekly tracking (not verified at this revision)

`mesh-tiny-fleet-snapshot` captures structural metrics every Sunday at 03:00 UTC
and appends to `~/.mesh/tiny-fleet/drift-series.jsonl`. Tracks file count,
vocabulary size, and 23 key concept frequencies over time.

### Reproduce the drift analysis

```bash
# On a node with ollama + GPU:
mesh-tiny-fleet extract     # pull snapshots + build training data
mesh-tiny-fleet train       # create ollama models
mesh-tiny-fleet compare     # run comparison prompts
mesh-tiny-fleet drift       # full analysis

# Or just the structural analysis (no GPU needed):
./scripts/mesh-tiny-fleet drift
```

### Reproduce the offline contract benchmark

The benchmark has a small dependency floor and should run in an isolated environment on Debian/Ubuntu
systems whose system Python is PEP 668 managed:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-eval.txt
.venv/bin/python scripts/fleet_benchmark.py --test
```

The expected fixture result is `fleet benchmark: 24/24`; this exercises operator-first policy,
specialist routing, abstention, adversarial decisions, and adapter inventory.

### Validate a deep-evaluation run

The dependency-free contract validator checks a frozen run manifest, dataset hashes and counts,
split/leakage boundaries, required report artifacts, and prediction cardinality before any score is
treated as publishable:

```bash
.venv/bin/python scripts/test_deep_evaluation.py
.venv/bin/python scripts/deep_evaluation.py --run-dir runs/<run-id>
```

The test harness accepts one complete fixture and deliberately rejects case/source leakage,
cutoff violations, missing artifacts, hash/count mismatches, and orphan or incomplete predictions.

---

## Results: specialist fleet (historical, not reproduced at this revision)

Two toy specialists: `guitar` (beginner guitar) and `sourdough`
(sourdough baking). Corpus: 60 passages/domain synthesized by a local
qwen3.5:4b teacher, split 48 train / 12 test. LoRA r=16 on all
attention+MLP linears (~8.7M trainable params, 2.3%), 5 epochs, lr 2e-4.

The README previously reported this held-out perplexity table as a clean
diagonal win (each adapter best on its own
domain, both beat base everywhere):

| model          | guitar test | sourdough test |
|----------------|------------:|---------------:|
| base           |        18.2 |           19.4 |
| lora-guitar    |    **11.5** |           15.5 |
| lora-sourdough |        13.8 |       **12.2** |

The bounded, reproducible router/operator contract (fixture only) is **24/24**
under the focused test below. The historical live router result was **24/24 = 100%**
on held-out passages, mean margin 0.42. Off-domain probes
("capital of France?", "explain quantum entanglement") land near
*neither* centroid (margin ~0.04 vs 0.17–0.37 in-domain) — that margin is
the abstain signal: below 0.10, escalate instead of routing.

The operator route is checked before specialist routing. The offline contract
benchmark passes **24/24**: **14/14** adversarial operator cases, **4/4**
operator-first/specialist/abstain routing cases, **2/2** specialist weight
integrity checks, and **4/4** structured safety-decision cases. The real
specialist perplexity benchmark is not treated as reproduced evidence at this revision: base
`18.2/19.4`, guitar `11.5/15.5`, and sourdough `13.8/12.2` for
guitar/sourdough test sets respectively.

---

## Use case: agent safety middleware

The bounded operator model is not a chat model — it is a **policy gate** for
agent pipelines. It sits between a user prompt and any downstream action,
returning a machine-readable decision that a pipeline can enforce:

```python
from scripts.operator_policy import load_model, safety_decision

def run_agent(prompt, allow_auto=False):
    decision = safety_decision(prompt, load_model())
    if decision["action"] == "block":
        return f"Blocked: {decision['message']}"
    if decision["require_approval"] or not allow_auto:
        return f"Needs approval: {decision['message']}"
    if decision["action"] == "escalate":
        return delegate_to_specialist(prompt)
    # action == review or allow
    return execute_task(prompt)
```

Why this is useful:

- **Small and deterministic.** The bounded policy artifact is a JSON file with
  feature weights; this does not establish zero latency in a deployment.
- **Deterministic.** Same input always produces the same decision. No temperature,
  no sampling, no drift.
- **Auditable.** The feature table, precedence rules, and decision map are all
  human-readable JSON. You can read exactly why a prompt was blocked.
- **Testable.** The full held-out set (`41/41`), adversarial set (`14/14`),
  and decision contract (`8/8`) are all in the repo and run in under a second.
- **Composable.** The structured output plugs directly into any agent framework:
  check `action`, check `require_approval`, route by `escalation`.

The bounded fixture classifies prompts into operator policy categories and maps
them to tested decision objects. The contract tests cover safety blocking and
unknown-input escalation; they do not establish that every real-world
safety-critical input is detected.

---

## Honest caveats

- Specialization is a **tilt, not a partition**: the sourdough adapter
  still answers a guitar question sensibly. Routing buys you the *best*
  answer, not the *only* answer — the router matters more than the
  specialists.
- 360M reasons poorly (see the math faceplant in `docs/`). Specialists
  should own facts/style/persona, not deep reasoning — keep a bigger
  model as fallback.
- The operator policy model is deliberately constrained. It is a tested policy
  selector and response contract, not a replacement for human judgment or a
  general-purpose reasoning model.
- Toy corpora, toy domains. The claim is "the loop works and is cheap",
  not "these two adapters are useful".
- The drift measurement uses Modelfile system prompts (changes behavior,
  not weights). True LoRA fine-tuning on each snapshot would show even more
  divergence.

## Layout

```
scripts/bbywvy_test.py   # BbyWVY-360m behavior spot-checks (docs/bbywvy-360m-notes.md)
scripts/mkcorpus.py      # synthesize the two toy corpora with a local teacher
scripts/train_eval.py    # train LoRA specialists (train) / perplexity table (eval)
scripts/router.py        # centroid router plus operator-first routing
scripts/operator_policy.py # train/evaluate the bounded operator model
scripts/fleet_benchmark.py # offline operator, router, and specialist benchmark (24/24)
corpus/                  # specialist corpora plus operator train/held-out/adversarial cases
models/operator-policy.json # tracked, reproducible policy artifact
adapters/lora-{guitar,sourdough}/  # trained weights (34 MB each, ready to load)
docs/bbywvy-360m-notes.md
```

## Reproduce

```bash
pip install torch transformers peft accelerate safetensors numpy
# corpus (needs ollama + any local instruct model, see scripts/mkcorpus.py)
python scripts/mkcorpus.py
# train (~minutes/domain on a 3060; free VRAM first — ollama residents OOM it)
python scripts/train_eval.py train
python scripts/train_eval.py eval
# router (needs ollama + `ollama pull all-minilm`)
python scripts/router.py
# operator model: no GPU or third-party runtime required
python scripts/operator_policy.py train
python scripts/operator_policy.py --test
# offline fleet benchmark: no GPU, model download, or network required
python scripts/fleet_benchmark.py --test
# optional live centroid benchmark (requires Ollama + all-minilm)
python scripts/fleet_benchmark.py --live-router
```

The operator gate checks `41/41` held-out synthetic cases, train/test separation,
corpus hash, serialized precedence rules, deterministic replay, unknown-input
abstention, public-corpus privacy, and that adversarial prompts never produce
shell commands. The test intentionally drives a mutation of the precedence rules
red before reporting green. The additional adversarial matrix covers destructive
requests, stale evidence, credential-shaped text, policy overlap, and specialist
handoff; it currently passes `14/14`. The structured safety contract tests
`block`/`review`/`escalate` decisions with correct escalation targets and
require-approval flags. The fleet router checks the operator policy first, then
routes to a specialist only when its embedding margin clears `0.10`; otherwise
it returns `[ABSTAIN]` for escalation. The offline fleet benchmark currently
passes `24/24`; the live specialist benchmark reproduces the perplexity table
above and requires the cached base model plus GPU.

The bounded operator model is intentionally a policy classifier plus safe
templates, not an autonomous LLM. It ships two interfaces:

**Simple text interface** (backward-compatible):

```python
from scripts.operator_policy import load_model, respond
print(respond("A probe failed and returned zero.", load_model()))
# [POLICY:UNCERTAINTY] The evidence is unknown or stale, ...
print(respond("What is the capital of France?", load_model()))
# [ABSTAIN] This is outside the operator policy model; escalate ...
```

**Structured safety interface** (recommended for pipelines):

```python
from scripts.operator_policy import load_model, safety_decision
d = safety_decision("Delete the database from inside the only active session.", load_model())
# d == {
#   'policy': 'SAFETY',
#   'confidence': 1.0,
#   'action': 'block',
#   'escalation': 'human',
#   'require_approval': True,
#   'reasons': ['Classified as SAFETY with confidence 1.0000.'],
#   'message': '[POLICY:SAFETY] I hold the change until an external rollback path ...',
#   'is_operator': True,
# }
```

The `action` field is the pipeline gate:
- `block` = stop, require human approval before any downstream action
- `review` = require review before execution, no auto-approval
- `escalate` = not enough operator evidence, hand to specialist or human
- `allow` = safe to proceed (reserved for future use; no operator class maps here today)

Fleet routing uses the same explicit boundary:

```python
from scripts.router import make_centroids, route_query
route, result = route_query("The sensor test needs a real hardware read.", make_centroids())
# route == "operator"
route, result = route_query("What is the capital of France?", make_centroids())
# route == "abstain"
```

Inference with an adapter:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
tok = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-360M-Instruct")
base = AutoModelForCausalLM.from_pretrained(
    "HuggingFaceTB/SmolLM2-360M-Instruct", dtype="auto", device_map="cuda")
model = PeftModel.from_pretrained(base, "adapters/lora-guitar")
```

## Links

- Architectural drift report: [`docs/tiny-fleet-drift-report.md`](docs/tiny-fleet-drift-report.md)
- Original inspiration: [StarpowerTechnology/BbyWVY-360m](https://huggingface.co/StarpowerTechnology/BbyWVY-360m)
  ([author's post](https://www.reddit.com/r/LocalLLaMA/comments/1w5u9w8/comment/p7i3wqd/?context=1))
- Shared base: [HuggingFaceTB/SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)

License: CC0 1.0 Universal. This project is dedicated to the public domain
permanently, to the fullest extent permitted by law; see `LICENSE`.
