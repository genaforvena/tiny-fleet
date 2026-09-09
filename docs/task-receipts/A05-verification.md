# A05 independent verification receipt — duplicate issue detection

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Submitted source revision: `6fb49c8a3ef88dd9a6e3124c7913a7265a960641`
- UTC: `2026-09-09T19:06:51Z`
- Verdict: **PASS**

## Isolation and source inspection

The submitted revision was checked out detached in `/tmp/a05-verify.yTiM8F/source`.
The worktree was clean at the submitted revision. `git diff --check` exited 0.
The commit is contained in local `master` and remote `origin/master` (`b6c97e053c06a7f2d29d86dd258b03c7e1d7df8`).
The exact submitted diff contains the ten scoped A05 files: the validator/runner,
its six-test contract suite, the manifest, study documentation, check output,
three raw baseline files, summary, and implementation receipt. No model weights,
network calls, runtime deployment, or live-routing changes are present.

## Commands and artifacts

The prescribed commands were attempted first in the isolated worktree:

```text
rtk proxy .venv/bin/python scripts/test_app_duplicate_incidents.py — exit 1
rtk proxy .venv/bin/python scripts/applications/duplicate_incidents.py --phase baseline --run-dir /tmp/a05-verify.yTiM8F/run — exit 1
```

Both failed before Python started because `.venv/bin/python` is absent in the
submitted checkout. Their stderr artifact SHA-256 is
`4ab2b4e4bff6ea0f38c9d66772fb053253bc5c1b882d40a71d5d5697af8aea2d`.

Using the available dependency-free interpreter and a fresh output directory:

```text
rtk proxy python3 scripts/test_app_duplicate_incidents.py — exit 0 (6 tests)
  stdout SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  stderr SHA-256: a1165af1892b2f480504bbb028d7537c1e493016a8b148a22a6db8681f68bcd1
rtk proxy python3 scripts/applications/duplicate_incidents.py --phase baseline --run-dir /tmp/a05-verify.yTiM8F/run-python3 --manifest corpus/applications/duplicate-incidents/manifest.json — exit 0
  stdout SHA-256: 19b5ee6c477794cbec2124ac31d5743a333a9137b0a4fc62d44ae628f296d868
  stderr SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

The independently generated raw outputs match the submitted hashes exactly:

```text
bm25-raw.jsonl          fae2c57bbe3e49e6ae69379bf5d609bd72d9cd1677392280793cd61d72e5f116
character-ngram-raw    0e032154eeac9f234efa48a35cecc6e38e6713e9df0abc9dbf13e1a46bc97683
normalized-hash-raw    ddf34d546572020a1e89118973c55a679c30067ae9a29736cd7d32701d29221d
```

The source manifest hash is `333182515d1011a50749c32d941d7da7e3b2a32bab2e3675567e5ab3aa208aff`.
The submitted summary hash is `081346815da1b858d66983257ab45e9da30fa63d6d96f2bcb8f98876ce626603`.
Summary hashes are expected to vary when regenerated because latency is measured;
the raw-output hashes are the stable result artifact.

## Independent checks

Recomputation from the raw heldout rows found 120 cases from 120 unique source
families: 100 positives and 20 explicit no-match cases. Results were:

| baseline | pair precision | pair recall | false accepts | abstentions |
|---|---:|---:|---:|---:|
| normalized-hash | 80/80 = 1.00 (95% Wilson 0.9542–1.0000) | 80/100 = 0.80 (0.7112–0.8666) | 0/20 = 0.00 (0.0000–0.1611) | 40/120 |
| character-ngram | 100/120 = 0.8333 (0.7565–0.8894) | 100/100 = 1.00 (0.9630–1.0000) | 20/20 = 1.00 (0.8389–1.0000) | 0/120 |
| BM25 | 100/120 = 0.8333 (0.7565–0.8894) | 100/100 = 1.00 (0.9630–1.0000) | 20/20 = 1.00 (0.8389–1.0000) | 0/120 |

Candidate-retrieval recall is 1.00 for every baseline. The model arm remains
explicitly unavailable, and the recorded verdict `INCONCLUSIVE` is justified:
the simple baseline does not simultaneously satisfy precision >=95%, recall
>=95%, and false acceptance <=5%; no model benefit is claimed.

An unseen heldout-shaped negative (`service error 999 unrelated resolution note`)
was evaluated independently. Normalized hashing abstained and scored correct;
BM25 falsely accepted `hold-inc-000`, demonstrating the known hard-negative
failure outside the author’s positive examples.

The required mutation changed normalized-hash’s `len(matches) != 1` guard to
`len(matches) != 0`. The isolated test run then exited 1 with one assertion
failure and one baseline error (stdout SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr
SHA-256 `1689ba639d544be1567e4bae3e2503784b9ca86f459a78db89c5f340ecb25f41`).
The original guard was restored and the test rerun exited 0 (stderr SHA-256
`e2331465a96b4b361c90ccfc5aca6d41549bf8eb66a58b3be0037ddf5db982da`).

## Exact next action

This verification is complete. Commit and push this receipt, verify remote
containment, then settle only
`tinyfleet-applications-20260908/verify-duplicate-incidents`; do not dispatch
or modify any later application step.
