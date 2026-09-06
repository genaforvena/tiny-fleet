# Review: deep-evaluation methodology and fixtures

Date: 2026-09-06
Chain step: `tinyfleet-specialists/review-eval-method`

## Result

The dependency-free validator correctly fails closed for the five implemented contract controls:

- duplicate case or normalized row across splits: `REJECT leakage`
- train/heldout source overlap or post-cutoff heldout row: `REJECT split-boundary`
- missing required report file: `REJECT missing-artifact`
- changed dataset/config hash or row count: `REJECT manifest-mismatch`
- unknown or incomplete prediction case/model pairs: `REJECT prediction-cardinality`

The valid fixture is accepted only when all required files, hashes, row counts, split metadata, and
prediction pairs agree.

## Verification

Commands run from `/home/mesh-home/tiny-fleet`:

```text
python3 scripts/test_deep_evaluation.py
Ran 6 tests in 0.010s
OK

PYTHONPATH=scripts python3 -m unittest -v scripts/test_deep_evaluation.py
Ran 6 tests in 0.010s
OK

python3 -m py_compile scripts/deep_evaluation.py scripts/test_deep_evaluation.py
```

The module-style invocation requires `PYTHONPATH=scripts`; the direct script invocation is the
repository's working entrypoint.

## Finding: routing/adversarial contents are not validated

As a mutation check, replacing either `routing.tsv` or `adversarial.tsv` in the complete fixture
with the single line `FORGED unsafe route accepted` still returned `ACCEPT`. The validator checks
that these files exist, but it does not parse their schemas, reconcile their rows with predictions,
or reject unsafe routes/forbidden outputs.

Therefore the current gates detect missing routing/adversarial artifacts, but do **not** yet detect
unsafe routing or adversarial failures. A follow-up implementation should add schema/cardinality
and forbidden-output assertions for those two tables before treating the specialist result as
publishable.

No source code was changed in this review step.
