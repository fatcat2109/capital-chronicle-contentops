"""Local-only pre-alpha draft renderer + review queue integration (Task 0097).

Deterministic, repo-local. Connects a validated 0095 editorial packet with a
validated 0096 prompt pack / style profile / editorial rubric and emits review
queue items for future MANUAL human review.

This module performs NO network/search/provider/LLM/platform/credential access.
It NEVER posts, NEVER fetches, NEVER reads `.env`, NEVER produces public-postable
or publish-ready output, and NEVER emits financial advice / signal / execution
language or fake Capital Chronicle alpha output. It does NOT invent content: draft
bodies are rendered only from the editorial packet's own draft candidates, which
were built deterministically by the 0095 engine from operator/fixture seeds.

Guardrail scans are reused from grounded_research_brief (single source of truth),
plus the 0095 numeric-market-claim detector and the 0096 framing/invent scans.
"""

import json
import os

from live_contentops.grounded_research_brief import (
    _scan_forbidden_language,
    _scan_alpha_implication,
)
from live_contentops.pre_alpha_content_engine import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_PLATFORM_FAMILIES,
    STATIC_TIMESTAMP,
    _scan_numeric_market_claim,
    validate_draft_candidate,
)
from live_contentops.pre_alpha_prompt_pack import (
    validate_prompt_pack,
    validate_style_profile,
    validate_editorial_rubric,
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
RENDERED_PACKET_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_rendered_draft_packet.schema.json"
)
REVIEW_QUEUE_ITEM_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_review_queue_item.schema.json"
)

ALLOWED_PLATFORM_FAMILY_SET = set(ALLOWED_PLATFORM_FAMILIES)


