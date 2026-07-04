"""Discord approval ledger and non-live outbox binding contract.

Append-only local governance layer. It records Discord dry-run approval packets,
binds non-dispatchable outbox entries to exact payload hashes and bindings, and
revalidates that no live dispatch can happen in this task.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_APPROVAL_LEDGER_AND_OUTBOX_BINDING_V0"
SCHEMA_VERSION = "discord_approval_ledger_outbox_contract.v1"
LEDGER_SCHEMA_VERSION = "discord_approval_ledger.v1"
OUTBOX_SCHEMA_VERSION = "discord_dispatch_outbox_non_live.v1"
AUDIT_SCHEMA_VERSION = "discord_outbox_redacted_audit_event.v1"
REFUSE = "REFUSE"
REQUIRED_OUTBOX_PAYLOAD_TYPES = ("announcement", "substack_drop", "product_update", "operator_private_summary")
LIVE_BLOCKER = "live_dispatch_not_authorized_in_this_task"
HASH_HEX_LENGTH = 64


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_sha256(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def is_valid_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == HASH_HEX_LENGTH and all(ch in "0123456789abcdef" for ch in value)


def ledger_status_for_approval(approval_packet: dict) -> str:
    if approval_packet.get("approval_status") == "dry_run_review_packet_created":
        return "recorded_for_review"
    if approval_packet.get("approval_status") == "blocked_payload_not_approval_eligible":
        return "blocked_not_recorded_for_dispatch"
    return "blocked_unknown_approval_status"


def build_ledger_record(approval_packet: dict) -> dict:
    return {
        "ledger_record_id": f"discord_ledger_{approval_packet.get('approval_packet_id')}",
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "source_approval_packet_id": approval_packet.get("approval_packet_id"),
        "payload_id": approval_packet.get("payload_id"),
        "payload_hash": approval_packet.get("payload_hash"),
        "payload_type": approval_packet.get("payload_type"),
        "target_name": approval_packet.get("target_name"),
        "destination_binding_id": approval_packet.get("destination_binding_id"),
        "credential_handle_id": approval_packet.get("credential_handle_id"),
        "adapter_type": approval_packet.get("adapter_type"),
        "operator_id": approval_packet.get("operator_id"),
        "approval_scope": approval_packet.get("approval_scope"),
        "approval_status": approval_packet.get("approval_status"),
        "approved_at": approval_packet.get("approved_at"),
        "expires_at": approval_packet.get("expires_at"),
        "revoked": bool(approval_packet.get("revoked", False)),
        "valid_for_outbox": bool(approval_packet.get("valid_for_outbox", False)),
        "valid_for_dispatch": False,
        "ledger_append_only": True,
        "ledger_entry_status": ledger_status_for_approval(approval_packet),
        "created_from_task_label": approval_packet.get("task_label"),
        "live_write_allowed_now": False,
        "dispatch_authorization_status": "not_authorized_in_this_task",
    }


def build_ledger_records(hash_approval_packet: dict) -> list[dict]:
    return [build_ledger_record(item) for item in hash_approval_packet.get("approval_packets", [])]


def hash_packets_by_payload_id(hash_approval_packet: dict) -> dict[str, dict]:
    return {item.get("payload_id"): item for item in hash_approval_packet.get("payload_hashes", [])}


def idempotency_key(payload_hash: str, destination_binding_id: str, credential_handle_id: str, payload_type: str, target_name: str) -> str:
    return stable_sha256({
        "payload_hash": payload_hash,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "payload_type": payload_type,
        "target_name": target_name,
        "outbox_schema_version": OUTBOX_SCHEMA_VERSION,
    })


def duplicate_suppression_key(payload_hash: str, target_name: str, destination_binding_id: str) -> str:
    return stable_sha256({
        "payload_hash": payload_hash,
        "target_name": target_name,
        "destination_binding_id": destination_binding_id,
    })


def revalidate_outbox_entry(ledger_record: dict, outbox_entry: dict, current_payload_hash_packet: dict | None = None) -> dict:
    blockers: list[str] = []
    comparison = current_payload_hash_packet or ledger_record
    checks = (
        ("payload_hash", "blocked_payload_hash_mismatch"),
        ("payload_id", "blocked_payload_id_mismatch"),
        ("payload_type", "blocked_payload_type_mismatch"),
        ("target_name", "blocked_target_mismatch"),
        ("destination_binding_id", "blocked_destination_mismatch"),
        ("credential_handle_id", "blocked_credential_handle_mismatch"),
    )
    if not is_valid_hash(outbox_entry.get("payload_hash")):
        blockers.append("blocked_hash_missing_or_invalid")
    for field, blocker in checks:
        if outbox_entry.get(field) != comparison.get(field):
            blockers.append(blocker)
    if ledger_record.get("valid_for_dispatch") is not False or outbox_entry.get("eligible_for_dispatch") is not False:
        blockers.append("blocked_dispatch_flag_not_false")
    if ledger_record.get("live_write_allowed_now") is not False or outbox_entry.get("live_write_allowed_now") is not False:
        blockers.append("blocked_live_write_flag_not_false")
    if blockers:
        priority = (
            "blocked_hash_missing_or_invalid",
            "blocked_payload_hash_mismatch",
            "blocked_destination_mismatch",
            "blocked_credential_handle_mismatch",
            "blocked_payload_id_mismatch",
            "blocked_payload_type_mismatch",
            "blocked_target_mismatch",
            "blocked_dispatch_flag_not_false",
            "blocked_live_write_flag_not_false",
        )
        status = next((item for item in priority if item in blockers), blockers[0])
    else:
        status = "pass_non_dispatchable"
    return {
        "revalidation_status": status,
        "blockers": list(dict.fromkeys(blockers)),
        "eligible_for_dispatch": False,
        "live_write_allowed_now": False,
    }


def outbox_status_for(ledger_record: dict, hash_packet: dict | None) -> str:
    if not hash_packet or not is_valid_hash(ledger_record.get("payload_hash")):
        return "blocked_hash_missing_or_invalid"
    if ledger_record.get("destination_binding_id") != hash_packet.get("destination_binding_id"):
        return "blocked_destination_mismatch"
    if ledger_record.get("credential_handle_id") != hash_packet.get("credential_handle_id"):
        return "blocked_credential_handle_mismatch"
    if ledger_record.get("approval_status") != "dry_run_review_packet_created":
        return "blocked_approval_not_eligible"
    return "queued_non_live_refusal_review"


def build_audit_event_preview(ledger_record: dict, outbox_entry_id: str) -> dict:
    return {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "event_type": "discord_outbox_entry_refused_non_live",
        "payload_hash": ledger_record.get("payload_hash"),
        "destination_binding_id": ledger_record.get("destination_binding_id"),
        "credential_handle_id": ledger_record.get("credential_handle_id"),
        "outbox_entry_id": outbox_entry_id,
        "ledger_record_id": ledger_record.get("ledger_record_id"),
        "send_gate_decision": REFUSE,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "response_class": "not_attempted",
        "public_url": None,
        "webhook_message_id": None,
        "secret_output_policy": {
            "webhook_url_output": False,
            "credential_material_output": False,
            "credential_metadata_output": False,
            "request_headers_output": False,
            "raw_response_body_output": False,
            "browser_or_session_storage_output": False,
        },
    }


def build_outbox_entry(ledger_record: dict, hash_packet: dict | None = None) -> dict:
    outbox_entry_id = f"discord_outbox_{ledger_record.get('payload_id')}"
    status = outbox_status_for(ledger_record, hash_packet)
    dispatch_blockers = [LIVE_BLOCKER]
    if status != "queued_non_live_refusal_review":
        dispatch_blockers.append(status)
    entry = {
        "outbox_entry_id": outbox_entry_id,
        "outbox_schema_version": OUTBOX_SCHEMA_VERSION,
        "source_ledger_record_id": ledger_record.get("ledger_record_id"),
        "source_approval_packet_id": ledger_record.get("source_approval_packet_id"),
        "payload_id": ledger_record.get("payload_id"),
        "payload_hash": ledger_record.get("payload_hash"),
        "payload_type": ledger_record.get("payload_type"),
        "target_name": ledger_record.get("target_name"),
        "destination_binding_id": ledger_record.get("destination_binding_id"),
        "credential_handle_id": ledger_record.get("credential_handle_id"),
        "adapter_type": ledger_record.get("adapter_type"),
        "outbox_status": status,
        "eligible_for_dispatch": False,
        "dispatch_blockers": dispatch_blockers,
        "revalidation_required": True,
        "revalidation_status": "pending",
        "send_gate_decision": REFUSE,
        "live_write_allowed_now": False,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "public_url": None,
        "webhook_message_id": None,
        "dispatch_attempt_count": 0,
        "auto_retry_allowed": False,
        "idempotency_key": idempotency_key(
            str(ledger_record.get("payload_hash")),
            str(ledger_record.get("destination_binding_id")),
            str(ledger_record.get("credential_handle_id")),
            str(ledger_record.get("payload_type")),
            str(ledger_record.get("target_name")),
        ),
        "duplicate_suppression_key": duplicate_suppression_key(
            str(ledger_record.get("payload_hash")),
            str(ledger_record.get("target_name")),
            str(ledger_record.get("destination_binding_id")),
        ),
    }
    revalidation = revalidate_outbox_entry(ledger_record, entry, hash_packet)
    entry["revalidation_status"] = revalidation["revalidation_status"]
    entry["revalidation_blockers"] = revalidation["blockers"]
    entry["audit_event_preview"] = build_audit_event_preview(ledger_record, outbox_entry_id)
    return entry


def build_outbox_entries(ledger_records: list[dict], hash_packet_map: dict[str, dict]) -> list[dict]:
    entries = []
    for record in ledger_records:
        if record.get("payload_type") in REQUIRED_OUTBOX_PAYLOAD_TYPES:
            entries.append(build_outbox_entry(record, hash_packet_map.get(record.get("payload_id"))))
    return entries


def build_approval_ledger_outbox_packet(hash_approval_packet: dict, source_path: str | None = None) -> dict:
    ledger_records = build_ledger_records(hash_approval_packet)
    hash_packet_map = hash_packets_by_payload_id(hash_approval_packet)
    outbox_entries = build_outbox_entries(ledger_records, hash_packet_map)
    revalidation_results = [
        {
            "outbox_entry_id": item["outbox_entry_id"],
            "payload_id": item["payload_id"],
            "revalidation_status": item["revalidation_status"],
            "blockers": item["revalidation_blockers"],
            "eligible_for_dispatch": False,
        }
        for item in outbox_entries
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "source_hash_approval_gate_packet_path": source_path,
        "source_hash_approval_gate_schema_version": hash_approval_packet.get("schema_version"),
        "live_write_allowed_now": False,
        "discord_bot_required": False,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "ledger_records": ledger_records,
        "outbox_entries": outbox_entries,
        "revalidation_results": revalidation_results,
        "idempotency_key_summary": {
            "count": len(outbox_entries),
            "keys": [item["idempotency_key"] for item in outbox_entries],
            "source_fields": ["payload_hash", "destination_binding_id", "credential_handle_id", "payload_type", "target_name", "outbox_schema_version"],
        },
        "duplicate_suppression_summary": {
            "count": len(outbox_entries),
            "keys": [item["duplicate_suppression_key"] for item in outbox_entries],
            "source_fields": ["payload_hash", "target_name", "destination_binding_id"],
        },
        "redacted_audit_event_previews": [item["audit_event_preview"] for item in outbox_entries],
        "summary": {
            "ledger_record_count": len(ledger_records),
            "outbox_entry_count": len(outbox_entries),
            "all_ledger_records_dispatchable": False,
            "all_outbox_entries_eligible_for_dispatch": False,
            "all_send_gate_decisions_refuse": all(item["send_gate_decision"] == REFUSE for item in outbox_entries),
            "all_revalidation_non_dispatchable": all(item["eligible_for_dispatch"] is False for item in revalidation_results),
        },
        "secret_output_policy": {
            "webhook_url_output": False,
            "credential_material_output": False,
            "credential_metadata_output": False,
            "cookie_session_local_storage_output": False,
            "browser_profile_storage_output": False,
            "raw_env_line_output": False,
        },
    }


def write_approval_ledger_outbox_packet(hash_approval_packet_path: str | Path, output_path: str | Path) -> dict:
    source = Path(hash_approval_packet_path)
    hash_approval_packet = json.loads(source.read_text(encoding="utf-8"))
    packet = build_approval_ledger_outbox_packet(hash_approval_packet, source.as_posix())
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Discord approval ledger and non-live outbox packet")
    parser.add_argument("--hash-approval-packet", required=True, help="Input hash approval gate packet path")
    parser.add_argument("--output", required=True, help="Output approval ledger outbox packet path")
    args = parser.parse_args(argv)
    packet = write_approval_ledger_outbox_packet(args.hash_approval_packet, args.output)
    print(json.dumps({
        "task_label": TASK_LABEL,
        "result": "PASS",
        "output": args.output,
        "ledger_record_count": packet["summary"]["ledger_record_count"],
        "outbox_entry_count": packet["summary"]["outbox_entry_count"],
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "live_write_allowed_now": False,
        "discord_bot_required": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
