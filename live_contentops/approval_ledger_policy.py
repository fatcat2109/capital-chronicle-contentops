"""Approval ledger policy (LOCAL, APPEND-ONLY FIXTURE CONTRACT)."""

import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XN_XO_XP_APPROVAL_LEDGER_CONTRACT_V0"
MODEL = "APPROVAL_LEDGER_POLICY_0174XN_XO_XP"
MODEL_VERSION = "0174XN_XO_XP_APPROVAL_LEDGER_POLICY_V1"
SOURCE_BASELINE_COMMIT = "a763e3aaa1cf079a472b9fe0f8748c36dae60a50"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XN_XO_XP")
POLICY_PACKET = "approval_ledger_policy_packet.json"
POLICY_DOC = "approval_ledger_policy.md"
FORBIDDEN_MATERIAL = ["raw_credential", "raw_token", "raw_chat_id", "raw_destination", "env_var", "secret_path", "live_url", "chat_id", "token", "secret"]
RESPONSE_CLASSES = ["explicit_approve", "explicit_reject", "explicit_edit_request", "explicit_hold", "ambiguous"]
EVENT_CLASSES = ["approval_candidate", "rejected_event", "edit_request_event", "hold_event", "blocked_event"]


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
        "scheduler_enabled": False,
        "live_post_performed": False,
        "autonomous_replies_or_dms": False,
        "scraping_performed": False,
        "public_ready_content_generated": False,
        "dispatch_outbox_mutated": False,
        "platform_dispatch_performed": False,
    }


def validate_no_forbidden_material(value):
    text = json.dumps(value, sort_keys=True).lower()
    for token in FORBIDDEN_MATERIAL:
        if token in text:
            raise ValueError("forbidden_ledger_material")
    return True


def blocked_proof_brief_ids(contract_packet):
    keys = [
        "blocked_direct_dispatch_proof",
        "blocked_approval_candidate_proof",
        "blocked_signal_advice_proof",
        "blocked_future_artifact_proof",
    ]
    out = set()
    for key in keys:
        out.update(contract_packet.get(key, []))
    return out


def classify_response(response, candidate, contract_packet):
    if candidate is None:
        return "blocked_event", ["unknown_challenge_candidate"]
    if response.get("replay_status") != "not_replay":
        return "blocked_event", ["replayed_response"]
    if candidate.get("expires_policy") != "future_required_not_active":
        return "blocked_event", ["expired_challenge_candidate"]
    if candidate.get("source_brief_id") in blocked_proof_brief_ids(contract_packet):
        return "blocked_event", ["blocked_source_brief_proof"]
    if response.get("response_payload_hash_short") != candidate.get("payload_hash_short"):
        return "blocked_event", ["payload_hash_short_mismatch"]
    response_class = response.get("response_class")
    if response_class == "explicit_approve":
        return "approval_candidate", []
    if response_class == "explicit_reject":
        return "rejected_event", ["operator_rejected"]
    if response_class == "explicit_edit_request":
        return "edit_request_event", ["operator_requested_revision"]
    if response_class == "explicit_hold":
        return "hold_event", ["operator_hold"]
    return "blocked_event", ["ambiguous_response_requires_clarification"]


def eligible_for_outbox_candidate(event_class, blocked_reasons):
    return event_class == "approval_candidate" and not blocked_reasons


def required_response_fields():
    return [
        "response_id", "source_challenge_candidate_id", "operator_id", "response_channel",
        "response_text_redacted", "response_class", "response_payload_hash_short",
        "received_at_order", "replay_status", "redaction_status", "trust_status",
    ]


def required_ledger_fields():
    return [
        "ledger_entry_id", "approved_at_order", "operator_id", "approval_channel",
        "source_challenge_candidate_id", "source_payload_id", "source_brief_id",
        "source_intent_id", "platform", "payload_class", "payload_hash",
        "payload_hash_short", "destination_binding_id", "credential_handle_id",
        "media_manifest_hash", "approval_text_redacted", "approval_method",
        "prior_payload_hash", "revoked", "expiration_policy", "valid_for_dispatch",
        "eligible_for_outbox_candidate", "blocked_reasons", "audit_hash",
        "human_review_required", "no_financial_advice", "no_signal_language",
        "public_postable", "can_dispatch", "can_create_outbox", "platform_api_called",
    ]


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "response_classes": RESPONSE_CLASSES,
        "event_classes": EVENT_CLASSES,
        "required_response_fields": required_response_fields(),
        "required_ledger_fields": required_ledger_fields(),
        "only_explicit_approve_exact_hash_can_create_approval": True,
        "reject_creates_rejected_event": True,
        "edit_routes_to_revision": True,
        "hold_pauses_eligibility": True,
        "ambiguous_requires_clarification": True,
        "mismatch_fails_closed": True,
        "unknown_challenge_fails_closed": True,
        "replay_fails_closed": True,
        "expiration_policy": "future_required_not_active",
        "valid_approval_can_be_outbox_candidate": True,
        "valid_for_dispatch_always_false": True,
        "can_dispatch_always_false": True,
        "can_create_outbox_always_false": True,
        "public_postable_always_false": True,
        "append_only_fixture_output_only": True,
        "status": "pass",
    }
    packet["approval_ledger_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(packet):
    lines = ["# Approval Ledger Policy", "", "> [!IMPORTANT]", "> Local append-only fixture contract. No dispatch, outbox creation, platform/provider call, network, or credential/env read.", ""]
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
    print("APPROVAL_LEDGER_POLICY_CHECKSUM", result["approval_ledger_policy_checksum"])
