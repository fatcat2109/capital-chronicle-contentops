"""Local-only pre-alpha LLM prompt pack + style profile validators (Task 0096).

Deterministic, repo-local. Validates static prompt packs, style profiles, and
editorial rubrics that may LATER guide LLM-assisted drafting. This module makes
NO network / provider / LLM / search / platform / credential access. It never
posts, never reads `.env`, and never permits public-postable, publish-ready,
provider-call, or live-execution states.

Forbidden-language and alpha-implication scans are reused from
grounded_research_brief to keep a single source of truth. Prompt templates that
ask a model to INVENT data, prices, forecasts, source IDs, or market claims are
rejected here.
"""

import json
import os
import re

from live_contentops.grounded_research_brief import (
    _scan_forbidden_language,
    _scan_alpha_implication,
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
PROMPT_PACK_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_prompt_pack.schema.json")
STYLE_PROFILE_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_style_profile.schema.json")
EDITORIAL_RUBRIC_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_editorial_rubric.schema.json")

ALLOWED_CONTENT_TYPES = {
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
    "build_in_public",
    "macro_education",
    "product_update",
    "market_note",
}

ALLOWED_SOURCE_TYPES = {"general_process", "product_update", "artifact_backed"}

ALLOWED_PLATFORM_FAMILIES = {"x", "linkedin", "threads", "newsletter", "generic"}

# Marketing/positioning framing that must never appear in a prompt pack.
FORBIDDEN_FRAMING_PATTERNS = [
    r"bloomberg\s+replacement",
    r"replace\s+bloomberg",
    r"trading\s+bot",
    r"signal\s+service",
    r"execution\s+engine",
    r"guaranteed\s+(forecast|prediction|return)",
]

# Prompt templates that instruct the model to fabricate are rejected.
INVENT_INSTRUCTION_PATTERNS = [
    r"\binvent\b",
    r"\bmake\s+up\b",
    r"\bfabricate\b",
    r"\bhallucinate\b",
    r"\bguess\s+(the\s+)?(price|number|figure|data|forecast)",
    r"\b(create|generate|produce)\s+(fake|fictional|synthetic)\s+(data|prices|forecasts|source\s+ids?|market\s+claims?)",
    r"\bestimate\s+(a\s+)?(price\s+target|forecast)\s+(if|when)\s+unknown",
    r"\bfill\s+in\s+(missing\s+)?(numbers|data|sources)\b",
]


def load_prompt_pack_schema():
    with open(os.path.abspath(PROMPT_PACK_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_style_profile_schema():
    with open(os.path.abspath(STYLE_PROFILE_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_editorial_rubric_schema():
    with open(os.path.abspath(EDITORIAL_RUBRIC_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_forbidden_framing(text):
    hits = []
    low = text.lower()
    for pat in FORBIDDEN_FRAMING_PATTERNS:
        if re.search(pat, low):
            hits.append(pat)
    return hits


def _scan_invent_instructions(text):
    hits = []
    low = text.lower()
    for pat in INVENT_INSTRUCTION_PATTERNS:
        if re.search(pat, low):
            hits.append(pat)
    return hits


def _prompt_pack_scan_text(pack):
    parts = [
        str(pack.get("system_instructions", "")),
        str(pack.get("user_prompt_template", "")),
    ]
    for fc in pack.get("forbidden_claims") or []:
        # forbidden_claims is a guardrail LIST (describing what NOT to do); it is
        # intentionally excluded from the forbidden-language scan to avoid
        # flagging the guardrail text itself.
        pass
    for d in pack.get("required_disclaimers") or []:
        parts.append(str(d))
    return "\n".join(parts)



def validate_prompt_pack(pack):
    """Return {"valid": bool, "errors": [codes], "warnings": [codes]}.

    Deterministic. errors block the prompt pack.
    """
    errors = []
    warnings = []

    if not isinstance(pack, dict):
        return {"valid": False, "errors": ["prompt_pack_not_object"], "warnings": []}

    required = [
        "prompt_pack_id", "intended_content_types", "allowed_source_types",
        "system_instructions", "user_prompt_template", "required_context_fields",
        "forbidden_claims", "required_disclaimers", "style_profile_id",
        "editorial_rubric_id", "output_contract",
    ]
    for field in required:
        if field not in pack:
            errors.append("missing_field:%s" % field)

    for ct in pack.get("intended_content_types") or []:
        if ct not in ALLOWED_CONTENT_TYPES:
            errors.append("content_type_not_allowed:%s" % ct)
    for st in pack.get("allowed_source_types") or []:
        if st not in ALLOWED_SOURCE_TYPES:
            errors.append("source_type_not_allowed:%s" % st)

    # Safety flags pinned to the non-publishing, non-live, no-provider posture.
    if pack.get("requires_manual_review") is not True:
        errors.append("requires_manual_review_must_be_true")
    if pack.get("provider_call_allowed_now") is not False:
        errors.append("provider_call_allowed_now_must_be_false")
    if pack.get("public_postable_default") is not False:
        errors.append("public_postable_default_must_be_false")
    if pack.get("live_execution_allowed_now") is not False:
        errors.append("live_execution_allowed_now_must_be_false")

    # Text guardrail scans over system instructions + user prompt template.
    scan_text = _prompt_pack_scan_text(pack)
    if _scan_forbidden_language(scan_text):
        errors.append("prompt_forbidden_language")
    if _scan_alpha_implication(scan_text):
        errors.append("prompt_implies_alpha_output")
    if _scan_forbidden_framing(scan_text):
        errors.append("prompt_forbidden_framing")
    if _scan_invent_instructions(scan_text):
        errors.append("prompt_invents_data_or_claims")

    # Output contract must align with the 0095 draft/packet shape and stay safe.
    errors.extend(_validate_output_contract(pack.get("output_contract")))

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def validate_style_profile(profile):
    """Validate a style profile. Deterministic. errors block."""
    errors = []
    if not isinstance(profile, dict):
        return {"valid": False, "errors": ["style_profile_not_object"], "warnings": []}

    required = [
        "style_profile_id", "audience", "tone", "allowed_voice",
        "forbidden_voice", "hook_patterns", "body_patterns", "cta_patterns",
        "platform_family_adaptations", "max_risk_level",
        "default_limitations_language",
    ]
    for field in required:
        if field not in profile:
            errors.append("missing_field:%s" % field)

    if profile.get("no_signal_service_framing") is not True:
        errors.append("no_signal_service_framing_must_be_true")
    if profile.get("no_financial_advice") is not True:
        errors.append("no_financial_advice_must_be_true")

    if profile.get("max_risk_level") not in ("low", "medium", "high"):
        errors.append("max_risk_level_not_allowed")

    adaptations = profile.get("platform_family_adaptations") or {}
    if isinstance(adaptations, dict):
        for pf in adaptations:
            if pf not in ALLOWED_PLATFORM_FAMILIES:
                errors.append("platform_family_not_allowed:%s" % pf)

    # Scan author-facing voice/pattern text (not the forbidden_voice guardrail list).
    scan_parts = [str(profile.get("tone", ""))]
    for key in ("allowed_voice", "hook_patterns", "body_patterns", "cta_patterns"):
        for item in profile.get(key) or []:
            scan_parts.append(str(item))
    if isinstance(adaptations, dict):
        for v in adaptations.values():
            scan_parts.append(str(v))
    scan_text = "\n".join(scan_parts)
    if _scan_forbidden_language(scan_text):
        errors.append("style_forbidden_language")
    if _scan_alpha_implication(scan_text):
        errors.append("style_implies_alpha_output")
    if _scan_forbidden_framing(scan_text):
        errors.append("style_forbidden_framing")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": []}


def validate_style_profile_file(path):
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    return validate_style_profile(profile)


def validate_editorial_rubric(rubric):
    """Validate an editorial rubric. Deterministic. errors block."""
    errors = []
    if not isinstance(rubric, dict):
        return {"valid": False, "errors": ["editorial_rubric_not_object"], "warnings": []}

    if "editorial_rubric_id" not in rubric:
        errors.append("missing_field:editorial_rubric_id")
    if "checklist" not in rubric:
        errors.append("missing_field:checklist")

    must_be_true = [
        "requires_content_type_classification",
        "requires_source_artifact_ids_or_general_process_marker",
        "requires_limitations_and_freshness_for_market_note",
        "requires_educational_only_for_market_content",
        "rejects_fake_alpha_claims",
        "rejects_unverified_numeric_claims",
        "rejects_financial_advice_or_signal_language",
        "requires_manual_review_before_publish",
    ]
    for field in must_be_true:
        if rubric.get(field) is not True:
            errors.append("%s_must_be_true" % field)

    if rubric.get("public_postable_until_manual_approval") is not False:
        errors.append("public_postable_until_manual_approval_must_be_false")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": []}


def validate_editorial_rubric_file(path):
    with open(path, "r", encoding="utf-8") as f:
        rubric = json.load(f)
    return validate_editorial_rubric(rubric)


def summary():
    """Deterministic local capability summary for the CLI. Schema reads only."""
    return {
        "status": "pre-alpha prompt pack and style profile active",
        "local_only": True,
        "design_only": True,
        "prompt_pack_enabled": True,
        "style_profile_enabled": True,
        "editorial_rubric_enabled": True,
        "supported_content_types": sorted(ALLOWED_CONTENT_TYPES),
        "supported_platform_families": sorted(ALLOWED_PLATFORM_FAMILIES),
        "provider_call_made": False,
        "provider_call_allowed_now": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "live_execution_allowed_now": False,
        "manual_review_required": True,
        "aligns_with_0095_output_contract": True,
    }


def _validate_output_contract(contract):
    errors = []
    if not isinstance(contract, dict):
        return ["output_contract_not_object"]
    produces = contract.get("produces")
    if produces not in ("draft_candidate", "editorial_packet_input"):
        errors.append("output_contract_produces_not_allowed")
    for pf in contract.get("platform_families") or []:
        if pf not in ALLOWED_PLATFORM_FAMILIES:
            errors.append("output_contract_platform_family_not_allowed:%s" % pf)
    if contract.get("public_postable") is not False:
        errors.append("output_contract_public_postable_must_be_false")
    if contract.get("requires_manual_review") is not True:
        errors.append("output_contract_requires_manual_review_must_be_true")
    return errors


def validate_prompt_pack_file(path):
    with open(path, "r", encoding="utf-8") as f:
        pack = json.load(f)
    return validate_prompt_pack(pack)
