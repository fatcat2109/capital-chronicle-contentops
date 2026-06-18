"""Manual export review policy (LOCAL, REVIEW-ONLY, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174YC_YD_YE_MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_V0"
MODEL = "MANUAL_EXPORT_REVIEW_POLICY_0174YC_YD_YE"
MODEL_VERSION = "0174YC_YD_YE_MANUAL_EXPORT_REVIEW_POLICY_V1"
SOURCE_BASELINE_COMMIT = "ca2e8c01327984fd90524e790406621a2668202d"
DOC_REL_DIR = os.path.join("docs", "automation", "0174YC_YD_YE")
POLICY_PACKET = "manual_export_review_policy_packet.json"
POLICY_DOC = "manual_export_review_policy.md"

READINESS_CLASS = "NOT_READY_FOR_LIVE_DISPATCH"
LOCAL_GOVERNANCE_STATUS = "PASS_DRY_RUN_CHAIN"
LIVE_DISPATCH_STATUS = "BLOCKED"
MANUAL_EXPORT_STATUS = "REVIEW_ONLY_READY_FOR_OPERATOR"
PLATFORMS = ["substack", "x", "telegram"]
OPERATOR_ACTIONS = [
    "copy_markdown_for_substack",
    "inspect_x_thread_preview",
    "inspect_telegram_channel_update_preview",
    "record_manual_publish_later",
    "request_revision",
    "hold",
]
FORBIDDEN_ACTIONS = [
    "live_dispatch",
    "credential_hydration",
    "platform_api_call",
    "autonomous_posting",
    "scheduling",
    "reply_or_dm",
    "scraping",
]
FORBIDDEN_READINESS_CLAIMS = [
    "production-ready",
    "live-ready",
    "dispatch-ready",
    "ready to send",
    "public-postable",
]
REQUIRED_FUTURE_GATES = [
    "kill_switch_activation",
    "redacted_audit_packet",
    "manual_fallback_proof",
    "operator_supervision_window",
    "live_dispatch_separate_approval",
]
PLATFORM_SURFACE_STATUSES = {
    "substack": "manual_export_review_strongest_path_no_api",
    "x": "preview_only_no_api",
    "telegram": "operator_and_channel_preview_only_no_send",
}
SAFETY_FLAGS = {
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
FORBIDDEN_MATERIAL_PATTERNS = [
    re.compile(r"bot\d+:[a-z0-9_-]{20,}", re.I),
    re.compile(r"\bchat[_-]?id\b", re.I),
    re.compile(r"\braw[_-]?destination\b", re.I),
    re.compile(r"\bsecret\b", re.I),
    re.compile(r"\.env", re.I),
    re.compile(r"https?://", re.I),
]


def safety_flags():
    return copy.deepcopy(SAFETY_FLAGS)


def policy_values():
    return {
        "readiness_class": READINESS_CLASS,
        "local_governance_status": LOCAL_GOVERNANCE_STATUS,
        "live_dispatch_status": LIVE_DISPATCH_STATUS,
        "manual_export_status": MANUAL_EXPORT_STATUS,
        "platforms": list(PLATFORMS),
        "operator_actions": list(OPERATOR_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "required_future_gates": list(REQUIRED_FUTURE_GATES),
        "platform_surface_statuses": copy.deepcopy(PLATFORM_SURFACE_STATUSES),
        "no_financial_advice": True,
        "no_signal_language": True,
        "public_postable": False,
        "human_review_required": True,
        "can_dispatch": False,
        "live_ready_state_created": False,
    }


def _scalar_strings(value, parent_key=""):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"forbidden_readiness_claims", "forbidden_material_patterns"}:
                continue
            yield from _scalar_strings(item, key)
    elif isinstance(value, list):
        for item in value:
            yield from _scalar_strings(item, parent_key)
    elif isinstance(value, str):
        yield value.lower()


def validate_no_forbidden_readiness_claims(value):
    text = " ".join(_scalar_strings(value))
    for claim in FORBIDDEN_READINESS_CLAIMS:
        if claim in text:
            raise ValueError("forbidden_readiness_claim")
    return True


def validate_no_forbidden_material(value):
    strings = list(_scalar_strings(value))
    for text in strings:
        for pattern in FORBIDDEN_MATERIAL_PATTERNS:
            if pattern.search(text):
                raise ValueError("forbidden_material")
    return True


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        **policy_values(),
        "forbidden_readiness_claims": list(FORBIDDEN_READINESS_CLAIMS),
        "forbidden_material_patterns": [p.pattern for p in FORBIDDEN_MATERIAL_PATTERNS],
        "surface_must_remain_manual_local_review_only": True,
        "next_task_must_be_cockpit_read_model": True,
        "status": "pass",
    }
    validate_no_forbidden_readiness_claims(packet)
    validate_no_forbidden_material(packet)
    packet["manual_export_review_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Local manual export review only. Live dispatch remains blocked and no platform API is called.", ""]
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
    (out / POLICY_DOC).write_text(render_doc("Manual Export Review Policy", packet), encoding="utf-8", newline="\n")
    return copy.deepcopy(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("MANUAL_EXPORT_REVIEW_POLICY_CHECKSUM", result["manual_export_review_policy_checksum"])
