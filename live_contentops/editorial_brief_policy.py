"""Editorial brief policy (LOCAL, NOT LIVE).

Defines non-authoritative policy for converting remote operator intents into
review-only editorial briefs. No provider/API/network/env behavior.
"""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XE_XF_XG_LLM_INTENT_EDITORIAL_BRIEF_CONTRACT_V0"
MODEL = "EDITORIAL_BRIEF_POLICY_0174XE_XF_XG"
MODEL_VERSION = "0174XE_XF_XG_EDITORIAL_BRIEF_POLICY_V1"
SOURCE_BASELINE_COMMIT = "73eb5797f2413f32989efa57c600eb014a1db507"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XE_XF_XG")
PACKET_FILENAME = "editorial_brief_policy_packet.json"
DOC_FILENAME = "editorial_brief_policy.md"
SUPPORTED_CONTENT_LANES = [
    "pre_alpha_general_process",
    "grounded_news_context",
    "future_artifact_backed",
    "blocked_or_unknown",
]
PLATFORM_TIERS = {
    "primary_brand_channel_fit": ["x", "telegram", "substack"],
    "secondary_channel_fit": ["linkedin"],
    "expansion_channel_fit": ["threads", "instagram", "facebook_page"],
}


def safety_flags():
    return {
        "is_local_only": True,
        "network_performed": False,
        "telegram_api_called": False,
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


def platform_tier_for(platform):
    for tier, platforms in PLATFORM_TIERS.items():
        if platform in platforms:
            return tier
    return "unknown_platform_tier"


def content_lane_for(intent):
    if intent.get("blocked_reasons"):
        return "blocked_or_unknown"
    lane = intent.get("extracted_content_lane") or "pre_alpha_general_process"
    if lane == "future_artifact_backed":
        return lane
    if lane not in SUPPORTED_CONTENT_LANES:
        return "blocked_or_unknown"
    return lane


def source_requirement_status(intent):
    lane = content_lane_for(intent)
    if lane == "grounded_news_context":
        return "source_needed"
    if lane == "future_artifact_backed":
        return "blocked_missing_artifact_intake_gate"
    if lane == "blocked_or_unknown":
        return "clarification_needed"
    return "operator_context_sufficient_for_brief"


def policy_for_intent(intent, artifact_intake_gate=False):
    targets = intent.get("extracted_platform_targets") or []
    lane = content_lane_for(intent)
    blocked = list(intent.get("blocked_reasons") or [])
    risks = list(intent.get("extracted_forbidden_risk_flags") or [])
    if lane == "future_artifact_backed" and not artifact_intake_gate:
        blocked.append("future_artifact_backed_without_artifact_intake_gate")
    if "approval_response_candidate_only" in risks:
        blocked.append("approval_intent_cannot_create_approval")
    if "blocked_direct_dispatch_request" in risks:
        blocked.append("direct_dispatch_intent_cannot_create_outbox")
    if "blocked_signal_or_advice_language" in risks:
        blocked.append("signal_or_advice_language_blocks_brief_generation")
    if intent.get("intent_class") == "unknown":
        blocked.append("empty_or_ambiguous_intent_requires_clarification")

    requirements = []
    limitations = ["human_review_required", "not_public_ready", "no_signal_language", "no_financial_advice"]
    forbidden_claims = ["investment_advice", "trade_signal", "price_target", "certainty_claim", "unsupported_news_causal_claim"]
    if "substack" in targets:
        requirements += ["owned_long_form_authority", "manual_markdown_export", "source_notes_required"]
    if "x" in targets:
        requirements += ["short_form_or_thread_preview_only", "no_posting"]
    if "telegram" in targets:
        requirements += ["telegram_channel_update_distinct_from_remote_inbox"]
    if "linkedin" in targets:
        requirements += ["professional_credibility_secondary", "review_gated"]
    if any(t in targets for t in ["threads", "instagram", "facebook_page"]):
        requirements += ["expansion_dry_run_only"]
    if lane == "grounded_news_context":
        limitations += ["news_hook_only_never_signal"]
        requirements += ["source_requirement", "limitations_required"]

    can_generate = not blocked and intent.get("can_create_content_brief") is True
    return {
        "content_lane": "blocked_or_unknown" if blocked else lane,
        "source_requirement_status": source_requirement_status(intent),
        "source_requirements": sorted(set(requirements)),
        "required_limitations": sorted(set(limitations)),
        "forbidden_claims": forbidden_claims,
        "claim_risk": "high" if risks or lane == "grounded_news_context" else "medium" if targets else "unknown",
        "market_sensitivity": "high" if lane == "grounded_news_context" or risks else "medium",
        "artifact_backed_allowed": bool(artifact_intake_gate and lane == "future_artifact_backed"),
        "can_generate_review_draft": can_generate,
        "blocked_reasons": sorted(set(blocked)),
        "platform_tiers": PLATFORM_TIERS,
    }


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "supported_content_lanes": SUPPORTED_CONTENT_LANES,
        "supported_platform_tiers": PLATFORM_TIERS,
        "policy_rules": {
            "substack": "owned_long_form_authority_manual_export_path",
            "x": "short_form_thread_preview_only_not_posting",
            "telegram": "channel_update_distinct_from_remote_inbox",
            "linkedin": "secondary_professional_credibility_review_gated",
            "expansion": "threads_instagram_facebook_page_dry_run_only",
            "future_artifact_backed": "blocked_without_artifact_intake_gate",
            "grounded_news_context": "news_hook_never_signal",
            "approval_like_intent": "cannot_create_approval",
            "direct_dispatch_intent": "cannot_create_outbox",
            "signal_advice_language": "blocks_brief_generation_or_safe_reframe",
            "empty_ambiguous_intent": "requires_clarification",
        },
        "no_financial_advice_always": True,
        "no_signal_language_always": True,
        "can_create_approval_always_false": True,
        "can_dispatch_always_false": True,
        "public_postable_always_false": True,
        "human_review_required_always": True,
        "status": "pass",
    }
    packet["editorial_brief_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def render_doc(packet):
    lines = ["# Editorial Brief Policy", ""]
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
    packet = build_policy_packet()
    (out / PACKET_FILENAME).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    (out / DOC_FILENAME).write_text(render_doc(packet), encoding="utf-8", newline="\n")
    return copy.deepcopy(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("EDITORIAL_BRIEF_POLICY_CHECKSUM", result["editorial_brief_policy_checksum"])
    print("SUPPORTED_CONTENT_LANES", ",".join(result["supported_content_lanes"]))
