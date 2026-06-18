"""Dispatch gate policy (LOCAL, NO LIVE-READY STATE)."""

import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XT_XU_XV_DISPATCH_GATE_MATRIX_CONTRACT_V0"
MODEL = "DISPATCH_GATE_POLICY_0174XT_XU_XV"
MODEL_VERSION = "0174XT_XU_XV_DISPATCH_GATE_POLICY_V1"
SOURCE_BASELINE_COMMIT = "bb68a171b5e1aa40c4d9ea9ecefd8f9d40de6aef"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XT_XU_XV")
POLICY_PACKET = "dispatch_gate_policy_packet.json"
POLICY_DOC = "dispatch_gate_policy.md"
SYMBOLIC_FIXTURE_ONLY = "symbolic_fixture_only"
FUTURE_GATES = ["kill_switch_activation", "redacted_audit_packet", "manual_fallback_proof", "operator_supervision_window", "live_dispatch_separate_approval"]
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
    }


def validate_no_forbidden_material(value):
    text = json.dumps(value, sort_keys=True).lower()
    for token in FORBIDDEN_MATERIAL:
        if token in text:
            raise ValueError("forbidden_gate_material")
    return True


def gate(status, reason=None, proof=None):
    result = {"status": status}
    if reason is not None:
        result["reason"] = reason
    if proof is not None:
        result["proof"] = proof
    return result


def platform_capability_status(platform):
    if platform == "telegram":
        return "proven_frozen_no_send"
    if platform == "x":
        return "dry_run_no_api"
    if platform == "substack":
        return "manual_export_no_api"
    return "unsupported_platform"


def payload_hash_gate(candidate):
    payload_hash = candidate.get("payload_hash")
    short = candidate.get("payload_hash_short")
    if payload_hash and short and str(payload_hash).startswith(str(short)):
        return gate("pass", proof="payload_hash_prefix_matches_hash_short")
    return gate("fail", "payload_hash_missing_or_hash_short_mismatch")


def evaluate_gates(candidate):
    results = {
        "approval_ledger_gate": gate("pass" if candidate.get("status") == "candidate" and candidate.get("eligible_for_gate_matrix") is True else "fail", "candidate_not_active_or_not_gate_eligible" if candidate.get("status") != "candidate" or candidate.get("eligible_for_gate_matrix") is not True else None),
        "payload_hash_gate": payload_hash_gate(candidate),
        "destination_binding_gate": gate("pass" if candidate.get("destination_binding_id") == SYMBOLIC_FIXTURE_ONLY else "fail", "destination_binding_not_symbolic_fixture_only" if candidate.get("destination_binding_id") != SYMBOLIC_FIXTURE_ONLY else None),
        "credential_handle_gate": gate("pass" if candidate.get("credential_handle_id") == SYMBOLIC_FIXTURE_ONLY else "fail", "credential_handle_not_symbolic_fixture_only" if candidate.get("credential_handle_id") != SYMBOLIC_FIXTURE_ONLY else None),
        "kill_switch_gate": gate("future_required_not_active", proof="kill_switch_required_present_not_activated"),
        "idempotency_gate": gate("duplicate_suppressed" if candidate.get("status") == "duplicate_suppressed" or candidate.get("duplicate_suppression_status") == "duplicate_suppressed" else "pass", proof=candidate.get("duplicate_suppression_status")),
        "request_budget_gate": gate("pass" if candidate.get("request_budget") == 1 else "fail", "request_budget_not_one" if candidate.get("request_budget") != 1 else None),
        "no_auto_retry_gate": gate("pass" if candidate.get("auto_retry_allowed") is False else "fail", "auto_retry_allowed_true" if candidate.get("auto_retry_allowed") is not False else None),
        "no_live_ready_gate": gate("pass", proof="valid_for_live_dispatch_false_and_can_dispatch_false_forced"),
        "platform_capability_gate": gate(platform_capability_status(candidate.get("platform")), proof="not_live"),
        "redacted_audit_gate_future": gate("future_required_not_active"),
        "manual_fallback_gate_future": gate("future_required_not_active"),
    }
    return results


def overall_status(candidate, gate_results):
    if candidate.get("status") == "duplicate_suppressed":
        return "duplicate_suppressed"
    if candidate.get("status") == "blocked":
        return "blocked"
    hard_gates = ["approval_ledger_gate", "payload_hash_gate", "destination_binding_gate", "credential_handle_gate", "request_budget_gate", "no_auto_retry_gate", "no_live_ready_gate"]
    if all(gate_results[name]["status"] == "pass" for name in hard_gates) and gate_results["idempotency_gate"]["status"] == "pass" and gate_results["platform_capability_gate"]["status"] in ["proven_frozen_no_send", "dry_run_no_api", "manual_export_no_api"]:
        return "local_dry_run_gate_passed_not_live_ready"
    return "blocked"


def required_future_gates():
    return list(FUTURE_GATES)


def required_matrix_fields():
    return ["gate_matrix_id", "source_outbox_candidate_id", "source_approval_ledger_entry_id", "platform", "payload_class", "payload_hash", "payload_hash_short", "destination_binding_id", "credential_handle_id", "idempotency_key", "gate_results", "overall_gate_status", "eligible_for_dispatch_audit_dry_run", "valid_for_live_dispatch", "can_dispatch", "live_ready_state_created", "blocked_reasons", "required_future_gates", "audit_hash", "evidence_refs"]


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "required_matrix_fields": required_matrix_fields(),
        "required_future_gates": required_future_gates(),
        "valid_for_live_dispatch_always_false": True,
        "can_dispatch_always_false": True,
        "live_ready_state_created_always_false": True,
        "telegram_platform_capability_status": "proven_frozen_no_send",
        "x_platform_capability_status": "dry_run_no_api",
        "substack_platform_capability_status": "manual_export_no_api",
        "status": "pass",
    }
    packet["dispatch_gate_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(packet):
    lines = ["# Dispatch Gate Policy", "", "> [!IMPORTANT]", "> Local deterministic gate evaluation only. No dispatch, credential hydration, platform/provider calls, network, or live-ready state.", ""]
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
    print("DISPATCH_GATE_POLICY_CHECKSUM", result["dispatch_gate_policy_checksum"])
