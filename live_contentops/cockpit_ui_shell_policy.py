"""Cockpit UI shell policy (LOCAL STATIC SHELL ONLY, NO LIVE ACTIONS)."""

import copy
import json
import os.path
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174YL_YM_YN_COCKPIT_UI_SHELL_CONTRACT_V0"
MODEL = "COCKPIT_UI_SHELL_POLICY_0174YL_YM_YN"
MODEL_VERSION = "0174YL_YM_YN_COCKPIT_UI_SHELL_POLICY_V1"
SOURCE_BASELINE_COMMIT = "ab6e9840f2dc1d73008bea3e6aabbbcf4db5abdd"
DOC_REL_DIR = os.path.join("docs", "automation", "0174YL_YM_YN")
POLICY_PACKET = "cockpit_ui_shell_policy_packet.json"
POLICY_DOC = "cockpit_ui_shell_policy.md"

READINESS_CLASS = "NOT_READY_FOR_LIVE_DISPATCH"
LIVE_DISPATCH_STATUS = "BLOCKED"
LOCAL_GOVERNANCE_STATUS = "PASS_DRY_RUN_CHAIN"
MANUAL_EXPORT_STATUS = "REVIEW_ONLY_READY_FOR_OPERATOR"

SHELL_REGIONS = [
    "CommandHero",
    "SignalLockStrip",
    "OperationalTruthRail",
    "BlockerStack",
    "ContentLane",
    "EvidenceCard",
    "AuditTable",
    "NextActionPanel",
]

SEMANTIC_COMPONENTS = {
    "CommandHero": ["title", "readiness_class", "local_governance_status", "live_dispatch_status", "next_safe_operator_action"],
    "SignalLockStrip": ["no_live_dispatch", "no_platform_api", "no_credential_hydration", "no_scheduler", "no_autonomous_replies_or_dms", "no_scraping", "no_financial_advice_or_signal_language"],
    "OperationalTruthRail": ["platform_statuses", "review_queue_count", "blocker_count"],
    "BlockerStack": ["current_truth", "required_future_gates", "live_blocker_reasons"],
    "ContentLane": ["manual_export_queue", "x_preview_queue", "telegram_preview_queue", "blocked_live_dispatch_queue"],
    "EvidenceCard": ["payload_hash_short", "payload_class", "platform", "source_payload_id", "source_notes", "evidence_refs", "can_dispatch", "public_postable"],
    "AuditTable": ["evidence_index", "checksum", "source_stage", "status"],
    "NextActionPanel": ["allowed_local_review_actions", "forbidden_live_platform_actions"],
}

PLATFORM_STATUSES = {
    "substack": "MANUAL_EXPORT_ONLY_NO_API",
    "x": "PREVIEW_ONLY_NO_API",
    "telegram": "PREVIEW_ONLY_FROZEN_NO_SEND",
}

ALLOWED_REVIEW_ONLY_ACTIONS = [
    "open_cockpit_ui_shell_preview_non_executing",
    "review_manual_export_queue_non_executing",
    "copy_markdown_for_substack_after_human_review",
    "inspect_x_preview_non_executing",
    "inspect_telegram_preview_non_executing",
    "record_manual_publish_later_non_executing",
    "request_revision_non_executing",
    "hold_non_executing",
]

FORBIDDEN_ACTIONS = [
    "live_dispatch",
    "approve_for_posting",
    "credential_hydration",
    "platform_api_call",
    "provider_api_call",
    "autonomous_posting",
    "scheduling",
    "reply_or_dm",
    "scraping",
    "live_state_creation",
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
    "approved for posting",
]

FORBIDDEN_MATERIAL_PATTERNS = [
    r"bot\d+:[a-z0-9_-]{20,}",
    r"\bchat[_-]?id\b",
    r"\braw[_-]?destination\b",
    r"\bsecret\b",
    r"\.env",
    r"https?://",
    r"provider_response",
    r"<\s*iframe",
    r"<\s*form",
    r"cdn\.",
]

DESIGN_TOKENS = {
    "surface_family": "matte_graphite_zinc",
    "authority_accent": "disciplined_neutral",
    "review_caution": "amber_only",
    "verified_blocker": "red_only",
    "verified_pass": "green_only",
    "forbidden_styles": ["blue_cyan_dashboard", "neon_glow", "fake_terminal_dump", "marketing_hero_cards", "fake_action_buttons"],
    "density": "institutional_compact_readable",
}


def safety_flags():
    return {
        "is_local_only": True,
        "static_shell_only": True,
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
        "platform_statuses": copy.deepcopy(PLATFORM_STATUSES),
        "shell_regions": list(SHELL_REGIONS),
        "semantic_components": copy.deepcopy(SEMANTIC_COMPONENTS),
        "allowed_review_only_actions": list(ALLOWED_REVIEW_ONLY_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "required_future_gates": list(REQUIRED_FUTURE_GATES),
        "forbidden_readiness_claims": list(FORBIDDEN_READINESS_CLAIMS),
        "forbidden_material_patterns": list(FORBIDDEN_MATERIAL_PATTERNS),
        "design_tokens": copy.deepcopy(DESIGN_TOKENS),
        "current_state_and_future_gates_must_be_separated": True,
        "historical_telegram_proof_is_not_current_live_readiness": True,
        "action_elements_must_be_review_only_or_non_executing": True,
        "hidden_live_affordances_allowed": False,
        "html_scripts_allowed": False,
        "html_forms_allowed": False,
        "external_assets_allowed": False,
        "iframe_allowed": False,
        "tracking_allowed": False,
        "runtime_network_allowed": False,
        "screenshot_safe_surface": True,
        "status": "pass",
    }
    validation_view = copy.deepcopy(packet)
    validation_view.pop("forbidden_readiness_claims", None)
    validation_view.pop("forbidden_material_patterns", None)
    validate_no_forbidden_readiness_claims(validation_view)
    validate_no_forbidden_material(validation_view)
    packet["cockpit_ui_shell_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def _policy_markdown(packet):
    rows = "\n".join(f"- `{region}`: {', '.join(packet['semantic_components'][region])}" for region in packet["shell_regions"])
    return f"""# Cockpit UI Shell Policy

Task: `{packet['task_label']}`

Status: `{packet['status']}`

Readiness: `{packet['readiness_class']}`

Live dispatch: `{packet['live_dispatch_status']}`

## Shell Regions

{rows}

## Safety Rails

- Local-only: `{packet['is_local_only']}`
- Dispatch allowed: `{packet['can_dispatch']}`
- Public-postable: `{packet['public_postable']}`
- Runtime network allowed: `{packet['runtime_network_allowed']}`
- External assets allowed: `{packet['external_assets_allowed']}`
- Hidden live affordances allowed: `{packet['hidden_live_affordances_allowed']}`

## Checksum

`{packet['cockpit_ui_shell_policy_checksum']}`
"""


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet = build_policy_packet()
    (out / POLICY_PACKET).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    (out / POLICY_DOC).write_text(_policy_markdown(packet), encoding="utf-8", newline="\n")
    return copy.deepcopy(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("COCKPIT_UI_SHELL_POLICY_CHECKSUM", result["cockpit_ui_shell_policy_checksum"])
