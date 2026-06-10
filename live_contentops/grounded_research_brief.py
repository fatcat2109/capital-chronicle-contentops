import json
import os
import re
import jsonschema

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "grounded_research_brief_packet.schema.json"
)

ALLOWED_LANE = "pre_alpha_general_process"

FORBIDDEN_LANGUAGE_PATTERNS = [
    r"\bbuy\b", r"\bsell\b", r"\bhold\b", r"\bgo long\b", r"\bgo short\b",
    r"\blong\b", r"\bshort\b", r"\bentry\b", r"\bexit\b",
    r"\bprice target\b", r"\btarget price\b", r"\bposition siz", r"\bbroker\b",
    r"\border routing\b", r"\bexecution\b", r"\bsignal\b",
    r"\bmodel predicts\b", r"\bmodel says\b",
]

ALPHA_IMPLICATION_PATTERNS = [
    r"capital chronicle('?s)?\s+alpha",
    r"\balpha\s+(says|output|model|signal)\b",
    r"capital chronicle('?s)?\s+forecast",
    r"\bartifact_id\b",
    r"\bdqr_status\b",
    r"our\s+model\s+predicts",
]

REQUIRED_SAFETY_REVIEW_FALSE = [
    "public_postable", "artifact_backed", "publish_ready", "auto_publish", "auto_approval",
    "provider_call_used_by_repo", "search_call_used_by_repo", "network_call_used_by_repo",
    "platform_action_used_by_repo", "credential_or_env_read_used", "raw_vendor_redistribution_allowed"
]

REQUIRED_SAFETY_REVIEW_TRUE = [
    "manual_review_required", "not_public_postable", "no_financial_advice",
    "no_signal_language", "no_execution_language"
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
    schema = load_schema()

    try:
        jsonschema.validate(instance=brief, schema=schema)
    except jsonschema.ValidationError as e:
        return {
            "valid": False,
            "errors": [f"Schema validation failed: {e.message}"],
            "packet_status": "blocked",
            "blocked_reasons": [f"Schema validation failed: {e.message}"]
        }

    reasons = []

    if brief.get("operator_supplied") is not True:
        reasons.append("operator_supplied_must_be_true")

    sr = brief.get("safety_review", {})
    for flag in REQUIRED_SAFETY_REVIEW_FALSE:
        if sr.get(flag) is True:
            reasons.append(f"safety_flag_must_be_false:{flag}")
    for flag in REQUIRED_SAFETY_REVIEW_TRUE:
        if sr.get(flag) is not True:
            reasons.append(f"safety_flag_must_be_true:{flag}")

    source_ids = set()
    sources = brief.get("sources", [])
    for src in sources:
        sid = src.get("source_id")
        if sid:
            source_ids.add(sid)
        if not src.get("url"):
            reasons.append(f"source_missing_url:{sid}")
        if not (src.get("publication_date") or src.get("accessed_date")):
            reasons.append(f"source_missing_date:{sid}")

    claims = brief.get("claims", [])
    for cl in claims:
        cid = cl.get("claim_id")
        ctype = cl.get("claim_type")
        crisk = cl.get("claim_risk")
        ctext = str(cl.get("claim_text", ""))

        if ctype == "forbidden_claim":
            reasons.append(f"claim_is_forbidden_claim:{cid}")

        if crisk == "blocked":
            reasons.append(f"claim_risk_blocked:{cid}")

        if ctype in ["cited_factual_claim", "current_factual_claim"]:
            if cl.get("requires_citation") is not True:
                reasons.append(f"claim_requires_citation_flag:{cid}")
            if cl.get("has_citation") is not True:
                reasons.append(f"claim_missing_citation:{cid}")
            cl_sources = cl.get("source_ids") or []
            if not cl_sources:
                reasons.append(f"claim_missing_source_ids:{cid}")
            for sid in cl_sources:
                if sid not in source_ids:
                    reasons.append(f"claim_source_id_unknown:{sid}")

        if _scan_forbidden_language(ctext):
            reasons.append(f"claim_forbidden_language:{cid}")
        if _scan_alpha_implication(ctext):
            reasons.append(f"claim_implies_alpha_output:{cid}")

    if reasons:
        return {
            "valid": False,
            "errors": reasons,
            "warnings": [],
            "packet_status": "blocked",
            "blocked_reasons": reasons
        }
    return {
        "valid": True,
        "errors": [],
        "warnings": [],
        "packet_status": "pass",
        "blocked_reasons": []
    }

def validate_brief_file(path):
    with open(path, "r", encoding="utf-8") as f:
        brief = json.load(f)
    return validate_brief(brief)

def summary():
    return {
        "packet_status": "pass",
        "source_count": 0,
        "claim_count": 0,
        "blocked_fixture_count": 5,
        "missing_citation_count": 0,
        "unsafe_flag_count": 11,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False
    }
