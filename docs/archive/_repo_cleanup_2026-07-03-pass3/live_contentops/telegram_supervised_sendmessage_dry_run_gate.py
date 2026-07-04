"""Telegram supervised sendMessage dry-run prep gate.

Pure local domain-contract module for preparing a deterministic Telegram sendMessage
candidate without self-approval, live dispatch, network calls, env reads, or credential
hydration.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import re
from typing import Any

from .approval_payload_hash import canonical_payload_hash_input, compute_payload_hash, payload_hash_short
from .idempotency_policy import compute_idempotency_basis, decide_idempotency
from .kill_switch_policy import build_platform_kill_switch_state, evaluate_kill_switch
from .redacted_dispatch_audit import build_blocked_dispatch_audit_event

TASK_LABEL = "TASK_CONTENTOPS_TELEGRAM_SUPERVISED_SENDMESSAGE_DRY_RUN_GATE_R1_REPAIR_V0"
PREVIOUS_TASK_LABEL = "TASK_CONTENTOPS_TELEGRAM_SUPERVISED_SENDMESSAGE_PREP_AND_DRY_RUN_GATE_V0"
MODEL = "contentops.telegram_supervised_sendmessage_dry_run_gate"
MODEL_VERSION = "0174TELEGRAM_SENDMESSAGE_DRY_RUN_GATE_R1_REVIEW_BLOCKED_V0"
RESULT_REVIEW_BLOCKED = "PASS_DRY_RUN_PREP_REVIEW_BLOCKED"

PLATFORM_ID = "telegram_channel_destination"
DESTINATION_BINDING_ID = "telegram_channel_destination_binding_symbolic_redacted"
CREDENTIAL_HANDLE_ID = "telegram_bot_credential_handle_symbolic_redacted"
PAYLOAD_SCHEMA_VERSION = "telegram_sendmessage_payload_v1"
ADAPTER_VERSION = "telegram_sendmessage_adapter_dry_run_v1"
PAYLOAD_CLASS_ID = "telegram_sendmessage_text_dry_run"
POLICY_SNAPSHOT_ID = "telegram_supervised_sendmessage_dry_run_policy_v1"
PAYLOAD_ID = "telegram-sendmessage-dry-run-payload-0001"
OUTBOX_ENTRY_ID = "telegram-sendmessage-dry-run-outbox-0001"
AUDIT_SINK_ID = "local_redacted_dispatch_audit_sink"
DRY_RUN_MARKER = "DRY_RUN_NOT_FOR_LIVE_SEND"
NO_APPROVAL_EVENT_ID = "approval_required_pending_operator"
SAFE_MESSAGE_TEXT = (
    "DRY_RUN_NOT_FOR_LIVE_SEND — Capital Chronicle supervised Telegram "
    "sendMessage dry-run fixture for operator review. This fixture contains "
    "no recommendations, no positions, no prices, no external links, and no secrets."
)

CANONICAL_PACKET_FILES = [
    "sendmessage_dry_run_payload_packet.json",
    "sendmessage_payload_hash_packet.json",
    "sendmessage_approval_requirement_packet.json",
    "sendmessage_outbox_candidate_packet.json",
    "sendmessage_idempotency_packet.json",
    "sendmessage_kill_switch_packet.json",
    "sendmessage_redacted_audit_packet.json",
    "sendmessage_live_gate_packet.json",
    "implementation_report.md",
    "evidence_packet.json",
    "next_task_pointer.md",
]

FORBIDDEN_VALUE_RE = re.compile(
    r"(\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|https://api\.telegram\.org/|\b-100\d{6,}\b|@[A-Za-z0-9_]{3,}|bearer\s+[A-Za-z0-9._\-]{20,})",
    re.IGNORECASE,
)
FORBIDDEN_TEXT_TERMS = (
    "buy",
    "sell",
    "hold",
    "long",
    "short",
    "target",
    "entry",
    "exit",
    "signal",
    "stop loss",
    "take profit",
    "guaranteed",
    "profit",
)
FORBIDDEN_KEYS = {
    "token",
    "bot_token",
    "chat_id",
    "channel_id",
    "channel_handle",
    "raw_url",
    "request_url",
    "headers",
    "raw_response",
    "provider_response",
    "authorization",
}


@dataclass(frozen=True)
class TelegramSendMessageDryRunGateResult:
    """Complete value-only dry-run prep result."""

    status: str
    payload_packet: dict[str, Any]
    hash_packet: dict[str, Any]
    approval_packet: dict[str, Any]
    outbox_packet: dict[str, Any]
    idempotency_packet: dict[str, Any]
    kill_switch_packet: dict[str, Any]
    audit_packet: dict[str, Any]
    live_gate_packet: dict[str, Any]
    evidence_packet: dict[str, Any]
    blocked_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_label": TASK_LABEL,
            "previous_task_label": PREVIOUS_TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": self.status,
            "payload_packet": self.payload_packet,
            "hash_packet": self.hash_packet,
            "approval_packet": self.approval_packet,
            "outbox_packet": self.outbox_packet,
            "idempotency_packet": self.idempotency_packet,
            "kill_switch_packet": self.kill_switch_packet,
            "audit_packet": self.audit_packet,
            "live_gate_packet": self.live_gate_packet,
            "evidence_packet": self.evidence_packet,
            "blocked_reasons": list(self.blocked_reasons),
            "sendmessage_called": False,
            "telegram_write_endpoint_called": False,
            "live_write_performed": False,
            "network_request_performed": False,
            "credential_hydrated": False,
            "dispatchable_now": False,
            "valid_for_live_dispatch_now": False,
        }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _walk_secret_risk(value: Any, path: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_s = str(key)
            child_path = f"{path}.{key_s}" if path else key_s
            if key_s.lower() in FORBIDDEN_KEYS:
                findings.append(child_path)
            findings.extend(_walk_secret_risk(child, child_path))
    elif isinstance(value, (list, tuple)):
        for idx, child in enumerate(value):
            findings.extend(_walk_secret_risk(child, f"{path}[{idx}]") )
    elif isinstance(value, str) and FORBIDDEN_VALUE_RE.search(value):
        findings.append(path or "<value>")
    return sorted(set(findings))


def scan_packet_for_telegram_secret_risk(packet: Any) -> list[str]:
    """Conservative Telegram-specific redaction scan."""
    return _walk_secret_risk(packet)


def build_telegram_sendmessage_dry_run_payload() -> dict[str, Any]:
    """Build deterministic safe sendMessage payload for dry-run prep only."""
    payload = canonical_payload_hash_input(
        platform_id=PLATFORM_ID,
        destination_binding_id=DESTINATION_BINDING_ID,
        credential_handle_id=CREDENTIAL_HANDLE_ID,
        payload_schema_version=PAYLOAD_SCHEMA_VERSION,
        adapter_version=ADAPTER_VERSION,
        payload_class_id=PAYLOAD_CLASS_ID,
        payload_text=SAFE_MESSAGE_TEXT,
        platform_formatting="telegram_plain_text",
        title="Telegram supervised sendMessage dry-run fixture",
        subtitle=DRY_RUN_MARKER,
        link_preview_class="disabled",
        visibility_class="public_channel_redacted_destination",
        disclosure_class="dry_run_not_for_live_send",
        content_lane="operator_supervised_dry_run",
        policy_snapshot_id=POLICY_SNAPSHOT_ID,
        source_or_research_packet_id="local_fixture_no_external_source",
        guardrail_result_id="telegram_sendmessage_dry_run_guardrail_passed",
        media_manifest_hash="no_media_manifest",
    )
    assert payload is not None
    return {
        "task_label": TASK_LABEL,
        "packet_type": "telegram_sendmessage_dry_run_payload_packet",
        "payload_id": PAYLOAD_ID,
        "telegram_method": "sendMessage",
        "dry_run_marker": DRY_RUN_MARKER,
        "parse_mode": "plain_text",
        "disable_web_page_preview": True,
        "payload_hash_input": payload,
        "sendmessage_called": False,
        "telegram_write_endpoint_called": False,
        "live_write_performed": False,
        "network_request_performed": False,
        "credential_hydrated": False,
        "raw_token_persisted": False,
        "raw_chat_id_persisted": False,
        "raw_url_persisted": False,
        "raw_headers_persisted": False,
        "raw_response_persisted": False,
        "dispatchable_now": False,
        "valid_for_live_dispatch_now": False,
    }


def validate_telegram_sendmessage_payload(payload_packet: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(payload_packet, dict):
        return {"valid": False, "blocked_reasons": ["payload_packet_not_object"]}
    if payload_packet.get("telegram_method") != "sendMessage":
        blockers.append("telegram_method_not_sendMessage")
    if payload_packet.get("dry_run_marker") != DRY_RUN_MARKER:
        blockers.append("dry_run_marker_missing")
    for flag in (
        "sendmessage_called",
        "telegram_write_endpoint_called",
        "live_write_performed",
        "network_request_performed",
        "credential_hydrated",
        "raw_token_persisted",
        "raw_chat_id_persisted",
        "raw_url_persisted",
        "raw_headers_persisted",
        "raw_response_persisted",
        "dispatchable_now",
        "valid_for_live_dispatch_now",
    ):
        if payload_packet.get(flag) is not False:
            blockers.append(f"{flag}_must_be_false")
    payload_input = payload_packet.get("payload_hash_input")
    if not isinstance(payload_input, dict):
        blockers.append("payload_hash_input_missing")
    else:
        text = str(payload_input.get("payload_text") or "")
        if DRY_RUN_MARKER not in text:
            blockers.append("payload_text_missing_dry_run_marker")
        lowered = f" {text.lower()} "
        for term in FORBIDDEN_TEXT_TERMS:
            if (" " in term and term in lowered) or (" " not in term and re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", lowered)):
                blockers.append(f"forbidden_text:{term.replace(' ', '_')}")
    secret_findings = scan_packet_for_telegram_secret_risk(payload_packet)
    if secret_findings:
        blockers.append(f"telegram_secret_risk:{','.join(secret_findings)}")
    return {
        "task_label": TASK_LABEL,
        "packet_type": "telegram_sendmessage_payload_validation_packet",
        "valid": not blockers,
        "blocked_reasons": sorted(set(blockers)),
        "sendmessage_called": False,
        "telegram_write_endpoint_called": False,
        "live_write_performed": False,
        "network_request_performed": False,
        "credential_hydrated": False,
        "dispatchable_now": False,
        "valid_for_live_dispatch_now": False,
    }


def build_payload_hash_packet(payload_packet: dict[str, Any]) -> dict[str, Any]:
    payload_input = deepcopy(payload_packet["payload_hash_input"])
    payload_input["payload_id"] = payload_packet["payload_id"]
    payload_hash = compute_payload_hash(payload_input)
    return {
        "task_label": TASK_LABEL,
        "packet_type": "telegram_sendmessage_payload_hash_packet",
        "payload_id": payload_packet["payload_id"],
        "payload_hash_algorithm": "sha256",
        "payload_hash": payload_hash,
        "payload_hash_short": payload_hash_short(payload_hash),
        "canonical_payload_json": _canonical_json(payload_input),
        "hash_input_contains_secret_risk": False,
        "exact_payload_hash_required": True,
        "dispatchable_now": False,
        "valid_for_live_dispatch_now": False,
    }


def build_approval_requirement_packet(payload_packet: dict[str, Any], hash_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "packet_type": "telegram_sendmessage_approval_requirement_packet",
        "approval_required": True,
        "current_operator_approval_present": False,
        "approval_status": "blocked_pending_operator_approval",
        "payload_id": payload_packet["payload_id"],
        "payload_hash": hash_packet["payload_hash"],
        "payload_hash_short": hash_packet["payload_hash_short"],
        "exact_payload_hash_required": True,
        "operator_approved_dry_run_payload_hash": False,
        "operator_approved_live_send": False,
        "valid_for_dispatch": False,
        "valid_for_live_dispatch_now": False,
        "dispatchable_now": False,
        "no_llm_self_approval": True,
        "no_implicit_approval_from_readonly_proof": True,
        "approval_event": None,
        "approval_event_id": None,
        "sendmessage_called": False,
        "telegram_write_endpoint_called": False,
        "live_write_performed": False,
        "network_request_performed": False,
        "credential_hydrated": False,
    }


def build_dry_run_kill_switch_state() -> dict[str, Any]:
    state = build_platform_kill_switch_state(
        PLATFORM_ID,
        False,
        "local_dry_run_gate_only_live_write_locked",
        "operator_supervised_dry_run_symbolic",
        "2026-06-24T00:00:00Z",
    )
    state["allow_local_outbox"] = True
    state["live_dispatch_enabled"] = False
    return state


def build_review_blocked_outbox_packet(
    payload_packet: dict[str, Any],
    hash_packet: dict[str, Any],
    idempotency_packet: dict[str, Any],
    kill_switch_packet: dict[str, Any],
) -> dict[str, Any]:
    payload_input = deepcopy(payload_packet["payload_hash_input"])
    payload_input["payload_id"] = payload_packet["payload_id"]
    candidate_basis = {
        "payload_hash": hash_packet["payload_hash"],
        "platform_id": payload_input["platform_id"],
        "payload_class_id": payload_input["payload_class_id"],
        "destination_binding_id": payload_input["destination_binding_id"],
        "credential_handle_id": payload_input["credential_handle_id"],
        "media_manifest_hash": payload_input["media_manifest_hash"],
        "policy_snapshot_id": payload_input["policy_snapshot_id"],
        "approval_ledger_entry_id": NO_APPROVAL_EVENT_ID,
        "approval_event_id": NO_APPROVAL_EVENT_ID,
        "dispatch_intent_class": "manual_supervised_dispatch_candidate",
    }
    return {
        "task_label": TASK_LABEL,
        "packet_type": "telegram_sendmessage_outbox_candidate_packet",
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "outbox_entry_id": OUTBOX_ENTRY_ID,
        "payload_id": payload_packet["payload_id"],
        "payload_hash": hash_packet["payload_hash"],
        "platform_id": payload_input["platform_id"],
        "payload_class_id": payload_input["payload_class_id"],
        "destination_binding_id": payload_input["destination_binding_id"],
        "credential_handle_id": payload_input["credential_handle_id"],
        "media_manifest_hash": payload_input["media_manifest_hash"],
        "policy_snapshot_id": payload_input["policy_snapshot_id"],
        "approval_ledger_entry_id": None,
        "approval_event_id": None,
        "operator_id": None,
        "outbox_status": "blocked_pending_operator_approval",
        "status": "blocked_pending_operator_approval",
        "blocked_reasons": ["operator_approval_required", "current_operator_approval_missing"],
        "idempotency_key": idempotency_packet.get("idempotency_key"),
        "idempotency_key_short": idempotency_packet.get("idempotency_key_short"),
        "idempotency_basis": candidate_basis,
        "idempotency_basis_check": compute_idempotency_basis(candidate_basis),
        "idempotency_status": idempotency_packet.get("status"),
        "kill_switch_status": kill_switch_packet.get("status"),
        "dispatch_intent_class": "manual_supervised_dispatch_candidate",
        "dispatch_mode": "dry_run",
        "dispatchable_now": False,
        "dispatch_performed": False,
        "valid_for_live_dispatch_now": False,
        "request_budget": 1,
        "auto_retry_allowed": False,
        "kill_switch_required": True,
        "redacted_audit_required": True,
        "audit_sink_required": True,
        "manual_fallback_required": True,
        "exact_payload_hash_required": True,
        "sendmessage_called": False,
        "telegram_write_endpoint_called": False,
        "live_write_performed": False,
        "network_request_performed": False,
        "credential_hydrated": False,
    }


def build_live_gate_packet(blocked_reasons: list[str] | tuple[str, ...]) -> dict[str, Any]:
    return {
        "task_label": TASK_LABEL,
        "packet_type": "telegram_sendmessage_dry_run_live_gate_packet",
        "live_gate_state": "dry_run_prepared_review_blocked_live_write_locked",
        "result_classification": RESULT_REVIEW_BLOCKED,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "approval_required": True,
        "current_operator_approval_present": False,
        "dispatchable_now": False,
        "sendmessage_called": False,
        "live_write_performed": False,
        "telegram_write_endpoint_called": False,
        "network_request_performed": False,
        "credential_hydrated": False,
        "live_write_allowed_now": False,
        "valid_for_live_dispatch_now": False,
        "next_gate_required_before_live_send": True,
    }


def _idempotency_candidate(payload_packet: dict[str, Any], hash_packet: dict[str, Any]) -> dict[str, Any]:
    payload_input = payload_packet["payload_hash_input"]
    return {
        "payload_hash": hash_packet["payload_hash"],
        "platform_id": payload_input["platform_id"],
        "payload_class_id": payload_input["payload_class_id"],
        "destination_binding_id": payload_input["destination_binding_id"],
        "credential_handle_id": payload_input["credential_handle_id"],
        "media_manifest_hash": payload_input["media_manifest_hash"],
        "policy_snapshot_id": payload_input["policy_snapshot_id"],
        "approval_ledger_entry_id": NO_APPROVAL_EVENT_ID,
        "approval_event_id": NO_APPROVAL_EVENT_ID,
        "dispatch_intent_class": "manual_supervised_dispatch_candidate",
    }


def run_telegram_supervised_sendmessage_dry_run_gate(
    *, existing_idempotency_keys: set[str] | tuple[str, ...] | list[str] | None = None
) -> TelegramSendMessageDryRunGateResult:
    payload_packet = build_telegram_sendmessage_dry_run_payload()
    validation = validate_telegram_sendmessage_payload(payload_packet)
    blocked: list[str] = list(validation.get("blocked_reasons") or [])
    hash_packet = build_payload_hash_packet(payload_packet)
    approval_packet = build_approval_requirement_packet(payload_packet, hash_packet)
    kill_switch_state = build_dry_run_kill_switch_state()
    kill_switch_packet = evaluate_kill_switch(kill_switch_state, PLATFORM_ID).as_dict()
    idempotency_packet = decide_idempotency(_idempotency_candidate(payload_packet, hash_packet), existing_idempotency_keys).as_dict()
    if idempotency_packet.get("duplicate") is True:
        blocked.extend(idempotency_packet.get("blocked_reasons") or ["duplicate_idempotency_key"])
    outbox_packet = build_review_blocked_outbox_packet(payload_packet, hash_packet, idempotency_packet, kill_switch_packet)
    if idempotency_packet.get("duplicate") is True and "duplicate_idempotency_key" not in outbox_packet["blocked_reasons"]:
        outbox_packet["blocked_reasons"].append("duplicate_idempotency_key")
    audit_packet = build_blocked_dispatch_audit_event(outbox_packet, outbox_packet["blocked_reasons"])
    for packet in (payload_packet, hash_packet, approval_packet, outbox_packet, idempotency_packet, kill_switch_packet, audit_packet):
        findings = scan_packet_for_telegram_secret_risk(packet)
        if findings:
            blocked.append(f"telegram_secret_risk:{','.join(findings)}")
    live_gate_packet = build_live_gate_packet(blocked)
    status = RESULT_REVIEW_BLOCKED if not validation.get("blocked_reasons") else "BLOCKED_DRY_RUN_GATE"
    evidence_packet = {
        "task_label": TASK_LABEL,
        "packet_type": "telegram_supervised_sendmessage_dry_run_gate_evidence_packet",
        "result_classification": status,
        "previous_accepted_baseline": "97bfb80ea48ca41d4592e9ecef765198881135f6",
        "starting_head": "3f1149de7787b39bab04e9611000c3c812457bb6",
        "canonical_packet_files": CANONICAL_PACKET_FILES,
        "dry_run_marker": DRY_RUN_MARKER,
        "payload_hash": hash_packet["payload_hash"],
        "payload_hash_short": hash_packet["payload_hash_short"],
        "outbox_status": outbox_packet["outbox_status"],
        "idempotency_status": idempotency_packet.get("status"),
        "kill_switch_status": kill_switch_packet.get("status"),
        "audit_event_type": audit_packet.get("event_type"),
        "blocked_reasons": sorted(set(blocked)),
        "approval_required": True,
        "operator_approval_required": True,
        "current_operator_approval_present": False,
        "operator_approved_dry_run_payload_hash": False,
        "operator_approved_live_send": False,
        "approval_completed": False,
        "no_llm_self_approval": True,
        "no_implicit_approval_from_readonly_proof": True,
        "dispatchable_now": False,
        "sendmessage_called": False,
        "telegram_write_endpoint_called": False,
        "live_write_allowed_now": False,
        "live_write_performed": False,
        "network_request_performed": False,
        "credential_hydrated": False,
        "raw_token_persisted": False,
        "raw_channel_id_persisted": False,
        "raw_url_persisted": False,
        "raw_headers_persisted": False,
        "raw_response_persisted": False,
        "valid_for_live_dispatch_now": False,
        "next_gate_required_before_live_send": True,
        "no_ui_change_proof": True,
        "no_browser_qa_proof": True,
        "no_provider_api_call_proof": True,
        "no_env_read_proof": True,
    }
    return TelegramSendMessageDryRunGateResult(
        status,
        payload_packet,
        hash_packet,
        approval_packet,
        outbox_packet,
        idempotency_packet,
        kill_switch_packet,
        audit_packet,
        live_gate_packet,
        evidence_packet,
        tuple(sorted(set(blocked))),
    )


def build_all_packets() -> dict[str, dict[str, Any]]:
    result = run_telegram_supervised_sendmessage_dry_run_gate()
    return {
        "sendmessage_dry_run_payload_packet.json": result.payload_packet,
        "sendmessage_payload_hash_packet.json": result.hash_packet,
        "sendmessage_approval_requirement_packet.json": result.approval_packet,
        "sendmessage_outbox_candidate_packet.json": result.outbox_packet,
        "sendmessage_idempotency_packet.json": result.idempotency_packet,
        "sendmessage_kill_switch_packet.json": result.kill_switch_packet,
        "sendmessage_redacted_audit_packet.json": result.audit_packet,
        "sendmessage_live_gate_packet.json": result.live_gate_packet,
        "evidence_packet.json": result.evidence_packet,
    }


def build_implementation_report() -> str:
    return """# Telegram sendMessage Dry-Run Gate R1 Repair

Result: PASS_DRY_RUN_PREP_REVIEW_BLOCKED

- Removed self-approval semantics.
- Gate now requires explicit operator approval for exact payload hash.
- Outbox candidate is blocked_pending_operator_approval.
- No sendMessage, write endpoint, network, env, credential hydration, raw URL/header/response/token/channel persistence.
- Next gate must collect operator approval before any supervised live-send preparation.
"""


def build_next_task_pointer() -> str:
    return """# Next Task Pointer

Next task: supervised operator approval capture for exact Telegram sendMessage payload hash.

Required before live send:

1. Human operator reviews payload hash and redacted destination binding.
2. Approval ledger records current operator approval for exact payload hash.
3. Separate live-write gate re-validates read-only proof, approval, idempotency, kill switch, and audit sink.
4. Live send remains locked until that future task explicitly enables it.
"""


def main() -> int:
    print(json.dumps(run_telegram_supervised_sendmessage_dry_run_gate().as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
