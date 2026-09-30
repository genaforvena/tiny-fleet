# Dictionary prerequisite packet — typed operator-input blocker

Result: `BLOCKED/operator-input` (2026-09-11T22:11:45Z)

- Resolver: `unblock/adint/4f1b25c11bcea743/resolve`
- Parent: `unblock/haunt/62c0662129fa8ee9/resolve`
- Actor: `adint`
- Repository: `/home/mesh-home/tiny-fleet`

## Evidence

The dispatch description names five scientific inputs that remain operator-missing:
dictionary source, language, normalization, immutable version, and corpus. A repository
inspection found no tracked dictionary/lexicon/vocabulary/word-list file and no approved
operator-selected dictionary declaration:

```text
cd /home/mesh-home/tiny-fleet
git ls-files | rg -i '(^|/)(dictionary|lexicon|vocab|word[-_]?list)([^/]*|/)' || true
rg -l -i 'approved dictionary|operator-selected dictionary|dictionary source' \
  docs runs scripts --glob '!docs/task-receipts/*' | head -40
exit=0; no matching paths
```

Existing receipts establish that the runtime and bounded six-case smoke are available, but
they do not establish a selected scientific dictionary. The A08 synthetic correction fixture
and prose-only references are not an approved install dictionary. Selecting one or installing
a package autonomously would change the experiment, so no code, package, model, or corpus was
changed by this resolver.

## Exact operator-action packet

Supply and freeze all five fields in a new manifest; placeholders are intentionally not valid:

```text
source: <approved dictionary/lexicon URI or repository-relative path>
language: <ISO language or explicit language set>
normalization: <exact Unicode/token normalization policy>
version: <immutable release, commit, or content checksum>
corpus: <immutable corpus path/URI plus SHA-256>
```

The manifest must record the SHA-256 of the source/corpus bytes (or immutable upstream
revision), and the preflight must print the effective language and normalization policy.

## Exact retry condition and command

After the five fields are frozen and hashed, rerun the parent prerequisite check and record its
versions, command, output hashes, and typed verdict in a new receipt. Only then retry:

```bash
cd /home/mesh-home/tiny-fleet
timeout 240 .venv/bin/python scripts/bbywvy_test.py
```

Until that manifest exists, the parent remains blocked. This packet does not claim a dictionary
result and does not resume the parent task.
