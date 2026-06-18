"""Remote operator intent ingress dry-run (LOCAL, NOT LIVE).

Deterministic stub classifier over local inbox packets. No LLM/provider/API,
network, env, posting, approval mutation, or dispatch mutation.
"""

import copy
import json
import os.path
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter
from live_contentops import telegram_remote_operator_inbox as inbox

TASK_LABEL = "TASK_CONTENTOPS_0174XB_XC_XD_REMOTE_OPERATOR_INBOX_INTENT_INGRESS_DRY_RUN_BATCH_V0"
MODEL = "REMOTE_OPERATOR_INTENT_INGRESS_0174XB_XC_XD"
MODEL_VERSION = "0174XB_XC_XD_REMOTE_OPERATOR_INTENT_INGRESS_V1"
SOURCE_BASELINE_COMMIT = "24450e8128244c0fb02e2948e78f32c0ffc9e86a"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XB_XC_XD")
PACKET_FILENAME = "remote_operator_intent_ingress_packet.json"
DOC_FILENAME = "remote_operator_intent_ingress.md"
NEXT_PACKET_FILENAME = "next_editorial_workflow_contract_packet.json"
NEXT_DOC_FILENAME = "next_editorial_workflow_contract.md"
SUPPORTED_INTENT_CLASSES = [
    "create_content_from_idea", "revise_draft", "approve_candidate", "reject_candidate",
    "hold_candidate", "ask_status", "request_preview", "request_sources",
    "submit_manual_metric_note", "unknown",
]
ADVICE_TERMS = ["buy", "long", "short", "target", "watch this level", "entry", "stop loss"]
DIRECT_DISPATCH_TERMS = ["post this now", "send this now", "publish now", "dispatch now"]


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


def _contains_any(text, terms):
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _targets(text):
    lowered = text.lower()
    found = []
    for name in ["x", "telegram", "substack", "linkedin", "threads", "instagram", "facebook"]:
        if re.search(rf"\b{name}\b", lowered):
            found.append("facebook_page" if name == "facebook" else name)
    if "thread" in lowered and "x" not in found:
        found.append("x")
    return found


def _lane(text, targets):
    lowered = text.lower()
    if "source" in lowered or "cpi" in lowered or "regime shift" in lowered:
        return "grounded_news_context"
    if "metric note" in lowered:
        return "operator_metrics"
    if "x" in targets or "thread" in lowered or "hook" in lowered:
        return "short_form_preview"
    return "pre_alpha_general_process"


def _topic(text):
    lowered = text.lower()
    if "cpi" in lowered or "macro regime shift" in lowered:
        return "cpi_macro_regime_shift"
    if "hook" in lowered:
        return "hook_revision"
    if "status" in lowered:
        return "workflow_status"
    if "bookmarks" in lowered:
        return "manual_metric_bookmarks"
    return "unspecified"


def _tone(text):
    lowered = text.lower()
    if "calmer" in lowered:
        return "calmer"
    if "professional" in lowered or "linkedin" in lowered:
        return "professional"
    return "unspecified"


def classify_intent(message, active_challenge=False):
    text = message.get("raw_text_redacted", "")
    lowered = text.lower()
    targets = _targets(text)
    risk_flags = []
    blocked = []
    intent_class = "unknown"
    confidence = "low"
    clarification = "Clarify requested operator intent and target platform."
    can_brief = False

    if _contains_any(lowered, DIRECT_DISPATCH_TERMS):
        risk_flags.append("blocked_direct_dispatch_request")
        blocked.append("direct_dispatch_request_forbidden")
    if _contains_any(lowered, ADVICE_TERMS):
        risk_flags.append("blocked_signal_or_advice_language")
        blocked.append("financial_signal_or_advice_language_forbidden")

    msg_class = message.get("message_class")
    if msg_class == "idea_message":
        intent_class, confidence, clarification, can_brief = "create_content_from_idea", "high", "", not blocked
    elif msg_class == "revision_instruction":
        intent_class, confidence, clarification = "revise_draft", "high", ""
    elif msg_class == "approval_response":
        intent_class, confidence = "approve_candidate", "medium"
        if not active_challenge:
            blocked.append("approval_without_active_challenge_forbidden")
            risk_flags.append("approval_response_candidate_only")
            clarification = "Which active approval challenge does this response answer?"
    elif msg_class == "rejection_response":
        intent_class, confidence, clarification = "reject_candidate", "high", ""
    elif msg_class == "hold_response":
        intent_class, confidence, clarification = "hold_candidate", "high", ""
    elif msg_class == "status_query":
        intent_class, confidence, clarification = "ask_status", "high", ""
    elif "preview" in lowered:
        intent_class, confidence, clarification = "request_preview", "high", ""
    elif msg_class == "source_note" or "source" in lowered:
        intent_class, confidence, clarification = "request_sources", "medium", ""
    elif msg_class == "manual_metric_note":
        intent_class, confidence, clarification = "submit_manual_metric_note", "high", ""
    elif blocked:
        confidence = "medium"
        clarification = "Request cannot proceed because it asks for forbidden behavior."

    if message.get("sender_class") != "verified_operator":
        blocked.append("sender_not_verified_for_intent_ingress")
        confidence = "low"
    if message.get("replay_status") != "fresh":
        blocked.append(f"message_replay_status_{message.get('replay_status')}")
    if not targets and intent_class in ["create_content_from_idea", "revise_draft", "request_preview"]:
        targets = ["substack"] if "long" in lowered or "issue" in lowered else ["x"] if "hook" in lowered or "thread" in lowered else []

    return {
        "intent_id": "intent_" + message["message_id"],
        "source_message_id": message["message_id"],
        "parser_type": "deterministic_stub",
        "parser_model_class": "disabled",
        "intent_class": intent_class,
        "confidence_class": "ambiguous" if intent_class == "unknown" and not blocked else confidence,
        "extracted_platform_targets": targets,
        "extracted_content_lane": _lane(text, targets),
        "extracted_topic": _topic(text),
        "extracted_tone": _tone(text),
        "extracted_constraints": ["manual_review_required", "untrusted_input", "no_public_ready_generation"],
        "extracted_forbidden_risk_flags": risk_flags,
        "requires_clarification": bool(clarification or blocked),
        "clarification_question": clarification,
        "can_create_content_brief": can_brief and not blocked,
        "can_create_approval": False,
        "can_dispatch": False,
        "blocked_reasons": sorted(set(blocked)),
        "evidence_refs": [message["transport_message_hash"]],
        **safety_flags(),
    }


