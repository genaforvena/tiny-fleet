# S02 independent verification receipt — freeze independent corpus

- Result: `BLOCKED/FAIL`
- Task: `tinyfleet-publication-science-20260908/verify-freeze-independent-corpus`
- Owner: `vpn`
- UTC: `2026-09-11`
- Verified source revision: `25fb7db7e43f2d75c96d8c339e698d143ccdd41c`
- Source receipt: `docs/task-receipts/S02-implementation.md`
- Source receipt sha256: `d206d351da606c99251a8f2f5cfff678dd24fe2fc3f11bd11d98bee95bd4c432`

## Independent procedure and evidence

Verification used a detached worktree at the exact source revision above. The source revision is
an ancestor of `origin/master` (`bcaf6504094e9395c1ab3f5accb38dbb0404ae79`). The source commit
contains exactly the eight scoped S02 paths: the two scripts, four split JSONL files, the manifest,
and `runs/fleet-study-v1/datasets.json`; no S03–S05 path was taken or changed.

Commands and results:

```text
rtk proxy .venv/bin/python scripts/build_study_corpus.py --output <isolated-output>/study-v1
exit 0
built 1600 rows in <isolated-output>/study-v1

rtk proxy env PYTHONPATH=<isolated-checkout>/scripts .venv/bin/python <isolated-checkout>/scripts/test_study_corpus.py
exit 0
ACCEPT study corpus: family-disjoint splits, references separated, counts/languages/hashes valid
NEGATIVE MUTATION PASS: duplicate heldout case rejected
```

The isolated rebuild matched the tracked split hashes byte-for-byte:

```text
train       b208a7dab05a34494e9672facb27341ec70d512b4f7b6f1df02d7d72b4188f4f
validation  8212842b2f0619c2557c4a3d3f9ab4c19c6470fabbfd87d5183cb0c7ff602e46
heldout     e509d767dab388fa99c4e1e117843db76d8403f6203ce2c2a62c97216d786040
adversarial d57dcfcda2691d63f68727b08fc4ce2b06b40a203327da71103672578001b213
```

Independent recomputation over the source artifacts found:

```text
rows total: 1600
rows per split/domain: 400 per split; 100 per domain in each split
unique case_id/source_family/normalized prompt: 1600/1600/1600
source-family split violations: 0
reference text in prompt: 0
language mismatches: 0
bad provenance records: 0
dataset registration and manifest split hashes: PASS
cross-split 5-gram Jaccard candidates >= 0.8: 0
legacy pilot prompt reuse: 0
```

The four-identical-case mutation was independently exercised by the prescribed test and was
rejected, satisfying the negative control. The rebuild also produced the same four split hashes,
so the checked-in corpus is the reproducible output of the source script.

## Failed receipt-integrity predicate

The implementation receipt cites
`65715079fe6fb956ef14e41547accdbfc7e1898241bc568bfeb92ecae33e17fd` for
`scripts/test_study_corpus.py`, but the file at the claimed source revision hashes to
`73c69c574a3d631a3da5ed0cd989ed10b1fa85e47015cc446b477be866c8dfbe`.

This fails the receipt-integrity predicate even though the corpus acceptance checks pass. The
owner receipt must not be treated as canonical until corrected and repushed.

## Keyed Haunt correction request

Owner `haunt`: correct `docs/task-receipts/S02-implementation.md` so the cited hash for
`scripts/test_study_corpus.py` is exactly
`73c69c574a3d631a3da5ed0cd989ed10b1fa85e47015cc446b477be866c8dfbe`, preserve the canonical
S02 source revision `25fb7db7e43f2d75c96d8c339e698d143ccdd41c`, commit and push the corrected
receipt, and report the new receipt commit and sha256. Do not alter S02 implementation files or
take S03–S05. After that correction is repushed, `vpn` must independently recheck the corrected
receipt before settlement.

## Settlement

`BLOCKED/FAIL`: receipt-integrity mismatch above. The verification gate remains open pending the
keyed Haunt correction and a fresh independent recheck. S03–S05 remain out of scope and were not
taken.
