"""Redacted dispatch audit models for local outbox preparation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .idempotency_policy import scan_for_secret_risk

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_OUTBOX_IDEMPOTENCY_KILL_SWITCH_AUDIT_R1_COMPLETION_PATCH_V0"
MODEL = "contentops.redacted_dispatch_audit"
MODEL_VERSION = "0174U2_REDACTED_DISPATCH_AUDIT_R1"


@dataclass(frozen=True)
class AuditSinkReadiness:
    """Readiness contract for local redacted audit sink."""

    sink_id: str
    append_only: bool
    redaction_required: bool
    accepts_raw_credentials: bool = False
    accepts_provider_responses: bool = False
    network_sink: bool = False

    def as_dict(self) -> dict[str, Any]:
        ready = (
            bool(self.sink_id)
            and self.append_only
            and self.redaction_required
            and not self.accepts_raw_credentials
            and not self.accepts_provider_responses
            and not self.network_sink
        )
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "sink_id": self.sink_id,
            "ready": ready,
            "append_only": self.append_only,
            "redaction_required": self.redaction_required,
            "accepts_raw_credentials": self.accepts_raw_credentials,
            "accepts_provider_responses": self.accepts_provider_responses,
            "network_sink": self.network_sink,
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "auto_retry_allowed": False,
        }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def audit_checksum(event: dict[str, Any]) -> str:
    body = {k: v for k, v in event.items() if k not in {"audit_checksum", "audit_hash"}}
    return sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def _base_audit_fields(
    outbox_entry: dict[str, Any],
    idempotency_decision: dict[str, Any] | None,
    kill_switch_decision: dict[str, Any] | None,
    sink_readiness: dict[str, Any] | None,
) -> dict[str, Any]:
    payload_hash = outbox_entry.get("payload_hash")
    idem_key = (idempotency_decision or {}).get("idempotency_key") or outbox_entry.get("idempotency_key")
    blocked_reasons = sorted(set(
        list(outbox_entry.get("blocked_reasons") or [])
        + list((idempotency_decision or {}).get("blocked_reasons") or [])
        + list((kill_switch_decision or {}).get("blocked_reasons") or [])
    ))
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "outbox_entry_id": outbox_entry.get("outbox_entry_id"),
        "approval_ledger_entry_id": outbox_entry.get("approval_ledger_entry_id"),
        "approval_event_id": outbox_entry.get("approval_event_id"),
        "platform_id": outbox_entry.get("platform_id"),
        "payload_class_id": outbox_entry.get("payload_class_id"),
        "destination_binding_id": outbox_entry.get("destination_binding_id"),
        "credential_handle_id": outbox_entry.get("credential_handle_id"),
        "payload_hash_short": payload_hash[:12] if payload_hash else None,
        "idempotency_key_short": idem_key[:12] if idem_key else None,
        "idempotency_status": (idempotency_decision or {}).get("status"),
        "kill_switch_status": (kill_switch_decision or {}).get("status"),
        "manual_fallback_state": (kill_switch_decision or {}).get("manual_fallback_state") or outbox_entry.get("manual_fallback_state"),
        "manual_fallback_status": outbox_entry.get("manual_fallback_status") or (idempotency_decision or {}).get("manual_fallback_status") or "manual_fallback_required",
        "audit_sink_ready": (sink_readiness or {}).get("ready") is True,
        "blocked_reasons": blocked_reasons,
        "endpoint_family": outbox_entry.get("endpoint_family", "mock_dispatch_preparation"),
        "method": outbox_entry.get("method", "NONE"),
        "response_class": outbox_entry.get("response_class", "not_sent"),
        "public_url": None,
        "platform_object_id_redacted": None,
        "redaction_status": "redacted_metadata_only",
        "no_secret_output": True,
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "raw_payload_text_stored": False,
        "raw_credential_stored": False,
        "raw_provider_response_stored": False,
        "token_logged": False,
        "headers_logged": False,
        "credential_value_logged": False,
        "final_url_verified": None,
        "retry_count": 0,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }


def build_blocked_dispatch_audit_event(
    outbox_entry: dict[str, Any],
    blocked_reasons: list[str] | tuple[str, ...],
    manual_fallback_status: str = "manual_fallback_required",
) -> dict[str, Any]:
    """Build blocked dispatch audit event with zero request budget used."""
    base = _base_audit_fields(
        {**outbox_entry, "blocked_reasons": list(blocked_reasons), "manual_fallback_status": manual_fallback_status},
        None,
        None,
        None,
    )
    event = {
        **base,
        "event_type": "blocked_dispatch_audit_event",
        "dispatch_classification": "blocked_non_live",
        "request_budget_used": 0,
        "mock_dispatch": False,
        "success_classification": None,
    }
    assert_redacted_audit_safe(event)
    event["audit_checksum"] = audit_checksum(event)
    return event


def build_mock_dispatch_audit_event(
    outbox_entry: dict[str, Any],
    idempotency_decision: dict[str, Any],
    kill_switch_decision: dict[str, Any],
    sink_readiness: dict[str, Any],
    response_class: str = "mock_success_non_live",
) -> dict[str, Any]:
    """Build clearly non-live mock dispatch audit event."""
    base = _base_audit_fields(
        {**outbox_entry, "response_class": response_class, "method": "MOCK", "endpoint_family": "mock_non_live"},
        idempotency_decision,
        kill_switch_decision,
        sink_readiness,
    )
    event = {
        **base,
        "event_type": "mock_dispatch_audit_event",
        "dispatch_classification": "mock_non_live",
        "request_budget_used": 1,
        "mock_dispatch": True,
        "success_classification": "mock_success_only_non_live" if "success" in response_class else None,
    }
    assert_redacted_audit_safe(event)
    event["audit_checksum"] = audit_checksum(event)
    return event


def build_redacted_dispatch_audit_event(
    outbox_entry: dict[str, Any],
    idempotency_decision: dict[str, Any],
    kill_switch_decision: dict[str, Any],
    sink_readiness: dict[str, Any],
) -> dict[str, Any]:
    """Build redacted audit event. Reject raw secrets/provider data fail-closed."""
    event = build_mock_dispatch_audit_event(
        outbox_entry,
        idempotency_decision,
        kill_switch_decision,
        sink_readiness,
        response_class="mock_prepared_not_sent",
    )
    event["event_type"] = "redacted_dispatch_preparation_audit_event"
    event["success_classification"] = None
    event["audit_checksum"] = audit_checksum(event)
    return event


def assert_redacted_audit_safe(event: dict[str, Any]) -> None:
    """Assert audit event contains no raw request/response/credential data."""
    scan_body = {
        key: value
        for key, value in event.items()
        if key not in {"no_secret_output", "token_logged", "headers_logged", "credential_value_logged"}
    }
    findings = scan_for_secret_risk(scan_body)
    if findings:
        raise AssertionError(f"secret_risk_detected:{findings}")
    false_flags = (
        "raw_request_persisted",
        "raw_response_persisted",
        "raw_payload_text_stored",
        "raw_credential_stored",
        "raw_provider_response_stored",
        "token_logged",
        "headers_logged",
        "credential_value_logged",
        "dispatch_performed",
        "live_request_performed",
        "platform_api_called",
        "credential_hydrated",
        "auto_retry_allowed",
    )
    for flag in false_flags:
        if event.get(flag) is not False:
            raise AssertionError(f"{flag}_must_be_false")
    if event.get("retry_count") != 0:
        raise AssertionError("retry_count_must_be_zero")
    if event.get("no_secret_output") is not True:
        raise AssertionError("no_secret_output_must_be_true")
    if event.get("public_url") is not None:
        raise AssertionError("public_url_must_be_null")
    if event.get("platform_object_id_redacted") is not None:
        raise AssertionError("platform_object_id_redacted_must_be_null")
    if event.get("final_url_verified") is not None:
        raise AssertionError("final_url_verified_must_be_null")


def validate_redacted_dispatch_audit_event(event: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        assert_redacted_audit_safe(event)
    except AssertionError as exc:
        blockers.append(str(exc))
    checksum = event.get("audit_checksum") or event.get("audit_hash")
    if checksum != audit_checksum(event):
        blockers.append("audit_checksum_mismatch")
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "valid": not blockers,
        "blocked_reasons": blockers,
    }


def redacted_dispatch_audit_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "helper_api_completed": [
            "build_blocked_dispatch_audit_event",
            "build_mock_dispatch_audit_event",
            "assert_redacted_audit_safe",
        ],
        "audit_event_types": [
            "redacted_dispatch_preparation_audit_event",
            "blocked_dispatch_audit_event",
            "mock_dispatch_audit_event",
        ],
        "audit_sink_readiness_contract": {
            "append_only": True,
            "redaction_required": True,
            "accepts_raw_credentials": False,
            "accepts_provider_responses": False,
            "network_sink": False,
        },
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "token_logged": False,
        "headers_logged": False,
        "credential_value_logged": False,
        "retry_count": 0,
        "blocked_request_budget_used": 0,
        "mock_audit_non_live": True,
        "success_allowed_only_as_mock_non_live": True,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }
