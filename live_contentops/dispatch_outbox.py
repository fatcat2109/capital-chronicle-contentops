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
    classify_duplicate_action,
    compute_idempotency_basis,
    decide_idempotency,
    scan_for_secret_risk,
)
from .kill_switch_policy import evaluate_kill_switch, no_auto_retry_policy
from .redacted_dispatch_audit import (
    AuditSinkReadiness,
    build_blocked_dispatch_audit_event,
    build_redacted_dispatch_audit_event,
)

TASK_LABEL = "TASK_CONTENTOPS_AUTHORITY_CORE_OUTBOX_IDEMPOTENCY_KILL_SWITCH_AUDIT_R1_COMPLETION_PATCH_V0"
MODEL = "contentops.dispatch_outbox"
MODEL_VERSION = "0174U2_DISPATCH_OUTBOX_R1"

OUTBOX_STATUS_CANDIDATE = "candidate"
OUTBOX_STATUS_BLOCKED_BY_APPROVAL = "blocked_by_approval"
OUTBOX_STATUS_BLOCKED_BY_KILL_SWITCH = "blocked_by_kill_switch"
OUTBOX_STATUS_BLOCKED_BY_DUPLICATE = "blocked_by_duplicate"
OUTBOX_STATUS_BLOCKED_BY_AUDIT_SINK = "blocked_by_audit_sink"
OUTBOX_STATUS_READY_FOR_MOCK_DISPATCH = "ready_for_mock_dispatch"
OUTBOX_STATUS_READY_FOR_SUPERVISED_LIVE_FUTURE = "ready_for_supervised_live_future"
OUTBOX_STATUS_MANUAL_FALLBACK_REQUIRED = "manual_fallback_required"

# Backward-compatible aliases from initial partial task.
OUTBOX_STATUS_CREATED = OUTBOX_STATUS_READY_FOR_MOCK_DISPATCH
OUTBOX_STATUS_BLOCKED = OUTBOX_STATUS_BLOCKED_BY_APPROVAL
OUTBOX_STATUS_DUPLICATE = OUTBOX_STATUS_BLOCKED_BY_DUPLICATE

OUTBOX_STATUS_VALUES: tuple[str, ...] = (
    OUTBOX_STATUS_CANDIDATE,
    OUTBOX_STATUS_BLOCKED_BY_APPROVAL,
    OUTBOX_STATUS_BLOCKED_BY_KILL_SWITCH,
    OUTBOX_STATUS_BLOCKED_BY_DUPLICATE,
    OUTBOX_STATUS_BLOCKED_BY_AUDIT_SINK,
    OUTBOX_STATUS_READY_FOR_MOCK_DISPATCH,
    OUTBOX_STATUS_READY_FOR_SUPERVISED_LIVE_FUTURE,
    OUTBOX_STATUS_MANUAL_FALLBACK_REQUIRED,
)

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


def _non_live_contract_fields(dispatch_mode: str = "dry_run") -> dict[str, Any]:
    return {
        "valid_for_live_dispatch_now": False,
        "request_budget": 1,
        "auto_retry_allowed": False,
        "kill_switch_required": True,
        "audit_sink_required": True,
        "manual_fallback_required": True,
        "dispatch_mode": dispatch_mode,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
    }


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
    valid_for_live_dispatch_now: bool = False

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
            "valid_for_live_dispatch_now": self.valid_for_live_dispatch_now,
        }


def derive_outbox_status(
    approval_state: str,
    kill_switch_decision: dict[str, Any] | None,
    idempotency_decision: dict[str, Any] | None,
    audit_sink_readiness: dict[str, Any] | None,
    dispatch_mode: str = "dry_run",
) -> str:
    """Derive compatible outbox status without ever enabling live dispatch now."""
    if approval_state != "approved_current":
        return OUTBOX_STATUS_BLOCKED_BY_APPROVAL
    if (kill_switch_decision or {}).get("local_outbox_allowed") is not True:
        return OUTBOX_STATUS_BLOCKED_BY_KILL_SWITCH
    if (idempotency_decision or {}).get("duplicate") is True:
        return OUTBOX_STATUS_BLOCKED_BY_DUPLICATE
    if (audit_sink_readiness or {}).get("ready") is not True:
        return OUTBOX_STATUS_BLOCKED_BY_AUDIT_SINK
    if (kill_switch_decision or {}).get("manual_fallback_state") == "manual_fallback_required_operator_review":
        return OUTBOX_STATUS_MANUAL_FALLBACK_REQUIRED
    if dispatch_mode == "supervised_live_future":
        return OUTBOX_STATUS_READY_FOR_SUPERVISED_LIVE_FUTURE
    return OUTBOX_STATUS_READY_FOR_MOCK_DISPATCH


