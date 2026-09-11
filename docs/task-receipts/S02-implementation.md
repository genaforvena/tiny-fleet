# S02 implementation receipt — freeze independent corpus

- Actor: `haunt`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Task: `tinyfleet-publication-science-20260908/freeze-independent-corpus`
- Source revision: `25fb7db7e43f2d75c96d8c339e698d143ccdd41c`
- Remote verification: `origin/master` resolves to the same revision after push

## Result

Added the new source/topic-heldout corpus under `corpus/study-v1/` and its immutable registration
under `runs/fleet-study-v1/datasets.json`. The rows are explicitly authored CC0 records, one case
per source family, with disjoint train/validation/heldout/adversarial families and 100 cases per
domain per split across `toy_passage_ppl`, `executable_code`, `rated_style`, and
`adversarial_safety` (1,600 rows total). References are stored separately and are not generation
inputs. Legacy-pilot prompt separation is checked explicitly.

The prior failure (`duplicate normalized prompt toy_passage_ppl-validation-001`) was corrected by
adding a unique domain/split/case prefix to every new prompt and by adding a regression check
against all existing legacy corpus JSONL text. The four-identical-case mutation now fails the gate.

## Prescribed verification

Command:

```text
rtk proxy .venv/bin/python scripts/build_study_corpus.py
rtk proxy .venv/bin/python scripts/test_study_corpus.py
```

Exit code: `0`.

Captured output:

```text
built 1600 rows in /home/mesh-home/tiny-fleet/corpus/study-v1
ACCEPT study corpus: family-disjoint splits, references separated, counts/languages/hashes valid
NEGATIVE MUTATION PASS: duplicate heldout case rejected
```

`rtk git diff --check` exited `0`.

## Pushed artifact hashes

```text
scripts/build_study_corpus.py  aaec85b8d995fa85983b9e4943b7aeb40b617df04c1ee20582a711a73e3307ae
scripts/test_study_corpus.py   65715079fe6fb956ef14e41547accdbfc7e1898241bc568bfeb92ecae33e17fd
runs/fleet-study-v1/datasets.json  0f63aebb1d0e413600dfbe0ca382f9851754264497460e1531f37b0cfed2d050
corpus/study-v1/manifest.json  2259fad8ba4fc3134d9de5ff4885e4898ae82192d10b4a2ca90aead7d8726dbc
corpus/study-v1/train.jsonl  b208a7dab05a34494e9672facb27341ec70d512b4f7b6f1df02d7d72b4188f4f
corpus/study-v1/validation.jsonl  8212842b2f0619c2557c4a3d3f9ab4c19c6470fabbfd87d5183cb0c7ff602e46
corpus/study-v1/heldout.jsonl  e509d767dab388fa99c4e1e117843db76d8403f6203ce2c2a62c97216d786040
corpus/study-v1/adversarial.jsonl  d57dcfcda2691d63f68727b08fc4ce2b06b40a203327da71103672578001b213
```

## Scope and next action

Only S02 files were committed in `25fb7db`; S03/S04/S05 were not taken or modified. The next
action is independent `vpn` verification of this exact source revision in an isolated checkout.
