"""Minimal deterministic authority core for Batch C Telegram sendMessage pilot."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .credential_redaction_policy import REDACTION_POLICY_ID, contains_secret_shaped_text

TASK_LABEL = "TASK_CONTENTOPS_TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY_AND_SUPERVISED_SENDMESSAGE_PILOT_V0"
PLATFORM_ID = "telegram_channel_destination"
DESTINATION_BINDING_ID = "telegram_channel_id_env_binding"
CREDENTIAL_HANDLE_ID = "telegram_bot_token_env_handle"
PAYLOAD_SCHEMA_VERSION = "telegram_live_payload_packet_v1"
ADAPTER_VERSION = "telegram_sendmessage_pilot_adapter_v1"
APPROVED_BY = "operator_prompt_explicit"
METHOD = "sendMessage"
CONTENT_LANE = "live_pilot_test_only"
REQUEST_BUDGET = 1
AUTO_RETRY_ALLOWED = False
ALLOWED_WRITE_METHODS = ("sendMessage",)
FORBIDDEN_WRITE_METHODS = ("sendPhoto", "sendDocument", "sendMediaGroup", "sendRichMessage")
APPROVED_PAYLOAD_TEXT = """Capital Chronicle ContentOps live Telegram pilot.

This is a supervised test post from the local ContentOps publish gate.
No market advice. No trading signal. No autonomous posting.
Payload approved for one Telegram sendMessage request only."""
KILL_SWITCH_TRUE_VALUES = {"1", "true", "yes", "on"}
KILL_SWITCH_FALSE_VALUES = {"", "0", "false", "no", "off"}

@dataclass(frozen=True)
class PayloadPacket:
    platform_id: str
    destination_binding_id: str
    credential_handle_id: str
    payload_text: str
    payload_hash: str
    payload_schema_version: str
    adapter_version: str
    method: str
    content_lane: str
    no_advice: bool
    no_signal: bool
    approved_by: str
    request_budget: int
    auto_retry_allowed: bool

def canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(data: Mapping[str, Any] | str) -> str:
    text = canonical_json(data) if isinstance(data, Mapping) else data
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def assert_no_secret_or_token_shaped_output(data: Any) -> None:
    text = json.dumps(data, sort_keys=True, ensure_ascii=False) if not isinstance(data, str) else data
    if contains_secret_shaped_text(text):
        raise ValueError("secret_shaped_text_blocked_by_batch_c_policy")

def _hash_input(payload_text: str, destination_binding_id: str, credential_handle_id: str, method: str) -> dict[str, Any]:
    if method not in ALLOWED_WRITE_METHODS:
        raise ValueError("telegram_write_method_not_allowlisted")
    for forbidden in FORBIDDEN_WRITE_METHODS:
        if forbidden == method:
            raise ValueError("telegram_write_method_forbidden")
    assert_no_secret_or_token_shaped_output(payload_text)
    return {
        "platform_id": PLATFORM_ID,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "payload_text": payload_text,
        "payload_schema_version": PAYLOAD_SCHEMA_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "method": method,
        "content_lane": CONTENT_LANE,
        "no_advice": True,
        "no_signal": True,
        "approved_by": APPROVED_BY,
        "request_budget": REQUEST_BUDGET,
        "auto_retry_allowed": AUTO_RETRY_ALLOWED,
    }

def compute_payload_hash(payload_text: str = APPROVED_PAYLOAD_TEXT, destination_binding_id: str = DESTINATION_BINDING_ID, credential_handle_id: str = CREDENTIAL_HANDLE_ID, method: str = METHOD) -> str:
    return sha256_hex(_hash_input(payload_text, destination_binding_id, credential_handle_id, method))

def build_payload_packet(payload_text: str = APPROVED_PAYLOAD_TEXT, destination_binding_id: str = DESTINATION_BINDING_ID, credential_handle_id: str = CREDENTIAL_HANDLE_ID, method: str = METHOD) -> dict[str, Any]:
    payload_hash = compute_payload_hash(payload_text, destination_binding_id, credential_handle_id, method)
    packet = PayloadPacket(PLATFORM_ID, destination_binding_id, credential_handle_id, payload_text, payload_hash, PAYLOAD_SCHEMA_VERSION, ADAPTER_VERSION, method, CONTENT_LANE, True, True, APPROVED_BY, REQUEST_BUDGET, AUTO_RETRY_ALLOWED)
    result = asdict(packet)
    assert_no_secret_or_token_shaped_output(result)
    return result

def build_approval_event(payload_packet: Mapping[str, Any]) -> dict[str, Any]:
    payload_hash = str(payload_packet["payload_hash"])
    event = {
        "task_label": TASK_LABEL,
        "approval_event_id": "approval_" + payload_hash[:16],
        "approved_by": APPROVED_BY,
        "approval_scope": "one_telegram_sendmessage_request_only",
        "payload_hash": payload_hash,
        "payload_text_exact_match": payload_packet.get("payload_text") == APPROVED_PAYLOAD_TEXT,
        "request_budget": REQUEST_BUDGET,
        "auto_retry_allowed": False,
        "raw_secret_persisted": False,
    }
    assert_no_secret_or_token_shaped_output(event)
    return event

def build_idempotency_key(payload_packet: Mapping[str, Any]) -> str:
    return sha256_hex({
        "task_label": TASK_LABEL,
        "platform_id": payload_packet["platform_id"],
        "destination_binding_id": payload_packet["destination_binding_id"],
        "credential_handle_id": payload_packet["credential_handle_id"],
        "payload_hash": payload_packet["payload_hash"],
        "method": payload_packet["method"],
        "adapter_version": payload_packet["adapter_version"],
    })

def build_outbox_candidate(payload_packet: Mapping[str, Any], approval_event: Mapping[str, Any]) -> dict[str, Any]:
    idempotency_key = build_idempotency_key(payload_packet)
    outbox = {
        "task_label": TASK_LABEL,
        "outbox_id": "outbox_" + idempotency_key[:16],
        "idempotency_key_hash": idempotency_key,
        "idempotency_key_class": "sha256_redacted_no_secret_inputs",
        "approval_event_id": approval_event["approval_event_id"],
        "payload_hash": payload_packet["payload_hash"],
        "platform_id": payload_packet["platform_id"],
        "destination_binding_id": payload_packet["destination_binding_id"],
        "credential_handle_id": payload_packet["credential_handle_id"],
        "method": payload_packet["method"],
        "request_budget": REQUEST_BUDGET,
        "auto_retry_allowed": False,
        "raw_destination_persisted": False,
        "raw_credential_persisted": False,
        "status": "candidate_created",
    }
    assert_no_secret_or_token_shaped_output(outbox)
    return outbox

def classify_kill_switch(value: str | None) -> dict[str, Any]:
    normalized = "" if value is None else value.strip().lower()
    enabled = normalized in KILL_SWITCH_TRUE_VALUES
    state = "on_redacted" if enabled else "off_or_missing_redacted"
    if normalized and normalized not in KILL_SWITCH_TRUE_VALUES and normalized not in KILL_SWITCH_FALSE_VALUES:
        state = "unrecognized_treated_off_redacted"
    packet = {"task_label": TASK_LABEL, "env_key_name": "CONTENTOPS_GLOBAL_KILL_SWITCH", "kill_switch_state": state, "live_send_blocked": enabled, "raw_value_persisted": False}
    assert_no_secret_or_token_shaped_output(packet)
    return packet

def check_idempotency(task_dir: str | Path, idempotency_key_hash: str) -> dict[str, Any]:
    root = Path(task_dir)
    root.mkdir(parents=True, exist_ok=True)
    matches: list[str] = []
    unknowns: list[str] = []
    for path in root.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        text = json.dumps(data, sort_keys=True)
        if idempotency_key_hash not in text:
            continue
        status_fields = {
            str(data.get("status") or ""),
            str(data.get("sendMessage", {}).get("result_classification") or ""),
            str(data.get("result_classification") or ""),
        }
        if status_fields.intersection({"success", "live_send_success"}):
            matches.append(path.name)
        elif status_fields.intersection({"unknown_requires_manual_reconciliation", "prior_unknown_requires_manual_reconciliation"}):
            unknowns.append(path.name)
    if matches:
        state, blocked = "prior_success_duplicate_suppressed", True
    elif unknowns:
        state, blocked = "prior_unknown_requires_manual_reconciliation", True
    else:
        state, blocked = "no_prior_success_or_unknown", False
    packet = {"task_label": TASK_LABEL, "idempotency_key_hash": idempotency_key_hash, "idempotency_state": state, "send_blocked": blocked, "matching_prior_success_count": len(matches), "matching_prior_unknown_count": len(unknowns), "raw_request_persisted": False, "raw_response_persisted": False}
    assert_no_secret_or_token_shaped_output(packet)
    return packet

def build_redacted_audit_event(payload_packet: Mapping[str, Any], approval_event: Mapping[str, Any], outbox: Mapping[str, Any], kill_switch: Mapping[str, Any], idempotency: Mapping[str, Any], probes: Mapping[str, Any], send_result: Mapping[str, Any], env_summary: Mapping[str, Any]) -> dict[str, Any]:
    event = {
        "task_label": TASK_LABEL,
        "redaction_policy_id": REDACTION_POLICY_ID,
        "payload_hash": payload_packet["payload_hash"],
        "approval_event_id": approval_event["approval_event_id"],
        "outbox_id": outbox["outbox_id"],
        "idempotency_key_hash": outbox["idempotency_key_hash"],
        "kill_switch_state": kill_switch["kill_switch_state"],
        "idempotency_state": idempotency["idempotency_state"],
        "env_summary": env_summary,
        "endpoint_family": "Telegram Bot API",
        "host": "api.telegram.org",
        "timeout_seconds": 10,
        "redirect_policy": "redirect_disabled_fail_closed",
        "auto_retry_allowed": False,
        "request_counts": {"getMe": probes.get("getMe", {}).get("request_count", 0), "getChat": probes.get("getChat", {}).get("request_count", 0), "sendMessage": send_result.get("request_count", 0)},
        "probes": probes,
        "sendMessage": send_result,
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "raw_url_persisted": False,
        "headers_persisted": False,
        "raw_secret_persisted": False,
        "no_retry_performed": True,
        "no_second_send_performed": True,
        "forbidden_methods_performed": [],
    }
    assert_no_secret_or_token_shaped_output(event)
    return event
