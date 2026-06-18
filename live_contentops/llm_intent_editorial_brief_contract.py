"""LLM intent to editorial brief contract (LOCAL, LLM DISABLED).

Converts deterministic remote operator intents into review-only editorial briefs.
No provider/API/network/env behavior and no approval/dispatch authority.
"""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import editorial_brief_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XE_XF_XG_LLM_INTENT_EDITORIAL_BRIEF_CONTRACT_V0"
MODEL = "LLM_INTENT_EDITORIAL_BRIEF_CONTRACT_0174XE_XF_XG"
MODEL_VERSION = "0174XE_XF_XG_LLM_INTENT_EDITORIAL_BRIEF_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "73eb5797f2413f32989efa57c600eb014a1db507"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XE_XF_XG")
INGRESS_REL = os.path.join("docs", "automation", "0174XB_XC_XD", "remote_operator_intent_ingress_packet.json")
PACKET_FILENAME = "llm_intent_editorial_brief_contract_packet.json"
DOC_FILENAME = "llm_intent_editorial_brief_contract.md"
FIXTURE_FILENAME = "editorial_brief_fixture_outputs.json"
NEXT_PACKET_FILENAME = "next_idea_to_primary_platform_variants_contract_packet.json"
NEXT_DOC_FILENAME = "next_idea_to_primary_platform_variants_contract.md"


def safety_flags():
    return policy.safety_flags()


def _load_intents(repo_root):
    path = pathlib.Path(repo_root) / INGRESS_REL
    return json.loads(path.read_text(encoding="utf-8"))


def _topic_summary(intent):
    topic = intent.get("extracted_topic") or "unspecified"
    if topic == "cpi_macro_regime_shift":
        return "CPI print as context, not proof of macro regime shift"
    if topic == "hook_revision":
        return "Calmer X hook revision"
    if topic == "manual_metric_bookmarks":
        return "Manual metric note for X bookmarks"
    if topic == "workflow_status":
        return "Workflow status request"
    return "Clarification needed for editorial topic"


def _audience_mode(targets):
    if "substack" in targets:
        return "owned_audience_long_form"
    if "x" in targets:
        return "public_short_form_context"
    if "linkedin" in targets:
        return "professional_credibility"
    return "operator_review"


def _primary_fit(targets):
    return [p for p in targets if p in policy.PLATFORM_TIERS["primary_brand_channel_fit"]]


def _secondary_fit(targets):
    return [p for p in targets if p in policy.PLATFORM_TIERS["secondary_channel_fit"]]


def _expansion_fit(targets):
    return [p for p in targets if p in policy.PLATFORM_TIERS["expansion_channel_fit"]]


def build_editorial_brief(intent, artifact_intake_gate=False):
    rules = policy.policy_for_intent(intent, artifact_intake_gate=artifact_intake_gate)
    targets = intent.get("extracted_platform_targets") or []
    brief = {
        "brief_id": "brief_" + intent["intent_id"],
        "source_intent_id": intent["intent_id"],
        "source_message_id": intent["source_message_id"],
        "source_transport": "telegram_fixture",
        "parser_type": "deterministic_stub",
        "llm_mode": "disabled",
        "content_lane": rules["content_lane"],
        "target_platforms": targets,
        "primary_brand_channel_fit": _primary_fit(targets),
        "secondary_channel_fit": _secondary_fit(targets),
        "expansion_channel_fit": _expansion_fit(targets),
        "topic_summary": _topic_summary(intent),
        "audience_mode": _audience_mode(targets),
        "tone_mode": intent.get("extracted_tone") or "unspecified",
        "source_requirement_status": rules["source_requirement_status"],
        "source_requirements": rules["source_requirements"],
        "required_limitations": rules["required_limitations"],
        "forbidden_claims": rules["forbidden_claims"],
        "claim_risk": rules["claim_risk"],
        "market_sensitivity": rules["market_sensitivity"],
        "no_financial_advice": True,
        "no_signal_language": True,
        "artifact_backed_allowed": rules["artifact_backed_allowed"],
        "can_generate_review_draft": rules["can_generate_review_draft"],
        "can_create_approval": False,
        "can_dispatch": False,
        "public_postable": False,
        "human_review_required": True,
        "blocked_reasons": rules["blocked_reasons"],
        "evidence_refs": intent.get("evidence_refs") or [],
        **safety_flags(),
    }
    return brief


def _future_artifact_intent():
    return {
        "intent_id": "intent_future_artifact_demo",
        "source_message_id": "fixture_future_artifact_demo",
        "parser_type": "deterministic_stub",
        "parser_model_class": "disabled",
        "intent_class": "create_content_from_idea",
        "confidence_class": "medium",
        "extracted_platform_targets": ["substack"],
        "extracted_content_lane": "future_artifact_backed",
        "extracted_topic": "future_artifact_backed_demo",
        "extracted_tone": "unspecified",
        "extracted_constraints": ["manual_review_required"],
        "extracted_forbidden_risk_flags": [],
        "requires_clarification": True,
        "clarification_question": "Which approved artifact intake gate backs this content?",
        "can_create_content_brief": True,
        "can_create_approval": False,
        "can_dispatch": False,
        "blocked_reasons": [],
        "evidence_refs": ["future_artifact_demo_ref"],
    }


