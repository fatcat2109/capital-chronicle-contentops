"""Local-only pre-alpha manual review workflow + approval packet builder (Task 0098).

Deterministic, repo-local. Consumes 0097 review queue items and a MANUAL human
review decision, then emits approval / revision / rejection packets. "Approval"
means the draft is ready for future MANUAL publish prep only -- it NEVER means
live posting, publish-now, or platform action.

This module performs NO network/search/provider/LLM/platform/credential access.
It NEVER posts, NEVER fetches, NEVER reads `.env`, NEVER auto-approves, NEVER
produces public-postable or publish-ready output, and NEVER emits financial
advice / signal / execution language or fake Capital Chronicle alpha output.

Guardrail scans are reused from grounded_research_brief (single source of truth)
plus the 0095 numeric-market-claim detector, so an externally supplied review
item or approved text cannot smuggle unsafe content through approval.
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
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
DECISION_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_manual_review_decision.schema.json"
)
APPROVAL_PACKET_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_approval_packet.schema.json"
)

ALLOWED_DECISIONS = {
    "approve_manual_publish_prep",
    "request_revision",
    "reject",
}

ALLOWED_PLATFORM_FAMILY_SET = set(ALLOWED_PLATFORM_FAMILIES)


def load_decision_schema():
    with open(os.path.abspath(DECISION_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_approval_packet_schema():
    with open(os.path.abspath(APPROVAL_PACKET_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)



def _review_item_unresolved_findings(review_item):
    """Return guardrail findings on the review item that must block approval.

    Combines findings the 0097 renderer already recorded with an independent
    re-scan of the item text, so a tampered/externally-supplied item cannot hide
    unsafe content. Deterministic; no external access.
    """
    findings = list(review_item.get("guardrail_findings") or [])

    if review_item.get("review_status") == "blocked" and "review_status_blocked" not in findings:
        findings.append("review_status_blocked")

    scan_text = "\n".join([
        str(review_item.get("title_or_hook", "")),
        str(review_item.get("body", "")),
    ])
    if _scan_forbidden_language(scan_text) and "forbidden_language" not in findings:
        findings.append("forbidden_language")
    if _scan_alpha_implication(scan_text) and "implies_alpha_output" not in findings:
        findings.append("implies_alpha_output")
    if _scan_numeric_market_claim(scan_text) and "unverified_numeric_market_claim" not in findings:
        findings.append("unverified_numeric_market_claim")

    return findings


def validate_decision(decision, review_item=None):
    """Validate a manual review decision. Returns {'valid': bool, 'errors': [...]}.

    If review_item is supplied, approval is only allowed when the item has no
    unresolved guardrail findings. Fail closed on any unsafe flag.
    """
    errors = []
    if not isinstance(decision, dict):
        return {"valid": False, "errors": ["decision_not_object"]}

    d = decision.get("decision")
    if d not in ALLOWED_DECISIONS:
        errors.append("decision_value_not_allowed")

    if not decision.get("review_decision_id"):
        errors.append("missing_review_decision_id")
    if not decision.get("review_queue_item_id"):
        errors.append("missing_review_queue_item_id")

    # Reviewer placeholder is mandatory; no auto-approval is permitted.
    reviewer = decision.get("reviewer_id_placeholder")
    if not isinstance(reviewer, str) or not reviewer.strip():
        errors.append("missing_reviewer_placeholder")
    if decision.get("auto_approval") is not False:
        errors.append("auto_approval_not_allowed")
    if decision.get("reviewer_required") is not True:
        errors.append("reviewer_required_must_be_true")

    # Non-publishing posture is pinned.
    if decision.get("manual_publish_only") is not True:
        errors.append("manual_publish_only_must_be_true")
    if decision.get("publish_allowed_now") is not False:
        errors.append("publish_allowed_now_must_be_false")
    if decision.get("platform_publish_allowed_now") is not False:
        errors.append("platform_publish_allowed_now_must_be_false")
    if decision.get("live_execution_allowed_now") is not False:
        errors.append("live_execution_allowed_now_must_be_false")

    # Decision-specific requirements.
    if d == "request_revision":
        if not (decision.get("required_revision_notes") or []):
            errors.append("request_revision_requires_notes")
    if d == "reject":
        if not str(decision.get("decision_reason") or "").strip():
            errors.append("reject_requires_reason")

    # Approval-only checks: must not approve over unresolved findings.
    if d == "approve_manual_publish_prep":
        platform = decision.get("approved_platform_family")
        if platform not in ALLOWED_PLATFORM_FAMILY_SET:
            errors.append("approved_platform_family_not_allowed")
        declared = decision.get("unresolved_guardrail_findings")
        if declared:
            errors.append("approve_with_unresolved_findings")
        if review_item is not None:
            actual = _review_item_unresolved_findings(review_item)
            if actual:
                errors.append("approve_with_unresolved_findings")

    return {"valid": len(errors) == 0, "errors": errors}



def build_approval_packet(rendered_packet_id, review_item, decision):
    """Build an approval/revision/rejection packet from a review item + decision.

    Validates the decision (against the review item for approvals). On any
    validation failure, the packet is emitted with approval_status="rejected",
    manual_publish_prep_ready=false, and blocked_reasons populated (fail closed).
    All non-publishing safety flags are pinned regardless of input.
    """
    blocked_reasons = []

    if not isinstance(review_item, dict):
        review_item = {}

    v = validate_decision(decision, review_item)
    if not v["valid"]:
        blocked_reasons.extend(v["errors"])

    d = decision.get("decision") if isinstance(decision, dict) else None

    # Independent re-scan of the approved text path as defense in depth.
    approved_text = str(review_item.get("body", ""))
    scan_text = "\n".join([
        str(review_item.get("title_or_hook", "")),
        approved_text,
    ])
    if _scan_forbidden_language(scan_text):
        if "approved_text_forbidden_language" not in blocked_reasons:
            blocked_reasons.append("approved_text_forbidden_language")
    if _scan_alpha_implication(scan_text):
        if "approved_text_implies_alpha_output" not in blocked_reasons:
            blocked_reasons.append("approved_text_implies_alpha_output")
    if _scan_numeric_market_claim(scan_text):
        if "approved_text_unverified_numeric_market_claim" not in blocked_reasons:
            blocked_reasons.append("approved_text_unverified_numeric_market_claim")

    # Decide the resulting status. A clean approval is the only path to
    # manual_publish_prep_ready=True. Everything else is non-ready.
    if d == "approve_manual_publish_prep" and not blocked_reasons:
        approval_status = "approved_manual_publish_prep"
        manual_publish_prep_ready = True
    elif d == "request_revision" and not blocked_reasons:
        approval_status = "revision_requested"
        manual_publish_prep_ready = False
    else:
        approval_status = "rejected"
        manual_publish_prep_ready = False

    decision_id = (decision or {}).get("review_decision_id") if isinstance(decision, dict) else None
    decision_id = decision_id or "unknown"

    audit_trail = [
        "review_queue_item:%s" % review_item.get("review_queue_item_id"),
        "decision:%s" % d,
        "reviewer:%s" % ((decision or {}).get("reviewer_id_placeholder") if isinstance(decision, dict) else None),
        "review_timestamp:%s" % ((decision or {}).get("review_timestamp") if isinstance(decision, dict) else None),
        "status:%s" % approval_status,
    ]

    return {
        "approval_packet_id": "approval_%s" % decision_id,
        "rendered_packet_id": rendered_packet_id,
        "review_decision_id": decision_id,
        "draft_id": review_item.get("draft_id"),
        "platform_family": review_item.get("platform_family"),
        "approved_text": approved_text if approval_status == "approved_manual_publish_prep" else "",
        "limitations": list(review_item.get("limitations") or []),
        "source_artifact_ids": list(review_item.get("source_artifact_ids") or []),
        "is_general_process_content": bool(review_item.get("is_general_process_content")),
        "content_type": review_item.get("content_type"),
        "approval_status": approval_status,
        "manual_publish_prep_ready": manual_publish_prep_ready,
        "approval_scope": (decision or {}).get("approval_scope") if isinstance(decision, dict) else None,
        "reviewer_id_placeholder": (decision or {}).get("reviewer_id_placeholder") if isinstance(decision, dict) else None,
        "approval_audit_trail": audit_trail,
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "final_operator_check_required": True,
        "blocked_reasons": blocked_reasons,
    }


def build_from_input_file(path):
    """Build an approval packet from a bundle fixture.

    Expected keys: rendered_packet_id, review_item, decision. Local file read only.
    """
    with open(path, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    return build_approval_packet(
        bundle.get("rendered_packet_id"),
        bundle.get("review_item"),
        bundle.get("decision"),
    )


def summary():
    """Deterministic local capability summary for the CLI. Schema reads only."""
    return {
        "status": "pre-alpha manual review workflow and approval packet active",
        "local_only": True,
        "design_only": True,
        "manual_review_enabled": True,
        "approval_packet_enabled": True,
        "supported_decisions": sorted(ALLOWED_DECISIONS),
        "integrates_with_0097_review_queue": True,
        "auto_approval": False,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "final_operator_check_required": True,
        "static_timestamp": STATIC_TIMESTAMP,
    }
