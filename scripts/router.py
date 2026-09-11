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
import os
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
EMBEDDING_MODEL = "all-minilm"
EMBEDDING_MODEL_REVISION = os.environ.get("TINY_FLEET_EMBEDDING_REVISION", "unresolved")
EMBEDDING_MODEL_DIGEST = os.environ.get("TINY_FLEET_EMBEDDING_DIGEST", "unresolved")


class RouterError(Exception):
    """A typed failure at the embedding/router boundary."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def embed(texts):
    try:
        out = subprocess.run(
            ["curl", "-s", "--max-time", "120", "localhost:11434/api/embed",
             "-d", json.dumps({"model": EMBEDDING_MODEL, "input": texts})],
            capture_output=True, text=True, timeout=150, check=True)
    except subprocess.TimeoutExpired as exc:
        raise RouterError("embedding_timeout") from exc
    except subprocess.CalledProcessError as exc:
        raise RouterError("embedding_backend_failure") from exc
    except OSError as exc:
        raise RouterError("embedding_backend_failure") from exc
    try:
        payload = json.loads(out.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RouterError("embedding_invalid_json") from exc
    embeddings = payload.get("embeddings") if isinstance(payload, dict) else None
    if not isinstance(embeddings, list):
        raise RouterError("embedding_response_schema")
    try:
        result = np.asarray(embeddings, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise RouterError("embedding_response_schema") from exc
    if result.ndim != 2 or result.shape[0] != len(texts):
        raise RouterError("embedding_response_shape")
    return result


def load(domain, split):
    with open(ROOT / "corpus" / f"{domain}-{split}.jsonl") as f:
        return [json.loads(line)["text"] for line in f]


def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def _detail(reason, scores=None, best_similarity=None, margin=None):
    return {
        "reason": reason,
        "scores": scores or {},
        "best_similarity": best_similarity,
        "margin": margin,
        "embedding_backend": "ollama-http",
        "embedding_model": EMBEDDING_MODEL,
        "embedding_model_revision": EMBEDDING_MODEL_REVISION,
        "embedding_model_digest": EMBEDDING_MODEL_DIGEST,
    }


def _validate_centroids(centroids):
    if not isinstance(centroids, dict) or not centroids:
        raise RouterError("invalid_centroids")
    arrays = {}
    dimension = None
    for domain, centroid in centroids.items():
        try:
            vector = np.asarray(centroid, dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise RouterError("invalid_centroid_schema") from exc
        if vector.ndim != 1:
            raise RouterError("invalid_centroid_shape")
        if dimension is None:
            dimension = vector.shape[0]
        if vector.shape[0] != dimension:
            raise RouterError("invalid_centroid_shape")
        if not np.all(np.isfinite(vector)):
            raise RouterError("invalid_centroid_nonfinite")
        if np.linalg.norm(vector) == 0:
            raise RouterError("invalid_centroid_norm")
        arrays[domain] = vector
    return arrays, dimension


def _validate_query_embedding(raw, dimension):
    try:
        matrix = np.asarray(raw, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise RouterError("invalid_embedding_shape") from exc
    if matrix.ndim != 2 or matrix.shape != (1, dimension):
        raise RouterError("invalid_embedding_shape")
    vector = matrix[0]
    if not np.all(np.isfinite(vector)):
        raise RouterError("invalid_embedding_nonfinite")
    if np.linalg.norm(vector) == 0:
        raise RouterError("invalid_embedding_norm")
    return vector


def make_centroids(embed_fn=embed):
    cent = {}
    for d in DOMAINS:
        texts = load(d, "train")
        E = embed_fn(texts)
        expected_count = len(texts)
        try:
            E = np.asarray(E, dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise RouterError("invalid_embedding_schema") from exc
        if E.ndim != 2 or E.shape[0] != expected_count:
            raise RouterError("invalid_embedding_shape")
        if not np.all(np.isfinite(E)):
            raise RouterError("invalid_embedding_nonfinite")
        if np.any(np.linalg.norm(E, axis=1) == 0):
            raise RouterError("invalid_embedding_norm")
        c = E.mean(axis=0)
        norm = np.linalg.norm(c)
        if not np.isfinite(norm) or norm == 0:
            raise RouterError("invalid_centroid_norm")
        cent[d] = c / norm
    return cent


def route_query(text, centroids, embed_fn=embed, operator_model=None, calibration=None):
    """Route operator requests first, then specialists, or abstain.

    ``embed_fn`` is injectable so route precedence and abstention can be tested
    without a network embedding service. The returned route is a stable
    machine-readable value: ``operator``, ``specialist:<domain>``, or
    ``abstain``.
    """
    operator_model = operator_model or load_model()
    if is_operator_query(text, operator_model):
        return "operator", respond(text, operator_model)
    try:
        valid_centroids, dimension = _validate_centroids(centroids)
        raw = embed_fn([text])
        vector = _validate_query_embedding(raw, dimension)
        vector /= np.linalg.norm(vector)
        scores = {domain: cos(vector, centroid)
                  for domain, centroid in valid_centroids.items()}
        if not all(np.isfinite(value) for value in scores.values()):
            raise RouterError("invalid_similarity")
    except RouterError as exc:
        return "abstain", _detail(exc.reason)
    except (TypeError, ValueError, FloatingPointError) as exc:
        return "abstain", _detail("router_runtime_failure")
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    margin = ranked[0][1] - ranked[1][1] if len(ranked) > 1 else ranked[0][1]
    similarity_min = calibration.get("similarity_min", -float("inf")) if calibration else -float("inf")
    margin_min = calibration.get("margin_min", ABSTAIN_MARGIN) if calibration else ABSTAIN_MARGIN
    if ranked[0][1] < similarity_min:
        return "abstain", _detail("absolute_similarity", scores, ranked[0][1], margin)
    if margin < margin_min:
        return "abstain", _detail("low_confidence", scores, ranked[0][1], margin)
    return f"specialist:{ranked[0][0]}", _detail("routed", scores, ranked[0][1], margin)


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
