"""Embedding-centroid router: route a query to the specialist whose domain
centroid is closest in embedding space. Also demonstrates the abstain
signal — off-domain queries land near NEITHER centroid (tiny margin),
which is where a fleet should escalate instead of answering.

  python router.py

Requires an embeddings backend. We used ollama + all-minilm
(`ollama pull all-minilm`), called here over the local HTTP API, but any
sentence-embedding model works — swap out embed().
"""
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ["guitar", "sourdough"]
ABSTAIN_MARGIN = 0.10  # below this, escalate instead of routing


def embed(texts):
    out = subprocess.run(
        ["curl", "-s", "--max-time", "120", "localhost:11434/api/embed",
         "-d", json.dumps({"model": "all-minilm", "input": texts})],
        capture_output=True, text=True, timeout=150)
    return np.array(json.loads(out.stdout)["embeddings"], dtype=np.float64)


def load(domain, split):
    with open(ROOT / "corpus" / f"{domain}-{split}.jsonl") as f:
        return [json.loads(line)["text"] for line in f]


def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    cent = {}
    for d in DOMAINS:
        E = embed(load(d, "train"))
        c = E.mean(axis=0)
        cent[d] = c / np.linalg.norm(c)
        print(f"centroid {d}: {len(E)} passages", flush=True)

    ok, n, margins = 0, 0, []
    for d in DOMAINS:
        for t in load(d, "test"):
            v = embed([t])[0]
            v /= np.linalg.norm(v)
            s = {k: cos(v, cent[k]) for k in DOMAINS}
            pred = max(s, key=s.get)
            n += 1
            ok += (pred == d)
            margins.append(abs(s["guitar"] - s["sourdough"]))
    print(f"\nROUTER ACCURACY: {ok}/{n} = {ok / n:.0%}, "
          f"mean margin={np.mean(margins):.3f}", flush=True)

    probes = ["How do I tune my guitar?",
              "My starter smells like acetone, help",
              "What is the capital of France?",
              "Explain quantum entanglement"]
    for q in probes:
        v = embed([q])[0]
        v /= np.linalg.norm(v)
        s = {k: cos(v, cent[k]) for k in DOMAINS}
        margin = abs(s["guitar"] - s["sourdough"])
        verdict = "ABSTAIN/ESCALATE" if margin < ABSTAIN_MARGIN else \
            f"route->{max(s, key=s.get)}"
        print(f"Q: {q}\n   sim_g={s['guitar']:.3f} "
              f"sim_s={s['sourdough']:.3f} margin={margin:.3f} => {verdict}",
              flush=True)


if __name__ == "__main__":
    main()
