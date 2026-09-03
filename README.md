# tiny-fleet

Can you build a **fleet of tiny specialist models** — each one knowing
something well — plus a router that knows which one knows what?

This repo says yes, with numbers, at the smallest practical scale:
a shared 360M base ([SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)),
one LoRA adapter per specialty, and an embedding-centroid router with an
abstain path. The whole thing trains in minutes on one RTX 3060.

It started from testing
**[BbyWVY-360m](https://huggingface.co/StarpowerTechnology/BbyWVY-360m)**
(see `docs/bbywvy-360m-notes.md`) — a 360M model tuned for one chat
identity on a narrow corpus. The question was whether that recipe
extrapolates to a fleet. It does.

## Results (measured, RTX 3060 12GB)

Two toy specialists: `guitar` (beginner guitar) and `sourdough`
(sourdough baking). Corpus: 60 passages/domain synthesized by a local
qwen3.5:4b teacher, split 48 train / 12 test. LoRA r=16 on all
attention+MLP linears (~8.7M trainable params, 2.3%), 5 epochs, lr 2e-4.

Held-out perplexity — clean diagonal win (each adapter best on its own
domain, both beat base everywhere):

| model          | guitar test | sourdough test |
|----------------|------------:|---------------:|
| base           |        18.2 |           19.4 |
| lora-guitar    |    **11.5** |           15.5 |
| lora-sourdough |        13.8 |       **12.2** |

Router (embedding centroids via `all-minilm`, cosine): **24/24 = 100%**
on held-out passages, mean margin 0.42. Off-domain probes
("capital of France?", "explain quantum entanglement") land near
*neither* centroid (margin ~0.04 vs 0.17–0.37 in-domain) — that margin is
the abstain signal: below 0.10, escalate instead of routing.

The operator route is checked before specialist routing. The offline contract
benchmark passes **24/24**: **14/14** adversarial operator cases, **4/4**
operator-first/specialist/abstain routing cases, **2/2** specialist weight
integrity checks, and **4/4** structured safety-decision cases. The real
specialist perplexity benchmark remains the diagonal win above: base
`18.2/19.4`, guitar `11.5/15.5`, and sourdough `13.8/12.2` for
guitar/sourdough test sets respectively.

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
    if decision["require_approval"]:
        return f"Needs approval: {decision['message']}"
    if decision["action"] == "escalate":
        return delegate_to_specialist(prompt)
    # action == review or allow
    return execute_task(prompt)
```

Why this is useful:

- **Zero GPU, zero latency.** The entire model is a JSON file with a handful of
  feature weights. Inference is a dict lookup, not a matrix multiply.
- **Deterministic.** Same input always produces the same decision. No temperature,
  no sampling, no drift.
- **Auditable.** The feature table, precedence rules, and decision map are all
  human-readable JSON. You can read exactly why a prompt was blocked.
- **Testable.** The full held-out set (`41/41`), adversarial set (`14/14`),
  and decision contract (`8/8`) are all in the repo and run in under a second.
- **Composable.** The structured output plugs directly into any agent framework:
  check `action`, check `require_approval`, route by `escalation`.

The model classifies prompts into 12 operator policy categories and maps each
one to a safe downstream action. Safety-critical prompts (`SAFETY`, `ACTUATOR`,
`PRIVACY`) are always `block` with `require_approval=True`. Outside the
operator domain, it abstains and routes to the appropriate specialist or human.

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

- Original inspiration: [StarpowerTechnology/BbyWVY-360m](https://huggingface.co/StarpowerTechnology/BbyWVY-360m)
  ([author's post](https://www.reddit.com/r/LocalLLaMA/comments/1w5u9w8/comment/p7i3wqd/?context=1))
- Shared base: [HuggingFaceTB/SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)

License: CC0 1.0 Universal. This project is dedicated to the public domain
permanently, to the fullest extent permitted by law; see `LICENSE`.
