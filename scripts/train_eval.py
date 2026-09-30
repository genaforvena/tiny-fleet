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

from loss_metrics import aggregate_perplexity, masked_labels, summed_nll
from run_manifest import prepare_run, record_completion

ROOT = Path(__file__).resolve().parent.parent
BASE = "HuggingFaceTB/SmolLM2-360M-Instruct"
DOMAINS = ["guitar", "sourdough"]
EPOCHS = 5
BATCH = 2
LR = 2e-4


def load_texts(domain, split):
    with open(ROOT / "corpus" / f"{domain}-{split}.jsonl") as f:
        return [json.loads(line)["text"] for line in f]


def train(domain, manifest_path=None, run_dir=None, seed=None):
    print(f"--- training {domain} ---", flush=True)
    prepared = None
    base_revision = None
    train_cfg = {"epochs": EPOCHS, "batch": BATCH, "gradient_accumulation": 1,
                 "learning_rate": LR, "max_length": 256}
    if manifest_path is not None:
        if run_dir is None:
            raise ValueError("--run-dir is required with --manifest")
        manifest = json.loads(Path(manifest_path).read_text())
        train_cfg.update(manifest.get("training", {}))
        seed = train_cfg.get("seed", 17) if seed is None else seed
        prepared = prepare_run(Path(manifest_path), Path(run_dir), seed, arm=domain,
                               device="cuda", dtype="float16")
        base_revision = manifest["base_model"]["revision"]
    tok = AutoTokenizer.from_pretrained(BASE, **({"revision": base_revision} if base_revision else {}))
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        BASE, dtype=torch.float16, device_map="cuda",
        **({"revision": base_revision} if base_revision else {}))
    cfg = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM")
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()
    texts = load_texts(domain, "train")
    enc = tok(texts, truncation=True, max_length=int(train_cfg["max_length"]), padding=True,
              return_tensors="pt")
    import torch.utils.data as D
    dl = D.DataLoader(
        D.TensorDataset(enc["input_ids"], enc["attention_mask"]),
        batch_size=int(train_cfg.get("batch", BATCH)), shuffle=True)
    accumulation = int(train_cfg.get("gradient_accumulation", 1))
    opt = torch.optim.AdamW(model.parameters(), lr=float(train_cfg.get("learning_rate", LR)))
    model.train()
    optimizer_steps = 0
    for ep in range(int(train_cfg.get("epochs", EPOCHS))):
        tot, n = 0.0, 0
        opt.zero_grad(set_to_none=True)
        for index, (ids, mask) in enumerate(dl):
            ids, mask = ids.cuda(), mask.cuda()
            labels = masked_labels(ids, mask)
            loss = model(input_ids=ids, attention_mask=mask,
                         labels=labels).loss / accumulation
            loss.backward()
            if (index + 1) % accumulation == 0 or index + 1 == len(dl):
                opt.step(); opt.zero_grad(set_to_none=True); optimizer_steps += 1
            tot += loss.item()
            n += 1
        print(f"{domain} ep{ep}: loss={tot * accumulation / n:.3f}", flush=True)
    out = Path(prepared["run"]["adapter_dir"]) if prepared else ROOT / "adapters" / f"lora-{domain}"
    model.save_pretrained(out)
    if prepared:
        result = {"status": "complete", "domain": domain, "seed": seed,
                  "optimizer_steps": optimizer_steps, "examples_seen": len(texts) * int(train_cfg.get("epochs", EPOCHS)),
                  "adapter": str(out), "base_revision": base_revision}
        Path(run_dir, f"train-{domain}.json").write_text(json.dumps(result, indent=2) + "\n")
        record_completion(Path(run_dir), result)
    print(f"saved {out}", flush=True)
    del model
    torch.cuda.empty_cache()


@torch.no_grad()
def perplexity(model, tok, texts):
    nll, ntok = 0.0, 0
    model.eval()
    for t in texts:
        encoded = tok(t, truncation=True, max_length=256,
                      return_tensors="pt")
        ids = encoded["input_ids"].cuda()
        mask = encoded["attention_mask"].cuda()
        labels = masked_labels(ids, mask)
        outputs = model(input_ids=ids, attention_mask=mask)
        item_nll, item_targets = summed_nll(outputs.logits, labels)
        nll += item_nll
        ntok += item_targets
    return aggregate_perplexity(nll, ntok)


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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("train", "eval"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    if args.command == "train":
        for d in DOMAINS:
            train(d, args.manifest, args.run_dir, args.seed) if args.manifest else train(d)
    else:
        evaluate()
