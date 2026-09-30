#!/usr/bin/env python3
"""Contract tests for the side-effect-free policy decision consumer."""
from __future__ import annotations

from policy_consumer import dispatch_decision


def _spies():
    calls = []

    def callback(name):
        def record(decision):
            calls.append((name, decision))
            return f"{name}-result"
        return record

    return calls, callback("execute"), callback("review"), callback("escalate")


def test_only_explicit_unapproved_allow_executes():
    for action in ("review", "block", "escalate", "unknown"):
        for approval in (False, True):
            calls, execute, review, escalate = _spies()
            result = dispatch_decision(
                {"action": action, "require_approval": approval},
                execute, review, escalate,
            )
            assert result["status"] in {"reviewed", "blocked", "escalated", "held"}
            assert calls == [] or calls[0][0] != "execute"

    calls, execute, review, escalate = _spies()
    result = dispatch_decision(
        {"action": "allow", "require_approval": False}, execute, review, escalate
    )
    assert result == {"status": "executed", "result": "execute-result"}
    assert [name for name, _ in calls] == ["execute"]


def test_approval_needed_allow_is_held_without_any_callback():
    calls, execute, review, escalate = _spies()
    result = dispatch_decision(
        {"action": "allow", "require_approval": True}, execute, review, escalate
    )
    assert result == {"status": "held", "reason": "approval-required"}
    assert calls == []


def test_review_and_escalate_route_to_their_callbacks():
    for action, expected in (("review", "reviewed"), ("escalate", "escalated")):
        calls, execute, review, escalate = _spies()
        result = dispatch_decision(
            {"action": action, "require_approval": False}, execute, review, escalate
        )
        assert result == {"status": expected, "result": f"{action}-result"}
        assert [name for name, _ in calls] == [action]


def test_block_unknown_missing_and_malformed_decisions_hold():
    for decision in (
        {"action": "block", "require_approval": False},
        {"action": "review"},
        {"action": "launch", "require_approval": False},
        None,
        "allow",
        {"action": "allow", "require_approval": "no"},
    ):
        calls, execute, review, escalate = _spies()
        result = dispatch_decision(decision, execute, review, escalate)
        assert result["status"] == "held"
        assert calls == []


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"policy consumer: {len(tests)}/{len(tests)}")
