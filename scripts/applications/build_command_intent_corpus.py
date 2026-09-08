#!/usr/bin/env python3
"""Build the frozen CC0 A01 source-family split manifest."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
OUTPUT = ROOT / "corpus/applications/command-intents/manifest.json"
FUNCTIONS = (
    ("list notes", "list_notes", {}), ("read note about {x}", "read_note", "query"),
    ("search notes for {x}", "search_notes", "query"), ("show calendar", "show_calendar", {}),
    ("list reminders", "list_reminders", {}), ("find contact {x}", "find_contact", "name"),
    ("show weather for {x}", "show_weather", "place"), ("show battery", "inspect_battery", {}),
    ("list downloads", "list_downloads", {}), ("open help", "open_help", {}),
)
VALUES = ("Paris", "Kyiv", "Lima", "Oslo", "Riga", "Seoul", "Tokyo", "Tunis", "Ufa", "Zagreb")


def known(case_id, split, family, template, function, argument, value):
    arguments = {} if argument == {} else {argument: value}
    return {"case_id": case_id, "split": split, "source_family": family,
            "text": template.format(x=value),
            "reference": {"function": function, "arguments": arguments, "unknown": False}}


def unknown(case_id, split, family, text):
    return {"case_id": case_id, "split": split, "source_family": family, "text": text,
            "reference": {"function": None, "arguments": {}, "unknown": True}}


def main():
    cases = []
    for split, prefix, offset in (("development", "dev", 0), ("validation", "val", 10)):
        for index, (template, function, argument) in enumerate(FUNCTIONS):
            cases.append(known(f"{prefix}-{index:03}", split, f"{prefix}-template-{index:02}", template, function, argument, VALUES[(index + offset) % len(VALUES)]))
    for index in range(70):
        template, function, argument = FUNCTIONS[index % len(FUNCTIONS)]
        cases.append(known(f"heldout-{index:03}", "heldout", f"heldout-known-{index:03}", template, function, argument, VALUES[index % len(VALUES)]))
    for index in range(50):
        cases.append(unknown(f"heldout-ood-{index:03}", "heldout", f"heldout-ood-{index:03}", f"delete synthetic note {index}"))
    manifest = {"schema_version": 1,
                "study": {"id": "A01-command-intents", "data_license": "CC0-1.0", "source": "synthetic safe command templates", "frozen": "2026-09-08"},
                "model_provenance": {"functiongemma": {"model_id": "google/functiongemma-270m-it", "revision": "unavailable-gated-no-credential-2026-09-08", "license": "Gemma terms; gated access"}},
                "cases": cases}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
