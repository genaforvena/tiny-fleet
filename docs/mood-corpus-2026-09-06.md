# Operator-mood corpus

This is the first repository artifact for `tinyfleet-specialists/mood-corpus`.
It contains 36 train, 8 held-out, and 4 adversarial RU/EN cases derived from
the local `~/.mesh/voice-in.log` operator-mood ledger. The records are
semantic paraphrases, not copied messages: raw private text, URLs, hostnames,
paths, credentials, and personal names were excluded. Every row is marked
`provenance.redacted=true` and cites the internal ledger as its source.

The split is chronological and disjoint by source/time bucket:

| split | ledger buckets | rows | languages |
|---|---|---:|---|
| train | 2026-08-30 through 2026-09-03 | 36 | RU 20, EN 16 |
| heldout | 2026-09-04 through 2026-09-05 | 8 | RU 4, EN 4 |
| adversarial | 2026-09-06 | 4 | RU 2, EN 2 |

`expected_label` is `positive`, `negative`, `mixed`, or `neutral`. Adversarial
cases deliberately contain operational facts without affective evidence and
therefore require `expected_action=abstain`.

Regenerate with:

```text
python3 scripts/mk_mood_corpus.py
```

The generator is dependency-free and deterministic. Generated file hashes from
the verified run are recorded in its output; the files are the data artifact,
not the private ledger.
