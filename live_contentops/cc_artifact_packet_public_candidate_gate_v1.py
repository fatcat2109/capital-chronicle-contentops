"""Public-candidate gate for CC artifact packet operator decisions.

This gate is local-only. It consumes a decision packet and returns a public
candidate state without calling platform adapters, reading credentials, using a
browser, or checking network/public readback.
"""
from __future__ import annotations

from typing import Any

PUBLIC_CANDIDATE_BLOCKED_BY_PACKET = "PUBLIC_CANDIDATE_BLOCKED_BY_PACKET"
PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS = "PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS"
PUBLIC_CANDIDATE_REHEARSAL_ELIGIBLE_LOCAL_ONLY = "PUBLIC_CANDIDATE_REHEARSAL_ELIGIBLE_LOCAL_ONLY"
PUBLIC_CANDIDATE_READY_REQUIRES_SEPARATE_OPERATOR_GO = "PUBLIC_CANDIDATE_READY_REQUIRES_SEPARATE_OPERATOR_GO"
FAIL_SCOPE_BREACH = "FAIL_SCOPE_BREACH"


def evaluate_public_candidate_gate(decision_packet: dict[str, Any]) -> dict[str, Any]:
    blockers = list(decision_packet.get("blockers") or [])
    scope_flags = decision_packet.get("safety_flags") if isinstance(decision_packet.get("safety_flags"), dict) else {}
    scope_breaches = [
        key for key, value in scope_flags.items()
        if key.endswith("_performed") and value is True
    ]
    if scope_breaches:
        return {
            "gate_status": FAIL_SCOPE_BREACH,
            "public_ready": False,
            "dispatch_allowed_now": False,
            "scope_breaches": scope_breaches,
            "blockers": blockers + [f"scope_breach:{item}" for item in scope_breaches],
            "requires_separate_operator_go": True,
        }

    if blockers or decision_packet.get("public_ready") is not True:
        return {
            "gate_status": PUBLIC_CANDIDATE_BLOCKED_BY_PACKET,
            "public_ready": False,
            "dispatch_allowed_now": False,
            "scope_breaches": [],
            "blockers": blockers or ["public_ready_false"],
            "requires_separate_operator_go": True,
        }

    if decision_packet.get("classification") == PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS:
        return {
            "gate_status": PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS,
            "public_ready": True,
            "dispatch_allowed_now": False,
            "scope_breaches": [],
            "blockers": [],
            "warnings": decision_packet.get("warnings") or [],
            "requires_separate_operator_go": True,
            "requires_separate_live_task": True,
            "candidate_commentary_only": True,
        }

    if decision_packet.get("candidate_rehearsal_local_only") is True:
        return {
            "gate_status": PUBLIC_CANDIDATE_REHEARSAL_ELIGIBLE_LOCAL_ONLY,
            "public_ready": False,
            "dispatch_allowed_now": False,
            "scope_breaches": [],
            "blockers": [],
            "requires_separate_operator_go": True,
        }

    return {
        "gate_status": PUBLIC_CANDIDATE_READY_REQUIRES_SEPARATE_OPERATOR_GO,
        "public_ready": True,
        "dispatch_allowed_now": False,
        "scope_breaches": [],
        "blockers": [],
        "requires_separate_operator_go": True,
    }
