"""Telegram supervised sendMessage dry-run gate.

Pure local domain-contract module for preparing a deterministic Telegram sendMessage
candidate without performing live dispatch, network calls, env reads, or credential
hydration.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import re
from typing import Any

from .approval_ledger import build_operator_approved_event, compute_audit_hash
from .approval_payload_hash import canonical_payload_hash_input, compute_payload_hash, payload_hash_short
from .dispatch_outbox import prepare_dispatch_outbox_entry
from .kill_switch_policy import build_platform_kill_switch_state

TASK_LABEL = "TASK_CONTENTOPS_TELEGRAM_SUPERVISED_SENDMESSAGE_PREP_AND_DRY_RUN_GATE_V0"
MODEL = "contentops.telegram_supervised_sendmessage_dry_run_gate"
MODEL_VERSION = "0174TELEGRAM_SENDMESSAGE_DRY_RUN_GATE_V0"

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
SAFE_MESSAGE_TEXT = (
    "DRY_RUN_NOT_FOR_LIVE_SEND — Capital Chronicle supervised Telegram "
    "sendMessage dry-run fixture for operator review. This fixture contains "
    "no recommendations, no positions, no prices, no external links, and no secrets."
)

FORBIDDEN_VALUE_RE = re.compile(
    r"(\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|https://api\.telegram\.org/|\b-100\d{6,}\b|@[A-Za-z0-9_]{3,}|bearer\s+[A-Za-z0-9._\-]{20,})",
    re.IGNORECASE,
)
FORBIDDEN_TEXT_TERMS = ("buy", "sell", "hold", "long", "short", "target", "entry", "exit", "signal", "stop loss", "take profit", "guaranteed", "profit")
FORBIDDEN_KEYS = {"token", "bot_token", "chat_id", "channel_id", "channel_handle", "raw_url", "request_url", "headers", "raw_response", "provider_response", "authorization"}


@dataclass(frozen=True)
class TelegramSendMessageDryRunGateResult:
    """Complete value-only dry-run result."""

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
            "live_write_performed": False,
            "network_request_performed": False,
            "credential_hydrated": False,
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
            findings.extend(_walk_secret_risk(child, f"{path}[{idx}]"))
    elif isinstance(value, str) and FORBIDDEN_VALUE_RE.search(value):
        findings.append(path or "<value>")
    return sorted(set(findings))


def scan_packet_for_telegram_secret_risk(packet: Any) -> list[str]:
    """Conservative Telegram-specific redaction scan."""
    return _walk_secret_risk(packet)


def build_telegram_sendmessage_dry_run_payload() -> dict[str, Any]:
    """Build deterministic safe sendMessage payload for dry-run only."""
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
        "live_write_performed": False,
        "network_request_performed": False,
        "credential_hydrated": False,
        "raw_token_persisted": False,
        "raw_chat_id_persisted": False,
        "raw_url_persisted": False,
        "raw_headers_persisted": False,
        "raw_response_persisted": False,
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
    for flag in ("sendmessage_called", "live_write_performed", "network_request_performed", "credential_hydrated", "raw_token_persisted", "raw_chat_id_persisted", "raw_url_persisted", "raw_headers_persisted", "raw_response_persisted", "valid_for_live_dispatch_now"):
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
    return {"task_label": TASK_LABEL, "packet_type": "telegram_sendmessage_payload_validation_packet", "valid": not blockers, "blocked_reasons": sorted(set(blockers)), "sendmessage_called": False, "live_write_performed": False, "network_request_performed": False, "credential_hydrated": False, "valid_for_live_dispatch_now": False}


def build_payload_hash_packet(payload_packet: dict[str, Any]) -> dict[str, Any]:
    payload_input = deepcopy(payload_packet["payload_hash_input"])
    payload_input["payload_id"] = payload_packet["payload_id"]
    payload_hash = compute_payload_hash(payload_input)
    return {"task_label": TASK_LABEL, "packet_type": "telegram_sendmessage_payload_hash_packet", "payload_id": payload_packet["payload_id"], "payload_hash_algorithm": "sha256", "payload_hash": payload_hash, "payload_hash_short": payload_hash_short(payload_hash), "canonical_payload_json": _canonical_json(payload_input), "hash_input_contains_secret_risk": False, "valid_for_live_dispatch_now": False}


def build_dry_run_approval_packet(payload_packet: dict[str, Any], hash_packet: dict[str, Any]) -> dict[str, Any]:
    event = build_operator_approved_event(
        operator_id="operator_supervised_dry_run_symbolic",
        approval_channel="manual_record",
        challenge_id="telegram_sendmessage_dry_run_challenge_symbolic",
        payload_id=payload_packet["payload_id"],
        payload_hash=hash_packet["payload_hash"],
        platform_id=PLATFORM_ID,
        payload_class_id=PAYLOAD_CLASS_ID,
        destination_binding_id=DESTINATION_BINDING_ID,
        credential_handle_id=CREDENTIAL_HANDLE_ID,
        policy_snapshot_id=POLICY_SNAPSHOT_ID,
        media_manifest_hash="no_media_manifest",
        approval_text="Operator approval for dry-run packet only; not live send approval.",
    ).__dict__
    event["created_at"] = "2026-06-24T00:00:00Z"
    event["ledger_event_id"] = f"app_{hash_packet['payload_hash_short']}_dryrun0001"
    event["audit_hash"] = compute_audit_hash(event)
    event["valid_for_dispatch"] = True
    event["valid_for_live_dispatch_now"] = False
    return {"task_label": TASK_LABEL, "packet_type": "telegram_sendmessage_dry_run_approval_packet", "approval_scope": "dry_run_only_not_live_send", "approval_event": event, "operator_approved_dry_run_payload_hash": True, "operator_approved_live_send": False, "valid_for_live_dispatch_now": False}


def build_dry_run_kill_switch_state() -> dict[str, Any]:
    state = build_platform_kill_switch_state(PLATFORM_ID, False, "local_dry_run_gate_only_live_write_locked", "operator_supervised_dry_run_symbolic", "2026-06-24T00:00:00Z")
    state["allow_local_outbox"] = True
    state["live_dispatch_enabled"] = False
    return state


def build_live_gate_packet(blocked_reasons: list[str] | tuple[str, ...]) -> dict[str, Any]:
    return {"task_label": TASK_LABEL, "packet_type": "telegram_sendmessage_dry_run_live_gate_packet", "live_gate_state": "dry_run_prepared_live_write_locked", "result_classification": "PASS_DRY_RUN_GATE" if not blocked_reasons else "BLOCKED_DRY_RUN_GATE", "blocked_reasons": sorted(set(blocked_reasons)), "sendmessage_called": False, "live_write_performed": False, "telegram_write_endpoint_called": False, "network_request_performed": False, "credential_hydrated": False, "live_write_allowed_now": False, "valid_for_live_dispatch_now": False, "next_gate_required_before_live_send": True}


def run_telegram_supervised_sendmessage_dry_run_gate(*, existing_idempotency_keys: set[str] | tuple[str, ...] | list[str] | None = None) -> TelegramSendMessageDryRunGateResult:
    payload_packet = build_telegram_sendmessage_dry_run_payload()
    validation = validate_telegram_sendmessage_payload(payload_packet)
    blocked: list[str] = list(validation.get("blocked_reasons") or [])
    hash_packet = build_payload_hash_packet(payload_packet)
    approval_packet = build_dry_run_approval_packet(payload_packet, hash_packet)
    kill_switch_state = build_dry_run_kill_switch_state()
    payload_input = deepcopy(payload_packet["payload_hash_input"])
    payload_input["payload_id"] = payload_packet["payload_id"]
    approval_event = deepcopy(approval_packet["approval_event"])
    outbox_result = prepare_dispatch_outbox_entry(payload_input, [approval_event], kill_switch_state, existing_idempotency_keys, OUTBOX_ENTRY_ID, AUDIT_SINK_ID, "dry_run").as_dict()
    if outbox_result["status"] not in {"ready_for_mock_dispatch", "ready_for_supervised_live_future"}:
        blocked.extend(outbox_result.get("blocked_reasons") or [])
    idempotency_packet = outbox_result["idempotency_decision"]
    kill_switch_packet = outbox_result["kill_switch_decision"]
    audit_packet = outbox_result["audit_event"] or {}
    outbox_packet = outbox_result["outbox_entry"] or {}
    for packet in (payload_packet, hash_packet, approval_packet, outbox_packet, idempotency_packet, kill_switch_packet, audit_packet):
        findings = scan_packet_for_telegram_secret_risk(packet)
        if findings:
            blocked.append(f"telegram_secret_risk:{','.join(findings)}")
    live_gate_packet = build_live_gate_packet(blocked)
    status = "PASS_DRY_RUN_GATE" if not blocked else "BLOCKED_DRY_RUN_GATE"
    evidence_packet = {"task_label": TASK_LABEL, "packet_type": "telegram_supervised_sendmessage_dry_run_gate_evidence_packet", "result_classification": status, "previous_accepted_baseline": "97bfb80ea48ca41d4592e9ecef765198881135f6", "final_head_self_recording_limitation": "Final commit SHA is unknown before commit; verify final HEAD from git after commit/push.", "canonical_packet_files": ["payload_packet.json", "payload_hash_packet.json", "approval_packet.json", "outbox_candidate_packet.json", "idempotency_packet.json", "kill_switch_packet.json", "redacted_audit_packet.json", "live_gate_packet.json", "evidence_packet.json"], "dry_run_marker": DRY_RUN_MARKER, "payload_hash": hash_packet["payload_hash"], "payload_hash_short": hash_packet["payload_hash_short"], "outbox_status": outbox_result["status"], "idempotency_status": idempotency_packet.get("status"), "kill_switch_status": kill_switch_packet.get("status"), "audit_event_type": audit_packet.get("event_type"), "blocked_reasons": sorted(set(blocked)), "sendmessage_called": False, "telegram_write_endpoint_called": False, "live_write_performed": False, "network_request_performed": False, "credential_hydrated": False, "raw_token_persisted": False, "raw_channel_id_persisted": False, "raw_url_persisted": False, "raw_headers_persisted": False, "raw_response_persisted": False, "valid_for_live_dispatch_now": False, "operator_approved_live_send": False, "next_gate_required_before_live_send": True, "no_ui_change_proof": True, "no_browser_qa_proof": True, "no_provider_api_call_proof": True}
    return TelegramSendMessageDryRunGateResult(status, payload_packet, hash_packet, approval_packet, outbox_packet, idempotency_packet, kill_switch_packet, audit_packet, live_gate_packet, evidence_packet, tuple(sorted(set(blocked))))


def build_all_packets() -> dict[str, dict[str, Any]]:
    result = run_telegram_supervised_sendmessage_dry_run_gate()
    return {"payload_packet.json": result.payload_packet, "payload_hash_packet.json": result.hash_packet, "approval_packet.json": result.approval_packet, "outbox_candidate_packet.json": result.outbox_packet, "idempotency_packet.json": result.idempotency_packet, "kill_switch_packet.json": result.kill_switch_packet, "redacted_audit_packet.json": result.audit_packet, "live_gate_packet.json": result.live_gate_packet, "evidence_packet.json": result.evidence_packet}


def main() -> int:
    print(json.dumps(run_telegram_supervised_sendmessage_dry_run_gate().as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())





