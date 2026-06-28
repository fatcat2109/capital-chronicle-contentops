"""Approval ledger core module for ContentOps.

Provides the append-only event ledger structure and constructors.
Guarantees immutability and integrity verification of historical ledger events.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any

from .approval_payload_hash import payload_hash_short

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_APPROVAL_LEDGER_PAYLOAD_HASH_INVALIDATION_V0"
MODEL = "contentops.approval_ledger"
MODEL_VERSION = "0174U1_APPROVAL_LEDGER_V1"

ALLOWED_CHANNELS = {"local_ui", "telegram_challenge", "manual_record"}

SECRET_PATTERNS = [
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),  # Telegram bot token
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),  # JWT token
]


@dataclass(frozen=True)
class ApprovalLedgerEvent:
    ledger_event_id: str
    event_type: str
    created_at: str
    operator_id: str
    approval_channel: str
    challenge_id: str | None
    payload_id: str
    payload_hash: str
    payload_hash_short: str
    platform_id: str
    payload_class_id: str
    destination_binding_id: str
    credential_handle_id: str
    media_manifest_hash: str | None
    policy_snapshot_id: str
    approval_text_redacted: str
    expiration_at: str | None
    supersedes_event_id: str | None
    valid_for_dispatch: bool
    blocked_reasons: tuple[str, ...]
    audit_hash: str


def redact_text(text: str) -> str:
    """Redacts potential secrets, passwords, cookies, or tokens in free text."""
    redacted = text
    # Redact potential Telegram bot tokens
    redacted = re.sub(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b", "[REDACTED_BOT_TOKEN]", redacted)
    # Redact potential JWTs
    redacted = re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "[REDACTED_JWT]", redacted)
    # Redact common credential/password indicators
    redacted = re.sub(r"(?i)(password|secret|token|cookie|session_id|bearer)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]+['\"]?", r"\1=[REDACTED]", redacted)
    return redacted


def compute_audit_hash(event_dict: dict[str, Any]) -> str:
    """Computes a deterministic hash of the event fields to prevent mutation."""
    # Exclude audit_hash itself
    d = {k: v for k, v in event_dict.items() if k != "audit_hash"}
    serialized = json.dumps(d, ensure_ascii=False, sort_keys=True)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_approval_requested_event(
    operator_id: str,
    payload_id: str,
    payload_hash: str,
    platform_id: str,
    payload_class_id: str,
    destination_binding_id: str,
    credential_handle_id: str,
    policy_snapshot_id: str,
    media_manifest_hash: str | None = None,
    approval_text: str = "",
    expiration_at: str | None = None,
) -> ApprovalLedgerEvent:
    """Builds an approval_requested ledger event."""
    short_hash = payload_hash_short(payload_hash)
    created_at = _now_iso()
    event_id = f"req_{short_hash}_{int(datetime.now(timezone.utc).timestamp())}"
    redacted = redact_text(approval_text)

    # Validate channels
    channel = "local_ui"
    
    event_dict = {
        "ledger_event_id": event_id,
        "event_type": "approval_requested",
        "created_at": created_at,
        "operator_id": operator_id,
        "approval_channel": channel,
        "challenge_id": None,
        "payload_id": payload_id,
        "payload_hash": payload_hash,
        "payload_hash_short": short_hash,
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "media_manifest_hash": media_manifest_hash,
        "policy_snapshot_id": policy_snapshot_id,
        "approval_text_redacted": redacted,
        "expiration_at": expiration_at,
        "supersedes_event_id": None,
        "valid_for_dispatch": False,
        "blocked_reasons": ("awaiting_operator_approval",),
    }
    audit_hash = compute_audit_hash(event_dict)
    event_dict["audit_hash"] = audit_hash
    return ApprovalLedgerEvent(**event_dict)


def build_operator_approved_event(
    operator_id: str,
    approval_channel: str,
    challenge_id: str | None,
    payload_id: str,
    payload_hash: str,
    platform_id: str,
    payload_class_id: str,
    destination_binding_id: str,
    credential_handle_id: str,
    policy_snapshot_id: str,
    media_manifest_hash: str | None = None,
    approval_text: str = "",
    expiration_at: str | None = None,
    supersedes_event_id: str | None = None,
) -> ApprovalLedgerEvent:
    """Builds an operator_approved ledger event."""
    if approval_channel not in ALLOWED_CHANNELS:
        raise ValueError(f"invalid_approval_channel:{approval_channel}")
    
    short_hash = payload_hash_short(payload_hash)
    created_at = _now_iso()
    event_id = f"app_{short_hash}_{int(datetime.now(timezone.utc).timestamp())}"
    redacted = redact_text(approval_text)

    # An approved event might be eligible for validation check, but is valid_for_dispatch=False
    # until the validator evaluates it.
    event_dict = {
        "ledger_event_id": event_id,
        "event_type": "operator_approved",
        "created_at": created_at,
        "operator_id": operator_id,
        "approval_channel": approval_channel,
        "challenge_id": challenge_id,
        "payload_id": payload_id,
        "payload_hash": payload_hash,
        "payload_hash_short": short_hash,
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "media_manifest_hash": media_manifest_hash,
        "policy_snapshot_id": policy_snapshot_id,
        "approval_text_redacted": redacted,
        "expiration_at": expiration_at,
        "supersedes_event_id": supersedes_event_id,
        "valid_for_dispatch": False,  # default is false, becomes true only via validator check
        "blocked_reasons": (),
    }
    audit_hash = compute_audit_hash(event_dict)
    event_dict["audit_hash"] = audit_hash
    return ApprovalLedgerEvent(**event_dict)


def build_operator_rejected_event(
    operator_id: str,
    payload_id: str,
    payload_hash: str,
    platform_id: str,
    payload_class_id: str,
    destination_binding_id: str,
    credential_handle_id: str,
    policy_snapshot_id: str,
    media_manifest_hash: str | None = None,
    approval_text: str = "",
    supersedes_event_id: str | None = None,
) -> ApprovalLedgerEvent:
    """Builds an operator_rejected ledger event."""
    short_hash = payload_hash_short(payload_hash)
    created_at = _now_iso()
    event_id = f"rej_{short_hash}_{int(datetime.now(timezone.utc).timestamp())}"
    redacted = redact_text(approval_text)

    event_dict = {
        "ledger_event_id": event_id,
        "event_type": "operator_rejected",
        "created_at": created_at,
        "operator_id": operator_id,
        "approval_channel": "local_ui",
        "challenge_id": None,
        "payload_id": payload_id,
        "payload_hash": payload_hash,
        "payload_hash_short": short_hash,
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "media_manifest_hash": media_manifest_hash,
        "policy_snapshot_id": policy_snapshot_id,
        "approval_text_redacted": redacted,
        "expiration_at": None,
        "supersedes_event_id": supersedes_event_id,
        "valid_for_dispatch": False,
        "blocked_reasons": ("operator_rejected_payload",),
    }
    audit_hash = compute_audit_hash(event_dict)
    event_dict["audit_hash"] = audit_hash
    return ApprovalLedgerEvent(**event_dict)


def build_operator_revoked_event(
    operator_id: str,
    payload_id: str,
    payload_hash: str,
    supersedes_event_id: str,
) -> ApprovalLedgerEvent:
    """Builds an operator_revoked ledger event."""
    short_hash = payload_hash_short(payload_hash)
    created_at = _now_iso()
    event_id = f"rev_{short_hash}_{int(datetime.now(timezone.utc).timestamp())}"

    event_dict = {
        "ledger_event_id": event_id,
        "event_type": "operator_revoked",
        "created_at": created_at,
        "operator_id": operator_id,
        "approval_channel": "local_ui",
        "challenge_id": None,
        "payload_id": payload_id,
        "payload_hash": payload_hash,
        "payload_hash_short": short_hash,
        "platform_id": "revoked_platform",
        "payload_class_id": "revoked_class",
        "destination_binding_id": "revoked_destination",
        "credential_handle_id": "revoked_credential",
        "media_manifest_hash": None,
        "policy_snapshot_id": "revoked_policy",
        "approval_text_redacted": "revoked_by_operator",
        "expiration_at": None,
        "supersedes_event_id": supersedes_event_id,
        "valid_for_dispatch": False,
        "blocked_reasons": ("operator_revoked_approval",),
    }
    audit_hash = compute_audit_hash(event_dict)
    event_dict["audit_hash"] = audit_hash
    return ApprovalLedgerEvent(**event_dict)


def build_approval_invalidated_event(
    operator_id: str,
    payload_id: str,
    payload_hash: str,
    invalidation_reason: str,  # edit | destination_change | credential_change | policy_change
    supersedes_event_id: str,
) -> ApprovalLedgerEvent:
    """Builds an invalidation ledger event."""
    if invalidation_reason not in {"edit", "destination_change", "credential_change", "policy_change"}:
        raise ValueError(f"invalid_invalidation_reason:{invalidation_reason}")

    short_hash = payload_hash_short(payload_hash)
    created_at = _now_iso()
    event_id = f"inv_{short_hash}_{int(datetime.now(timezone.utc).timestamp())}"
    event_type = f"approval_invalidated_by_{invalidation_reason}"

    event_dict = {
        "ledger_event_id": event_id,
        "event_type": event_type,
        "created_at": created_at,
        "operator_id": operator_id,
        "approval_channel": "local_ui",
        "challenge_id": None,
        "payload_id": payload_id,
        "payload_hash": payload_hash,
        "payload_hash_short": short_hash,
        "platform_id": "invalidated_platform",
        "payload_class_id": "invalidated_class",
        "destination_binding_id": "invalidated_destination",
        "credential_handle_id": "invalidated_credential",
        "media_manifest_hash": None,
        "policy_snapshot_id": "invalidated_policy",
        "approval_text_redacted": f"invalidated due to {invalidation_reason}",
        "expiration_at": None,
        "supersedes_event_id": supersedes_event_id,
        "valid_for_dispatch": False,
        "blocked_reasons": (f"invalidated_by_{invalidation_reason}",),
    }
    audit_hash = compute_audit_hash(event_dict)
    event_dict["audit_hash"] = audit_hash
    return ApprovalLedgerEvent(**event_dict)


def build_approval_expired_event(
    operator_id: str,
    payload_id: str,
    payload_hash: str,
    supersedes_event_id: str,
) -> ApprovalLedgerEvent:
    """Builds an approval_expired ledger event."""
    short_hash = payload_hash_short(payload_hash)
    created_at = _now_iso()
    event_id = f"exp_{short_hash}_{int(datetime.now(timezone.utc).timestamp())}"

    event_dict = {
        "ledger_event_id": event_id,
        "event_type": "approval_expired",
        "created_at": created_at,
        "operator_id": operator_id,
        "approval_channel": "local_ui",
        "challenge_id": None,
        "payload_id": payload_id,
        "payload_hash": payload_hash,
        "payload_hash_short": short_hash,
        "platform_id": "expired_platform",
        "payload_class_id": "expired_class",
        "destination_binding_id": "expired_destination",
        "credential_handle_id": "expired_credential",
        "media_manifest_hash": None,
        "policy_snapshot_id": "expired_policy",
        "approval_text_redacted": "expired_by_time_limit",
        "expiration_at": None,
        "supersedes_event_id": supersedes_event_id,
        "valid_for_dispatch": False,
        "blocked_reasons": ("approval_expired",),
    }
    audit_hash = compute_audit_hash(event_dict)
    event_dict["audit_hash"] = audit_hash
    return ApprovalLedgerEvent(**event_dict)


def assert_ledger_append_only_shape(ledger_list: list[dict[str, Any]]) -> None:
    """Verifies that the ledger list has valid sequential events and hashes match."""
    # Check that all keys and hashes match event parameters
    seen_ids = set()
    for item in ledger_list:
        event_id = item.get("ledger_event_id")
        if not event_id:
            raise AssertionError("Event missing ledger_event_id.")
        if event_id in seen_ids:
            raise AssertionError(f"Duplicate ledger_event_id '{event_id}' found.")
        seen_ids.add(event_id)

        # Check audit hash matches
        stored_hash = item.get("audit_hash")
        computed = compute_audit_hash(item)
        if stored_hash != computed:
            raise AssertionError(f"Audit hash mismatch for event {event_id}. Tampering detected.")


def approval_ledger_demo_packet() -> dict[str, Any]:
    """Generates a demo approval ledger packet containing multiple history entries."""
    req = build_approval_requested_event(
        operator_id="jim_op",
        payload_id="payload_123",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
    )
    app = build_operator_approved_event(
        operator_id="jim_op",
        approval_channel="local_ui",
        challenge_id=None,
        payload_id="payload_123",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        platform_id="x_profile",
        payload_class_id="x_short_post",
        destination_binding_id="x_profile_default",
        credential_handle_id="x_bearer",
        policy_snapshot_id="v1",
        supersedes_event_id=req.ledger_event_id,
    )
    demo_list = [asdict(req), asdict(app)]
    assert_ledger_append_only_shape(demo_list)
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "demo_events": demo_list,
    }
