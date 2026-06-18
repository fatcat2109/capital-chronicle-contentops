"""Dispatch audit dry-run contract (LOCAL, REDACTED, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import dispatch_audit_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XW_XX_XY_DISPATCH_AUDIT_DRY_RUN_CONTRACT_V0"
MODEL = "DISPATCH_AUDIT_DRY_RUN_CONTRACT_0174XW_XX_XY"
MODEL_VERSION = "0174XW_XX_XY_DISPATCH_AUDIT_DRY_RUN_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "f38b489cd6ec54012ddff7ed7010625c6609d2d6"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XW_XX_XY")
GATE_DIR = os.path.join("docs", "automation", "0174XT_XU_XV")
OUTBOX_DIR = os.path.join("docs", "automation", "0174XQ_XR_XS")
LEDGER_DIR = os.path.join("docs", "automation", "0174XN_XO_XP")
WY_DIR = os.path.join("docs", "automation", "0174WY_WZ_XA")
OUTPUTS = "dispatch_audit_dry_run_fixture_outputs.json"
CONTRACT_PACKET = "dispatch_audit_dry_run_contract_packet.json"
CONTRACT_DOC = "dispatch_audit_dry_run_contract.md"
NEXT_PACKET = "next_supervised_dispatch_readiness_summary_packet.json"
NEXT_DOC = "next_supervised_dispatch_readiness_summary.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174XZ_YA_YB_SUPERVISED_DISPATCH_READINESS_SUMMARY_V0"


def _read_json(repo_root, rel_path):
    return json.loads((pathlib.Path(repo_root) / rel_path).read_text(encoding="utf-8"))


def load_inputs(repo_root="."):
    return {
        "gate_contract": _read_json(repo_root, os.path.join(GATE_DIR, "dispatch_gate_matrix_contract_packet.json")),
        "gate_policy": _read_json(repo_root, os.path.join(GATE_DIR, "dispatch_gate_policy_packet.json")),
        "gate_outputs": _read_json(repo_root, os.path.join(GATE_DIR, "dispatch_gate_matrix_fixture_outputs.json")),
        "next_audit": _read_json(repo_root, os.path.join(GATE_DIR, "next_dispatch_audit_dry_run_contract_packet.json")),
        "outbox_contract": _read_json(repo_root, os.path.join(OUTBOX_DIR, "dispatch_outbox_candidate_contract_packet.json")),
        "ledger_contract": _read_json(repo_root, os.path.join(LEDGER_DIR, "approval_ledger_contract_packet.json")),
        "telegram_registry": _read_json(repo_root, os.path.join(WY_DIR, "telegram_supervised_dispatch_capability_registry_packet.json")),
        "platform_registry": _read_json(repo_root, os.path.join(WY_DIR, "platform_universe_registry_v2_packet.json")),
    }


def audit_hash_material(matrix, event_without_hash, policy_packet):
    return {
        "source_gate_matrix_id": matrix.get("gate_matrix_id"),
        "source_outbox_candidate_id": matrix.get("source_outbox_candidate_id"),
        "source_approval_ledger_entry_id": matrix.get("source_approval_ledger_entry_id"),
        "platform": matrix.get("platform"),
        "payload_hash": matrix.get("payload_hash"),
        "payload_hash_short": matrix.get("payload_hash_short"),
        "idempotency_key": matrix.get("idempotency_key"),
        "gate_matrix_status": matrix.get("overall_gate_status"),
        "audit_status": event_without_hash.get("audit_status"),
        "provider_response_class": event_without_hash.get("provider_response_class"),
        "request_budget_used": event_without_hash.get("request_budget_used"),
        "redaction_status": event_without_hash.get("redaction_status"),
        "manual_fallback_required": event_without_hash.get("manual_fallback_required"),
        "policy_checksum": policy_packet["dispatch_audit_policy_checksum"],
    }


def compute_audit_hash(matrix, event_without_hash, policy_packet):
    return adapter.compute_checksum(audit_hash_material(matrix, event_without_hash, policy_packet))


def build_event(matrix, policy_packet):
    event = {
        "audit_event_id": f"audit_{matrix.get('gate_matrix_id')}",
        "source_gate_matrix_id": matrix.get("gate_matrix_id"),
        "source_outbox_candidate_id": matrix.get("source_outbox_candidate_id"),
        "source_approval_ledger_entry_id": matrix.get("source_approval_ledger_entry_id"),
        "platform": matrix.get("platform"),
        "payload_class": matrix.get("payload_class"),
        "payload_hash": matrix.get("payload_hash"),
        "payload_hash_short": matrix.get("payload_hash_short"),
        "destination_binding_id": matrix.get("destination_binding_id"),
        "credential_handle_id": matrix.get("credential_handle_id"),
        "idempotency_key": matrix.get("idempotency_key"),
        **policy.fixed_event_values(),
        "gate_matrix_status": matrix.get("overall_gate_status"),
        "audit_status": policy.audit_status_for(matrix.get("overall_gate_status")),
        "blocked_reasons": list(matrix.get("blocked_reasons", [])),
        "required_future_gates": list(matrix.get("required_future_gates", [])),
        "evidence_refs": list(matrix.get("evidence_refs", [])) + [matrix.get("audit_hash")],
        **policy.safety_flags(),
    }
    event["audit_hash"] = compute_audit_hash(matrix, event, policy_packet)
    policy.validate_no_forbidden_material(event)
    return event


def build_events(gate_outputs, policy_packet):
    return [build_event(matrix, policy_packet) for matrix in gate_outputs]


def counts(events):
    return {
        "audit_event_count": len(events),
        "local_audit_dry_run_recorded_count": sum(1 for e in events if e["audit_status"] == "local_audit_dry_run_recorded"),
        "blocked_audit_recorded_count": sum(1 for e in events if e["audit_status"] == "blocked_audit_recorded"),
        "duplicate_suppressed_audit_recorded_count": sum(1 for e in events if e["audit_status"] == "duplicate_suppressed_audit_recorded"),
    }


def platform_statuses(inputs):
    return {
        "telegram": "proven_frozen_no_send",
        "x": "dry_run_no_api",
        "substack": "manual_export_no_api",
        "telegram_registry_status": inputs["telegram_registry"]["telegram_channel_dispatch_status"],
        "platform_registry_substack": inputs["platform_registry"]["platform_roles"]["substack"]["initial_support"],
        "platform_registry_x": inputs["platform_registry"]["platform_roles"]["x"]["execution_status"],
    }


def build_contract_packet(inputs, events, policy_packet):
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "dispatch_gate_matrix_contract_checksum": inputs["gate_contract"]["dispatch_gate_matrix_contract_checksum"],
        "dispatch_gate_policy_checksum": inputs["gate_policy"]["dispatch_gate_policy_checksum"],
        "dispatch_gate_matrix_fixture_outputs_checksum": inputs["gate_contract"]["dispatch_gate_matrix_fixture_outputs_checksum"],
        "next_dispatch_audit_dry_run_contract_checksum": inputs["next_audit"]["next_dispatch_audit_dry_run_contract_checksum"],
        "dispatch_outbox_candidate_contract_checksum": inputs["outbox_contract"]["dispatch_outbox_candidate_contract_checksum"],
        "approval_ledger_contract_checksum": inputs["ledger_contract"]["approval_ledger_contract_checksum"],
        "telegram_dispatch_registry_checksum": inputs["telegram_registry"]["registry_checksum"],
        "platform_universe_registry_checksum": inputs["platform_registry"]["platform_universe_registry_checksum"],
        **counts(events),
        "platform_statuses": platform_statuses(inputs),
        "required_future_gates": inputs["gate_contract"]["required_future_gates"],
        "provider_response_class_values": sorted(set(e["provider_response_class"] for e in events)),
        "request_budget_used_values": sorted(set(e["request_budget_used"] for e in events)),
        "request_budget_allowed_values": sorted(set(e["request_budget_allowed"] for e in events)),
        "all_provider_response_redacted_empty": all(e["provider_response_redacted"] == {} for e in events),
        "all_raw_request_persisted_false": all(e["raw_request_persisted"] is False for e in events),
        "all_raw_response_persisted_false": all(e["raw_response_persisted"] is False for e in events),
        "all_token_logged_false": all(e["token_logged"] is False for e in events),
        "all_retry_count_zero": all(e["retry_count"] == 0 for e in events),
        "all_final_url_verified_null": all(e["final_url_verified"] is None for e in events),
        "all_redaction_status_pass": all(e["redaction_status"] == "pass" for e in events),
        "all_manual_fallback_required_true": all(e["manual_fallback_required"] is True for e in events),
        "all_valid_for_live_dispatch_false": all(e["valid_for_live_dispatch"] is False for e in events),
        "all_can_dispatch_false": all(e["can_dispatch"] is False for e in events),
        "all_platform_dispatch_performed_false": all(e["platform_dispatch_performed"] is False for e in events),
        "all_credential_hydration_performed_false": all(e["credential_hydration_performed"] is False for e in events),
        "all_live_ready_state_false": all(e["live_ready_state_created"] is False for e in events),
        "status": "pass",
    }
    packet["dispatch_audit_policy_checksum"] = policy_packet["dispatch_audit_policy_checksum"]
    packet["dispatch_audit_dry_run_fixture_outputs_checksum"] = adapter.compute_checksum(events)
    packet["dispatch_audit_dry_run_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(contract_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_SUPERVISED_DISPATCH_READINESS_SUMMARY_0174XW_XX_XY",
        "model_version": "0174XW_XX_XY_NEXT_SUPERVISED_DISPATCH_READINESS_SUMMARY_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "supervised_dispatch_readiness_summary_local_only",
        "allowed_inputs": ["dispatch_audit_dry_run_event", "redaction_proof", "manual_fallback_requirement", "required_future_gates"],
        "forbidden_outputs": ["live_dispatch", "credential_hydration", "platform_api_call", "live_ready_state", "raw_request_response_persistence", "token_logging"],
        "dispatch_audit_dry_run_contract_checksum": contract_packet["dispatch_audit_dry_run_contract_checksum"],
        "dispatch_audit_policy_checksum": policy_packet["dispatch_audit_policy_checksum"],
        "dispatch_audit_dry_run_fixture_outputs_checksum": contract_packet["dispatch_audit_dry_run_fixture_outputs_checksum"],
        "readiness_summary_must_remain_blocked_for_live_dispatch": True,
        "required_future_gates": contract_packet["required_future_gates"],
    }
    packet["next_supervised_dispatch_readiness_summary_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Local redacted audit dry-run only. No dispatch, no platform/provider call, no credential hydration, no raw request/response persistence, no token logging, and no live-ready state.", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    policy_packet = policy.write_artifacts(repo_root)
    inputs = load_inputs(repo_root)
    events = build_events(inputs["gate_outputs"], policy_packet)
    contract_packet = build_contract_packet(inputs, events, policy_packet)
    next_packet = build_next_packet(contract_packet, policy_packet)
    (out / OUTPUTS).write_text(adapter.serialize(events), encoding="utf-8", newline="\n")
    (out / CONTRACT_PACKET).write_text(adapter.serialize(contract_packet), encoding="utf-8", newline="\n")
    (out / CONTRACT_DOC).write_text(render_doc("Dispatch Audit Dry-Run Contract", contract_packet), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Supervised Dispatch Readiness Summary", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"events": events, "contract_packet": contract_packet, "policy_packet": policy_packet, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("DISPATCH_AUDIT_DRY_RUN_CONTRACT_CHECKSUM", result["contract_packet"]["dispatch_audit_dry_run_contract_checksum"])
    print("DISPATCH_AUDIT_POLICY_CHECKSUM", result["policy_packet"]["dispatch_audit_policy_checksum"])
    print("DISPATCH_AUDIT_DRY_RUN_FIXTURE_OUTPUTS_CHECKSUM", result["contract_packet"]["dispatch_audit_dry_run_fixture_outputs_checksum"])
    print("NEXT_SUPERVISED_DISPATCH_READINESS_SUMMARY_CHECKSUM", result["next_packet"]["next_supervised_dispatch_readiness_summary_checksum"])
