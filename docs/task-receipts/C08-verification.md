# C08 verification receipt — enforce decision consumer

- Actor: `vpn`
- Repository: `/home/mesh-home/tiny-fleet`
- UTC: 2026-09-11
- Exact source revision inspected: `e65c78d5b1bb042aeef390a01813d5ab773a9912`
- Verdict: `PASS`

## Independent verification

The exact submitted source revision was checked out in an isolated detached
worktree at `/tmp/tinyfleet-c08-verify.x2Orvd`. The worktree was clean and the
revision contained only the C08 implementation files and README changes.

Command and result:

```text
/home/mesh-home/tiny-fleet/.venv/bin/python scripts/test_policy_consumer.py
exit 0; policy consumer: 4/4
```

An independent inline matrix covered six decisions, including the negative
cases absent from the positive execution example:

```text
{}                                  -> held/malformed-decision
allow, require_approval=true       -> held/approval-required
review, require_approval=false     -> review callback
escalate, require_approval=false   -> escalate callback
block, require_approval=false      -> held/blocked
allow, require_approval=false      -> execute callback
exit 0; independent counterexample matrix: 6/6; execute calls only explicit allow=False
```

The callback spy observed exactly `review`, `escalate`, and `execute` for the
three routing cases; malformed, approval-needed, and block invoked no callback.
No shell command or real-world action is executed by the consumer.

## Recomputed source hashes

```text
scripts/policy_consumer.py       7fb00e52efd8e398883810d29c45d8bf4ebe184746f39eae0573229660d8881c
scripts/test_policy_consumer.py  d034c0ff5acf726701598f63725d48dd61491b67029d4a3e70717e07ff979939
README.md                        51b28f1301cb9a7a9520e753cc89812a3b4fae61dc4c6f1764ca184891e0395e
```

The C08 acceptance predicates are satisfied: only an explicitly valid,
unapproved `allow` executes; review and escalation route to their callbacks;
block, unknown, missing, malformed, and approval-needed decisions do not
execute.
