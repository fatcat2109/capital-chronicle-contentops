"""Dispatch audit dry-run policy (LOCAL, REDACTED, NOT CALLED)."""

import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XW_XX_XY_DISPATCH_AUDIT_DRY_RUN_CONTRACT_V0"
MODEL = "DISPATCH_AUDIT_POLICY_0174XW_XX_XY"
MODEL_VERSION = "0174XW_XX_XY_DISPATCH_AUDIT_POLICY_V1"
SOURCE_BASELINE_COMMIT = "f38b489cd6ec54012ddff7ed7010625c6609d2d6"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XW_XX_XY")
POLICY_PACKET = "dispatch_audit_policy_packet.json"
POLICY_DOC = "dispatch_audit_policy.md"
FORBIDDEN_MATERIAL = ["raw_credential", "raw_token", "raw_chat_id", "raw_destination", "env_var", "secret_path", "live_url", "chat_id", "token", "secret"]


def safety_flags():
    return {
        "is_local_only": True,
        "network_performed": False,
        "telegram_api_called": False,
        "x_api_called": False,
        "substack_api_called": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "llm_provider_api_called": False,
        "env_read": False,
        "dotenv_read": False,
        "credential_read": False,
        "credential_hydration_performed": False,
        "scheduler_enabled": False,
        "live_post_performed": False,
        "autonomous_replies_or_dms": False,
        "scraping_performed": False,
        "public_ready_content_generated": False,
        "platform_dispatch_performed": False,
        "live_ready_state_created": False,
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "token_logged": False,
    }


def fixed_event_values():
    return {
        "request_budget_used": 0,
        "request_budget_allowed": 1,
        "auto_retry_allowed": False,
        "dispatch_mode": "audit_dry_run_only",
        "provider_response_class": "not_called",
        "provider_response_redacted": {},
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "token_logged": False,
        "retry_count": 0,
        "final_url_verified": None,
        "redaction_status": "pass",
        "manual_fallback_required": True,
        "valid_for_live_dispatch": False,
        "can_dispatch": False,
        "platform_dispatch_performed": False,
        "live_post_performed": False,
        "credential_hydration_performed": False,
        "live_ready_state_created": False,
    }


def audit_status_for(gate_matrix_status):
    if gate_matrix_status == "local_dry_run_gate_passed_not_live_ready":
        return "local_audit_dry_run_recorded"
    if gate_matrix_status == "duplicate_suppressed":
        return "duplicate_suppressed_audit_recorded"
    return "blocked_audit_recorded"


def _scalar_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _scalar_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _scalar_strings(item)
    elif isinstance(value, str):
        yield value.lower()


def validate_no_forbidden_material(value):
    text = " ".join(_scalar_strings(value))
    for item in FORBIDDEN_MATERIAL:
        if item in text:
            raise ValueError("forbidden_audit_material")
    return True


def required_audit_event_fields():
    return ["audit_event_id", "source_gate_matrix_id", "source_outbox_candidate_id", "source_approval_ledger_entry_id", "platform", "payload_class", "payload_hash", "payload_hash_short", "destination_binding_id", "credential_handle_id", "idempotency_key", "request_budget_used", "request_budget_allowed", "auto_retry_allowed", "dispatch_mode", "gate_matrix_status", "provider_response_class", "provider_response_redacted", "raw_request_persisted", "raw_response_persisted", "token_logged", "retry_count", "final_url_verified", "redaction_status", "manual_fallback_required", "valid_for_live_dispatch", "can_dispatch", "platform_dispatch_performed", "live_post_performed", "credential_hydration_performed", "live_ready_state_created", "blocked_reasons", "required_future_gates", "audit_hash", "evidence_refs"]


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "required_audit_event_fields": required_audit_event_fields(),
        "fixed_event_values": fixed_event_values(),
        "audit_status_map": {
            "local_dry_run_gate_passed_not_live_ready": "local_audit_dry_run_recorded",
            "blocked": "blocked_audit_recorded",
            "duplicate_suppressed": "duplicate_suppressed_audit_recorded",
        },
        "telegram_dispatch_status": "proven_frozen_no_send",
        "x_dispatch_status": "dry_run_no_api",
        "substack_dispatch_status": "manual_export_no_api",
        "provider_response_class_always": "not_called",
        "request_budget_used_always": 0,
        "manual_fallback_required_always": True,
        "redaction_status_always": "pass",
        "status": "pass",
    }
    packet["dispatch_audit_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(packet):
    lines = ["# Dispatch Audit Policy", "", "> [!IMPORTANT]", "> Local redacted audit dry-run only. Provider not called, raw request/response not persisted, token not logged, and no live-ready state.", ""]
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
    packet = build_policy_packet()
    (out / POLICY_PACKET).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    (out / POLICY_DOC).write_text(render_doc(packet), encoding="utf-8", newline="\n")
    return dict(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("DISPATCH_AUDIT_POLICY_CHECKSUM", result["dispatch_audit_policy_checksum"])
