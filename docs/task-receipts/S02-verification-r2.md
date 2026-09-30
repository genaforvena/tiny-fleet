# S02 independent verification receipt — corrected receipt recheck

- Result: `PASS`
- Task: `tinyfleet-publication-science-20260908/verify-freeze-independent-corpus`
- Owner: `vpn`
- UTC: `2026-09-11`
- Verified source revision: `25fb7db7e43f2d75c96d8c339e698d143ccdd41c`
- Source receipt commit: `c83974becad53281d9e95cc59f03af29c2135ebb`
- Source receipt SHA-256: `68eaf167064168f0164a195536aa03dbea0f71d7a23381071aea76cab6d21a53`

## Independent procedure and evidence

The source revision was checked in a detached worktree and confirmed as an ancestor of
`origin/master`. Its commit diff contains exactly the eight scoped S02 paths: the two corpus
scripts, four split JSONL files, the manifest, and `runs/fleet-study-v1/datasets.json`; no S03–S05
path was taken or changed.

The corrected implementation receipt cites
`73c69c574a3d631a3da5ed0cd989ed10b1fa85e47015cc446b477be866c8dfbe` for
`scripts/test_study_corpus.py`, and independent hashing of that file at the pinned source revision
matched exactly. The corrected receipt itself hashed to
`68eaf167064168f0164a195536aa03dbea0f71d7a23381071aea76cab6d21a53`.

Using the canonical repository virtualenv against the detached worktree:

```text
build_study_corpus.py --output <isolated>/rebuilt-study-v1
built 1600 rows
test_study_corpus.py
ACCEPT study corpus: family-disjoint splits, references separated, counts/languages/hashes valid
NEGATIVE MUTATION PASS: duplicate heldout case rejected
```

The isolated rebuild matched tracked split hashes byte-for-byte:

```text
train       b208a7dab05a34494e9672facb27341ec70d512b4f7b6f1df02d7d72b4188f4f
validation  8212842b2f0619c2557c4a3d3f9ab4c19c6470fabbfd87d5183cb0c7ff602e46
heldout     e509d767dab388fa99c4e1e117843db76d8403f6203ce2c2a62c97216d786040
adversarial d57dcfcda2691d63f68727b08fc4ce2b06b40a203327da71103672578001b213
```

Independent structural predicates passed: 1,600 total rows; 400 per split; 100 per domain per
split; 1,600 unique case IDs, source families, and normalized prompts; zero source-family split
violations; zero reference text in prompts; zero language mismatches; zero bad provenance;
manifest hashes valid; all four split hashes present in dataset registration. The prescribed test
also independently exercised the duplicate-case negative control and legacy-prompt regression.

S02-V is now eligible for `DONE/PASS`. S03 remains unreleased and was not taken.
