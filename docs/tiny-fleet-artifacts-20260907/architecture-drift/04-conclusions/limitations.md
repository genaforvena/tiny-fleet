# Limitations and unresolved blocks

The external sample contains one repository and one parent-to-child window.
The selection is path-bounded and intentionally excludes all other tracked
files. The structural summary therefore cannot stand in for a repository-wide
architecture comparison.

The lexical arm has no pinned tokenizer, normalization rules, or concept
dictionary. The behavioral arm has no clean runtime and no paired execution
capture. The generative arm has no reproducible prompt/seed/model/scorer
binding, raw outputs, or uncertainty record. These are missing observations,
not measured zeros. The coverage loss is consequently 3 of 4 declared arms
blocked.

The supply decision is explicit: obtain a separately pinned runtime and an
old-snapshot-equivalent board test (or preregister a comparable replacement);
obtain tokenizer/dictionary and generative raw records separately. Until then,
do not rerun on moving `HEAD` or substitute zeros for missing observations. The
frozen sample manifest must remain unchanged.
