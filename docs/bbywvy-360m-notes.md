# BbyWVY-360m hands-on notes

Model: [StarpowerTechnology/BbyWVY-360m](https://huggingface.co/StarpowerTechnology/BbyWVY-360m)
— an experimental conversational checkpoint based on
[HuggingFaceTB/SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct):
first instruction-tuned for a "WVY" chat identity, then continued-pretrained
(last 4 transformer layers, lr 2e-6, 1 epoch) on a user-message-only corpus.
Author's thread:
[r/LocalLLaMA comment](https://www.reddit.com/r/LocalLLaMA/comments/1w5u9w8/comment/p7i3wqd/?context=1).

Test rig: RTX 3060 12GB, FP16, `transformers` + sampling
(`temperature=0.7, top_p=0.95`). Script: `scripts/bbywvy_test.py`.

## Perf

- 362M params, loads in ~1.3 s, **~50 tok/s**, sips VRAM (~0.7 GB in FP16).
  A dozen of these can live in 12 GB at once — the fact the fleet pilot
  in this repo builds on.

## Behavior vs the author's stated intent

WVY is tuned to be "conversational, curious, and uncertainty-aware".
What we saw:

- **Identity holds.** `Who are you?` (with the WVY system prompt) →
  `I am WVY.`
- **Uncertainty-aware, mostly.** `what do u know about quantum physics?` →
  `i know quantum physics is about tiny particles like atoms and photons
  behaving in weird ways, but i dont know the full details yet. is it like
  magic or something?` — admits limits, asks a follow-up. On a second
  sample it gave a decent superposition explanation instead. Sampling
  variance is wide at this size.
- **Follow-up energy.** Guitar-tips answer ends with engagement; casual
  `wassup bro what are u thinking about?` gets a question back.
- **Factual recall fine for easy stuff.** Capital of France → correct,
  fluent Paris paragraph.
- **Long-form coherent.** A 256-token robot-painting story stays on plot;
  mild name/topic repetition (`R.E.M.`, trees) but no degenerate loops.

## Weak spots (expected at 360M)

- **Math reasoning is shaky.** `60 km/h for 2.5 hours` sent it into an
  unnecessary m/s conversion — and it converted wrong (60 km/h is
  16.67 m/s, not 60,000 m/s) before hitting the token limit.
- **Placeholder hallucination.** The casual reply mentioned `the upcoming
  tech conference in [city]` — a template slot leaked into output.
- **Sampling variance.** Same prompt, notably different answers run to run.

## Verdict

Worth keeping for tiny-identity experiments; genuinely conversational for
362M. Needs more SFT/alignment before it's tight — exactly what the model
card says. The interesting property for us is not the weights, it's the
**recipe** (narrow corpus + last-layers tuning = cheap specialist), which
`scripts/train_eval.py` reproduces from scratch in this repo.
