"""V6 Local Canonical Draft Preview and Review Packet Builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUTH_PACKET_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_DRAFT_AUTHORIZATION_AND_READINESS/next_article_draft_authorization_and_readiness_packet.json"
INTAKE_PACKET_PATH = ROOT / "docs/automation/V6_NEXT_ARTICLE_SOURCE_PACK_INTAKE_AND_VALIDATION/next_article_source_pack_intake_validation_packet.json"

TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_CANONICAL_DRAFT_PREVIEW_AND_REVIEW_HEAVY_BATCH_V0"
FORBIDDEN_WORDING = (
    "buy", "sell", "hold", "price target", "position sizing",
    "guaranteed prediction", "signal-service", "trading instruction",
    "trade signal", "buy signal", "sell signal", "hold recommendation",
    "guaranteed return", "prediction guarantee",
)


def _stable_hash(payload: dict[str, Any]) -> str:
    p = {k: v for k, v in payload.items() if k not in ("local_draft_preview_packet_id", "draft_review_packet_id")}
    return hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_auth_packet() -> dict[str, Any]:
    return json.loads(AUTH_PACKET_PATH.read_text(encoding="utf-8"))


def _load_intake_packet() -> dict[str, Any]:
    return json.loads(INTAKE_PACKET_PATH.read_text(encoding="utf-8"))


def _assert_safe_text(value: str) -> None:
    lowered = value.lower()
    for term in FORBIDDEN_WORDING:
        if term in lowered:
            raise ValueError(f"Packet contains forbidden wording or financial advice: {term}")


def build_local_canonical_draft_preview(
    auth_packet: dict[str, Any] | None = None,
    intake_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the local canonical draft preview and review packet."""
    auth = auth_packet or _load_auth_packet()
    intake = intake_packet or _load_intake_packet()

    # Input validations
    if auth.get("ready_for_local_canonical_draft_workflow") is not True:
        raise ValueError("Input draft readiness ready_for_local_canonical_draft_workflow is not True")
    if auth.get("ready_for_llm_drafting") is True:
        raise ValueError("Input ready_for_llm_drafting is True")
    if auth.get("ready_for_provider_drafting") is True:
        raise ValueError("Input ready_for_provider_drafting is True")
    if auth.get("ready_for_auto_publish") is True:
        raise ValueError("Input ready_for_auto_publish is True")
    if auth.get("ready_for_dispatch") is True:
        raise ValueError("Input ready_for_dispatch is True")
    if auth.get("live_action_allowed") is True:
        raise ValueError("Input live_action_allowed is True")
    if auth.get("checklist_coverage_status") != "complete_coverage":
        raise ValueError("Input checklist coverage is not complete")

    # Assert safe text
    headline = auth["article_working_headline"]
    _assert_safe_text(headline)

    for entry in intake.get("source_entries", []):
        _assert_safe_text(entry.get("source_title", ""))
        _assert_safe_text(entry.get("operator_supplied_summary", ""))

    # Construct local preview contents deterministically
    working_title = "Educational Explainer: Cash-Flow Quality and Key Accounting Formulas"
    dek = "A structured analysis of cash conversion and dividend coverage metrics based on SEC documentation."
    thesis = "Analyzing the quality of reported earnings requires tracking cash conversion timelines and dividend safety cushions qualitatively."
    audience_question = "How do we evaluate the quality of a firm's reported cash flows without reliance on advisory predictions?"

    section_outline = [
        "1. Introduction to Earnings Quality",
        "2. Understanding the Cash Conversion Cycle Formula",
        "3. Dividend Coverage Ratios and Liquidity Measures",
        "4. Practical Limits of Qualitative SEC Guidance"
    ]

    draft_preview_sections = [
        {
            "section_title": "1. Introduction to Earnings Quality",
            "section_body": "Financial reporting lists profits, but cash quality shows underlying strength. This educational explainer focuses on understanding standard accounting principles."
        },
        {
            "section_title": "2. Understanding the Cash Conversion Cycle Formula",
            "section_body": "The Cash Conversion Cycle is computed as Days Inventory Outstanding plus Days Sales Outstanding minus Days Payable Outstanding. We evaluate this formula parameters qualitatively."
        },
        {
            "section_title": "3. Dividend Coverage Ratios and Liquidity Measures",
            "section_body": "Dividend Coverage is Net Income divided by Dividend Paid. Higher coverage suggests a safer cushion, while a ratio below 1 indicates net profits do not cover payments."
        },
        {
            "section_title": "4. Practical Limits of Qualitative SEC Guidance",
            "section_body": "SEC filings provide guidelines on cash conversion cycle definitions. All source-pack URLs in this workflow are text metadata only and have not been fetched or verified over the network."
        }
    ]

    evidence_callouts = [
        "Source SEC cash flow guidance document covers conversion cycle definitions.",
        "Operator-supplied draft outline sets structured conceptual limits.",
        "Definitions list details conversion and coverage formula details."
    ]

    definitions_to_include = [
        "Days Inventory Outstanding (DIO): Average inventory divided by cost of goods sold, multiplied by 365.",
        "Days Sales Outstanding (DSO): Average accounts receivable divided by total credit sales, multiplied by 365.",
        "Days Payable Outstanding (DPO): Average accounts payable divided by cost of goods sold, multiplied by 365."
    ]

    caveats_to_include = [
        "Formulas assume standard 365-day accounting conventions.",
        "Qualitative markers such as [operator-supplied figure required] are used for any specific metrics.",
        "This document is strictly educational and does not make predictions that are guaranteed."
    ]

    non_advisory_disclaimer = (
        "This document is for educational purposes only. It does not contain financial guidance, "
        "transaction recommendations, target pricing, or portfolio allocations."
    )

    operator_review_questions = [
        "Does the drafted text avoid all forbidden advisory terminology?",
        "Are the cash conversion cycle formulas formatted correctly?",
        "Is the non-advisory disclaimer displayed clearly?"
    ]

    # Validate preview text fields to be absolutely safe
    _assert_safe_text(working_title)
    _assert_safe_text(dek)
    _assert_safe_text(thesis)
    _assert_safe_text(audience_question)
    for section in draft_preview_sections:
        _assert_safe_text(section["section_title"])
        _assert_safe_text(section["section_body"])
    for definition in definitions_to_include:
        _assert_safe_text(definition)
    for caveat in caveats_to_include:
        _assert_safe_text(caveat)
    _assert_safe_text(non_advisory_disclaimer)

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "local_canonical_draft_preview_and_review_v0",
        "task_label": TASK_LABEL,
        "source_draft_authorization_packet_id": auth["draft_authorization_packet_id"],
        "source_draft_authorization_packet_hash": auth["exact_payload_hash"],
        "source_draft_readiness_packet_id": auth["draft_readiness_packet_id"],
        "source_draft_readiness_packet_hash": auth["exact_payload_hash"],
        "source_pack_intake_packet_id": auth["source_pack_intake_packet_id"],
        "source_pack_intake_packet_hash": auth["source_pack_intake_packet_hash"],
        "source_next_article_brief_packet_id": auth["source_next_article_brief_packet_id"],
        "source_next_article_brief_packet_hash": auth["source_next_article_brief_packet_hash"],
        
        "article_working_headline": headline,
        "selected_backlog_candidate_id": auth["selected_backlog_candidate_id"],
        
        "draft_preview_status": "local_draft_preview_created_for_review",
        "draft_review_status": "pending_operator_review",
        "draft_generation_method": "deterministic_template_no_llm",
        "canonical_draft_created": True,
        "article_body_created": True,
        "final_article_approved": False,
        
        "ready_for_llm_drafting": False,
        "ready_for_provider_drafting": False,
        "ready_for_auto_publish": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        
        "working_title": working_title,
        "dek": dek,
        "thesis": thesis,
        "audience_question": audience_question,
        "section_outline": section_outline,
        "draft_preview_sections": draft_preview_sections,
        "evidence_callouts": evidence_callouts,
        "definitions_to_include": definitions_to_include,
        "caveats_to_include": caveats_to_include,
        "non_advisory_disclaimer": non_advisory_disclaimer,
        "operator_review_questions": operator_review_questions,
        
        "source_support_review_required": True,
        "definitions_review_required": True,
        "caveat_review_required": True,
        "non_advisory_review_required": True,
        "final_operator_approval_required": True,
        
        "separate_final_approval_task_required": True,
        "separate_platform_variant_task_required": True,
        "separate_publish_authorization_required": True,
        "public_url_verification_performed": False,
        
        "llm_provider_call_made": False,
        "provider_call_made": False,
        "platform_api_used": False,
        "network_call_made": False,
        "public_url_fetch_made": False,
        "env_value_read_made": False,
        "credential_read_made": False,
        "browser_session_used": False,
        "live_publish_performed_by_contentops": False,
        "enabled_publish_send_dispatch_approve_controls": False,
        
        "forbidden_financial_advice_or_signal_wording_present": False,
        "scanned_for_terms": [
            "buy", "sell", "hold", "price target", "position sizing",
            "guaranteed prediction", "signal-service", "trading instruction"
        ]
    }

    h = _stable_hash(packet)
    packet["exact_payload_hash"] = h
    packet["local_draft_preview_packet_id"] = f"local_draft_preview_{h[:16]}"
    packet["draft_review_packet_id"] = f"draft_review_{h[:16]}"

    return packet


if __name__ == "__main__":
    out_dir = ROOT / "docs/automation/V6_LOCAL_CANONICAL_DRAFT_PREVIEW_AND_REVIEW"
    out_dir.mkdir(parents=True, exist_ok=True)
    p = build_local_canonical_draft_preview()
    (out_dir / "local_canonical_draft_preview_and_review_packet.json").write_text(
        json.dumps(p, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("Successfully built draft preview packet.")
