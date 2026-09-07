# Frozen cross-repository report

## Scope

The comparison is a bounded sample from `lte-workstation`, not a claim about
the whole repository or about Tiny Fleet as a population. Inclusion was fixed
before analysis: the four registered changed shell/test paths plus `LICENSE`.
The old and new objects are pinned by full commit ID in the sample manifest.

## Observed structural delta

| measure | old | new | delta |
|---|---:|---:|---:|
| manifest-present files | 3 | 5 | +2 |
| bytes | 274,906 | 284,322 | +9,416 |
| median bytes | 14,167 | 7,048 | -7,119 |
| p95 bytes | 253,691 | 254,960 | +1,269 |
| text files | 1 | 1 | 0 |
| shell files | 2 | 4 | +2 |
| units | 3 | 5 | +2 |
| additions | 0 | 2 | +2 |
| modifications | 0 | 2 | +2 |

These are sample descriptors, not semantic measurements. Structural change
alone cannot establish architecture drift, behavior change, or a cross-repo
generalization.

## Arm coverage

- Structural: **PASS / descriptive only**.
- Lexical/concept: **BLOCKED**; no pinned tokenizer, normalization contract,
  or versioned concept dictionary.
- Behavioral: **BLOCKED**; no clean pinned runtime, paired native test
  capture, command record, exit codes, or output hashes.
- Generative: **BLOCKED**; no prompts, seeds, decoding settings, model digest,
  scorer revision, paired outputs, or uncertainty data.

