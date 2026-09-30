# BbyWVY-360m baseline reproduction receipt

- Task: `tinyfleet-operator-ideas-20260912/verify-bbywvy-baseline`
- Verdict: **AVAILABLE — exact pinned model loaded and real inference completed.**
- Run completed: 2026-09-12 UTC; local run used the existing HF cache, with `HF_HUB_OFFLINE=1`.

## Artifact identity

| Field | Value |
|---|---|
| Repository | `StarpowerTechnology/BbyWVY-360m` |
| Immutable revision | `154a243ffa13d3259a824c40a23d709d3ea42fa7` |
| Upstream check | HF `/api/models/StarpowerTechnology/BbyWVY-360m/commits/main` returned this same revision as `main` at check time |
| Weights | `model.safetensors`, 1,447,317,080 bytes; SHA-256 `3e26b40ed65c3fcd53e2930c38e3c9b9a5912389e0a6924f047cafa8eaa68c14` |
| Architecture / parameter count | `LlamaForCausalLM`; 361,821,120 parameters |
| Config SHA-256 | `cf71666f04597f61e8a61ab77f142155cb6f76c15384f2b1d48ee117f4a82228` |

Tokenizer came from this same revision; metadata declares `GPT2Tokenizer`, vocabulary size 49,152,
`<|im_start|>` ID 1 and `<|im_end|>` ID 2. `tokenizer.json` SHA-256 is
`bf346d64f6f0fbcefb4c1b6928a98241467dff36c6fbae5fe1785c4ff90667f4`; `tokenizer_config.json`
SHA-256 is `8df5009f725eba8f7c0b2f6872f65de5932f7fca7ff1786abfa3f37be741dbaf`; the chat template
SHA-256 is `872be49dbb638044ad01b60388f48d469ff2980e5f0dccdc22ec907db54d0788`.

## Runtime and resource choice

- Runtime: `/home/mesh-home/.venv-ai/bin/python`, PyTorch `2.13.0+cu130`, Transformers `5.14.1`,
  Tokenizers `0.22.2`; FP16.
- Device: NVIDIA GeForce RTX 3060, 12,288 MiB. Immediately before loading, CUDA reported
  7,784,038,400 bytes free; GPU telemetry showed 4,225 MiB used and 0% utilization. After the
  process, telemetry showed 4,380 MiB used and 0% utilization.
- Resource decision: use the local GPU rather than the saturated CPU. The local 16-core host had
  load averages 35.75/48.25/33.13; the only other online Linux peer checked, Phaedra, had load
  18.98/9.65/8.65 on 2 CPUs and 1.3 GiB available RAM. The selected GPU had ample measured
  headroom for this short run.
- This process peak: 3,083,716 KiB RSS, 753,185,792 bytes CUDA allocated and 771,751,936 bytes
  CUDA reserved. CUDA free memory after inference was 7,141,392,384 bytes.

## Inference smoke

Loaded by repository ID plus the immutable revision with `local_files_only=True`; tokenizer special
tokens were supplied as `{im_start: "<|im_start|>", im_end: "<|im_end|>"}` to match the published
tokenizer metadata. Used the model's chat template, seed `20260912`, `temperature=0.7`, `top_p=0.95`,
sampling enabled, and `max_new_tokens=64`. Prompt (32 tokens):

```text
system: u are WVY. be curious, honest, and conversational.
user: Who are you?
```

Model load took 5.6092 s. First inference took 9.5407 s (64 tokens, 6.71 tokens/s); the warm second
inference took 4.0523 s (64 tokens, 15.79 tokens/s). Both reached the 64-token cap, so these are
latency smoke measurements, not completion-quality scores.

Cold output:

```text
I am WVY. I am a linguistic and cultural anthropologist, specializing in the study of language contact and the social dynamics of language communities. My research focuses on how language is shaped by cultural, historical, and social contexts, and how it reflects and influences the identities of its speakers. I am based in
```

Warm output:

```text
I am WVY. That's my name, but my friends and family call me WVY. I'm a digital assistant, a chatbot, and a language model that helps people understand the world through text. I'm designed to learn from the conversations I have and improve my responses over time. I'm
```

## Historical disposition

The 2026-09-06 audit's statement that it had not reproduced or downloaded the model remains an
accurate historical record. This receipt adds a successful reproduction at the pinned revision on
2026-09-12; it does not rewrite that earlier result or claim benchmark/quality validation.
