# C03 independent verification receipt — prediction identity

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Submitted implementation receipt: `docs/task-receipts/C03-implementation.md`
- Implementation receipt SHA-256: `2a2c9ec6b4faddcc20d2265c64e213ccd5c437d822b393a2bec7e14e9357b597`
- Exact source revision verified: `f9145e840ae5c519f3f9bc3b65c9109332428dfb`
- Isolation: clean detached clone at `/tmp/tinyfleet-c03-vfy.jcV0I1/repo`; existing Tiny Fleet `.venv` was linked into that temporary clone only because it is untracked and absent from the Git checkout.

## Checks and evidence

1. Prescribed check, from the isolated checkout:

   ```text
   Command: rtk proxy .venv/bin/python scripts/test_deep_evaluation.py
   Exit: 0
   Output: Ran 18 tests in 0.037s; OK
   stdout artifact: /tmp/tinyfleet-c03-vfy.jcV0I1/restored.stdout
   stdout SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
   stderr artifact: /tmp/tinyfleet-c03-vfy.jcV0I1/restored.stderr
   stderr SHA-256: eee9eca4b167c9dd35407f7031a553bd026e80959e9a95c986f6f52a3a0ab3c9
   ```

2. Load-bearing mutation: changed the duplicate-cardinality guard from `if duplicates:` to
   `if False and duplicates:` in the isolated copy. The same command exited `1`; the duplicate
   test failed because the validator then reported `expected=4 observed=5` instead of rejecting
   the duplicate. This proves the gate observes the duplicate guard, not merely test startup.

   ```text
   stderr artifact: /tmp/tinyfleet-c03-vfy.jcV0I1/mutated.stderr
   stderr SHA-256: 22f42d7ae0d316c86568e68056decbc34ea69f5f85c878435be9842afd222c92
   ```

3. Independent negative case: constructed a fresh fixture through the test fixture builder,
   appended a duplicate `(heldout-1, base, 17, 0)` prediction, and called `validate_run` directly.
   It exited `0` only because the expected `ValidationError` was caught, with:

   ```text
   REJECT prediction-cardinality duplicate ('heldout-1', 'base', 17, 0)
   ```

   Output artifact: `/tmp/tinyfleet-c03-vfy.jcV0I1/independent-negative.stdout`
   Output SHA-256: `a6659fb72eb018394fad3346b6c0d1401dabc11065b7d0822e0c1daed1067fad`

4. Source and scope inspection:

   - The validator uses exact Counter equality over `(case_id, model, seed, repetition)` and
     separately rejects duplicate observed keys.
   - Required typed fields, input hashes, status/error reasons, model IDs, seeds/repetitions,
     rendering/config digests, raw-output schema, migration report, dataset containment and
     referenced model-artifact hashes are checked in the pinned source.
   - `f9145e8` changes only `scripts/deep_evaluation.py`, `scripts/test_deep_evaluation.py`, and
     `docs/deep-evaluation-contract.md`.
   - `git diff f9145e8^ f9145e8 -- runs corpus` exited `0`; raw historical artifacts are unchanged.
   - `git merge-base --is-ancestor f9145e8 origin/master` exited `0`; remote contains the source.
   - The implementation receipt's author command was independently repeated; its cited `/tmp`
     artifact was not reused as verification output.

## Result

**PASS** — C03 acceptance is met: duplicate predictions reject, the complete fixture accounts for
all case/model/seed/repetition combinations including typed failure rows, and raw historical
artifacts are unchanged. Residual limitation: this is contract/fixture verification; it does not
claim a live model evaluation or publication-quality experiment result.

Next action: settle `verify-validate-prediction-identity`; C04 implementation may then be released
by the chain coordinator.
