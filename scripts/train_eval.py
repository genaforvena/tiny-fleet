"""Train one LoRA specialist per domain on a shared small base model,
then compare held-out perplexity (expect a diagonal win: each adapter
scores best on its own domain).

  python train_eval.py train   # trains adapters/<domain> for each domain
  python train_eval.py eval    # prints base vs adapter perplexity table

Corpus layout (see scripts/mkcorpus.py):
  corpus/<domain>-train.jsonl   one {"topic":..., "text":...} per line
  corpus/<domain>-test.jsonl

Trained on an RTX 3060 12GB: ~minutes per domain (360M base, LoRA r=16).
If VRAM is tight, stop other GPU residents first (we had to evict ollama
models) and lower BATCH.
"""
import json
import math
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, PeftModel

ROOT = Path(__file__).resolve().parent.parent
BASE = "HuggingFaceTB/SmolLM2-360M-Instruct"
DOMAINS = ["guitar", "sourdough"]
EPOCHS = 5
BATCH = 2
LR = 2e-4


def load_texts(domain, split):
    with open(ROOT / "corpus" / f"{domain}-{split}.jsonl") as f:
        return [json.loads(line)["text"] for line in f]


def train(domain):
    print(f"--- training {domain} ---", flush=True)
    tok = AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        BASE, dtype=torch.float16, device_map="cuda")
    cfg = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM")
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()
    texts = load_texts(domain, "train")
    enc = tok(texts, truncation=True, max_length=256, padding=True,
              return_tensors="pt")
    import torch.utils.data as D
    dl = D.DataLoader(
        D.TensorDataset(enc["input_ids"], enc["attention_mask"]),
        batch_size=BATCH, shuffle=True)
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    model.train()
    for ep in range(EPOCHS):
        tot, n = 0.0, 0
        for ids, mask in dl:
            ids, mask = ids.cuda(), mask.cuda()
            loss = model(input_ids=ids, attention_mask=mask,
                         labels=ids).loss
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += loss.item()
            n += 1
        print(f"{domain} ep{ep}: loss={tot / n:.3f}", flush=True)
    out = ROOT / "adapters" / f"lora-{domain}"
    model.save_pretrained(out)
    print(f"saved {out}", flush=True)
    del model
    torch.cuda.empty_cache()


@torch.no_grad()
def perplexity(model, tok, texts):
    nll, ntok = 0.0, 0
    model.eval()
    for t in texts:
        ids = tok(t, truncation=True, max_length=256,
                  return_tensors="pt")["input_ids"].cuda()
        n = ids.shape[-1]
        nll += model(input_ids=ids, labels=ids).loss.item() * n
        ntok += n
    return math.exp(nll / ntok)


def evaluate():
    tok = AutoTokenizer.from_pretrained(BASE)
    base = AutoModelForCausalLM.from_pretrained(
        BASE, dtype=torch.float16).cuda()
    tests = {d: load_texts(d, "test") for d in DOMAINS}
    print(f"base: guitar-ppl={perplexity(base, tok, tests['guitar']):.1f} "
          f"sourdough-ppl={perplexity(base, tok, tests['sourdough']):.1f}",
          flush=True)
    del base
    torch.cuda.empty_cache()
    for d in DOMAINS:
        m = AutoModelForCausalLM.from_pretrained(
            BASE, dtype=torch.float16).cuda()
        m = PeftModel.from_pretrained(m, str(ROOT / "adapters" / f"lora-{d}"))
        pg = perplexity(m, tok, tests["guitar"])
        ps = perplexity(m, tok, tests["sourdough"])
        print(f"lora-{d}: guitar-ppl={pg:.1f} sourdough-ppl={ps:.1f}",
              flush=True)
        del m
        torch.cuda.empty_cache()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("train", "eval"):
        sys.exit("usage: python train_eval.py [train|eval]")
    if sys.argv[1] == "train":
        for d in DOMAINS:
            train(d)
    else:
        evaluate()
