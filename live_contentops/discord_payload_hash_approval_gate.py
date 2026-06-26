"""Discord payload hash, approval packet, and send-gate refusal contract.

Local-only safety layer. It hashes Discord dry-run payload content, creates
non-dispatchable review packets, and returns refusal decisions without loading
webhook URLs or attempting network calls.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_PAYLOAD_HASH_APPROVAL_AND_SEND_GATE_STUB_V0"
SCHEMA_VERSION = "discord_payload_hash_approval_gate.v1"
HASH_CONTRACT_VERSION = "discord_payload_hash_contract.v1"
APPROVAL_SCHEMA_VERSION = "discord_payload_approval_packet.v1"
SEND_GATE_SCHEMA_VERSION = "discord_send_gate_refusal.v1"
AUDIT_EVENT_SCHEMA_VERSION = "discord_redacted_send_gate_audit_event.v1"
REFUSAL_DECISION = "REFUSE"
REFUSAL_REASON = "live_dispatch_not_authorized_in_this_task"
OPERATOR_ID = "Jim"
APPROVAL_SCOPE = "dry_run_review_only"
REQUIRED_DECISION_TYPES = ("announcement", "substack_drop", "product_update", "operator_private_summary")
HASH_INPUT_FIELDS = (
    "schema_version",
    "payload_id",
    "payload_type",
    "target_name",
    "destination_binding_id",
    "credential_handle_id",
    "title",
    "body",
    "disclosure",
    "discussion_question",
    "source_url",
    "content_refs",
    "dry_run_only",
    "live_write_allowed_now",
    "validation_status",
    "blockers",
    "warnings",
    "secret_output_policy",
)


def canonical_json(obj: Any) -> str:
    """Return deterministic sorted JSON with stable separators."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def adapter_type_for_payload(payload: dict) -> str:
    if payload.get("target_name") == "operator_private":
        return "manual_operator_private_binding"
    return "webhook_adapter"


def payload_hash_input(payload: dict) -> dict:
    """Build canonical hash input from approved dry-run payload fields only."""
    return {
        **{field: copy.deepcopy(payload.get(field)) for field in HASH_INPUT_FIELDS},
        "adapter_type": adapter_type_for_payload(payload),
        "hash_contract_version": HASH_CONTRACT_VERSION,
    }


def compute_payload_hash(payload: dict) -> str:
    canonical = canonical_json(payload_hash_input(payload))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_payload_hash_packet(payload: dict) -> dict:
    hash_input = payload_hash_input(payload)
    return {
        "schema_version": HASH_CONTRACT_VERSION,
        "task_label": TASK_LABEL,
        "payload_id": payload.get("payload_id"),
        "payload_type": payload.get("payload_type"),
        "target_name": payload.get("target_name"),
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
        "adapter_type": hash_input["adapter_type"],
        "payload_hash": compute_payload_hash(payload),
        "hash_algorithm": "SHA-256",
        "hash_scope": "discord_dry_run_payload_content_only",
        "canonical_hash_input": hash_input,
        "excluded_from_hash": {
            "raw_webhook_url": True,
            "credential_material": True,
            "credential_metadata": True,
            "cookie_session_local_storage": True,
            "browser_profile_storage": True,
            "raw_env_line": True,
            "raw_credential_file_content": True,
            "current_timestamp": True,
            "local_machine_secret_path": True,
            "human_preview_text": True,
            "webhook_json_preview": True,
        },
    }


def build_approval_packet(payload: dict, hash_packet: dict) -> dict:
    blockers = tuple(payload.get("blockers") or ())
    valid_payload = payload.get("validation_status") == "valid" and not blockers
    approval_status = "dry_run_review_packet_created" if valid_payload else "blocked_payload_not_approval_eligible"
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "approval_packet_id": f"discord_approval_{payload.get('payload_id')}",
        "approval_status": approval_status,
        "operator_id": OPERATOR_ID,
        "payload_id": payload.get("payload_id"),
        "payload_hash": hash_packet["payload_hash"],
        "payload_type": payload.get("payload_type"),
        "target_name": payload.get("target_name"),
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
        "adapter_type": hash_packet["adapter_type"],
        "dry_run_only": bool(payload.get("dry_run_only")),
        "live_write_allowed_now": False,
        "validation_status": payload.get("validation_status"),
        "blockers": list(blockers),
        "warnings": list(payload.get("warnings") or ()),
        "approved_at": None,
        "expires_at": None,
        "revoked": False,
        "valid_for_outbox": False,
        "valid_for_dispatch": False,
        "approval_scope": APPROVAL_SCOPE,
        "approval_required_for_future_dispatch": True,
    }


