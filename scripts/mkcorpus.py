"""Synthesize the two toy domain corpora with a local teacher model.

  python mkcorpus.py

Writes corpus/<domain>-{train,test}.jsonl (4:1 split), one
{"topic": ..., "text": ...} per line. We used qwen3.5:4b via the local
ollama API with thinking disabled (a thinking model otherwise spends most
of its time reasoning out loud and pollutes the passages). Any decent
local instruct model works — swap MODEL.

20 topics x 3 angles per domain = 60 passages per domain.
Takes ~10 minutes on an RTX 3060. Progress is append-flushed per passage,
so a killed run keeps what it wrote.
"""
import json
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "qwen3.5:4b"

DOMAINS = {
    "guitar": [
        "tuning a guitar by ear", "holding the pick correctly",
        "first open chords G C D", "switching between chords smoothly",
        "basic strumming patterns", "reading guitar tablature",
        "finger pain and building calluses", "practicing with a metronome",
        "the parts of the guitar", "changing strings", "capo basics",
        "power chords", "palm muting", "simple fingerpicking patterns",
        "tuning with an electronic tuner", "posture while playing",
        "hammer-ons and pull-offs", "the pentatonic scale box one",
        "playing your first song", "cleaning and storing the guitar",
    ],
    "sourdough": [
        "creating a starter from flour and water",
        "feeding schedule for a new starter",
        "signs the starter is ready to bake", "autolyse technique",
        "stretch and fold method", "bulk fermentation timing",
        "shaping a boule", "scoring the loaf", "baking in a dutch oven",
        "steam and oven spring", "whole wheat vs white flour",
        "hydration percentages explained", "cold retard in the fridge",
        "storing bread to keep crust", "reviving a neglected starter",
        "discard recipes", "reading crumb structure", "salt timing",
        "mixing by hand", "cooling before slicing",
    ],
}

ANGLES = ["the basics", "common beginner mistakes", "practice tips"]


def gen(domain, topic, angle):
    prompt = (
        f"Write one short instructional passage of 4-6 sentences for a beginner "
        f"about: {topic} (in the context of {domain}), focusing on {angle}. "
        f"Plain paragraphs, no bullet lists, no headings, no thinking process, "
        f"just the passage. Concrete practical detail, under 120 words.")
    payload = {"model": MODEL, "prompt": prompt, "stream": False,
               "think": False,
               "options": {"temperature": 0.9, "num_predict": 220}}
    out = subprocess.run(
        ["curl", "-s", "--max-time", "120", "localhost:11434/api/generate",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=150)
    return json.loads(out.stdout)["response"].strip()


def main():
    random.seed(7)
    (ROOT / "corpus").mkdir(exist_ok=True)
    for domain, topics in DOMAINS.items():
        train_f = open(ROOT / "corpus" / f"{domain}-train.jsonl", "w")
        test_f = open(ROOT / "corpus" / f"{domain}-test.jsonl", "w")
        jobs = [(t, a) for t in topics for a in ANGLES]
        random.shuffle(jobs)
        for i, (topic, angle) in enumerate(jobs):
            try:
                text = gen(domain, topic, angle)
            except Exception as e:  # keep going; a thin corpus still works
                print(f"FAIL {domain}/{topic}: {e}", flush=True)
                continue
            rec = json.dumps({"topic": topic, "text": text}) + "\n"
            dest = test_f if i % 5 == 0 else train_f
            dest.write(rec)
            dest.flush()
            print(f"[{domain} {i + 1}/{len(jobs)}] {len(text)} chars",
                  flush=True)
        train_f.close()
        test_f.close()
    print("CORPUS DONE")


if __name__ == "__main__":
    main()
