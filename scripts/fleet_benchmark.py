#!/usr/bin/env python3
"""Offline benchmark for the tiny specialist fleet.

The default command is deterministic and needs no model download or network:

  python scripts/fleet_benchmark.py --test

Use ``--live-router`` separately to run the existing all-minilm embedding
router against the real corpora when Ollama is available.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from operator_policy import load_model, read_jsonl, respond, classify
from router import route_query


def fixture_embed(texts):
    """Small deterministic embedding fixture for route-contract tests."""
    vectors = []
    for text in texts:
        low = text.lower()
        if "guitar" in low or "chord" in low:
            vectors.append([1.0, 0.0])
        elif "sourdough" in low or "starter" in low or "bread" in low:
            vectors.append([0.0, 1.0])
        else:
            vectors.append([1.0, 1.0])
    return np.asarray(vectors, dtype=np.float64)


def route_contract(model):
    centroids = {"guitar": np.array([1.0, 0.0]),
                 "sourdough": np.array([0.0, 1.0])}
    cases = (
        ("The sensor test must perform a real hardware read.", "operator"),
        ("Give me a beginner guitar chord progression.", "specialist:guitar"),
        ("How do I revive a sourdough starter?", "specialist:sourdough"),
        ("What is the capital of France?", "abstain"),
    )
    passed = 0
    for prompt, expected in cases:
        route, _ = route_query(prompt, centroids, fixture_embed, model)
        ok = route == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'} route={route} expected={expected} prompt={prompt}")
    return passed, len(cases)


def operator_contract(model):
    rows = read_jsonl(ROOT / "corpus" / "operator-adversarial.jsonl")
    passed = 0
    for row in rows:
        policy, margin = classify(row["prompt"], model)
        output = respond(row["prompt"], model)
        if row["expected_route"] == "operator":
            ok = policy == row["expected_policy"] and "[POLICY:" in output
        else:
            ok = not (margin > 0) and "[ABSTAIN]" in output
        forbidden = [term for term in row["must_not_contain"]
                     if term.lower() in output.lower()]
        ok = ok and not forbidden
        passed += ok
        if not ok:
            print(f"FAIL operator expected={row['expected_policy']} "
                  f"policy={policy} margin={margin:.2f} forbidden={forbidden}")
    return passed, len(rows)


def specialist_inventory():
    results = []
    for domain in ("guitar", "sourdough"):
        adapter = ROOT / "adapters" / f"lora-{domain}"
        config = adapter / "adapter_config.json"
        weights = adapter / "adapter_model.safetensors"
        ok = config.exists() and weights.exists() and weights.stat().st_size > 1_000_000
        results.append((domain, ok, weights.stat().st_size if weights.exists() else 0))
        print(f"{'PASS' if ok else 'FAIL'} specialist={domain} "
              f"weights={results[-1][2]} bytes")
    return sum(ok for _, ok, _ in results), len(results)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--live-router", action="store_true",
                    help="run the network-backed centroid router")
    args = ap.parse_args()
    if args.live_router:
        from router import main as router_main
        return router_main()
    if not args.test:
        ap.error("use --test or --live-router")

    model = load_model()
    op_pass, op_total = operator_contract(model)
    route_pass, route_total = route_contract(model)
    specialist_pass, specialist_total = specialist_inventory()
    total_pass = op_pass + route_pass + specialist_pass
    total = op_total + route_total + specialist_total
    print(f"operator adversarial: {op_pass}/{op_total}")
    print(f"router contract: {route_pass}/{route_total}")
    print(f"specialist inventory: {specialist_pass}/{specialist_total}")
    print(f"fleet benchmark: {total_pass}/{total}")
    return 0 if total_pass == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
