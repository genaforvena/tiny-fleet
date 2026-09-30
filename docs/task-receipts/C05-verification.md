# C05 verification receipt — correct causal loss

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: `2026-09-11`
- Implementation receipt: `docs/task-receipts/C05-implementation.md`
- Implementation receipt SHA-256: `1d8818286842ece67f04b71e8313912a8e69a6693f1b0a5a13c4dfa64b94883a`
- Exact source commit independently checked: `dca2d10cabcb2da8e07270ba19bb29eccbadb6a1`
- Remote containment checked: source commit is an ancestor of `b5cb41652d5060a7ead7543ae69d538d7f2afd85` (`origin/master` at verification start)
- Result: **PASS — C05 acceptance predicates verified**

## Scope and source inspection

The source commit contains exactly the four scoped files named by C05:

```text
A scripts/loss_metrics.py
M scripts/persona_code.py
A scripts/test_loss_metrics.py
M scripts/train_eval.py
```

`masked_labels(input_ids, attention_mask)` masks padding to `-100`; `summed_nll(logits, labels)` scores `logits[:, :-1]` against `labels[:, 1:]` with `ignore_index=-100` and returns `(nll_sum, target_count)`; `aggregate_perplexity` uses `exp(nll_sum / target_count)` and rejects zero targets. Both evaluator paths use the shared helpers and report per-case NLL/target counts and truncation counts. No historical numerical tables are relabeled, and the receipt explicitly leaves corrected empirical scores pending S06.

## Independent verification

All commands below ran from a detached clean worktree at the exact source commit:
`/tmp/tinyfleet-c05-verify-ocIKZY`.

```text
rtk proxy .venv/bin/python scripts/test_loss_metrics.py
Exit: 0
Output: Ran 4 tests ... OK
Output artifact: /tmp/tinyfleet-c05-verify-ocIKZY/c05-test-output.txt
SHA-256: d094b1bd2c8318c96097f80c50da282add5b2972970a77046de8db6c8935f6ca

rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python <independent non-uniform-logit fixture>
Exit: 0
Output: independent nonuniform-logit, masked-suffix, and zero-target checks: OK
Output artifact: /tmp/tinyfleet-c05-verify-ocIKZY/c05-independent-countercheck.txt
SHA-256: b0b75cd5d0cdec50136cb7db1a11e11d74d8d0b6007f37a9b1bc5d28d3992704
```

The independent fixture manually recomputed selected-token NLL from `torch.log_softmax`, used unequal sequences with padding, changed all masked IDs and masked-position logits, and checked a `-100` target/zero-target case absent from the authored positive fixture. It confirmed three scored targets and invariant NLL.

Additional source checks:

```text
rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python -m compileall -q scripts/loss_metrics.py scripts/train_eval.py scripts/persona_code.py
Exit: 0
Output artifact: /tmp/tinyfleet-c05-verify-ocIKZY/c05-compile-output.txt
SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

rtk proxy /home/mesh-home/tiny-fleet/.venv/bin/python scripts/persona_code.py self-test --manifest runs/persona-code/manifest.json
Exit: 0
Output: self-test: ok
Output artifact: /tmp/tinyfleet-c05-verify-ocIKZY/c05-persona-selftest-output.txt
SHA-256: b8ed9769688118577dab7a5190e37e97a8ed7e07ec11d37638e9d44b32c03672
```

Residual limitation: this gate verifies the accounting implementation and fixtures only. It does not run fresh model training or produce corrected empirical tables; those remain the separately scoped S06 obligation.