def assert_no_live_dispatch_ready_now(entries: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> None:
    """Fail if any outbox entry claims live readiness for this task."""
    for index, entry in enumerate(entries):
        if entry.get("valid_for_live_dispatch_now") is not False:
            raise AssertionError(f"entry[{index}] claims live readiness now")
        for flag in ("dispatch_performed", "live_request_performed", "platform_api_called", "credential_hydrated", "auto_retry_allowed"):
            if entry.get(flag) is not False:
                raise AssertionError(f"entry[{index}] {flag} must be false")


def build_dispatch_outbox_candidate(
    payload_data: dict[str, Any],
    approval_event: dict[str, Any],
    dispatch_intent_class: str = "manual_supervised_dispatch_candidate",
    dispatch_mode: str = "dry_run",
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
        "status": OUTBOX_STATUS_CANDIDATE,
        **_non_live_contract_fields(dispatch_mode),
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


def _blocked_idempotency(blockers: list[str]) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": "blocked_before_idempotency",
        "idempotency_key": None,
        "idempotency_key_short": None,
        "duplicate": False,
        "duplicate_action": "block_candidate",
        "manual_fallback_status": "manual_fallback_required",
        "request_budget": 1,
        "blocked_reasons": sorted(set(blockers)),
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
    }


def prepare_dispatch_outbox_entry(
    payload_data: dict[str, Any],
    ledger_events: list[dict[str, Any]],
    kill_switch_state: dict[str, Any] | None,
    existing_idempotency_keys: set[str] | tuple[str, ...] | list[str] | None = None,
    outbox_entry_id: str | None = None,
    audit_sink_id: str = "local_redacted_dispatch_audit_sink",
    dispatch_mode: str = "dry_run",
) -> DispatchPreparationResult:
    """Prepare local outbox entry and audit event. Never dispatch."""
    findings = scan_for_secret_risk({
        "payload_data": payload_data,
        "ledger_events": ledger_events,
        "kill_switch_state": kill_switch_state or {},
    })
    if findings:
        blocked = (f"secret_risk_detected:{','.join(findings)}",)
        ks = evaluate_kill_switch(kill_switch_state, payload_data.get("platform_id")).as_dict()
        idem = _blocked_idempotency(list(blocked))
        audit = build_blocked_dispatch_audit_event(_non_live_contract_fields(), list(blocked))
        return DispatchPreparationResult(OUTBOX_STATUS_MANUAL_FALLBACK_REQUIRED, None, idem, ks, audit, blocked)

    payload_id = payload_data.get("payload_id")
    state = derive_latest_approval_state(ledger_events, payload_id, payload_data)
    approval_event = (ledger_events or [{}])[-1] if ledger_events else {}
    approval_blockers = _validate_inputs(payload_data, approval_event)
    if state != "approved_current":
        approval_blockers.append(f"approval_state_not_current:{state}")
        approval_blockers.extend(explain_approval_blockers(ledger_events, payload_id, payload_data))

    kill_switch_decision = evaluate_kill_switch(kill_switch_state, payload_data.get("platform_id")).as_dict()
    sink = AuditSinkReadiness(
        sink_id=audit_sink_id,
        append_only=True,
        redaction_required=True,
    ).as_dict()

    blockers = list(approval_blockers)
    blockers.extend(kill_switch_decision.get("blocked_reasons") or [])
    if sink.get("ready") is not True:
        blockers.append("audit_sink_not_ready")

    if blockers:
        status = derive_outbox_status(state, kill_switch_decision, None, sink, dispatch_mode)
        if any("kill_switch" in reason or "live_dispatch" in reason for reason in blockers):
            status = OUTBOX_STATUS_BLOCKED_BY_KILL_SWITCH
        elif "audit_sink_not_ready" in blockers:
            status = OUTBOX_STATUS_BLOCKED_BY_AUDIT_SINK
        blocked_entry = {
            "outbox_entry_id": outbox_entry_id,
            "payload_id": payload_id,
            "platform_id": payload_data.get("platform_id"),
            "blocked_reasons": sorted(set(blockers)),
            "status": status,
            **_non_live_contract_fields(dispatch_mode),
            "manual_fallback_status": "manual_fallback_required",
        }
        idem = _blocked_idempotency(blockers)
        audit = build_blocked_dispatch_audit_event(blocked_entry, sorted(set(blockers)))
        return DispatchPreparationResult(
            status,
            None,
            idem,
            kill_switch_decision,
            audit,
            tuple(sorted(set(blockers))),
        )

    candidate = build_dispatch_outbox_candidate(payload_data, approval_event, dispatch_mode=dispatch_mode)
    idempotency_decision = decide_idempotency(candidate, existing_idempotency_keys).as_dict()
    if idempotency_decision.get("duplicate"):
        action = classify_duplicate_action(idempotency_decision)
        blockers = tuple(action.get("blocked_reasons") or ["duplicate_idempotency_key"])
        audit = build_blocked_dispatch_audit_event({**candidate, "blocked_reasons": list(blockers)}, list(blockers))
        return DispatchPreparationResult(
            OUTBOX_STATUS_BLOCKED_BY_DUPLICATE,
            None,
            {**idempotency_decision, **action},
            kill_switch_decision,
            audit,
            blockers,
        )

    if idempotency_decision.get("status") == "blocked":
        blockers = tuple(idempotency_decision.get("blocked_reasons") or [])
        audit = build_blocked_dispatch_audit_event({**candidate, "blocked_reasons": list(blockers)}, list(blockers))
        return DispatchPreparationResult(
            OUTBOX_STATUS_MANUAL_FALLBACK_REQUIRED,
            None,
            idempotency_decision,
            kill_switch_decision,
            audit,
            blockers,
        )

    status = derive_outbox_status(state, kill_switch_decision, idempotency_decision, sink, dispatch_mode)
    entry = {
        **candidate,
        "outbox_entry_id": outbox_entry_id or f"outbox_{idempotency_decision['idempotency_key_short']}",
        "idempotency_key": idempotency_decision.get("idempotency_key"),
        "idempotency_key_short": idempotency_decision.get("idempotency_key_short"),
        "idempotency_basis": compute_idempotency_basis(candidate),
        "status": status,
        "blocked_reasons": [],
        "manual_fallback_state": kill_switch_decision.get("manual_fallback_state"),
        "manual_fallback_status": "manual_fallback_not_required",
        **_non_live_contract_fields(dispatch_mode),
        **no_auto_retry_policy(),
    }
    assert_no_live_dispatch_ready_now([entry])
    audit = build_redacted_dispatch_audit_event(entry, idempotency_decision, kill_switch_decision, sink)
    return DispatchPreparationResult(
        status,
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
        "helper_api_completed": ["derive_outbox_status", "assert_no_live_dispatch_ready_now"],
        "contract_status": "deterministic_local_dispatch_preparation_complete_r1",
        "outbox_statuses": list(OUTBOX_STATUS_VALUES),
        "required_payload_fields": list(REQUIRED_PAYLOAD_FIELDS),
        "required_approval_fields": list(REQUIRED_APPROVAL_FIELDS),
        "every_outbox_entry_includes": {
            "valid_for_live_dispatch_now": False,
            "request_budget": 1,
            "auto_retry_allowed": False,
            "kill_switch_required": True,
            "audit_sink_required": True,
            "manual_fallback_required": True,
            "dispatch_mode": ["dry_run", "supervised_live_future"],
        },
        "ready_for_supervised_live_future_still_live_now_false": True,
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
        "valid_for_live_dispatch_now": False,
    }
