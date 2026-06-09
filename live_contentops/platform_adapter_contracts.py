"""Local-only platform adapter contracts and dry-run renderer (Task 0078).

Automation READINESS only. This module performs NO network/search/provider/LLM/
platform/credential access. It maps a valid review-only canonical social post
into deterministic per-platform DRY-RUN payload previews. It never posts,
schedules, replies, DMs, scrapes, or marks anything publish-ready/public-postable.

Platform limits here are CONSERVATIVE LOCAL PLACEHOLDERS, not verified official
truth. Official platform docs verification is deferred to Task 0081.
"""

import json
import os

from live_contentops.grounded_research_brief import (
    _scan_forbidden_language,
    _scan_alpha_implication,
)

CANONICAL_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "canonical_social_post.schema.json"
)
PAYLOAD_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "platform_dry_run_payload.schema.json"
)

CONSTRAINT_SOURCE = "local_placeholder_until_0081_official_docs_verification"

ALLOWED_LANE = "pre_alpha_general_process"

ALLOWED_APPROVAL_STATES = {"operator_review_required", "platform_dry_run_ready"}

# Conservative local placeholder capability registry. NOT verified official truth.
PLATFORM_REGISTRY = {
    "x": {
        "platform_id": "x",
        "display_name": "X",
        "supported_text_modes": ["short_post", "thread"],
        "supported_media_types": ["none", "image", "video", "link"],
        "text_length_policy": {"max_chars": 280, "constraint_source": CONSTRAINT_SOURCE},
        "media_requirement": {"constraint_source": CONSTRAINT_SOURCE},
        "live_api_status": "disabled",
        "credential_required_for_live": True,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "official_docs_verified": False,
    },
    "linkedin": {
        "platform_id": "linkedin",
        "display_name": "LinkedIn",
        "supported_text_modes": ["short_post", "long_post", "article"],
        "supported_media_types": ["none", "image", "video", "document", "link"],
        "text_length_policy": {"max_chars": 3000, "constraint_source": CONSTRAINT_SOURCE},
        "media_requirement": {"constraint_source": CONSTRAINT_SOURCE},
        "live_api_status": "disabled",
        "credential_required_for_live": True,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "official_docs_verified": False,
    },
    "telegram": {
        "platform_id": "telegram",
        "display_name": "Telegram",
        "supported_text_modes": ["short_post", "long_post"],
        "supported_media_types": ["none", "image", "video", "document", "link"],
        "text_length_policy": {"max_chars": 4096, "constraint_source": CONSTRAINT_SOURCE},
        "media_requirement": {"constraint_source": CONSTRAINT_SOURCE},
        "live_api_status": "disabled",
        "credential_required_for_live": True,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "official_docs_verified": False,
    },
    "facebook_page": {
        "platform_id": "facebook_page",
        "display_name": "Facebook Page",
        "supported_text_modes": ["short_post", "long_post"],
        "supported_media_types": ["none", "image", "video", "link"],
        "text_length_policy": {"max_chars": 5000, "constraint_source": CONSTRAINT_SOURCE},
        "media_requirement": {"constraint_source": CONSTRAINT_SOURCE},
        "live_api_status": "disabled",
        "credential_required_for_live": True,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "official_docs_verified": False,
    },
    "instagram": {
        "platform_id": "instagram",
        "display_name": "Instagram",
        "supported_text_modes": ["caption"],
        "supported_media_types": ["image", "video"],
        "text_length_policy": {"max_chars": 2200, "constraint_source": CONSTRAINT_SOURCE},
        "media_requirement": {
            "media_required": True,
            "note": "Instagram requires media; text-only is unsupported.",
            "constraint_source": CONSTRAINT_SOURCE,
        },
        "live_api_status": "disabled",
        "credential_required_for_live": True,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "official_docs_verified": False,
    },
    "tiktok": {
        "platform_id": "tiktok",
        "display_name": "TikTok",
        "supported_text_modes": ["caption"],
        "supported_media_types": ["video", "image"],
        "text_length_policy": {"max_chars": 2200, "constraint_source": CONSTRAINT_SOURCE},
        "media_requirement": {
            "media_required": True,
            "note": "TikTok requires video/photo media; text-only is unsupported.",
            "constraint_source": CONSTRAINT_SOURCE,
        },
        "live_api_status": "disabled",
        "credential_required_for_live": True,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "official_docs_verified": False,
    },
}

SUPPORTED_PLATFORMS = list(PLATFORM_REGISTRY.keys())



