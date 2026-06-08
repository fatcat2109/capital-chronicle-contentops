"""Local-only grounded research brief validation (Task 0076).

Deterministic, repo-local validation of OPERATOR-SUPPLIED grounded research
briefs for the pre-alpha Grounded News / Research Context Lane documented in
docs/PRE_ALPHA_GENERAL_PROCESS_AND_GROUNDED_NEWS_MASTER_PLAN_AFTER_0075.md.

This module performs NO network/search/provider/LLM/platform/credential access.
It only validates manually supplied JSON brief structures already present on disk.
It never generates public-ready content and never marks anything publish-ready.
"""

import json
import os
import re

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "grounded_research_brief.schema.json"
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
}

ALLOWED_CLAIM_TYPES = {
    "first_party_philosophy",
    "evergreen_education",
    "cited_factual_claim",
    "current_factual_claim",
    "market_sensitive_context",
    "forbidden_claim",
}

ALLOWED_CLAIM_RISK = {"low", "medium", "high", "blocked"}

CITATION_REQUIRED_CLAIM_TYPES = {"cited_factual_claim", "current_factual_claim"}

# Direct market-action / signal / execution language. Guardrail is intentionally
# strict: matches block the brief. Word-boundary, case-insensitive.
FORBIDDEN_LANGUAGE_PATTERNS = [
    r"\bbuy\b", r"\bsell\b", r"\bhold\b", r"\bgo long\b", r"\bgo short\b",
    r"\blong\b", r"\bshort\b", r"\bentry\b", r"\bexit\b",
    r"\bprice target\b", r"\btarget price\b", r"\bposition siz", r"\bbroker\b",
    r"\border routing\b", r"\bexecution\b", r"\bsignal\b",
    r"\bmodel predicts\b", r"\bmodel says\b",
]

# Phrases implying Capital Chronicle already produces alpha/forecast artifacts.
ALPHA_IMPLICATION_PATTERNS = [
    r"capital chronicle('?s)?\s+alpha",
    r"\balpha\s+(says|output|model|signal)\b",
    r"capital chronicle('?s)?\s+forecast",
    r"\bartifact_id\b",
    r"\bdqr_status\b",
    r"our\s+model\s+predicts",
]

REQUIRED_SOURCE_FIELDS = [
    "source_id", "title", "url", "publisher_or_author",
    "source_type", "credibility_note", "freshness_note", "limitation_note",
]

REQUIRED_SAFETY_REVIEW_FALSE = [
    "public_postable", "artifact_backed", "publish_ready",
    "provider_call_used_by_repo", "search_call_used_by_repo",
    "platform_action_used_by_repo",
]

REQUIRED_SAFETY_REVIEW_TRUE = [
    "manual_review_required", "no_financial_advice",
    "no_signal_language", "no_execution_language",
]