def build_contract_packet(repo_root="."):
    ingress = _load_intents(repo_root)
    intents = list(ingress["intents"]) + [_future_artifact_intent()]
    briefs = [build_editorial_brief(i) for i in intents]
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "parser_type": "deterministic_stub",
        "llm_mode": "disabled",
        "supported_content_lanes": policy.SUPPORTED_CONTENT_LANES,
        "supported_platform_tiers": policy.PLATFORM_TIERS,
        "editorial_briefs": briefs,
        "blocked_approval_proof": [b for b in briefs if "approval_intent_cannot_create_approval" in b["blocked_reasons"]],
        "blocked_direct_dispatch_proof": [b for b in briefs if "direct_dispatch_intent_cannot_create_outbox" in b["blocked_reasons"]],
        "blocked_signal_advice_proof": [b for b in briefs if "signal_or_advice_language_blocks_brief_generation" in b["blocked_reasons"]],
        "future_artifact_backed_blocked_proof": [b for b in briefs if "future_artifact_backed_without_artifact_intake_gate" in b["blocked_reasons"]],
        "telegram_channel_update_distinct_from_inbox": True,
        "all_no_financial_advice": all(b["no_financial_advice"] is True for b in briefs),
        "all_no_signal_language": all(b["no_signal_language"] is True for b in briefs),
        "all_public_postable_false": all(b["public_postable"] is False for b in briefs),
        "all_human_review_required": all(b["human_review_required"] is True for b in briefs),
        "all_can_create_approval_false": all(b["can_create_approval"] is False for b in briefs),
        "all_can_dispatch_false": all(b["can_dispatch"] is False for b in briefs),
        "intent_ingress_packet_checksum": ingress["intent_ingress_packet_checksum"],
        "status": "pass",
    }
    packet["editorial_brief_fixture_outputs_checksum"] = adapter.compute_checksum(briefs)
    packet["editorial_brief_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_variants_contract(contract_packet):
    packet = {
        "task_label": "TASK_CONTENTOPS_0174XH_XI_XJ_IDEA_TO_PRIMARY_PLATFORM_VARIANTS_DRY_RUN_V0",
        "model": "NEXT_IDEA_TO_PRIMARY_PLATFORM_VARIANTS_CONTRACT_0174XE_XF_XG",
        "model_version": "0174XE_XF_XG_NEXT_IDEA_TO_PRIMARY_PLATFORM_VARIANTS_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "next_batch_prompt": "TASK_CONTENTOPS_0174XH_XI_XJ_IDEA_TO_PRIMARY_PLATFORM_VARIANTS_DRY_RUN_V0",
        "next_scope": "idea_to_primary_platform_variants_dry_run_local_only",
        "allowed_outputs": ["review_draft_candidate", "x_thread_preview", "substack_manual_export_draft", "telegram_inbox_response_candidate"],
        "forbidden_outputs": ["approval", "dispatch", "public_post", "credential_access", "platform_api_call"],
        "editorial_brief_contract_checksum": contract_packet["editorial_brief_contract_checksum"],
        "editorial_brief_fixture_outputs_checksum": contract_packet["editorial_brief_fixture_outputs_checksum"],
    }
    packet["next_variants_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def render_doc(title, packet):
    lines = [f"# {title}", ""]
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
    contract = build_contract_packet(repo_root)
    variants = build_next_variants_contract(contract)
    (out / PACKET_FILENAME).write_text(adapter.serialize(contract), encoding="utf-8", newline="\n")
    (out / DOC_FILENAME).write_text(render_doc("LLM Intent Editorial Brief Contract", contract), encoding="utf-8", newline="\n")
    (out / FIXTURE_FILENAME).write_text(adapter.serialize(contract["editorial_briefs"]), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET_FILENAME).write_text(adapter.serialize(variants), encoding="utf-8", newline="\n")
    (out / NEXT_DOC_FILENAME).write_text(render_doc("Next Idea To Primary Platform Variants Contract", variants), encoding="utf-8", newline="\n")
    return copy.deepcopy({"contract": contract, "next_variants_contract": variants})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("EDITORIAL_BRIEF_CONTRACT_CHECKSUM", result["contract"]["editorial_brief_contract_checksum"])
    print("EDITORIAL_BRIEF_FIXTURE_OUTPUTS_CHECKSUM", result["contract"]["editorial_brief_fixture_outputs_checksum"])
    print("NEXT_VARIANTS_CONTRACT_CHECKSUM", result["next_variants_contract"]["next_variants_contract_checksum"])