def build_audit_event_preview(payload: dict, hash_packet: dict, approval_packet: dict, decision: str = REFUSAL_DECISION, reason: str = REFUSAL_REASON) -> dict:
    return {
        "schema_version": AUDIT_EVENT_SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "audit_event_id": f"discord_send_gate_refused_{payload.get('payload_id')}",
        "event_type": "discord_send_gate_refused",
        "platform": "discord",
        "target_name": payload.get("target_name"),
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
        "payload_hash": hash_packet["payload_hash"],
        "approval_status": approval_packet.get("approval_status"),
        "decision": decision,
        "reason": reason,
        "network_call_attempted": False,
        "response_class": "not_attempted",
        "public_url": None,
        "webhook_message_id": None,
        "secret_output_policy": {
            "webhook_url_output": False,
            "token_output": False,
            "token_metadata_output": False,
            "request_headers_output": False,
            "raw_response_body_output": False,
            "browser_or_session_storage_output": False,
        },
        "live_write_allowed_now": False,
    }


def evaluate_send_gate(payload: dict, hash_packet: dict, approval_packet: dict, discord_environment_packet: dict | None = None) -> dict:
    audit_event_preview = build_audit_event_preview(payload, hash_packet, approval_packet)
    return {
        "schema_version": SEND_GATE_SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "decision_id": f"discord_send_gate_decision_{payload.get('payload_id')}",
        "decision": REFUSAL_DECISION,
        "reason": REFUSAL_REASON,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "live_write_allowed_now": False,
        "dispatch_adapter": "webhook_adapter",
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
        "payload_hash": hash_packet["payload_hash"],
        "payload_id": payload.get("payload_id"),
        "payload_type": payload.get("payload_type"),
        "target_name": payload.get("target_name"),
        "approval_status": approval_packet.get("approval_status"),
        "environment_schema_version": (discord_environment_packet or {}).get("schema_version"),
        "outbox_mutated": False,
        "dispatch_success_marked": False,
        "discord_bot_required": False,
        "audit_event_preview": audit_event_preview,
    }


def build_hash_approval_gate_packet(payload_packet: dict, discord_environment_packet: dict | None = None) -> dict:
    payloads = list(payload_packet.get("payloads", []))
    hash_packets = [build_payload_hash_packet(payload) for payload in payloads]
    approvals = [build_approval_packet(payload, hash_packet) for payload, hash_packet in zip(payloads, hash_packets)]
    decisions = []
    for payload, hash_packet, approval in zip(payloads, hash_packets, approvals):
        if payload.get("payload_type") in REQUIRED_DECISION_TYPES:
            decisions.append(evaluate_send_gate(payload, hash_packet, approval, discord_environment_packet))
    return {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "source_payload_packet_schema_version": payload_packet.get("schema_version"),
        "dry_run_only": True,
        "live_write_allowed_now": False,
        "discord_bot_required": False,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "hash_contract_version": HASH_CONTRACT_VERSION,
        "payload_hashes": hash_packets,
        "approval_packets": approvals,
        "send_gate_refusal_decisions": decisions,
        "audit_event_previews": [decision["audit_event_preview"] for decision in decisions],
        "summary": {
            "payload_count": len(payloads),
            "hash_count": len(hash_packets),
            "approval_packet_count": len(approvals),
            "send_gate_refusal_decision_count": len(decisions),
            "all_approval_packets_dispatchable": False,
            "all_send_gate_decisions_refuse": all(decision["decision"] == REFUSAL_DECISION for decision in decisions),
        },
        "secret_output_policy": {
            "webhook_url_output": False,
            "token_output": False,
            "token_metadata_output": False,
            "cookie_session_local_storage_output": False,
            "browser_profile_storage_output": False,
            "raw_env_line_output": False,
        },
    }


def write_hash_approval_gate_packet(payload_packet_path: str | Path, output_path: str | Path, discord_environment_path: str | Path | None = None) -> dict:
    payload_packet = json.loads(Path(payload_packet_path).read_text(encoding="utf-8"))
    discord_environment_packet = None
    if discord_environment_path:
        discord_environment_packet = json.loads(Path(discord_environment_path).read_text(encoding="utf-8"))
    packet = build_hash_approval_gate_packet(payload_packet, discord_environment_packet)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Discord payload hash approval gate dry-run packet")
    parser.add_argument("--payload-packet", required=True, help="Discord dry-run payload packet path")
    parser.add_argument("--output", required=True, help="Output path for hash approval gate packet")
    parser.add_argument("--discord-environment-packet", default=None, help="Optional redacted Discord environment packet path")
    args = parser.parse_args(argv)
    packet = write_hash_approval_gate_packet(args.payload_packet, args.output, args.discord_environment_packet)
    print(json.dumps({
        "task_label": TASK_LABEL,
        "result": "PASS",
        "output": args.output,
        "payload_count": packet["summary"]["payload_count"],
        "hash_count": packet["summary"]["hash_count"],
        "approval_packet_count": packet["summary"]["approval_packet_count"],
        "send_gate_refusal_decision_count": packet["summary"]["send_gate_refusal_decision_count"],
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "live_write_allowed_now": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
