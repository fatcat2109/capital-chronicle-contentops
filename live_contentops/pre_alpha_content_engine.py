"""Local-only pre-alpha content engine and editorial packet builder (Task 0095).

Deterministic, repo-local. Consumes safe operator/fixture-supplied content
SEEDS already present on disk and builds editorial packets with draft
candidates for future MANUAL review.

This module performs NO network/search/provider/LLM/platform/credential access.
It NEVER posts, NEVER fetches, NEVER reads `.env`, NEVER produces public-postable
or publish-ready output, and NEVER emits financial advice / signal / execution
language or fake Capital Chronicle alpha output.

Guardrail scan helpers are reused from grounded_research_brief to keep a single
source of truth for forbidden-language and alpha-implication detection.
"""

import json
import os
import re

from live_contentops.grounded_research_brief import (
    _scan_forbidden_language,
    _scan_alpha_implication,
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
SEED_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_content_seed.schema.json")
DRAFT_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_draft_candidate.schema.json")
PACKET_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_editorial_packet.schema.json")

# Static deterministic timestamp for fixture/demo reproducibility.
STATIC_TIMESTAMP = "2026-01-01T00:00:00Z"

ALLOWED_CONTENT_TYPES = {
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
    "build_in_public",
    "macro_education",
    "product_update",
    "market_note",
}

ALLOWED_CONTENT_SOURCE_TYPES = {
    "general_process",
    "product_update",
    "artifact_backed",
}

ALLOWED_PLATFORM_FAMILIES = ["x", "linkedin", "threads", "newsletter", "generic"]

# Content types that assert a claim backed by a real Capital Chronicle artifact
# and therefore REQUIRE source_artifact_ids unless flagged general/process.
ARTIFACT_BACKED_CONTENT_TYPES = {
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
}

# Unverified numeric market claim detector: a number (optionally %, $, bps, pts)
# adjacent to market direction/level wording. Deterministic, case-insensitive.
NUMERIC_MARKET_CLAIM_PATTERNS = [
    r"\b\d+(\.\d+)?\s?%(\s+(gain|loss|upside|downside|rally|drop|move|return))",
    r"\b(up|down|rise|fall|rally|drop|gain|lose|surge|plunge)\s+\d+(\.\d+)?\s?%",
    r"\$\s?\d[\d,]*(\.\d+)?\s+(target|by\s+(eo\w+|year|month|q[1-4]))",
    r"\b\d+(\.\d+)?\s?(bps|basis points)\s+(cut|hike|move)",
    r"\bs&p\s+\d{3,}",
    r"\bdow\s+\d{4,}",
    r"\bwill\s+(hit|reach|test)\s+\$?\d",
]


def load_seed_schema():
    with open(os.path.abspath(SEED_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_draft_schema():
    with open(os.path.abspath(DRAFT_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_packet_schema():
    with open(os.path.abspath(PACKET_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_numeric_market_claim(text):
    hits = []
    low = text.lower()
    for pat in NUMERIC_MARKET_CLAIM_PATTERNS:
        if re.search(pat, low):
            hits.append(pat)
    return hits



def validate_seed(seed):
    """Return {"valid": bool, "errors": [codes], "warnings": [codes]}.

    Deterministic. errors block the seed; warnings are advisory only.
    """
    errors = []
    warnings = []

    if not isinstance(seed, dict):
        return {"valid": False, "errors": ["seed_not_object"], "warnings": []}

    for field in ("seed_id", "content_type", "content_source_type",
                  "is_general_process_content", "title", "key_points"):
        if field not in seed:
            errors.append("missing_field:%s" % field)

    ctype = seed.get("content_type")
    if ctype is not None and ctype not in ALLOWED_CONTENT_TYPES:
        errors.append("content_type_not_allowed")

    cstype = seed.get("content_source_type")
    if cstype is not None and cstype not in ALLOWED_CONTENT_SOURCE_TYPES:
        errors.append("content_source_type_not_allowed")

    is_gp = seed.get("is_general_process_content")
    artifact_ids = seed.get("source_artifact_ids") or []

    # Artifact-backed claims require source artifact IDs unless flagged
    # general/process content.
    if cstype == "artifact_backed" or ctype in ARTIFACT_BACKED_CONTENT_TYPES:
        if is_gp is not True and not artifact_ids:
            errors.append("artifact_backed_requires_source_artifact_ids")

    # A seed claiming artifact_backed source type cannot also call itself
    # general/process content. That would mask the missing-artifact guardrail.
    if cstype == "artifact_backed" and is_gp is True:
        errors.append("artifact_backed_cannot_be_general_process")

    # Forecast readiness can only be claimed when explicitly supported by source.
    if seed.get("forecast_readiness_claim_requested") is True:
        if seed.get("forecast_readiness_supported_by_source") is not True:
            errors.append("forecast_readiness_not_supported_by_source")
        if not artifact_ids:
            errors.append("forecast_readiness_requires_source_artifact_ids")
        dss = seed.get("data_sufficiency_status")
        if dss in ("insufficient", "missing", "proxy_only", "partial"):
            errors.append("forecast_readiness_blocked_by_data_sufficiency")

    # Text guardrail scans over title + key points + limitations.
    scan_text = _seed_scan_text(seed)
    if _scan_forbidden_language(scan_text):
        errors.append("seed_forbidden_language")
    if _scan_alpha_implication(scan_text):
        errors.append("seed_implies_alpha_output")
    if _scan_numeric_market_claim(scan_text):
        errors.append("seed_unverified_numeric_market_claim")

    # market_note specific guardrails.
    if ctype == "market_note":
        errors.extend(_validate_market_note_seed(seed))

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _seed_scan_text(seed):
    parts = [str(seed.get("title", ""))]
    for kp in seed.get("key_points") or []:
        parts.append(str(kp))
    for lim in seed.get("limitations") or []:
        parts.append(str(lim))
    return "\n".join(parts)


def _validate_market_note_seed(seed):
    errors = []
    if not (seed.get("limitations") or []):
        errors.append("market_note_missing_limitations")
    if not seed.get("freshness_label"):
        errors.append("market_note_missing_freshness_label")
    # Educational/general posture: a market note must be general/process content
    # (Capital Chronicle has no alpha artifacts yet).
    if seed.get("is_general_process_content") is not True:
        errors.append("market_note_must_be_general_process")
    dss = seed.get("data_sufficiency_status")
    if dss in ("proxy_only", "missing", "insufficient") and not (seed.get("limitations") or []):
        errors.append("market_note_must_label_degraded_data")
    return errors


def validate_seed_file(path):
    with open(path, "r", encoding="utf-8") as f:
        seed = json.load(f)
    return validate_seed(seed)



def _make_draft_candidate(seed, platform_family, index):
    """Deterministically build one draft candidate from a validated seed.

    Body is assembled ONLY from seed-supplied text. The engine does not invent
    market claims, numbers, or alpha output.
    """
    ctype = seed["content_type"]
    title = str(seed.get("title", "")).strip()
    key_points = [str(p).strip() for p in (seed.get("key_points") or [])]
    limitations = [str(p).strip() for p in (seed.get("limitations") or [])]
    artifact_ids = list(seed.get("source_artifact_ids") or [])
    educational_only = ctype == "market_note" or bool(seed.get("is_general_process_content"))

    hook = title
    body_lines = []
    for kp in key_points:
        body_lines.append("- " + kp)
    if limitations:
        body_lines.append("")
        body_lines.append("Limitations:")
        for lim in limitations:
            body_lines.append("- " + lim)
    if ctype == "market_note":
        fl = str(seed.get("freshness_label", "")).strip()
        if fl:
            body_lines.append("")
            body_lines.append("Freshness: " + fl)
        body_lines.append("Educational/general context only. Not advice.")
    body = "\n".join(body_lines)

    cta = "Manual review required before any use."

    return {
        "draft_id": "%s_draft_%s_%d" % (seed["seed_id"], platform_family, index),
        "platform_family": platform_family,
        "hook": hook,
        "body": body,
        "cta": cta,
        "content_type": ctype,
        "source_artifact_ids": artifact_ids,
        "limitations": limitations,
        "educational_only": educational_only,
        "public_postable": False,
        "requires_manual_review": True,
    }


def build_editorial_packet(seed):
    """Build a deterministic editorial packet from a content seed.

    If the seed fails guardrail validation, the packet is emitted with
    guardrail_status="blocked", blocked_reasons populated, and NO draft
    candidates. Safety flags are always pinned to the non-publishing,
    non-live posture regardless of input.
    """
    result = validate_seed(seed)
    seed_id = seed.get("seed_id") if isinstance(seed, dict) else None
    ctype = seed.get("content_type") if isinstance(seed, dict) else None
    cstype = seed.get("content_source_type") if isinstance(seed, dict) else None

    platform_families = []
    if isinstance(seed, dict):
        platform_families = [
            p for p in (seed.get("target_platform_families") or [])
            if p in ALLOWED_PLATFORM_FAMILIES
        ]
    if not platform_families:
        platform_families = ["generic"]

    draft_candidates = []
    if result["valid"]:
        for i, pf in enumerate(platform_families):
            draft_candidates.append(_make_draft_candidate(seed, pf, i))

    guardrail_status = "pass" if result["valid"] else "blocked"

    packet = {
        "editorial_packet_id": "packet_%s" % (seed_id or "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "input_seed_id": seed_id,
        "content_type": ctype,
        "content_source_type": cstype,
        "source_artifact_ids": list(seed.get("source_artifact_ids") or []) if isinstance(seed, dict) else [],
        "is_general_process_content": bool(seed.get("is_general_process_content")) if isinstance(seed, dict) else False,
        "limitations": list(seed.get("limitations") or []) if isinstance(seed, dict) else [],
        "freshness_label": seed.get("freshness_label") if isinstance(seed, dict) else None,
        "data_sufficiency_status": seed.get("data_sufficiency_status") if isinstance(seed, dict) else None,
        "forecast_readiness_claim_allowed": False,
        "draft_candidates": draft_candidates,
        "review_required": True,
        "manual_publish_only": True,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "guardrail_status": guardrail_status,
        "blocked_reasons": result["errors"],
    }
    return packet


def build_editorial_packet_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        seed = json.load(f)
    return build_editorial_packet(seed)


def validate_draft_candidate(draft):
    """Validate a draft candidate against the non-publishing posture."""
    errors = []
    if not isinstance(draft, dict):
        return {"valid": False, "errors": ["draft_not_object"], "warnings": []}

    for field in ("draft_id", "platform_family", "hook", "body", "content_type"):
        if field not in draft:
            errors.append("missing_field:%s" % field)

    if draft.get("platform_family") not in ALLOWED_PLATFORM_FAMILIES:
        errors.append("platform_family_not_allowed")
    if draft.get("content_type") not in ALLOWED_CONTENT_TYPES:
        errors.append("content_type_not_allowed")
    if draft.get("public_postable") is not False:
        errors.append("public_postable_must_be_false")
    if draft.get("requires_manual_review") is not True:
        errors.append("requires_manual_review_must_be_true")

    scan_text = "\n".join([
        str(draft.get("hook", "")),
        str(draft.get("body", "")),
        str(draft.get("cta", "")),
    ])
    if _scan_forbidden_language(scan_text):
        errors.append("draft_forbidden_language")
    if _scan_alpha_implication(scan_text):
        errors.append("draft_implies_alpha_output")
    if _scan_numeric_market_claim(scan_text):
        errors.append("draft_unverified_numeric_market_claim")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": []}


def summary():
    """Deterministic local capability summary for the CLI. Schema reads only."""
    return {
        "status": "pre-alpha content engine active",
        "local_only": True,
        "design_only": True,
        "engine_enabled": True,
        "supported_content_types": sorted(ALLOWED_CONTENT_TYPES),
        "supported_platform_families": list(ALLOWED_PLATFORM_FAMILIES),
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "manual_review_required": True,
        "forecast_readiness_claim_allowed_by_default": False,
    }
