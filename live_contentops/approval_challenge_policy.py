"""Approval challenge policy (LOCAL, NOT APPROVAL AUTHORITY)."""

import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XK_XL_XM_APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V0"
MODEL = "APPROVAL_CHALLENGE_POLICY_0174XK_XL_XM"
MODEL_VERSION = "0174XK_XL_XM_APPROVAL_CHALLENGE_POLICY_V1"
SOURCE_BASELINE_COMMIT = "1f7d2f96d468cbc0d88091f5e7d94201222c3c69"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XK_XL_XM")
POLICY_PACKET = "approval_challenge_policy_packet.json"
POLICY_DOC = "approval_challenge_policy.md"

FORBIDDEN_MATERIAL = [
    "raw_credential",
    "raw_token",
    "raw_chat_id",
    "raw_destination",
    "env_var",
    "secret_path",
    "live_url",
    "chat_id",
    "token",
    "secret",
]


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
        "approval_ledger_mutated": False,
        "dispatch_outbox_mutated": False,
    }


def hash_short(payload_hash):
    if not payload_hash or len(payload_hash) < 12:
        raise ValueError("payload_hash_required")
    return payload_hash[:12]


def allowed_response_phrases(payload_hash):
    short = hash_short(payload_hash)
    return {
        "approval_phrase_required": f"APPROVE {short}",
        "rejection_phrase_required": f"REJECT {short}",
        "edit_phrase_allowed": f"EDIT {short}: <instruction>",
        "hold_phrase_allowed": f"HOLD {short}",
    }


def validate_no_forbidden_material(value):
    text = json.dumps(value, sort_keys=True).lower()
    for token in FORBIDDEN_MATERIAL:
        if token in text:
            raise ValueError("forbidden_candidate_material")
    return True


def can_create_candidate(payload, blocked_brief_ids=None):
    blocked_brief_ids = set(blocked_brief_ids or [])
    if payload.get("source_brief_id") in blocked_brief_ids:
        return False
    if payload.get("visibility_class") != "review_only_payload_preview":
        return False
    if not payload.get("payload_hash"):
        return False
    if payload.get("human_review_required") is not True:
        return False
    if payload.get("dispatch_ready") is True:
        return False
    if payload.get("public_postable") is True:
        return False
    if payload.get("approval_ledger_mutated") is True:
        return False
    if payload.get("dispatch_outbox_mutated") is True:
        return False
    validate_no_forbidden_material({
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
    })
    return True


def required_candidate_fields():
    return [
        "challenge_candidate_id",
        "source_payload_id",
        "source_brief_id",
        "source_intent_id",
        "platform",
        "payload_class",
        "payload_hash",
        "payload_hash_short",
        "destination_summary_redacted",
        "destination_binding_id",
        "credential_handle_id",
        "visibility_class",
        "challenge_channel",
        "challenge_text",
        "approval_phrase_required",
        "rejection_phrase_required",
        "edit_phrase_allowed",
        "hold_phrase_allowed",
        "expires_policy",
        "one_time_nonce_policy",
        "limitations",
        "source_notes",
        "no_financial_advice",
        "no_signal_language",
        "approval_required",
        "can_record_approval",
        "can_dispatch",
        "can_create_outbox",
        "public_postable",
        "human_review_required",
        "evidence_refs",
        "blocked_reasons",
    ]


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "required_candidate_fields": required_candidate_fields(),
        "candidate_input_required_visibility_class": "review_only_payload_preview",
        "requires_payload_hash": True,
        "requires_human_review_required_true": True,
        "blocks_dispatch_ready_true": True,
        "blocks_public_postable_true": True,
        "blocks_direct_dispatch_proof": True,
        "blocks_approval_candidate_proof": True,
        "blocks_signal_advice_proof": True,
        "blocks_future_artifact_proof": True,
        "telegram_operator_review_distinct_from_channel_dispatch": True,
        "telegram_dispatch_status": "proven_frozen_no_send",
        "substack_preserves_manual_export": True,
        "x_preserves_short_thread_split": True,
        "can_record_approval": False,
        "can_dispatch": False,
        "can_create_outbox": False,
        "expires_policy": "future_required_not_active",
        "one_time_nonce_policy": "future_required_not_active",
        "status": "pass",
    }
    packet["approval_challenge_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(packet):
    lines = ["# Approval Challenge Policy", ""]
    lines.append("> [!IMPORTANT]")
    lines.append("> Candidate construction only. No approval, ledger mutation, outbox mutation, dispatch, network, platform/provider call, or credential/env read.")
    lines.append("")
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
    print("APPROVAL_CHALLENGE_POLICY_CHECKSUM", result["approval_challenge_policy_checksum"])
