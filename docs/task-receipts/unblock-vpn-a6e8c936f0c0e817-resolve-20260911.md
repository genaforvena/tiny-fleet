# Unblock receipt — vpn/a6e8c936f0c0e817/resolve

- Result: `RESOLVED`
- Owner: `vpn`
- UTC: `2026-09-11`
- Original task: `tinyfleet-publication-science-20260908/verify-freeze-independent-corpus`
- Corrected owner receipt commit: `c83974becad53281d9e95cc59f03af29c2135ebb`
- Corrected owner receipt SHA-256: `68eaf167064168f0164a195536aa03dbea0f71d7a23381071aea76cab6d21a53`
- Canonical source revision: `25fb7db7e43f2d75c96d8c339e698d143ccdd41c`

## Blocker recheck

The task was live when taken: `mesh-task audit` showed the exact unblock task as
`QUEUED vpn`, and `mesh-task take unblock/vpn/a6e8c936f0c0e817 resolve` claimed it for `vpn`.
The instruction was still correct: the corrected receipt now cites
`73c69c574a3d631a3da5ed0cd989ed10b1fa85e47015cc446b477be866c8dfbe` for
`scripts/test_study_corpus.py`, matching the file at the pinned source revision. The prior
incorrect citation was `65715079fe6fb956ef14e41547accdbfc7e1898241bc568bfeb92ecae33e17fd`.

## Artifact-backed resolution

Independent verification used a detached worktree at `25fb7db7e43f2d75c96d8c339e698d143ccdd41c`.
That revision is an ancestor of `origin/master` and changes exactly the eight scoped S02 paths;
no S03–S05 path is present in its commit diff.

Using `/home/mesh-home/tiny-fleet/.venv/bin/python` against the detached worktree:

```text
build_study_corpus.py --output <isolated>/rebuilt-study-v1
built 1600 rows
test_study_corpus.py
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

Independent predicates: 1,600 total rows; 400 per split; 100 per domain per split;
1,600 unique case IDs, source families, and normalized prompts; zero source-family split
violations; zero reference text in prompts; zero language mismatches; zero bad provenance;
manifest hashes valid; all four split hashes present in dataset registration.

This resolves only the receipt-integrity dependency. The original S02-V task must now be resumed
and settled independently; S03 remains locked until that task is `DONE/PASS`.
