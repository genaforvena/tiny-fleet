# C02 independent verification receipt — dataset boundaries

- Verdict: **PASS**
- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Verification UTC: `2026-09-11`
- Exact source revision: `f2f3ebcfbbb19af0fb5ec59b5b06301706e2da73`
- Isolated checkout: detached worktree at `/tmp/tinyfleet-c02-v.qaRZMj`
- Remote containment: source revision is an ancestor of fetched `origin/master`
  (`1341eacdc60f1f6fe2e38e6cfd46d92081d65fa7`)

## Scope and source inspection

Inspected the implementation receipt and the exact C02 files at the source revision:

- `scripts/deep_evaluation.py`
- `scripts/test_deep_evaluation.py`
- `docs/deep-evaluation-contract.md`

Recomputed source SHA-256 values:

```text
ac755b58efdaff178f95b79388391a5250ba4cfa9c2b8b514267a88e3a6f8aba  scripts/deep_evaluation.py
71c02652547eb5a64c99784b90679809bb58a1587739c02b85f818503f733657  scripts/test_deep_evaluation.py
fc8565fd9ddf68dc94b1c40f22b2baf7142db46914e1a69d6ce4a0d9603f5dc4  docs/deep-evaluation-contract.md
```

## Independent checks

Command, run from the detached checkout with the node-local project interpreter:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_deep_evaluation.py
```

- Exit: `0`
- Result: `Ran 12 tests ... OK`
- Output artifact: `/tmp/c02-v-independent-full.1106867.txt`
- Output SHA-256: `fc523972b6a1714a1d54810e5e0468e39c4bd3e3d5232a86ffd2e808fc829bd9`

The 12 tests include valid v2 acceptance and rejection of missing artifacts, cross-split case
leakage, source/cutoff boundary violations, hash mismatch, prediction cardinality, duplicate IDs,
normalized prompt leakage, source-family overlap, empty required splits, malformed typed fields,
and symlink escape without opening the target.

Additional counterexample, independent of the checked-in positive fixture: changed the validation
prompt to full-width Unicode with irregular whitespace and a case change, updated only its dataset
hash, and validated the run. The validator rejected the NFKC/casefold/whitespace-equivalent prompt
as required:

```text
REJECT leakage normalized prompt crosses train/validation
```

- Exit: `0` (expected rejection observed)
- Output artifact: `/tmp/c02-v-counter.1149736.txt`
- Output SHA-256: `032420fd39ee6c31e5e14b8b281c54a73b8aa494597870ae820835708dba9c48`

Remote verification:

```text
git fetch --quiet origin master
git merge-base --is-ancestor f2f3ebcfbbb19af0fb5ec59b5b06301706e2da73 origin/master
```

Both commands completed successfully. The source commit is contained by the fetched remote branch.

## Residual limitations

`git diff --check f2f3ebc^ f2f3ebc` reports one pre-existing trailing-space line in the Markdown
version marker (`docs/deep-evaluation-contract.md:4`); this does not affect the executable contract
checks. No claim is made beyond the C02 acceptance predicates.