def build_intent_ingress_packet(messages=None):
    inbox_packet = inbox.build_inbox_packet(messages)
    intents = [classify_intent(m) for m in inbox_packet["inbound_messages"]]
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "parser_type": "deterministic_stub",
        "parser_model_class": "disabled",
        "supported_intent_classes": SUPPORTED_INTENT_CLASSES,
        "intents": intents,
        "all_can_create_approval_false": all(i["can_create_approval"] is False for i in intents),
        "all_can_dispatch_false": all(i["can_dispatch"] is False for i in intents),
        "blocked_direct_dispatch_proof": [i for i in intents if "blocked_direct_dispatch_request" in i["extracted_forbidden_risk_flags"]],
        "blocked_approval_without_challenge_proof": [i for i in intents if "approval_without_active_challenge_forbidden" in i["blocked_reasons"]],
        "blocked_signal_advice_language_proof": [i for i in intents if "blocked_signal_or_advice_language" in i["extracted_forbidden_risk_flags"]],
        "telegram_channel_update_distinct_from_inbox": True,
        "inbox_packet_checksum": inbox_packet["inbox_packet_checksum"],
        "fixture_messages_checksum": inbox_packet["fixture_messages_checksum"],
        "status": "pass",
    }
    packet["intent_ingress_packet_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_editorial_workflow_contract(intent_packet):
    contract = {
        "task_label": "TASK_CONTENTOPS_0174XE_XF_XG_LLM_INTENT_EDITORIAL_BRIEF_CONTRACT_V0",
        "model": "NEXT_EDITORIAL_WORKFLOW_CONTRACT_0174XB_XC_XD",
        "model_version": "0174XB_XC_XD_NEXT_EDITORIAL_WORKFLOW_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        "next_batch_prompt": "TASK_CONTENTOPS_0174XE_XF_XG_LLM_INTENT_EDITORIAL_BRIEF_CONTRACT_V0",
        "next_scope": "llm_intent_to_editorial_brief_contract_local_only",
        "inputs": ["remote_operator_intent_ingress_packet", "platform_universe_registry_v2_packet"],
        "must_preserve": ["untrusted_input", "no_dispatch", "no_approval_creation", "manual_review_required"],
        "intent_ingress_packet_checksum": intent_packet["intent_ingress_packet_checksum"],
        "fixture_messages_checksum": intent_packet["fixture_messages_checksum"],
    }
    contract["next_editorial_workflow_contract_checksum"] = adapter.compute_checksum(contract)
    return contract


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
    packet = build_intent_ingress_packet()
    contract = build_next_editorial_workflow_contract(packet)
    (out / PACKET_FILENAME).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    (out / DOC_FILENAME).write_text(render_doc("Remote Operator Intent Ingress", packet), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET_FILENAME).write_text(adapter.serialize(contract), encoding="utf-8", newline="\n")
    (out / NEXT_DOC_FILENAME).write_text(render_doc("Next Editorial Workflow Contract", contract), encoding="utf-8", newline="\n")
    return copy.deepcopy({"intent_ingress": packet, "next_editorial_workflow_contract": contract})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("INTENT_INGRESS_PACKET_CHECKSUM", result["intent_ingress"]["intent_ingress_packet_checksum"])
    print("NEXT_EDITORIAL_WORKFLOW_CONTRACT_CHECKSUM", result["next_editorial_workflow_contract"]["next_editorial_workflow_contract_checksum"])
    print("SUPPORTED_INTENT_CLASSES", ",".join(result["intent_ingress"]["supported_intent_classes"]))
