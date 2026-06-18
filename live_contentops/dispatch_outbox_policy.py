"""Dispatch outbox policy (LOCAL, DRY-RUN CANDIDATE ONLY)."""

import hashlib
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XQ_XR_XS_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V0"
MODEL = "DISPATCH_OUTBOX_POLICY_0174XQ_XR_XS"
MODEL_VERSION = "0174XQ_XR_XS_DISPATCH_OUTBOX_POLICY_V1"
SOURCE_BASELINE_COMMIT = "2f80831bce881f26e6bff3109a4731aaaad3e167"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XQ_XR_XS")
POLICY_PACKET = "dispatch_outbox_policy_packet.json"
POLICY_DOC = "dispatch_outbox_policy.md"
SUPPORTED_DISPATCH_PREP_PLATFORMS = ["substack", "telegram", "x"]
SYMBOLIC_FIXTURE_ONLY = "symbolic_fixture_only"
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
            raise ValueError("forbidden_outbox_material")
    return True


def idempotency_material(entry):
    return {
        "platform": entry.get("platform"),
        "payload_hash": entry.get("payload_hash"),
        "destination_binding_id": entry.get("destination_binding_id"),
        "credential_handle_id": entry.get("credential_handle_id"),
        "approval_ledger_entry_id": entry.get("ledger_entry_id"),
    }


def compute_idempotency_key(entry):
    material = json.dumps(idempotency_material(entry), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def idempotency_determinism_proof(entry):
    base = compute_idempotency_key(entry)
    proof = {"same_input_same_key": compute_idempotency_key(dict(entry)) == base}
    for field in ["platform", "payload_hash", "destination_binding_id", "credential_handle_id", "ledger_entry_id"]:
        changed = dict(entry)
        changed[field] = f"changed_{field}"
        proof[f"{field}_change_changes_key"] = compute_idempotency_key(changed) != base
    return proof


def classify_entry(entry, seen_idempotency_keys=None):
    seen_idempotency_keys = seen_idempotency_keys or set()
    reasons = []
    status = "candidate"
    if entry.get("eligible_for_outbox_candidate") is not True:
        reasons.append("ledger_entry_not_eligible_for_outbox_candidate")
    if not entry.get("payload_hash"):
        reasons.append("missing_payload_hash")
    if entry.get("destination_binding_id") != SYMBOLIC_FIXTURE_ONLY:
        reasons.append("destination_binding_not_symbolic_fixture_only")
    if entry.get("credential_handle_id") != SYMBOLIC_FIXTURE_ONLY:
        reasons.append("credential_handle_not_symbolic_fixture_only")
    if entry.get("platform") not in SUPPORTED_DISPATCH_PREP_PLATFORMS:
        reasons.append("unsupported_dispatch_prep_platform")
    if reasons:
        return "blocked", reasons, "not_evaluated_due_to_block"
    key = compute_idempotency_key(entry)
    if key in seen_idempotency_keys:
        return "duplicate_suppressed", ["duplicate_idempotency_key"], "duplicate_suppressed"
    return status, [], "unique"


def required_outbox_candidate_fields():
    return [
        "outbox_candidate_id", "source_approval_ledger_entry_id", "source_challenge_candidate_id",
        "source_payload_id", "source_brief_id", "source_intent_id", "platform", "payload_class",
        "payload_hash", "payload_hash_short", "destination_binding_id", "credential_handle_id",
        "idempotency_key", "idempotency_key_algorithm", "dispatch_mode", "request_budget",
        "auto_retry_allowed", "kill_switch_required", "credential_hydration_allowed",
        "platform_api_call_allowed", "live_dispatch_allowed", "status", "blocked_reasons",
        "duplicate_suppression_status", "eligible_for_gate_matrix", "valid_for_dispatch",
        "can_dispatch", "provider_api_called", "platform_api_called", "live_post_performed",
        "audit_hash", "evidence_refs",
    ]


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "supported_dispatch_prep_platforms": SUPPORTED_DISPATCH_PREP_PLATFORMS,
        "required_outbox_candidate_fields": required_outbox_candidate_fields(),
        "idempotency_key_algorithm": "sha256",
        "idempotency_key_binds": ["platform", "payload_hash", "destination_binding_id", "credential_handle_id", "approval_ledger_entry_id"],
        "dispatch_mode": "dry_run_candidate_only",
        "request_budget_required": 1,
        "auto_retry_allowed": False,
        "kill_switch_required": True,
        "credential_hydration_allowed": False,
        "platform_api_call_allowed": False,
        "live_dispatch_allowed": False,
        "valid_for_dispatch_always_false": True,
        "can_dispatch_always_false": True,
        "telegram_dispatch_status": "proven_frozen_no_send",
        "substack_dispatch_status": "manual_export_no_api",
        "x_dispatch_status": "dry_run_no_api",
        "status": "pass",
    }
    packet["dispatch_outbox_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(packet):
    lines = ["# Dispatch Outbox Policy", "", "> [!IMPORTANT]", "> Local dry-run outbox candidate policy only. No dispatch, credential hydration, platform/provider calls, network, or live-ready state.", ""]
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
    print("DISPATCH_OUTBOX_POLICY_CHECKSUM", result["dispatch_outbox_policy_checksum"])
