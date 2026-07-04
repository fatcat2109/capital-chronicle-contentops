"""Discord operator review and non-dispatchable dispatch candidate contract.

Local-only review layer. It builds human review records and future live pilot
candidate packets from non-live Discord outbox entries without loading endpoint
material, secrets, env files, or sending network requests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_OPERATOR_REVIEW_AND_DISPATCH_CANDIDATE_PACKET_V0"
SCHEMA_VERSION = "discord_operator_review_candidate_contract.v1"
REVIEW_SCHEMA_VERSION = "discord_operator_review_record.v1"
CANDIDATE_SCHEMA_VERSION = "discord_dispatch_candidate_non_live.v1"
AUDIT_SCHEMA_VERSION = "discord_dispatch_candidate_redacted_audit_preview.v1"
OPERATOR_ID = "Jim"
REFUSE = "REFUSE"
CANDIDATE_READY = "future_live_pilot_candidate_ready"
BLOCKED_REVIEW = "blocked_review_gate_failed"
BLOCKED_SECRET = "blocked_secret_or_endpoint_material_present"

FORBIDDEN_SUBSTRINGS = (
    "discord.com/api/webhooks",
    "discordapp.com/api/webhooks",
    "token_value",
    "token_length",
    "token_prefix",
    "token_suffix",
    "token_digest",
    "token_hash",
    "authorization",
    "cookie",
    "localstorage",
    "sessionstorage",
)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _string_values(obj: Any) -> list[str]:
    if isinstance(obj, dict):
        values: list[str] = []
        for value in obj.values():
            values.extend(_string_values(value))
        return values
    if isinstance(obj, (list, tuple)):
        values: list[str] = []
        for value in obj:
            values.extend(_string_values(value))
        return values
    if isinstance(obj, str):
        return [obj]
    return []


def contains_forbidden_material(obj: Any) -> bool:
    text = "\n".join(_string_values(obj)).lower()
    return any(item in text for item in FORBIDDEN_SUBSTRINGS)


def review_gate_blockers(outbox_entry: dict) -> list[str]:
    blockers: list[str] = []
    if outbox_entry.get("revalidation_status") != "pass_non_dispatchable":
        blockers.append("blocked_revalidation_not_pass_non_dispatchable")
    if outbox_entry.get("send_gate_decision") != REFUSE:
        blockers.append("blocked_send_gate_not_refuse")
    if outbox_entry.get("eligible_for_dispatch") is not False:
        blockers.append("blocked_eligible_for_dispatch_not_false")
    if outbox_entry.get("live_write_allowed_now") is not False:
        blockers.append("blocked_live_write_allowed_now_not_false")
    if contains_forbidden_material(outbox_entry):
        blockers.append(BLOCKED_SECRET)
    return blockers


def candidate_allowed(outbox_entry: dict) -> bool:
    return not review_gate_blockers(outbox_entry)


def display_summary_for(outbox_entry: dict, allowed: bool) -> str:
    status = CANDIDATE_READY if allowed else BLOCKED_REVIEW
    return (
        f"{outbox_entry.get('payload_type')} -> {outbox_entry.get('target_name')} | "
        f"hash={outbox_entry.get('payload_hash')} | "
        f"binding={outbox_entry.get('destination_binding_id')} | "
        f"credential={outbox_entry.get('credential_handle_id')} | "
        f"candidate_status={status} | current_task_dispatchable=false"
    )


def build_review_record(outbox_entry: dict) -> dict:
    blockers = review_gate_blockers(outbox_entry)
    allowed = not blockers
    review_status = "ready_for_future_live_pilot_review" if allowed else "blocked_operator_review_gate_failed"
    if BLOCKED_SECRET in blockers:
        review_status = BLOCKED_SECRET
    return {
        "review_record_id": f"discord_review_{outbox_entry.get('outbox_entry_id')}",
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "source_outbox_entry_id": outbox_entry.get("outbox_entry_id"),
        "source_ledger_record_id": outbox_entry.get("source_ledger_record_id"),
        "source_approval_packet_id": outbox_entry.get("source_approval_packet_id"),
        "payload_id": outbox_entry.get("payload_id"),
        "payload_hash": outbox_entry.get("payload_hash"),
        "payload_type": outbox_entry.get("payload_type"),
        "target_name": outbox_entry.get("target_name"),
        "destination_binding_id": outbox_entry.get("destination_binding_id"),
        "credential_handle_id": outbox_entry.get("credential_handle_id"),
        "adapter_type": outbox_entry.get("adapter_type"),
        "outbox_status": outbox_entry.get("outbox_status"),
        "revalidation_status": outbox_entry.get("revalidation_status"),
        "send_gate_decision": outbox_entry.get("send_gate_decision"),
        "review_status": review_status,
        "operator_id": OPERATOR_ID,
        "operator_action_required": True,
        "live_write_allowed_now": False,
        "dispatch_candidate_allowed": allowed,
        "dispatch_candidate_dispatchable": False,
        "blockers": blockers,
        "warnings": ["candidate_is_for_future_live_pilot_review_only", "no_live_dispatch_authorized_in_this_task"],
        "display_summary": display_summary_for(outbox_entry, allowed),
        "secret_output_policy": {
            "webhook_url_output": False,
            "token_output": False,
            "token_metadata_output": False,
            "endpoint_url_output": False,
            "request_headers_output": False,
            "raw_response_body_output": False,
            "cookie_session_local_storage_output": False,
            "browser_profile_storage_output": False,
        },
    }


def build_redacted_audit_preview(review_record: dict, outbox_entry: dict, candidate_id: str, candidate_status: str) -> dict:
    return {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "event_type": "discord_dispatch_candidate_created_non_live",
        "dispatch_candidate_id": candidate_id,
        "review_record_id": review_record.get("review_record_id"),
        "source_outbox_entry_id": outbox_entry.get("outbox_entry_id"),
        "payload_id": outbox_entry.get("payload_id"),
        "payload_hash": outbox_entry.get("payload_hash"),
        "destination_binding_id": outbox_entry.get("destination_binding_id"),
        "credential_handle_id": outbox_entry.get("credential_handle_id"),
        "candidate_status": candidate_status,
        "send_gate_decision": REFUSE,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "response_class": "not_attempted",
        "public_url": None,
        "webhook_message_id": None,
        "secret_output_policy": review_record.get("secret_output_policy"),
    }


def build_dispatch_candidate(review_record: dict, outbox_entry: dict) -> dict:
    secret_blocked = contains_forbidden_material(outbox_entry) or contains_forbidden_material(review_record)
    if secret_blocked:
        candidate_status = BLOCKED_SECRET
    elif review_record.get("dispatch_candidate_allowed") is True:
        candidate_status = CANDIDATE_READY
    else:
        candidate_status = BLOCKED_REVIEW
    blockers = list(review_record.get("blockers") or [])
    if candidate_status != CANDIDATE_READY and not blockers:
        blockers.append(candidate_status)
    candidate_id = f"discord_candidate_{review_record.get('source_outbox_entry_id')}"
    return {
        "dispatch_candidate_id": candidate_id,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "review_record_id": review_record.get("review_record_id"),
        "source_outbox_entry_id": review_record.get("source_outbox_entry_id"),
        "payload_id": review_record.get("payload_id"),
        "payload_hash": review_record.get("payload_hash"),
        "payload_type": review_record.get("payload_type"),
        "target_name": review_record.get("target_name"),
        "destination_binding_id": review_record.get("destination_binding_id"),
        "credential_handle_id": review_record.get("credential_handle_id"),
        "adapter_type": review_record.get("adapter_type"),
        "candidate_status": candidate_status,
        "future_live_task_required": True,
        "explicit_operator_live_approval_required": True,
        "current_task_dispatchable": False,
        "valid_for_dispatch": False,
        "live_write_allowed_now": False,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "request_budget": None,
        "endpoint_family": None,
        "method": None,
        "host_allowlist": [],
        "path_family_allowlist": [],
        "idempotency_key": outbox_entry.get("idempotency_key"),
        "duplicate_suppression_key": outbox_entry.get("duplicate_suppression_key"),
        "blockers": blockers,
        "redacted_audit_preview": build_redacted_audit_preview(review_record, outbox_entry, candidate_id, candidate_status),
    }


def build_review_records(outbox_packet: dict) -> list[dict]:
    return [build_review_record(entry) for entry in outbox_packet.get("outbox_entries", [])]


def build_dispatch_candidates(review_records: list[dict], outbox_entries: list[dict]) -> list[dict]:
    by_id = {entry.get("outbox_entry_id"): entry for entry in outbox_entries}
    return [build_dispatch_candidate(record, by_id[record["source_outbox_entry_id"]]) for record in review_records]


def build_operator_review_candidate_packet(outbox_packet: dict, source_outbox_packet_path: str | None = None) -> dict:
    review_records = build_review_records(outbox_packet)
    candidates = build_dispatch_candidates(review_records, list(outbox_packet.get("outbox_entries", [])))
    packet = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "source_outbox_packet_path": source_outbox_packet_path,
        "source_hash_approval_gate_packet_path": outbox_packet.get("source_hash_approval_gate_packet_path"),
        "source_outbox_schema_version": outbox_packet.get("schema_version"),
        "live_write_allowed_now": False,
        "discord_bot_required": False,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "endpoint_url_loaded": False,
        "review_records": review_records,
        "dispatch_candidates": candidates,
        "summary": {
            "review_record_count": len(review_records),
            "dispatch_candidate_count": len(candidates),
            "candidate_ready_count": sum(1 for item in candidates if item["candidate_status"] == CANDIDATE_READY),
            "current_task_dispatchable_count": sum(1 for item in candidates if item["current_task_dispatchable"] is True),
            "valid_for_dispatch_count": sum(1 for item in candidates if item["valid_for_dispatch"] is True),
            "all_candidates_non_dispatchable": all(item["current_task_dispatchable"] is False for item in candidates),
            "all_future_live_task_required": all(item["future_live_task_required"] is True for item in candidates),
            "all_explicit_operator_live_approval_required": all(item["explicit_operator_live_approval_required"] is True for item in candidates),
        },
        "secret_output_policy": {
            "webhook_url_output": False,
            "token_output": False,
            "token_metadata_output": False,
            "endpoint_url_output": False,
            "request_headers_output": False,
            "raw_response_body_output": False,
            "cookie_session_local_storage_output": False,
            "browser_profile_storage_output": False,
        },
    }
    packet["summary"]["forbidden_material_detected"] = contains_forbidden_material(packet)
    return packet


def _review_value(packet: dict, candidate: dict, key: str) -> str:
    review_id = candidate.get("review_record_id")
    for record in packet.get("review_records", []):
        if record.get("review_record_id") == review_id:
            return str(record.get(key))
    return "None"


def render_operator_review_summary(packet: dict) -> str:
    lines = [
        "# Discord Operator Review Candidate Summary",
        "",
        f"- Task label: `{TASK_LABEL}`",
        f"- Source baseline: `{packet.get('source_outbox_packet_path')}`",
        f"- Source hash approval gate packet: `{packet.get('source_hash_approval_gate_packet_path')}`",
        "- current_task_dispatchable=false for every candidate",
        "- live_write_allowed_now=false",
        "- future live task required=true",
        "- explicit operator live approval required=true",
        "- endpoint_family=null, method=null, request_budget=null",
        "- host_allowlist=[] and path_family_allowlist=[]",
        "- no webhook URL/token values are included",
        "- no live send happened",
        "",
        "| payload_type | target_name | payload_hash | destination_binding_id | credential_handle_id | outbox_status | revalidation_status | send_gate_decision | candidate_status | current_task_dispatchable | live_write_allowed_now |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in packet.get("dispatch_candidates", []):
        lines.append(
            "| "
            + " | ".join([
                str(candidate.get("payload_type")),
                str(candidate.get("target_name")),
                str(candidate.get("payload_hash")),
                str(candidate.get("destination_binding_id")),
                str(candidate.get("credential_handle_id")),
                _review_value(packet, candidate, "outbox_status"),
                _review_value(packet, candidate, "revalidation_status"),
                "REFUSE",
                str(candidate.get("candidate_status")),
                "false",
                "false",
            ])
            + " |"
        )
    lines.extend([
        "",
        "## Future Live Handoff Skeleton",
        "",
        "Future live pilot must require exact dispatch_candidate_id, payload_hash, payload_id, target_name, destination_binding_id, credential_handle_id, rendered payload preview, endpoint family Discord webhook execute, official host allowlist, method POST, request budget 1 request and 0 retries unless separately approved, fixed timeout, kill switch check, idempotency key, post-request redacted audit, and stop on any mismatch or hidden destination/account/channel change.",
    ])
    summary = "\n".join(lines) + "\n"
    if contains_forbidden_material(summary):
        raise ValueError("summary contains forbidden endpoint or secret material")
    return summary


def write_operator_review_candidate_packet(outbox_packet_path: str | Path, output_path: str | Path, summary_output_path: str | Path) -> dict:
    source = Path(outbox_packet_path)
    outbox_packet = json.loads(source.read_text(encoding="utf-8"))
    packet = build_operator_review_candidate_packet(outbox_packet, source.as_posix())
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = render_operator_review_summary(packet)
    summary_path = Path(summary_output_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Discord operator review candidate packet")
    parser.add_argument("--outbox-packet", required=True, help="Input Discord approval ledger outbox packet path")
    parser.add_argument("--output", required=True, help="Output operator review candidate packet path")
    parser.add_argument("--summary-output", required=True, help="Output operator review summary markdown path")
    args = parser.parse_args(argv)
    packet = write_operator_review_candidate_packet(args.outbox_packet, args.output, args.summary_output)
    print(json.dumps({
        "task_label": TASK_LABEL,
        "result": "PASS",
        "output": args.output,
        "summary_output": args.summary_output,
        "review_record_count": packet["summary"]["review_record_count"],
        "dispatch_candidate_count": packet["summary"]["dispatch_candidate_count"],
        "candidate_ready_count": packet["summary"]["candidate_ready_count"],
        "current_task_dispatchable_count": 0,
        "network_call_attempted": False,
        "webhook_url_loaded": False,
        "endpoint_url_loaded": False,
        "live_write_allowed_now": False,
        "discord_bot_required": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
