"""Redacted dispatch audit models for local outbox preparation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .idempotency_policy import scan_for_secret_risk

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_OUTBOX_IDEMPOTENCY_KILL_SWITCH_AUDIT_V0"
MODEL = "contentops.redacted_dispatch_audit"
MODEL_VERSION = "0174U2_REDACTED_DISPATCH_AUDIT_V1"


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
    body = {k: v for k, v in event.items() if k != "audit_checksum"}
    return sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def build_redacted_dispatch_audit_event(
    outbox_entry: dict[str, Any],
    idempotency_decision: dict[str, Any],
    kill_switch_decision: dict[str, Any],
    sink_readiness: dict[str, Any],
) -> dict[str, Any]:
    """Build redacted audit event. Reject raw secrets/provider data fail-closed."""
    raw_inputs = {
        "outbox_entry": outbox_entry,
        "idempotency_decision": idempotency_decision,
        "kill_switch_decision": kill_switch_decision,
        "sink_readiness": sink_readiness,
    }
    findings = scan_for_secret_risk(raw_inputs)
    if findings:
        raise ValueError(f"secret risk in audit input: {findings}")

    payload_hash = outbox_entry.get("payload_hash")
    idem_key = idempotency_decision.get("idempotency_key") or outbox_entry.get("idempotency_key")
    event = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "event_type": "redacted_dispatch_preparation_audit_event",
        "outbox_entry_id": outbox_entry.get("outbox_entry_id"),
        "approval_ledger_entry_id": outbox_entry.get("approval_ledger_entry_id"),
        "approval_event_id": outbox_entry.get("approval_event_id"),
        "platform_id": outbox_entry.get("platform_id"),
        "payload_class_id": outbox_entry.get("payload_class_id"),
        "destination_binding_id": outbox_entry.get("destination_binding_id"),
        "credential_handle_id": outbox_entry.get("credential_handle_id"),
        "payload_hash_short": payload_hash[:12] if payload_hash else None,
        "idempotency_key_short": idem_key[:12] if idem_key else None,
        "idempotency_status": idempotency_decision.get("status"),
        "kill_switch_status": kill_switch_decision.get("status"),
        "manual_fallback_state": kill_switch_decision.get("manual_fallback_state"),
        "audit_sink_ready": sink_readiness.get("ready") is True,
        "blocked_reasons": sorted(set(
            list(outbox_entry.get("blocked_reasons") or [])
            + list(idempotency_decision.get("blocked_reasons") or [])
            + list(kill_switch_decision.get("blocked_reasons") or [])
        )),
        "raw_payload_text_stored": False,
        "raw_credential_stored": False,
        "raw_provider_response_stored": False,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }
    event["audit_checksum"] = audit_checksum(event)
    return event


def validate_redacted_dispatch_audit_event(event: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    findings = scan_for_secret_risk(event)
    if findings:
        blockers.append("secret_risk_detected")
    for flag in (
        "raw_payload_text_stored",
        "raw_credential_stored",
        "raw_provider_response_stored",
        "dispatch_performed",
        "live_request_performed",
        "platform_api_called",
        "credential_hydrated",
        "auto_retry_allowed",
    ):
        if event.get(flag) is not False:
            blockers.append(f"{flag}_must_be_false")
    if event.get("audit_checksum") != audit_checksum(event):
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
        "audit_event_type": "redacted_dispatch_preparation_audit_event",
        "audit_sink_readiness_contract": {
            "append_only": True,
            "redaction_required": True,
            "accepts_raw_credentials": False,
            "accepts_provider_responses": False,
            "network_sink": False,
        },
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }
