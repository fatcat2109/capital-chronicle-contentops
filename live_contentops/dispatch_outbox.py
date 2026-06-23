"""Deterministic dispatch outbox preparation layer.

Creates local outbox candidates only. Never dispatches, never calls platform APIs,
never hydrates credentials, never schedules, never retries automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .approval_payload_hash import compute_payload_hash
from .approval_validator import derive_latest_approval_state, explain_approval_blockers
from .idempotency_policy import (
    compute_idempotency_basis,
    decide_idempotency,
    scan_for_secret_risk,
)
from .kill_switch_policy import evaluate_kill_switch, no_auto_retry_policy
from .redacted_dispatch_audit import AuditSinkReadiness, build_redacted_dispatch_audit_event

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_OUTBOX_IDEMPOTENCY_KILL_SWITCH_AUDIT_V0"
MODEL = "contentops.dispatch_outbox"
MODEL_VERSION = "0174U2_DISPATCH_OUTBOX_V1"

OUTBOX_STATUS_CREATED = "local_outbox_candidate_created_not_dispatched"
OUTBOX_STATUS_BLOCKED = "local_outbox_candidate_blocked"
OUTBOX_STATUS_DUPLICATE = "duplicate_outbox_candidate_blocked"

REQUIRED_PAYLOAD_FIELDS: tuple[str, ...] = (
    "platform_id",
    "destination_binding_id",
    "credential_handle_id",
    "payload_class_id",
    "media_manifest_hash",
    "policy_snapshot_id",
)

REQUIRED_APPROVAL_FIELDS: tuple[str, ...] = (
    "payload_id",
    "payload_hash",
    "event_type",
    "operator_id",
)


@dataclass(frozen=True)
class DispatchPreparationResult:
    """Complete value-only dispatch-preparation result."""

    status: str
    outbox_entry: dict[str, Any] | None
    idempotency_decision: dict[str, Any]
    kill_switch_decision: dict[str, Any]
    audit_event: dict[str, Any] | None
    blocked_reasons: tuple[str, ...]
    dispatch_performed: bool = False
    live_request_performed: bool = False
    platform_api_called: bool = False
    credential_hydrated: bool = False
    auto_retry_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": self.status,
            "outbox_entry": self.outbox_entry,
            "idempotency_decision": self.idempotency_decision,
            "kill_switch_decision": self.kill_switch_decision,
            "audit_event": self.audit_event,
            "blocked_reasons": list(self.blocked_reasons),
            "dispatch_performed": self.dispatch_performed,
            "live_request_performed": self.live_request_performed,
            "platform_api_called": self.platform_api_called,
            "credential_hydrated": self.credential_hydrated,
            "auto_retry_allowed": self.auto_retry_allowed,
        }


def build_dispatch_outbox_candidate(
    payload_data: dict[str, Any],
    approval_event: dict[str, Any],
    dispatch_intent_class: str = "manual_supervised_dispatch_candidate",
) -> dict[str, Any]:
    """Build local outbox candidate from payload + current approval event."""
    findings = scan_for_secret_risk({"payload_data": payload_data, "approval_event": approval_event})
    if findings:
        raise ValueError(f"secret risk in outbox candidate input: {findings}")
    payload_hash = compute_payload_hash(payload_data)
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "payload_id": approval_event.get("payload_id") or payload_data.get("payload_id"),
        "payload_hash": payload_hash,
        "platform_id": payload_data.get("platform_id"),
        "payload_class_id": payload_data.get("payload_class_id"),
        "destination_binding_id": payload_data.get("destination_binding_id"),
        "credential_handle_id": payload_data.get("credential_handle_id"),
        "media_manifest_hash": payload_data.get("media_manifest_hash"),
        "policy_snapshot_id": payload_data.get("policy_snapshot_id"),
        "approval_ledger_entry_id": approval_event.get("ledger_entry_id") or approval_event.get("ledger_event_id") or approval_event.get("event_id"),
        "approval_event_id": approval_event.get("ledger_event_id") or approval_event.get("event_id"),
        "operator_id": approval_event.get("operator_id"),
        "dispatch_intent_class": dispatch_intent_class,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }


def _validate_inputs(payload_data: dict[str, Any], approval_event: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for field in REQUIRED_PAYLOAD_FIELDS:
        if payload_data.get(field) in (None, ""):
            blockers.append(f"missing_payload_field:{field}")
    for field in REQUIRED_APPROVAL_FIELDS:
        if approval_event.get(field) in (None, ""):
            blockers.append(f"missing_approval_field:{field}")
    if approval_event.get("event_type") != "operator_approved":
        blockers.append("approval_event_type_not_operator_approved")
    return blockers


def prepare_dispatch_outbox_entry(
    payload_data: dict[str, Any],
    ledger_events: list[dict[str, Any]],
    kill_switch_state: dict[str, Any] | None,
    existing_idempotency_keys: set[str] | tuple[str, ...] | list[str] | None = None,
    outbox_entry_id: str | None = None,
    audit_sink_id: str = "local_redacted_dispatch_audit_sink",
) -> DispatchPreparationResult:
    """Prepare local outbox entry and audit event. Never dispatch."""
    findings = scan_for_secret_risk({
        "payload_data": payload_data,
        "ledger_events": ledger_events,
        "kill_switch_state": kill_switch_state or {},
    })
    if findings:
        blocked = (f"secret_risk_detected:{','.join(findings)}",)
        ks = evaluate_kill_switch(kill_switch_state).as_dict()
        idem = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": "blocked",
            "idempotency_key": None,
            "idempotency_key_short": None,
            "duplicate": False,
            "blocked_reasons": list(blocked),
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "auto_retry_allowed": False,
        }
        return DispatchPreparationResult(OUTBOX_STATUS_BLOCKED, None, idem, ks, None, blocked)

    payload_id = payload_data.get("payload_id")
    state = derive_latest_approval_state(ledger_events, payload_id, payload_data)
    approval_event = (ledger_events or [{}])[-1] if ledger_events else {}
    blockers = _validate_inputs(payload_data, approval_event)
    if state != "approved_current":
        blockers.append(f"approval_state_not_current:{state}")
        blockers.extend(explain_approval_blockers(ledger_events, payload_id, payload_data))

    kill_switch_decision = evaluate_kill_switch(kill_switch_state).as_dict()
    blockers.extend(kill_switch_decision.get("blocked_reasons") or [])

    candidate: dict[str, Any] | None = None
    idempotency_decision: dict[str, Any]
    if blockers:
        idempotency_decision = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": "blocked_before_idempotency",
            "idempotency_key": None,
            "idempotency_key_short": None,
            "duplicate": False,
            "blocked_reasons": sorted(set(blockers)),
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "auto_retry_allowed": False,
        }
        return DispatchPreparationResult(
            OUTBOX_STATUS_BLOCKED,
            None,
            idempotency_decision,
            kill_switch_decision,
            None,
            tuple(sorted(set(blockers))),
        )

    candidate = build_dispatch_outbox_candidate(payload_data, approval_event)
    idempotency_decision = decide_idempotency(candidate, existing_idempotency_keys).as_dict()
    if idempotency_decision.get("duplicate"):
        return DispatchPreparationResult(
            OUTBOX_STATUS_DUPLICATE,
            None,
            idempotency_decision,
            kill_switch_decision,
            None,
            tuple(idempotency_decision.get("blocked_reasons") or []),
        )

    if idempotency_decision.get("status") == "blocked":
        return DispatchPreparationResult(
            OUTBOX_STATUS_BLOCKED,
            None,
            idempotency_decision,
            kill_switch_decision,
            None,
            tuple(idempotency_decision.get("blocked_reasons") or []),
        )

    entry = {
        **candidate,
        "outbox_entry_id": outbox_entry_id or f"outbox_{idempotency_decision['idempotency_key_short']}",
        "idempotency_key": idempotency_decision.get("idempotency_key"),
        "idempotency_key_short": idempotency_decision.get("idempotency_key_short"),
        "idempotency_basis": compute_idempotency_basis(candidate),
        "status": OUTBOX_STATUS_CREATED,
        "blocked_reasons": [],
        "manual_fallback_state": kill_switch_decision.get("manual_fallback_state"),
        **no_auto_retry_policy(),
    }
    sink = AuditSinkReadiness(
        sink_id=audit_sink_id,
        append_only=True,
        redaction_required=True,
    ).as_dict()
    audit = build_redacted_dispatch_audit_event(entry, idempotency_decision, kill_switch_decision, sink)
    return DispatchPreparationResult(
        OUTBOX_STATUS_CREATED,
        entry,
        idempotency_decision,
        kill_switch_decision,
        audit,
        (),
    )


def dispatch_outbox_packet() -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "contract_status": "deterministic_local_dispatch_preparation_ready",
        "outbox_statuses": [OUTBOX_STATUS_CREATED, OUTBOX_STATUS_BLOCKED, OUTBOX_STATUS_DUPLICATE],
        "required_payload_fields": list(REQUIRED_PAYLOAD_FIELDS),
        "required_approval_fields": list(REQUIRED_APPROVAL_FIELDS),
        "approval_validator_api_used": [
            "derive_latest_approval_state",
            "explain_approval_blockers",
        ],
        "removed_approval_ledger_apis_not_used": [
            "validate_approval_record",
            "validate_kill_switch_state",
            "validate_audit_event",
            "check_action_allowed",
        ],
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }
