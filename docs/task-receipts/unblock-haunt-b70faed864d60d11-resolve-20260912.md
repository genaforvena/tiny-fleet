# Resolver receipt — `unblock/haunt/b70faed864d60d11/resolve`

- Date: 2026-09-12 UTC
- Owner: `haunt`
- Parent: `haunt-install-unblock-20260907/install-and-retry-tinyfleet`
- Repository revision inspected: `78c346b15a343d8126f63bd77e6517956818173d`
- Result: `BLOCKED/operator-input` (`BLOCKED_DICTIONARY_INPUT`)

## Diagnosis

The parent receipt confirms that the protobuf/runtime repair and six-case BbyWVY
generation smoke succeeded. It also says that smoke is not a frozen study bundle
and leaves the dictionary arm blocked. The current `scripts/bbywvy_test.py`
contains only the six generative cases; it has no dictionary arm or command that
can consume a dictionary corpus.

There is now a separate, versioned lexical tool contract: `scripts/drift_lexical.py`
reads `docs/concepts-v1.json`, applies Unicode `casefold` plus the declared
`(?u)\\b[\\w]+\\b` tokenizer, and analyzes D01 old/new extraction artifacts.
`docs/task-receipts/D02-verification.md` records an independent pass for that
tool. This is architectural-drift analysis, not the missing dictionary input for
the parent install task: it does not identify an operator-selected dictionary
dataset, its study language, or a corpus approved for that task. Reusing it would
silently change the experiment.

Evidence inspected:

- `docs/task-receipts/haunt-install-unblock-20260908.md`
- `docs/task-receipts/unblock-haunt-69db9419928a4a06-20260911.md`
- `docs/task-receipts/D02-implementation.md` and `D02-verification.md`
- `scripts/bbywvy_test.py`, `scripts/drift_lexical.py`, and `docs/concepts-v1.json`
- Parent task status: blocked on `operator-input`

## Exact operator input required

Add a tracked immutable study-input record and corpus with these fields:

```yaml
source: <operator-approved dictionary/lexicon dataset and canonical URL or local source>
language: <language or locale covered by this study>
normalization: <executable Unicode normalization and tokenization policy>
version: <immutable release/commit and source checksum, with retrieval date>
corpus: <exact corpus path and SHA-256 of the bytes used>
```

The source and corpus must be selected for the parent study, not inferred from the
D02 concept list or installed as an unpinned package. The corpus digest must match
the bytes consumed, and the normalization policy must be executable and recorded.
Until those inputs exist, there is no safe local prerequisite to implement: any
choice would supply a scientific input the task explicitly leaves to the operator.

## Exact next action

Once the record and corpus are present, verify the corpus SHA-256, then run the
parent study's dictionary-arm command and dependency preflight, recording exact
versions, command output, and artifact hashes in a new receipt. The existing
`timeout 240 .venv/bin/python scripts/bbywvy_test.py` command may be rerun only
for its six-case runtime smoke; it cannot clear this dictionary blocker. Resume
the parent task only after the dictionary arm produces its own verified result.

No source, package, corpus, model, or runtime configuration was changed by this
resolver.