def load_schema():
    with open(os.path.abspath(SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_forbidden_language(text):
    hits = []
    low = text.lower()
    for pat in FORBIDDEN_LANGUAGE_PATTERNS:
        if re.search(pat, low):
            hits.append(pat)
    return hits


def _scan_alpha_implication(text):
    hits = []
    low = text.lower()
    for pat in ALPHA_IMPLICATION_PATTERNS:
        if re.search(pat, low):
            hits.append(pat)
    return hits


def validate_brief(brief):
    """Return {"valid": bool, "errors": [codes], "warnings": [codes]}.

    Deterministic. errors block the brief; warnings are advisory only.
    """
    errors = []
    warnings = []

    if not isinstance(brief, dict):
        return {"valid": False, "errors": ["brief_not_object"], "warnings": []}

    for field in ("brief_id", "lane", "subtype", "title", "operator_supplied",
                  "source_collection_method", "sources", "claims",
                  "safety_review", "allowed_output_use"):
        if field not in brief:
            errors.append("missing_field:%s" % field)

    if "lane" in brief and brief.get("lane") != ALLOWED_LANE:
        errors.append("lane_must_be_pre_alpha_general_process")

    if brief.get("subtype") is not None and brief.get("subtype") not in ALLOWED_SUBTYPES:
        errors.append("subtype_not_allowed")

    if brief.get("operator_supplied") is not True:
        errors.append("operator_supplied_must_be_true")

    scm = str(brief.get("source_collection_method", "")).lower()
    if scm and ("repo" in scm and "fetch" in scm):
        errors.append("source_collection_method_implies_repo_fetch")
    if scm and not any(k in scm for k in ("manual", "operator", "supplied", "external")):
        warnings.append("source_collection_method_unclear")

    sr = brief.get("safety_review")
    if not isinstance(sr, dict):
        errors.append("safety_review_missing_or_invalid")
        sr = {}
    for flag in REQUIRED_SAFETY_REVIEW_FALSE:
        if sr.get(flag) is not False:
            errors.append("safety_flag_must_be_false:%s" % flag)
    for flag in REQUIRED_SAFETY_REVIEW_TRUE:
        if sr.get(flag) is not True:
            errors.append("safety_flag_must_be_true:%s" % flag)

    aou = brief.get("allowed_output_use")
    if isinstance(aou, list):
        if "not_public_postable" not in aou:
            errors.append("allowed_output_use_missing_not_public_postable")
        if not any(x in aou for x in ("research_context_only", "local_review_only")):
            errors.append("allowed_output_use_missing_review_only")
    elif aou is not None:
        errors.append("allowed_output_use_must_be_list")

    errors.extend(_validate_sources_and_claims(brief))
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}



def _validate_sources_and_claims(brief):
    errors = []

    source_ids = set()
    sources = brief.get("sources")
    if isinstance(sources, list):
        for i, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append("source_not_object:%d" % i)
                continue
            for rf in REQUIRED_SOURCE_FIELDS:
                if not src.get(rf):
                    errors.append("source_missing_field:%s" % rf)
            if not (src.get("publication_date") or src.get("accessed_date")):
                errors.append("source_missing_date:%s" % src.get("source_id", i))
            if src.get("source_id"):
                source_ids.add(src["source_id"])
    elif sources is not None:
        errors.append("sources_must_be_list")

    claims = brief.get("claims")
    if isinstance(claims, list):
        for i, cl in enumerate(claims):
            if not isinstance(cl, dict):
                errors.append("claim_not_object:%d" % i)
                continue
            cid = cl.get("claim_id", str(i))
            ctype = cl.get("claim_type")
            crisk = cl.get("claim_risk")
            ctext = str(cl.get("claim_text", ""))

            if ctype not in ALLOWED_CLAIM_TYPES:
                errors.append("claim_type_not_allowed:%s" % cid)
            if ctype == "forbidden_claim":
                errors.append("claim_is_forbidden_claim:%s" % cid)

            if crisk not in ALLOWED_CLAIM_RISK:
                errors.append("claim_risk_not_allowed:%s" % cid)
            if crisk == "blocked":
                errors.append("claim_risk_blocked:%s" % cid)

            if ctype in CITATION_REQUIRED_CLAIM_TYPES:
                if cl.get("requires_citation") is not True:
                    errors.append("claim_requires_citation_flag:%s" % cid)
                if cl.get("has_citation") is not True:
                    errors.append("claim_missing_citation:%s" % cid)
                cl_sources = cl.get("source_ids") or []
                if not cl_sources:
                    errors.append("claim_missing_source_ids:%s" % cid)
                for sid in cl_sources:
                    if sid not in source_ids:
                        errors.append("claim_source_id_unknown:%s" % sid)

            if _scan_forbidden_language(ctext):
                errors.append("claim_forbidden_language:%s" % cid)
            if _scan_alpha_implication(ctext):
                errors.append("claim_implies_alpha_output:%s" % cid)
    elif claims is not None:
        errors.append("claims_must_be_list")

    return errors


def validate_brief_file(path):
    with open(path, "r", encoding="utf-8") as f:
        brief = json.load(f)
    return validate_brief(brief)

    return hits
