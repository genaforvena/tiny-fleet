# Review verification receipt — 2026-09-08

Actor: tg. Repository: /home/mesh-home/tiny-fleet.
Reviewed source revision: 62ba7282505eb447486b9a18468cce72457171ce.
Scope: review and task creation, not implementation of the queued work.

## Observed checks

| Command/check | Observed result |
|---|---|
| `.venv/bin/python scripts/fleet_benchmark.py --test` | exit 0; 24/24 contract/inventory cases |
| `.venv/bin/python scripts/operator_policy.py --test` | exit 0; 41/41 heldout, 14/14 adversarial, 8/8 structured decisions; precedence mutation fails as expected |
| `.venv/bin/python scripts/test_deep_evaluation.py` | exit 0; 6 existing tests |
| `.venv/bin/python scripts/test_persona_code.py` | exit 0; 2/2 |
| `.venv/bin/python scripts/persona_code.py self-test --manifest runs/persona-code/manifest.json` | exit 0; self-test ok |
| `mesh-task --test` | exit 0; canonical ask/task, exact owner, lease/progress, typed block/resume, artifact hash, idempotent done smoke-test OK |
| Parse all four plan TSVs and compare exact owner/slug/description to live chain JSON | PASS; 80 rows, 40 haunt / 40 vpn, strict pairs, no duplicate slugs, 40 unique implementation sections |
| Read registered chain state | Four roots open, dispatch=sent at observation; no claim that execution began |
| Review/applications Markdown relative links | All resolved at verification time |

Commands were invoked with `rtk proxy` from the appropriate repository.
[Live registration snapshot](ledger-registration-20260908.json) includes observation time, exact IDs, owner/status, chain paths and counts.

## Independently reproduced defects

The following probe uses the existing temporary fixture builder and an in-memory read patch. It does not edit production code or model artifacts.

```python
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0, "scripts")
from test_deep_evaluation import DeepEvaluationValidatorTests
from deep_evaluation import validate_run
from router import route_query

root = DeepEvaluationValidatorTests().make_run()
original = Path.read_text

def altered(path, *args, **kwargs):
    content = original(path, *args, **kwargs)
    if path.name == "predictions.jsonl":
        content += content.splitlines()[0] + "\n"
    return content

with patch.object(Path, "read_text", altered):
    print("duplicate_predictions", validate_run(root))
with np.errstate(invalid="ignore", divide="ignore"):
    print("zero_embedding", route_query(
        "zzzz",
        {"guitar": np.array([1., 0.]), "sourdough": np.array([0., 1.])},
        lambda texts: np.array([[0., 0.]])
    )[0])
```

Actual output:

```text
duplicate_predictions ACCEPT
zero_embedding specialist:guitar
corpus/persona-heldout.jsonl rows 4 unique_texts 1
corpus/code-heldout.jsonl rows 4 unique_texts 1
```

The last two lines came from reading those JSONL files and counting distinct `text` fields. These are failure evidence at the reviewed revision, not desired regression-test output. After repairs the duplicate/zero-vector cases must reject/abstain.

## Plan audit corrections made before registration

A separate read-only review checked the task plan. Corrected: supported ledger blocker type; separate case/rendered-input hashes; isolated verifier output directories; bounded seed-17 verification smoke with declared tolerance; data no-go versus runtime block; explicit operator-policy robustness task; D04 label freezing before the existing external analysis; clear query-rewrite versus encoder baseline; priority order of application pilots. Then all registered step descriptions were compared byte-for-byte with their TSV source.

## What remains

All 80 implementation/verification steps remain work to execute. Existing runtime, closeout, real-mesh pilot and external-study chains remain distinct, with nine unfinished steps at initial review. Strong scientific claims and deployment eligibility remain unproven. No new training, live dispatch, mesh route, scheduler, model deployment, external paper submission or release announcement was performed.

Exact first next command for haunt:

```bash
rtk proxy env MESH_TASK_ACTOR=haunt mesh-task take tinyfleet-publication-science-20260908 reconcile-evidence
```

Read C01 and the global rules in [the plan](superpowers/plans/2026-09-08-publication-science.md), then submit its artifact to the separate vpn gate. Board-dispatch exploration is B01–B04 and remains advisory/offline.