def load_canonical_schema():
    with open(CANONICAL_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_payload_schema():
    with open(PAYLOAD_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _text_for_scan(post):
    parts = [
        str(post.get("title", "")),
        str(post.get("summary", "")),
        str(post.get("body", "")),
    ]
    return "\n".join(parts)


def validate_canonical_post(post):
    """Deterministic safety validation of a canonical social post.

    Returns {"valid": bool, "errors": [str]}. Never mutates input. Never marks
    anything publish-ready or public-postable.
    """
    errors = []

    if post.get("lane") != ALLOWED_LANE:
        errors.append("lane_must_be_pre_alpha_general_process")

    if post.get("approval_state") not in ALLOWED_APPROVAL_STATES:
        errors.append("approval_state_must_be_review_or_dry_run_only")

    if post.get("public_postable") is not False:
        errors.append("public_postable_must_be_false")
    if post.get("live_posting_enabled") is not False:
        errors.append("live_posting_enabled_must_be_false")

    flags = post.get("safety_flags", {})
    for f in ("public_postable", "live_posting_enabled", "artifact_backed"):
        if flags.get(f) is not False:
            errors.append("safety_flag_must_be_false:%s" % f)
    for f in ("no_financial_advice", "no_signal_language", "no_execution_language"):
        if flags.get(f) is not True:
            errors.append("safety_flag_must_be_true:%s" % f)

    text = _text_for_scan(post)
    if _scan_forbidden_language(text):
        errors.append("forbidden_language_in_post")
    if _scan_alpha_implication(text):
        errors.append("post_implies_alpha_output")

    return {"valid": len(errors) == 0, "errors": errors}


def _media_types(post):
    media = post.get("media") or []
    types = set()
    for m in media:
        mt = m.get("media_type")
        if mt:
            types.add(mt)
    if not types:
        types.add("none")
    return types


def render_platform_payload(post, platform_id):
    """Render a deterministic DRY-RUN payload preview for one platform.

    Fails closed (render_status=blocked) on any safety or capability problem.
    Performs no network/credential access.
    """
    warnings = []
    blocking_errors = []

    reg = PLATFORM_REGISTRY.get(platform_id)
    if reg is None:
        blocking_errors.append("unknown_platform:%s" % platform_id)
        return _build_result(post, platform_id, {}, warnings, blocking_errors)

    # Safety gate first; an unsafe post never renders for any platform.
    safety = validate_canonical_post(post)
    if not safety["valid"]:
        blocking_errors.extend("post_safety:%s" % e for e in safety["errors"])

    text = post.get("body", "") or ""
    max_chars = reg["text_length_policy"].get("max_chars")
    if max_chars is not None and len(text) > max_chars:
        warnings.append(
            "text_exceeds_local_placeholder_limit:%d>%d" % (len(text), max_chars)
        )

    # Media capability check.
    post_media = _media_types(post)
    supported = set(reg["supported_media_types"])
    unsupported = post_media - supported
    if unsupported:
        blocking_errors.append(
            "unsupported_media_for_platform:%s" % ",".join(sorted(unsupported))
        )

    media_req = reg.get("media_requirement", {})
    if media_req.get("media_required") and post_media == {"none"}:
        blocking_errors.append("media_required_but_none_provided")

    payload_preview = {
        "platform_id": platform_id,
        "display_name": reg["display_name"],
        "text": text,
        "title": post.get("title", ""),
        "media_types": sorted(post_media),
        "source_references_used": post.get("source_references_used", []),
        "limitations": post.get("limitations", ""),
        "freshness_note": post.get("freshness_note", ""),
    }

    return _build_result(post, platform_id, payload_preview, warnings, blocking_errors)


def _build_result(post, platform_id, payload_preview, warnings, blocking_errors):
    render_status = "blocked" if blocking_errors else "rendered"
    return {
        "dry_run": True,
        "platform_id": platform_id,
        "post_id": post.get("post_id", ""),
        "payload_preview": payload_preview,
        "warnings": warnings,
        "blocking_errors": blocking_errors,
        "render_status": render_status,
        "constraint_source": CONSTRAINT_SOURCE,
        "requires_operator_approval": True,
        "not_public_postable": True,
        "live_posting_enabled": False,
        "credential_accessed": False,
        "network_accessed": False,
        "mock_endpoint_name": "mock://%s/dry_run" % platform_id,
    }


def render_all_platforms(post, platforms=None):
    """Render dry-run payloads for the given platforms (default: all six)."""
    if platforms is None:
        platforms = list(SUPPORTED_PLATFORMS)
    return {pid: render_platform_payload(post, pid) for pid in platforms}


def render_from_file(path, platforms=None):
    with open(path, "r", encoding="utf-8") as f:
        post = json.load(f)
    return render_all_platforms(post, platforms)


def summary():
    """Local capability summary. No external calls."""
    return {
        "status": "ok",
        "local_only": True,
        "advisory_only": True,
        "platform_adapter_contracts_enabled": True,
        "dry_run_renderer_enabled": True,
        "supported_platforms": list(SUPPORTED_PLATFORMS),
        "constraint_source": CONSTRAINT_SOURCE,
        "official_docs_verified": False,
        "live_posting_enabled": False,
        "credential_read_allowed_now": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "scraping_allowed_now": False,
        "network_accessed": False,
        "all_outputs_not_public_postable": True,
        "requires_operator_approval": True,
    }
