"""Static cockpit surface policy (LOCAL, STATIC PREVIEW ONLY, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_CONTRACT_V0"
MODEL = "STATIC_COCKPIT_SURFACE_POLICY_0174YI_YJ_YK"
MODEL_VERSION = "0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_POLICY_V1"
SOURCE_BASELINE_COMMIT = "ebe0b3c9c792a6eb0c8a80b8b73d41a6538665a1"
DOC_REL_DIR = os.path.join("docs", "automation", "0174YI_YJ_YK")
POLICY_PACKET = "static_cockpit_surface_policy_packet.json"

READINESS_CLASS = "NOT_READY_FOR_LIVE_DISPATCH"
LIVE_DISPATCH_STATUS = "BLOCKED"
LOCAL_GOVERNANCE_STATUS = "PASS_DRY_RUN_CHAIN"
MANUAL_EXPORT_STATUS = "REVIEW_ONLY_READY_FOR_OPERATOR"

PLATFORMS = ["substack", "x", "telegram"]
PLATFORM_STATUSES = {
    "substack": "MANUAL_EXPORT_ONLY_NO_API",
    "x": "PREVIEW_ONLY_NO_API",
    "telegram": "PREVIEW_ONLY_FROZEN_NO_SEND",
}
ALLOWED_ACTIONS = [
    "open_static_cockpit_surface_preview",
    "copy_markdown_for_substack",
    "inspect_x_thread_preview",
    "inspect_x_short_preview",
    "inspect_telegram_channel_update_preview",
    "record_manual_publish_later",
    "request_revision",
    "hold",
]
FORBIDDEN_ACTIONS = [
    "live_dispatch",
    "credential_hydration",
    "platform_api_call",
    "provider_api_call",
    "autonomous_posting",
    "scheduling",
    "reply_or_dm",
    "scraping",
]
REQUIRED_FUTURE_GATES = [
    "kill_switch_activation",
    "redacted_audit_packet",
    "manual_fallback_proof",
    "operator_supervision_window",
    "live_dispatch_separate_approval",
]
FORBIDDEN_READINESS_CLAIMS = [
    "production-ready",
    "live-ready",
    "dispatch-ready",
    "ready to send",
    "public-postable",
]
FORBIDDEN_MATERIAL_PATTERNS = [
    r"bot\d+:[a-z0-9_-]{20,}",
    r"\bchat[_-]?id\b",
    r"\braw[_-]?destination\b",
    r"\bsecret\b",
    r"\.env",
    r"https?://",
    r"provider_response",
    r"<\s*script",
    r"<\s*form",
]


def safety_flags():
    return {
        "is_local_only": True,
        "static_preview_only": True,
        "can_dispatch": False,
        "public_postable": False,
        "human_review_required": True,
        "network_performed": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "llm_provider_api_called": False,
        "substack_api_called": False,
        "x_api_called": False,
        "telegram_api_called": False,
        "platform_dispatch_performed": False,
        "live_post_performed": False,
        "credential_hydration_performed": False,
        "credential_read": False,
        "env_read": False,
        "dotenv_read": False,
        "token_logged": False,
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "scheduler_enabled": False,
        "scraping_performed": False,
        "autonomous_replies_or_dms": False,
        "live_ready_state_created": False,
        "public_ready_content_generated": False,
        "no_financial_advice": True,
        "no_signal_language": True,
    }


def _scalar_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _scalar_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _scalar_strings(item)


def validate_no_forbidden_readiness_claims(value):
    lowered = "\n".join(_scalar_strings(value)).lower()
    for claim in FORBIDDEN_READINESS_CLAIMS:
        if claim in lowered:
            raise ValueError(f"forbidden_readiness_claim:{claim}")
    return True


def validate_no_forbidden_material(value):
    lowered = "\n".join(_scalar_strings(value)).lower()
    for pattern in FORBIDDEN_MATERIAL_PATTERNS:
        if re.search(pattern, lowered):
            raise ValueError(f"forbidden_material:{pattern}")
    return True


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "readiness_class": READINESS_CLASS,
        "live_dispatch_status": LIVE_DISPATCH_STATUS,
        "local_governance_status": LOCAL_GOVERNANCE_STATUS,
        "manual_export_status": MANUAL_EXPORT_STATUS,
        "platforms": list(PLATFORMS),
        "platform_statuses": copy.deepcopy(PLATFORM_STATUSES),
        "allowed_actions": list(ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "required_future_gates": list(REQUIRED_FUTURE_GATES),
        "forbidden_readiness_claims": list(FORBIDDEN_READINESS_CLAIMS),
        "forbidden_material_patterns": list(FORBIDDEN_MATERIAL_PATTERNS),
        "surface_must_be_screenshot_safe": True,
        "html_scripts_allowed": False,
        "html_forms_allowed": False,
        "external_assets_allowed": False,
        "status": "pass",
    }
    validation_view = copy.deepcopy(packet)
    validation_view.pop("forbidden_readiness_claims", None)
    validation_view.pop("forbidden_material_patterns", None)
    validate_no_forbidden_readiness_claims(validation_view)
    validate_no_forbidden_material(validation_view)
    packet["static_cockpit_surface_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


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
    return copy.deepcopy(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("STATIC_COCKPIT_SURFACE_POLICY_CHECKSUM", result["static_cockpit_surface_policy_checksum"])
