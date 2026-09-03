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

try:
    from operator_policy import load_model, is_operator_query, respond
except ModuleNotFoundError:  # package-style import from the repository root
    from scripts.operator_policy import load_model, is_operator_query, respond

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


def make_centroids(embed_fn=embed):
    cent = {}
    for d in DOMAINS:
        E = embed_fn(load(d, "train"))
        c = E.mean(axis=0)
        cent[d] = c / np.linalg.norm(c)
    return cent


def route_query(text, centroids, embed_fn=embed, operator_model=None):
    """Route operator requests first, then specialists, or abstain.

    ``embed_fn`` is injectable so route precedence and abstention can be tested
    without a network embedding service. The returned route is a stable
    machine-readable value: ``operator``, ``specialist:<domain>``, or
    ``abstain``.
    """
    operator_model = operator_model or load_model()
    if is_operator_query(text, operator_model):
        return "operator", respond(text, operator_model)
    vector = embed_fn([text])[0]
    vector /= np.linalg.norm(vector)
    scores = {domain: cos(vector, centroid)
              for domain, centroid in centroids.items()}
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    margin = ranked[0][1] - ranked[1][1] if len(ranked) > 1 else ranked[0][1]
    if margin < ABSTAIN_MARGIN:
        return "abstain", "[ABSTAIN] No specialist has sufficient routing margin."
    return f"specialist:{ranked[0][0]}", scores


def main():
    cent = make_centroids()
    for d in DOMAINS:
        print(f"centroid {d}: {len(load(d, 'train'))} passages", flush=True)

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
        route, detail = route_query(q, cent)
        print(f"Q: {q}\n   {route}: {detail}", flush=True)


if __name__ == "__main__":
    main()
