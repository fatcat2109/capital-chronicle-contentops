"""Platform payload preview contract (LOCAL, NOT LIVE).

Defines deterministic review-only payload previews for primary platform variants.
No provider/API/network/env behavior and no approval/dispatch authority.
"""

import copy
import hashlib
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XH_XI_XJ_IDEA_TO_PRIMARY_PLATFORM_VARIANTS_DRY_RUN_V0"
MODEL = "PLATFORM_PAYLOAD_PREVIEW_CONTRACT_0174XH_XI_XJ"
MODEL_VERSION = "0174XH_XI_XJ_PLATFORM_PAYLOAD_PREVIEW_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "e77acd9f74b9ce2e65e569b6bf576e3896c1333e"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XH_XI_XJ")
PACKET_FILENAME = "platform_payload_preview_contract_packet.json"
DOC_FILENAME = "platform_payload_preview_contract.md"
SUPPORTED_PLATFORMS = ["x", "telegram", "substack", "facebook_page", "threads", "instagram"]
SUPPORTED_PAYLOAD_CLASSES = [
    "x_short_post",
    "x_thread",
    "telegram_channel_update",
    "telegram_operator_review_message",
    "substack_newsletter_issue",
    "substack_longform_post",
]
SYMBOLIC_BINDING_ID = "symbolic_fixture_only"
FORBIDDEN_HASH_INPUT_TERMS = ["token", "secret", "chat_id", "provider_response", "env", "api_url", "https://api", ".env"]


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
        "credential_read": False,
        "env_read": False,
        "dotenv_read": False,
        "scheduler_enabled": False,
        "live_post_performed": False,
        "autonomous_replies_or_dms": False,
        "scraping_performed": False,
        "public_ready_content_generated": False,
        "approval_ledger_mutated": False,
        "dispatch_outbox_mutated": False,
    }


def hash_input_for_payload(payload):
    return {
        "platform": payload.get("platform", ""),
        "payload_class": payload.get("payload_class", ""),
        "destination_binding_id": payload.get("destination_binding_id", ""),
        "credential_handle_id": payload.get("credential_handle_id", ""),
        "body": payload.get("body", ""),
        "title": payload.get("title", ""),
        "subtitle": payload.get("subtitle", ""),
        "thread_parts": payload.get("thread_parts", []),
        "manual_export": payload.get("manual_export", {}),
        "visibility_class": payload.get("visibility_class", ""),
        "source_brief_id": payload.get("source_brief_id", ""),
        "platform_formatting_metadata": payload.get("platform_formatting_metadata", {}),
    }


def compute_payload_hash(payload):
    material = adapter.serialize(hash_input_for_payload(payload))
    lower = material.lower()
    for term in FORBIDDEN_HASH_INPUT_TERMS:
        if term in lower:
            raise ValueError("forbidden_hash_input_material")
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def finalize_payload(payload):
    finalized = copy.deepcopy(payload)
    finalized.update(
        {
            "destination_binding_id": SYMBOLIC_BINDING_ID,
            "credential_handle_id": SYMBOLIC_BINDING_ID,
            "payload_hash_algorithm": "sha256",
            "approval_required": True,
            "dispatch_ready": False,
            "public_postable": False,
            "human_review_required": True,
            "no_financial_advice": True,
            "no_signal_language": True,
            **safety_flags(),
        }
    )
    finalized["payload_hash"] = compute_payload_hash(finalized)
    return finalized


def build_contract_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "supported_platforms": SUPPORTED_PLATFORMS,
        "supported_payload_classes": SUPPORTED_PAYLOAD_CLASSES,
        "required_payload_fields": [
            "payload_id", "source_brief_id", "source_intent_id", "platform", "payload_class",
            "destination_binding_id", "credential_handle_id", "body", "title", "subtitle",
            "thread_parts", "source_notes", "limitations", "seo_metadata", "manual_export",
            "visibility_class", "platform_constraints_status", "platform_warnings", "payload_hash",
            "payload_hash_algorithm", "approval_required", "dispatch_ready", "public_postable",
            "human_review_required", "no_financial_advice", "no_signal_language", "evidence_refs",
        ],
        "hash_includes": list(hash_input_for_payload({}).keys()),
        "hash_excludes": ["raw_credential", "raw_token", "raw_chat_id", "raw_provider_response", "env_var", "secret_path", "live_api_url", "unredacted_destination"],
        "symbolic_binding_id": SYMBOLIC_BINDING_ID,
        "status": "pass",
    }
    packet["platform_payload_preview_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def render_doc(packet):
    lines = ["# Platform Payload Preview Contract", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    (out / PACKET_FILENAME).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    (out / DOC_FILENAME).write_text(render_doc(packet), encoding="utf-8", newline="\n")
    return copy.deepcopy(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("PLATFORM_PAYLOAD_PREVIEW_CONTRACT_CHECKSUM", result["platform_payload_preview_contract_checksum"])
    print("SUPPORTED_PAYLOAD_CLASSES", ",".join(result["supported_payload_classes"]))
