"""Local-only deterministic operator decision capture (v0).

Records manual-review decision records for grounded packet review queue items.
No decision ever becomes publishing authority. Synthetic/demo/fixture content
stays NOT PUBLIC POSTABLE. Performs NO network, provider, LLM, search, or
platform calls.
"""

import hashlib

# Allowed local-only decision types. None of these grant public approval.
ALLOWED_DECISION_TYPES = [
    "REQUEST_REVISION",
    "REJECT_PACKET",
    "HOLD_FOR_REAL_ARTIFACT",
    "ACCEPT_FOR_INTERNAL_REVIEW_ONLY",
    "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY",
]

# Decision-type -> resulting decision_status (advisory, non-publishing).
DECISION_STATUS_MAP = {
    "REQUEST_REVISION": "REVISION_REQUESTED",
    "REJECT_PACKET": "REJECTED",
    "HOLD_FOR_REAL_ARTIFACT": "ON_HOLD",
    "ACCEPT_FOR_INTERNAL_REVIEW_ONLY": "ACCEPTED_INTERNAL_REVIEW_ONLY",
    "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY": "ACCEPTED_MANUAL_EXPORT_PACKET_ONLY",
}

# Phrases that signal an attempt to grant publishing/platform authority.
FORBIDDEN_DECISION_SIGNALS = [
    "approve_public_post",
    "publish",
    "schedule",
    "send",
    "upload",
    "platform_action",
    "go_live",
    "post_to_platform",
]


def _deterministic_id(prefix: str, seed: str) -> str:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def _detect_forbidden_intent(req: dict) -> list:
    """Detect any attempt to grant publishing/platform/scheduling authority."""
    issues = []
    decision_type = str(req.get("decision_type", ""))

    if decision_type not in ALLOWED_DECISION_TYPES:
        issues.append(f"Unknown or disallowed decision type: {decision_type}")

    # Explicit authority-grant attempts in the request payload.
    if req.get("approve_public_post"):
        issues.append("Decision attempts to approve public posting.")
    if req.get("publish_ready"):
        issues.append("Decision attempts to set publish_ready=true.")
    if req.get("schedule") or req.get("scheduled"):
        issues.append("Decision attempts to schedule content.")
    if req.get("platform_action_allowed"):
        issues.append("Decision attempts to grant platform_action_allowed=true.")
    if req.get("provider_call_allowed") or req.get("search_call_allowed"):
        issues.append("Decision attempts to grant provider/search authority.")
    if req.get("mark_public_postable"):
        issues.append("Decision attempts to mark synthetic/demo content public-postable.")

    # Free-text intent scan over notes / requested_action.
    text = (str(req.get("operator_notes", "")) + " "
            + str(req.get("requested_action", ""))).lower()
    for signal in FORBIDDEN_DECISION_SIGNALS:
        token = signal.replace("_", " ")
        if token in text and "no " + token not in text:
            issues.append(f"Decision text requests forbidden action: {signal}")
    return issues


def build_decision_record(queue_item: dict, req: dict) -> dict:
    """Build one deterministic operator decision record for a queue item.

    The decision never grants publishing authority. Forbidden intent is
    captured as blockers and the decision_status is downgraded to BLOCKED.
    Synthetic/demo/fixture content remains NOT PUBLIC POSTABLE.
    """
    queue_item_id = queue_item.get("queue_item_id", "unknown_queue_item")
    export_packet_id = queue_item.get("export_packet_id", "unknown_export_packet")
    source_id = (queue_item.get("source_fixture_id")
                 or queue_item.get("source_draft_id")
                 or "export_fixture")

    decision_type = req.get("decision_type", "")
    operator_id = req.get("operator_id") or req.get("reviewer_id")

    audit_detail = queue_item.get("audit_detail", {})
    citation_guardrail_status = audit_detail.get("citation_guardrail_status", "UNKNOWN")
    blocker_snapshot = list(queue_item.get("blockers", []))
    warning_snapshot = list(queue_item.get("warnings", []))
    audit_status_snapshot = queue_item.get("audit_status", "UNKNOWN")

    forbidden_issues = _detect_forbidden_intent(req)
    blockers = list(forbidden_issues)

    # A decision cannot hide a BLOCKED audit/citation state.
    if audit_status_snapshot == "BLOCKED" or citation_guardrail_status == "BLOCKED":
        if decision_type in ("ACCEPT_FOR_INTERNAL_REVIEW_ONLY",
                             "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY"):
            blockers.append(
                "Decision cannot accept a packet while audit/citation is BLOCKED."
            )

    # A decision cannot override missing source/limitation problems for acceptance.
    if decision_type == "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY":
        if audit_detail.get("source_reference_status") == "MISSING":
            blockers.append("Decision cannot accept a packet with missing source references.")
        if audit_detail.get("limitation_visibility_status") == "MISSING":
            blockers.append("Decision cannot accept a packet with missing limitations.")

    if blockers:
        decision_status = "BLOCKED"
    else:
        decision_status = DECISION_STATUS_MAP.get(decision_type, "BLOCKED")

    # no_public_post_reason is always preserved.
    no_public_post_reason = (queue_item.get("no_public_post_reason")
                             or "Synthetic/demo/fixture packet - not public postable.")

    return {
        "decision_id": _deterministic_id("dec", f"{queue_item_id}:{decision_type}"),
        "queue_item_id": queue_item_id,
        "export_packet_id": export_packet_id,
        "source_fixture_id": source_id,
        "operator_id": operator_id,
        "reviewer_id": operator_id,
        "decision_timestamp": "DETERMINISTIC_TIMESTAMP",
        "decision_type": decision_type,
        "decision_status": decision_status,
        "operator_notes": req.get("operator_notes", ""),
        "selected_preview_id": req.get("selected_preview_id"),
        "blocker_snapshot": blocker_snapshot,
        "warning_snapshot": warning_snapshot,
        "audit_status_snapshot": audit_status_snapshot,
        "citation_guardrail_status_snapshot": citation_guardrail_status,
        "decision_blockers": blockers,
        "no_public_post_reason": no_public_post_reason,
        "advisory_only": True,
        "manual_decision_recorded": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }


def validate_decision_record(record: dict) -> dict:
    """Local validation of a single decision record."""
    warnings = []
    blockers = list(record.get("decision_blockers", []))

    if record.get("decision_type") not in ALLOWED_DECISION_TYPES:
        blockers.append(f"Unknown decision type: {record.get('decision_type')}")
    if record.get("approval_granted") or record.get("publish_ready"):
        blockers.append("Decision record grants approval/publish authority.")
    if record.get("platform_action_allowed") or record.get("provider_call_allowed") \
            or record.get("search_call_allowed"):
        blockers.append("Decision record grants provider/search/platform authority.")
    if not record.get("no_public_post_reason"):
        blockers.append("Decision record missing no_public_post_reason.")
    if record.get("operator_id") is None and record.get("reviewer_id") is None:
        warnings.append("Decision record missing operator/reviewer placeholder.")
    if not record.get("decision_timestamp"):
        warnings.append("Decision record missing timestamp.")

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}