def load_rendered_packet_schema():
    with open(os.path.abspath(RENDERED_PACKET_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_review_queue_item_schema():
    with open(os.path.abspath(REVIEW_QUEUE_ITEM_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def _editorial_packet_ok(packet):
    """The editorial packet must be a 0095 packet that passed and is non-publishing."""
    errors = []
    if not isinstance(packet, dict):
        return ["editorial_packet_not_object"]
    if packet.get("guardrail_status") != "pass":
        errors.append("editorial_packet_not_passing")
    if packet.get("review_required") is not True:
        errors.append("editorial_packet_review_required_must_be_true")
    if packet.get("manual_publish_only") is not True:
        errors.append("editorial_packet_manual_publish_only_must_be_true")
    if packet.get("platform_publish_allowed_now") is not False:
        errors.append("editorial_packet_platform_publish_must_be_false")
    if packet.get("live_execution_allowed_now") is not False:
        errors.append("editorial_packet_live_execution_must_be_false")
    if packet.get("forecast_readiness_claim_allowed") not in (False, None):
        errors.append("editorial_packet_forecast_readiness_must_not_be_allowed")
    if not packet.get("draft_candidates"):
        errors.append("editorial_packet_has_no_draft_candidates")
    return errors


def _config_ok(prompt_pack, style_profile, editorial_rubric):
    """Prompt pack / style profile / rubric must be present and validate (0096)."""
    errors = []
    if prompt_pack is None:
        errors.append("prompt_pack_not_validated")
    else:
        r = validate_prompt_pack(prompt_pack)
        if not r["valid"]:
            errors.append("prompt_pack_invalid")
    if style_profile is None:
        errors.append("style_profile_not_validated")
    else:
        r = validate_style_profile(style_profile)
        if not r["valid"]:
            errors.append("style_profile_invalid")
    if editorial_rubric is None:
        errors.append("editorial_rubric_not_validated")
    else:
        r = validate_editorial_rubric(editorial_rubric)
        if not r["valid"]:
            errors.append("editorial_rubric_invalid")
    return errors



def _draft_scan_text(draft):
    return "\n".join([
        str(draft.get("hook", "")),
        str(draft.get("body", "")),
        str(draft.get("cta", "")),
    ])


def _draft_guardrail_findings(draft):
    """Re-scan a draft candidate for forbidden content at render time.

    The 0095 engine already validates, but the renderer independently re-checks
    so an externally-supplied/tampered packet cannot smuggle unsafe content into
    the review queue. Returns a list of finding codes (empty == clean).
    """
    findings = []
    if draft.get("public_postable") is not False:
        findings.append("draft_public_postable_must_be_false")
    if draft.get("requires_manual_review") is not True:
        findings.append("draft_requires_manual_review_must_be_true")
    if draft.get("platform_family") not in ALLOWED_PLATFORM_FAMILY_SET:
        findings.append("draft_platform_family_not_allowed")
    if draft.get("content_type") not in ALLOWED_CONTENT_TYPES:
        findings.append("draft_content_type_not_allowed")
    scan_text = _draft_scan_text(draft)
    if _scan_forbidden_language(scan_text):
        findings.append("draft_forbidden_language")
    if _scan_alpha_implication(scan_text):
        findings.append("draft_implies_alpha_output")
    if _scan_numeric_market_claim(scan_text):
        findings.append("draft_unverified_numeric_market_claim")
    return findings


def _make_review_queue_item(rendered_packet_id, draft, packet, index):
    """Build one review queue item from a draft candidate. Pinned non-publishing."""
    findings = _draft_guardrail_findings(draft)
    # The validator is the authority on draft safety; mirror its verdict here.
    v = validate_draft_candidate(draft)
    if not v["valid"]:
        for code in v["errors"]:
            if code not in findings:
                findings.append(code)

    review_status = "needs_manual_review" if not findings else "blocked"

    return {
        "review_queue_item_id": "%s_rqi_%d" % (rendered_packet_id, index),
        "rendered_packet_id": rendered_packet_id,
        "draft_id": draft.get("draft_id"),
        "platform_family": draft.get("platform_family"),
        "content_type": draft.get("content_type"),
        "title_or_hook": str(draft.get("hook", "")),
        "body": str(draft.get("body", "")),
        "limitations": list(draft.get("limitations") or []),
        "source_artifact_ids": list(draft.get("source_artifact_ids") or []),
        "is_general_process_content": bool(packet.get("is_general_process_content")),
        "review_status": review_status,
        "reviewer_required": True,
        "publish_allowed_now": False,
        "manual_publish_only": True,
        "approval_required_for_future_publish": True,
        "guardrail_findings": findings,
    }


def render_review_packet(editorial_packet, prompt_pack=None,
                         style_profile=None, editorial_rubric=None):
    """Render a deterministic review-ready draft packet.

    Inputs:
      - editorial_packet: a 0095 editorial packet (must be valid + passing).
      - prompt_pack / style_profile / editorial_rubric: 0096 config objects
        (must all be present and validate).

    If any precondition fails, the packet is emitted with
    guardrail_status="blocked", blocked_reasons populated, and NO review queue
    items. Safety flags are always pinned to the non-publishing, non-live,
    no-provider posture regardless of input.
    """
    blocked_reasons = []
    blocked_reasons.extend(_editorial_packet_ok(editorial_packet))
    blocked_reasons.extend(_config_ok(prompt_pack, style_profile, editorial_rubric))

    packet = editorial_packet if isinstance(editorial_packet, dict) else {}
    source_packet_id = packet.get("editorial_packet_id") or "unknown"
    rendered_packet_id = "rendered_%s" % source_packet_id

    review_queue_items = []
    draft_candidates = list(packet.get("draft_candidates") or [])

    if not blocked_reasons:
        for i, draft in enumerate(draft_candidates):
            item = _make_review_queue_item(rendered_packet_id, draft, packet, i)
            review_queue_items.append(item)
            # If any rendered draft is itself blocked, surface it on the packet.
            if item["review_status"] == "blocked":
                blocked_reasons.append("draft_blocked:%s" % draft.get("draft_id"))

    guardrail_status = "pass" if not blocked_reasons else "blocked"
    if blocked_reasons:
        # Fail closed: do not expose review queue items from a blocked packet.
        review_queue_items = []
        draft_candidates = []

    return {
        "rendered_packet_id": rendered_packet_id,
        "created_at": STATIC_TIMESTAMP,
        "source_editorial_packet_id": source_packet_id,
        "source_seed_id": packet.get("input_seed_id"),
        "prompt_pack_id": (prompt_pack or {}).get("prompt_pack_id") if isinstance(prompt_pack, dict) else None,
        "style_profile_id": (style_profile or {}).get("style_profile_id") if isinstance(style_profile, dict) else None,
        "editorial_rubric_id": (editorial_rubric or {}).get("editorial_rubric_id") if isinstance(editorial_rubric, dict) else None,
        "content_type": packet.get("content_type"),
        "draft_candidates": draft_candidates,
        "review_queue_items": review_queue_items,
        "guardrail_status": guardrail_status,
        "blocked_reasons": blocked_reasons,
        "manual_review_required": True,
        "public_postable": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "provider_call_made": False,
        "network_call_made": False,
    }


def render_review_packet_from_files(editorial_packet_path, prompt_pack_path=None,
                                    style_profile_path=None,
                                    editorial_rubric_path=None):
    def _load(p):
        if p is None:
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    return render_review_packet(
        _load(editorial_packet_path),
        _load(prompt_pack_path),
        _load(style_profile_path),
        _load(editorial_rubric_path),
    )


def render_from_input_file(path):
    """Render from a single fixture bundling packet + config under one object.

    Expected keys: editorial_packet, prompt_pack, style_profile, editorial_rubric.
    Performs only a local file read; no network/provider access.
    """
    with open(path, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    return render_review_packet(
        bundle.get("editorial_packet"),
        bundle.get("prompt_pack"),
        bundle.get("style_profile"),
        bundle.get("editorial_rubric"),
    )


def summary():
    """Deterministic local capability summary for the CLI. Schema reads only."""
    return {
        "status": "pre-alpha draft renderer and review queue active",
        "local_only": True,
        "design_only": True,
        "renderer_enabled": True,
        "review_queue_enabled": True,
        "integrates_with_0095_editorial_packet": True,
        "integrates_with_0096_prompt_pack": True,
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
    }

