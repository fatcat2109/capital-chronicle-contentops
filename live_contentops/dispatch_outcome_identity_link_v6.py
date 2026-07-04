"""Local-only V6 bridge from publication identity to dispatch outcome audit input.

No browser, network, API, webhook, env, credential, cookie, storage, session, token,
or header material belongs here.
"""
from __future__ import annotations

from typing import Any

from live_contentops.platform_publication_identity_registry_v6 import validate_registry_record

SAFE_FALSE_FLAGS = (
    "cookie_read_performed",
    "local_storage_read_performed",
    "session_storage_read_performed",
    "token_or_header_read_performed",
    "raw_secret_output",
)
ALLOWED_SAFETY_KEYS = {
    *SAFE_FALSE_FLAGS,
    "api_request_performed",
    "browser_session_started",
    "credential_value_read",
    "live_write_attempted",
    "no_paid_api_used",
    "webhook_request_performed",
}
SECRET_KEY_MARKERS = (
    "cookie",
    "token",
    "secret",
    "authorization",
    "password",
    "session",
    "localstorage",
    "sessionstorage",
    "credential_value",
    "raw_header",
)
REQUIRED_DISPATCH_CONTEXT = ("approval_id", "outbox_entry_id", "dispatch_attempt_id")


def _has_secret_like_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower not in ALLOWED_SAFETY_KEYS and any(marker in key_lower for marker in SECRET_KEY_MARKERS):
                return True
            if _has_secret_like_key(child):
                return True
    if isinstance(value, list):
        return any(_has_secret_like_key(child) for child in value)
    return False


def make_dispatch_outcome_identity_link(record: dict[str, Any]) -> dict[str, Any]:
    """Build a redacted local-only dispatch outcome/audit identity link."""
    blockers: list[str] = []
    if _has_secret_like_key(record):
        blockers.append("secret_like_registry_field_blocked")
    try:
        validate_registry_record(record)
    except ValueError as exc:
        blockers.append(str(exc))

    for flag in SAFE_FALSE_FLAGS:
        if record.get(flag) is not False:
            blockers.append(f"{flag}_must_be_false")

    if record.get("platform") == "x" and record.get("no_paid_api_used") is not True:
        blockers.append("x_paid_api_flag_blocked")

    missing_context = [field for field in REQUIRED_DISPATCH_CONTEXT if not record.get(field)]
    blockers.extend(f"{field}_missing" for field in missing_context)

    unsafe = any(
        blocker == "secret_like_registry_field_blocked"
        or blocker.endswith("_must_be_false")
        or blocker == "x_paid_api_flag_blocked"
        for blocker in blockers
    )
    ready = not blockers
    if unsafe:
        status = "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    elif missing_context:
        status = "REVIEW_MISSING_DISPATCH_CONTEXT"
    else:
        status = "READY_FOR_PUBLICATION_AUDIT_RECORD"

    link = {
        "link_status": status,
        "registry_record_id": record.get("registry_record_id"),
        "platform": record.get("platform"),
        "public_url": record.get("public_url"),
        "platform_publication_id": record.get("platform_publication_id"),
        "payload_hash": record.get("payload_hash"),
        "approval_id": record.get("approval_id"),
        "outbox_entry_id": record.get("outbox_entry_id"),
        "dispatch_attempt_id": record.get("dispatch_attempt_id"),
        "account_binding_ref": record.get("account_binding_ref"),
        "destination_binding_ref": record.get("destination_binding_ref"),
        "confirmation_class": record.get("confirmation_class"),
        "capture_method": record.get("capture_method"),
        "no_paid_api_used": record.get("no_paid_api_used") is True,
        "live_write_attempted": False,
        "api_request_performed": False,
        "webhook_request_performed": False,
        "browser_session_started": False,
        "credential_value_read": False,
        "cookie_read_performed": False,
        "local_storage_read_performed": False,
        "session_storage_read_performed": False,
        "token_or_header_read_performed": False,
        "raw_secret_output": False,
        "ready_for_publication_audit_record": ready,
        "blockers": blockers,
    }
    validate_dispatch_outcome_identity_link(link)
    return link


def validate_dispatch_outcome_identity_link(link: dict[str, Any]) -> None:
    """Validate the redacted local-only identity link."""
    if _has_secret_like_key(link):
        raise ValueError("secret_like_identity_link_field_blocked")
    if not link.get("platform"):
        raise ValueError("platform_required")
    if not link.get("public_url"):
        raise ValueError("public_url_required")
    if not link.get("payload_hash"):
        raise ValueError("payload_hash_required")
    for flag in (
        "live_write_attempted",
        "api_request_performed",
        "webhook_request_performed",
        "browser_session_started",
        "credential_value_read",
        *SAFE_FALSE_FLAGS,
    ):
        if link.get(flag) is not False:
            raise ValueError(f"{flag}_must_be_false")
    if link.get("ready_for_publication_audit_record") is True and link.get("blockers"):
        raise ValueError("ready_link_cannot_have_blockers")
