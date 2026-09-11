# Install-unblock resolver receipt — typed operator-input block

Date: 2026-09-11 UTC  
Task: `unblock/haunt/01fdec883ff0475d/resolve`  
Parent: `haunt-install-unblock-20260907/install-and-retry-tinyfleet`  
Actor: `haunt`  
Repository: `/home/mesh-home/tiny-fleet`

## Result

`BLOCKED/operator-input`: the runtime/model installation is already repaired and verified, but
the dictionary arm cannot be retried without an operator-selected scientific input. No safe
repository-local prerequisite can supply that decision.

## Evidence checked

- `docs/task-receipts/haunt-install-unblock-20260908.md` records a successful protobuf/runtime
  repair and six-case BbyWVY smoke generation, then the typed state `BLOCKED_DICTIONARY_INPUT`.
- `docs/task-receipts/haunt-install-unblock-20260909.md` records that the repository has no
  dictionary, lexicon, vocabulary, or word-list artifact and no operator decision selecting one.
- The existing resolver receipts through 2026-09-11 repeat the same five missing inputs; selecting
  a public lexicon or installing a package here would invent the experimental input.

## Exact operator action required

Supply one immutable input record containing all five fields:

```text
source: <dataset name and canonical URL or local path>
language: <language/locale>
normalization: <exact Unicode/token normalization policy>
version: <immutable release/tag/commit and retrieval date>
corpus: <exact file/path plus SHA256>
```

The unblock condition is satisfied only when the source is retrievable, the version is immutable,
the corpus hash matches the supplied record, and the normalization policy is executable by the
dictionary-arm code. A prose preference or an unpinned package name is insufficient.

## Exact retry after the input is supplied

From `/home/mesh-home/tiny-fleet`, record the supplied input in the parent registration/config,
then run the parent dependency preflight and capture its typed result:

```bash
cd /home/mesh-home/tiny-fleet
MESH_TASK_ACTOR=haunt mesh-task progress haunt-install-unblock-20260907 install-and-retry-tinyfleet \
  docs/task-receipts/unblock-haunt-01fdec883ff0475d-20260911.md \
  "operator supplied dictionary source/language/normalization/version/corpus; rerun dependency preflight" \
  "after preflight, attach versions, corpus SHA256, and typed result"
```

Then execute the parent task's registered preflight command, preserving its stdout/stderr and
versions in a new receipt. Do not resume the S06 study from this resolver until that preflight
receipt explicitly verifies the dictionary prerequisite.

No package, corpus, model file, or runtime configuration was changed by this resolver.
