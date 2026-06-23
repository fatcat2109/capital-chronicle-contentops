"""Approval validator core module for ContentOps.

Provides validation of ledger events against payload inputs,
checks boundaries, and derives current state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from .approval_ledger import ApprovalLedgerEvent
from .approval_payload_hash import compute_payload_hash

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_APPROVAL_LEDGER_PAYLOAD_HASH_INVALIDATION_V0"

SECRET_PATTERNS = [
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
]


def validate_approval_event_against_payload(
    event: dict[str, Any] | ApprovalLedgerEvent,
    payload_data: dict[str, Any]
) -> list[str]:
    """Validates an individual approval ledger event against current payload fields."""
    blockers: list[str] = []

    # Safe cast/extract fields
    ev = event if isinstance(event, dict) else event.__dict__

    # Validate exact payload hash exists
    payload_hash = ev.get("payload_hash")
    if not payload_hash:
        blockers.append("payload_hash_missing")
        return blockers

    # Verify computed hash matches
    try:
        computed_hash = compute_payload_hash(payload_data)
        if computed_hash != payload_hash:
            blockers.append("payload_hash_mismatch")
    except Exception:
        blockers.append("payload_hash_computation_failed")

    # Verify event type
    if ev.get("event_type") != "operator_approved":
        blockers.append("event_type_not_approved")

    # Verify missing operator
    if not ev.get("operator_id"):
        blockers.append("missing_operator_id")

    # Verify matches for platform, class, bindings, credentials, media, policy
    if ev.get("platform_id") != payload_data.get("platform_id"):
        blockers.append("platform_id_mismatch")
    if ev.get("payload_class_id") != payload_data.get("payload_class_id"):
        blockers.append("payload_class_id_mismatch")
    if ev.get("destination_binding_id") != payload_data.get("destination_binding_id"):
        blockers.append("destination_binding_id_mismatch")
    if ev.get("credential_handle_id") != payload_data.get("credential_handle_id"):
        blockers.append("credential_handle_id_mismatch")
    if ev.get("media_manifest_hash") != payload_data.get("media_manifest_hash"):
        blockers.append("media_manifest_hash_mismatch")
    if ev.get("policy_snapshot_id") != payload_data.get("policy_snapshot_id"):
        blockers.append("policy_snapshot_id_mismatch")

    # Verify secret-shaped text presence
    text = ev.get("approval_text_redacted", "")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            blockers.append("secret_text_detected")

    # Verify challenge expiration
    exp = ev.get("expiration_at")
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp_dt:
                blockers.append("approval_expired")
        except ValueError:
            blockers.append("invalid_expiration_format")

    return blockers


def derive_latest_approval_state(
    ledger_events: list[dict[str, Any] | ApprovalLedgerEvent],
    payload_id: str,
    payload_data: dict[str, Any] | None = None
) -> str:
    """Walks the ledger events sequentially and derives the latest status state for a payload."""
    events = []
    for item in ledger_events:
        d = item if isinstance(item, dict) else item.__dict__
        if d.get("payload_id") == payload_id:
            events.append(d)

    # Sort by created_at time
    events.sort(key=lambda x: x.get("created_at", ""))

    if not events:
        return "not_requested"

    latest = events[-1]
    etype = latest.get("event_type")

    if etype == "approval_requested":
        return "requested"
    elif etype == "operator_rejected":
        return "rejected"
    elif etype == "operator_revoked":
        return "revoked"
    elif etype == "approval_expired":
        return "expired"
    elif etype == "approval_invalidated_by_edit":
        return "invalidated_by_edit"
    elif etype == "approval_invalidated_by_destination_change":
        return "invalidated_by_destination_change"
    elif etype == "approval_invalidated_by_credential_change":
        return "invalidated_by_credential_change"
    elif etype == "approval_invalidated_by_policy_change":
        return "invalidated_by_policy_change"
    elif etype == "operator_approved":
        if payload_data is None:
            # If payload_data is not provided, evaluate basic expiration check
            exp = latest.get("expiration_at")
            if exp:
                try:
                    exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) > exp_dt:
                        return "expired"
                except ValueError:
                    return "blocked"
            return "approved_current"

        blockers = validate_approval_event_against_payload(latest, payload_data)
        if blockers:
            if "approval_expired" in blockers:
                return "expired"
            if "invalidated_by_edit" in blockers:
                return "invalidated_by_edit"
            if "invalidated_by_destination_change" in blockers:
                return "invalidated_by_destination_change"
            if "invalidated_by_credential_change" in blockers:
                return "invalidated_by_credential_change"
            if "invalidated_by_policy_change" in blockers:
                return "invalidated_by_policy_change"
            return "blocked"
        return "approved_current"

    return "blocked"


def is_approval_current_for_payload(
    ledger_events: list[dict[str, Any] | ApprovalLedgerEvent],
    payload_id: str,
    payload_data: dict[str, Any]
) -> bool:
    """Returns True if the approval is current, non-expired, and completely valid for payload."""
    state = derive_latest_approval_state(ledger_events, payload_id, payload_data)
    return state == "approved_current"


def explain_approval_blockers(
    ledger_events: list[dict[str, Any] | ApprovalLedgerEvent],
    payload_id: str,
    payload_data: dict[str, Any]
) -> list[str]:
    """Returns a descriptive list of blocker strings explaining why approval validation failed."""
    events = []
    for item in ledger_events:
        d = item if isinstance(item, dict) else item.__dict__
        if d.get("payload_id") == payload_id:
            events.append(d)

    events.sort(key=lambda x: x.get("created_at", ""))

    if not events:
        return ["no_approval_event_found"]

    latest = events[-1]
    etype = latest.get("event_type")

    if etype == "operator_approved":
        return validate_approval_event_against_payload(latest, payload_data)
    else:
        return [f"latest_event_is_{etype}"]
