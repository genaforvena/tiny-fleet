# S01-V independent verification receipt — preregister fleet study

- Verifier: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- Exact source commit verified: `a63239fe07436bae69b03741144889d224537296`
- Verification checkout: fresh detached isolated worktree at `/tmp/tinyfleet-s01-verify-KInQik`
- Verdict: **PASS**

## Exact acceptance checks

The isolated checkout was clean at the submitted source commit. The mandated syntax check was run
against that checkout with the repository's absolute interpreter because detached worktrees do not
carry the ignored local `.venv` directory:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python -m json.tool \
  /tmp/tinyfleet-s01-verify-KInQik/runs/fleet-study-v1/registration.json
exit 0
```

`rtk git diff --check` in the isolated checkout exited `0`. The registration contains exactly five
arms (four controls and one candidate), three separate outcomes, 100 independent units for each
quality domain plus 100 adversarial units, 10,000 paired-bootstrap replicates at 95% confidence,
seeds `[17, 29, 43]`, the stated 97-to-100 precision rationale, explicit quality/safety/coverage
margins, and positive training/wall/GPU/token resource caps. Its split, freeze, missing-data, and
decision policies prohibit outcome-dependent arm, seed, slice, metric, or domain selection.

Independent audit output:

```text
INDEPENDENT AUDIT PASS: arms=5 domains=3 units={'toy_passage_ppl': 100, 'executable_code': 100, 'rated_style': 100, 'adversarial_safety': 100} bootstrap=10000 seeds=[17, 29, 43]
```

An independent in-memory mutation removed one comparison arm. The audit rejected it:

```text
NEGATIVE MUTATION PASS: missing comparison arm rejected
```

No held-out prediction output exists under `runs/fleet-study-v1` at this commit; only the
registration is present. The submitted commit contains only the three registration documents and
the implementation receipt named by S01.

## Recomputed artifact hashes

```text
docs/study-registration.md
7dd204ac20774a87756fd064363a3a67768ad2236d6396caabee92bd6b6bad0a
runs/fleet-study-v1/registration.json
2498cc3146b673751f15106d39c31b059188c9af60668dfa6998e00eb5e230ba
docs/related-work.md
8c3910d8fa3ecfc79917269af2b78ac0f8eb6cf2091c20a14215e61eece0abd0
docs/task-receipts/S01-implementation.md
80e000271ad78271857ef80bb7a81db6b24165785ffaaba7ad55558ad9566dc0
```

The hashes match the blobs at the exact submitted commit and the current remote ancestor.

## Residual limitation

The ignored `.venv` is not part of the isolated checkout, so the literal relative `.venv/bin/python`
path cannot be invoked from a fresh worktree. The same pinned node interpreter ran the pure-stdlib
JSON check successfully; this is an environment-reproduction limitation, not a registration
predicate failure.

## Next action

S01-V is accepted. The chain may release `freeze-independent-corpus`; no S03, S04, or S05 task was
taken or modified by this verification.
