"""Local-only draft review packet validation (Task 0077).

Deterministic, repo-local review of pre-alpha general/process and grounded-news
DRAFTS written OUTSIDE the repo (operator / LLM-assisted / Deep Research context).

This module performs NO network/search/provider/LLM/platform/credential access.
It reviews safety, citation, and claim quality of manually supplied draft packets
already present on disk. It NEVER generates final public copy, never auto-approves,
and never marks anything publish-ready or public-postable.
"""

import json
import os

from live_contentops.grounded_research_brief import (
    _scan_forbidden_language,
    _scan_alpha_implication,
)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "draft_review_packet.schema.json"
)

ALLOWED_LANE = "pre_alpha_general_process"

ALLOWED_SUBTYPES = {
    "grounded_news_context",
    "official_data_explainer",
    "policy_process_commentary",
    "macro_education_from_news",
    "forecast_readiness_from_news",
    "data_sufficiency_from_news",
    "failure_forensics_from_news",
    "build_in_public",
    "product_philosophy",
}

ALLOWED_DRAFT_ORIGINS = {
    "manually_supplied_by_operator",
    "llm_assisted_outside_repo",
    "chatgpt_deep_research_context_outside_repo",
}

ALLOWED_CLAIM_TYPES = {
    "first_party_philosophy",
    "evergreen_education",
    "cited_factual_claim",
    "current_factual_claim",
    "market_sensitive_context",
    "forbidden_claim",
}

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "blocked"}

CITATION_REQUIRED_CLAIM_TYPES = {"cited_factual_claim", "current_factual_claim"}

ALLOWED_VERDICT_STATUS = {
    "local_review_pass",
    "local_review_warn",
    "local_review_block",
}

REQUIRED_SAFETY_FALSE = [
    "public_postable", "publish_ready", "artifact_backed",
    "provider_call_used_by_repo", "search_call_used_by_repo",
    "platform_action_used_by_repo",
]

REQUIRED_SAFETY_TRUE = [
    "review_only", "manual_review_required", "jim_final_review_required",
    "no_financial_advice", "no_signal_language", "no_execution_language",
]


def load_schema():
    with open(os.path.abspath(SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def validate_packet(packet):
    """Return {"valid": bool, "errors": [codes], "warnings": [codes]}.

    Deterministic. errors block the packet; warnings are advisory only.
    """
    errors = []
    warnings = []

    if not isinstance(packet, dict):
        return {"valid": False, "errors": ["packet_not_object"], "warnings": []}

    for field in ("packet_id", "lane", "subtype", "draft_origin", "draft_text",
                  "linked_research_brief", "source_references_used",
                  "claim_reviews", "platform_fit", "safety_review", "verdict",
                  "allowed_output_use"):
        if field not in packet:
            errors.append("missing_field:%s" % field)

    if "lane" in packet and packet.get("lane") != ALLOWED_LANE:
        errors.append("lane_must_be_pre_alpha_general_process")

    if packet.get("subtype") is not None and packet.get("subtype") not in ALLOWED_SUBTYPES:
        errors.append("subtype_not_allowed")

    if packet.get("draft_origin") is not None and packet.get("draft_origin") not in ALLOWED_DRAFT_ORIGINS:
        errors.append("draft_origin_not_allowed")

    lrb = packet.get("linked_research_brief")
    if not isinstance(lrb, dict):
        errors.append("linked_research_brief_missing_or_invalid")
    else:
        if not lrb.get("brief_id"):
            errors.append("linked_research_brief_missing_brief_id")
        if lrb.get("brief_validated") is not True:
            errors.append("linked_research_brief_not_validated")

    sr = packet.get("safety_review")
    if not isinstance(sr, dict):
        errors.append("safety_review_missing_or_invalid")
        sr = {}
    for flag in REQUIRED_SAFETY_FALSE:
        if sr.get(flag) is not False:
            errors.append("safety_flag_must_be_false:%s" % flag)
    for flag in REQUIRED_SAFETY_TRUE:
        if sr.get(flag) is not True:
            errors.append("safety_flag_must_be_true:%s" % flag)

    aou = packet.get("allowed_output_use")
    if isinstance(aou, list):
        if "not_public_postable" not in aou:
            errors.append("allowed_output_use_missing_not_public_postable")
        if "local_review_only" not in aou:
            errors.append("allowed_output_use_missing_local_review_only")
    elif aou is not None:
        errors.append("allowed_output_use_must_be_list")

    # draft_text guardrail scans.
    draft_text = str(packet.get("draft_text", ""))
    if _scan_forbidden_language(draft_text):
        errors.append("draft_text_forbidden_language")
    if _scan_alpha_implication(draft_text):
        errors.append("draft_text_implies_alpha_output")

    errors.extend(_validate_claim_reviews(packet))
    errors.extend(_validate_verdict(packet, errors))

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}



def _validate_claim_reviews(packet):
    errors = []

    # Build set of source_ids declared in source_references_used.
    declared_sources = set()
    srefs = packet.get("source_references_used")
    if isinstance(srefs, list):
        for sref in srefs:
            if isinstance(sref, dict) and sref.get("source_id"):
                declared_sources.add(sref["source_id"])

    claims = packet.get("claim_reviews")
    if isinstance(claims, list):
        for i, cl in enumerate(claims):
            if not isinstance(cl, dict):
                errors.append("claim_review_not_object:%d" % i)
                continue
            cid = cl.get("claim_id", str(i))
            ctype = cl.get("claim_type")
            risk = cl.get("risk_level")
            ctext = str(cl.get("claim_text", ""))

            if ctype not in ALLOWED_CLAIM_TYPES:
                errors.append("claim_type_not_allowed:%s" % cid)
            if ctype == "forbidden_claim":
                errors.append("claim_is_forbidden_claim:%s" % cid)

            if risk not in ALLOWED_RISK_LEVELS:
                errors.append("risk_level_not_allowed:%s" % cid)
            if risk == "blocked":
                errors.append("risk_level_blocked:%s" % cid)

            if ctype in CITATION_REQUIRED_CLAIM_TYPES:
                if cl.get("has_citation") is not True:
                    errors.append("claim_missing_citation:%s" % cid)
                cl_sources = cl.get("source_ids") or []
                if not cl_sources:
                    errors.append("claim_missing_source_ids:%s" % cid)
                for sid in cl_sources:
                    if sid not in declared_sources:
                        errors.append("claim_source_not_in_brief:%s" % sid)
                if cl.get("source_present_in_brief") is False:
                    errors.append("claim_source_present_in_brief_false:%s" % cid)

            if _scan_forbidden_language(ctext):
                errors.append("claim_forbidden_language:%s" % cid)
            if _scan_alpha_implication(ctext):
                errors.append("claim_implies_alpha_output:%s" % cid)
    elif claims is not None:
        errors.append("claim_reviews_must_be_list")

    return errors


def _validate_verdict(packet, prior_errors):
    errors = []
    verdict = packet.get("verdict")
    if not isinstance(verdict, dict):
        errors.append("verdict_missing_or_invalid")
        return errors
    status = verdict.get("status")
    if status not in ALLOWED_VERDICT_STATUS:
        errors.append("verdict_status_not_allowed")
    # A pass verdict cannot coexist with blocking issues found elsewhere.
    if status == "local_review_pass" and prior_errors:
        errors.append("verdict_pass_with_blocking_issues")
    return errors


def validate_packet_file(path):
    with open(path, "r", encoding="utf-8") as f:
        packet = json.load(f)
    return validate_packet(packet)
