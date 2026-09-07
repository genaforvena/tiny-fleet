# Limitations and unresolved blocks

The external sample contains one repository and one parent-to-child window.
The selection is path-bounded and intentionally excludes all other tracked
files. The structural summary therefore cannot stand in for a repository-wide
architecture comparison.

The lexical arm has no pinned tokenizer, normalization rules, or concept
dictionary. The generative arm has no reproducible prompt/seed/model/scorer
binding, raw outputs, or uncertainty record. These are missing observations,
not measured zeros. The coverage loss is consequently 3 of 4 declared arms
blocked.

The behavioral parity retry is bounded: the old snapshot's absent
`scripts/test-mesh-board` is replaced by common `scripts/uxn/test-board-check`,
run from both immutable archives under `03-analysis/runtime-lock.json`. It does
not establish semantic drift. Obtain tokenizer/dictionary and generative raw
records separately. Until then,
do not rerun on moving `HEAD` or substitute zeros for missing observations. The
frozen sample manifest must remain unchanged.
