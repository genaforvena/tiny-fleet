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
scripts/router.py        # centroid router accuracy + abstain demo
scripts/operator_policy.py # train/evaluate the bounded operator model
corpus/                  # specialist corpora plus operator train/held-out cases
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
```

The operator gate checks `41/41` held-out synthetic cases, train/test separation,
corpus hash, serialized precedence rules, deterministic replay, unknown-input
abstention, public-corpus privacy, and that adversarial prompts never produce
shell commands. The test intentionally drives a mutation of the precedence rules
red before reporting green.

Inference with the bounded operator model:

```python
from scripts.operator_policy import load_model, respond
print(respond("A probe failed and returned zero.", load_model()))
# [POLICY:UNCERTAINTY] The evidence is unknown or stale, ...
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

License: MIT.
