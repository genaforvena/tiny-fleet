#!/usr/bin/env python3
"""Consume a policy decision without performing real-world side effects."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


Decision = dict[str, Any]
Callback = Callable[[Decision], Any]
_ACTIONS = frozenset(("allow", "review", "escalate", "block"))


def _valid_decision(decision: Any) -> bool:
    return (
        isinstance(decision, dict)
        and decision.get("action") in _ACTIONS
        and isinstance(decision.get("require_approval"), bool)
    )


def dispatch_decision(
    decision: Any,
    execute: Callback,
    review: Callback,
    escalate: Callback,
) -> dict[str, Any]:
    """Route a structured decision to an injected callback.

    The consumer owns the safety boundary: only an explicitly valid ``allow``
    with ``require_approval=False`` can invoke ``execute``. Every invalid,
    approval-needed, or blocking decision is held without invoking a callback.
    """
    if not _valid_decision(decision):
        return {"status": "held", "reason": "malformed-decision"}

    action = decision["action"]
    if action == "allow":
        if decision["require_approval"]:
            return {"status": "held", "reason": "approval-required"}
        return {"status": "executed", "result": execute(decision)}
    if action == "review":
        return {"status": "reviewed", "result": review(decision)}
    if action == "escalate":
        return {"status": "escalated", "result": escalate(decision)}
    return {"status": "held", "reason": "blocked"}

