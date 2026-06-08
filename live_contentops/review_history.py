"""Local-only deterministic operator review history (v0).

Preserves an append-only local history of operator decision records for a
review queue item / exported packet. No decision becomes publishing authority.
Synthetic/demo/fixture content stays NOT PUBLIC POSTABLE. Performs NO network,
provider, LLM, search, or platform calls.
"""

import hashlib

from . import operator_decision

MARKDOWN_BANNERS = [
    "LOCAL ONLY",
    "ADVISORY ONLY",
    "OPERATOR DECISION HISTORY",
    "HUMAN REVIEW REQUIRED",
    "NOT PUBLIC POSTABLE",
    "NO PROVIDER CALL",
    "NO SEARCH CALL",
    "NO PLATFORM ACTION",
]

APPEND_ONLY_NOTE = (
    "History is append-only by semantics: prior decision records are preserved "
    "and never mutated. New decisions are appended; interpretation may change "
    "but recorded decisions remain immutable."
)


def _deterministic_id(prefix: str, seed: str) -> str:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def build_history(queue_item: dict, decision_records: list) -> dict:
    """Build a deterministic review history from ordered decision records."""
    queue_item_id = queue_item.get("queue_item_id", "unknown_queue_item")
    export_packet_id = queue_item.get("export_packet_id", "unknown_export_packet")

    revision_count = 0
    rejection_count = 0
    hold_count = 0
    internal_review_accept_count = 0
    manual_export_packet_accept_count = 0

    for record in decision_records:
        dtype = record.get("decision_type")
        # Only count effective (non-BLOCKED) acceptances toward accept tallies.
        blocked = record.get("decision_status") == "BLOCKED"
        if dtype == "REQUEST_REVISION":
            revision_count += 1
        elif dtype == "REJECT_PACKET":
            rejection_count += 1
        elif dtype == "HOLD_FOR_REAL_ARTIFACT":
            hold_count += 1
        elif dtype == "ACCEPT_FOR_INTERNAL_REVIEW_ONLY" and not blocked:
            internal_review_accept_count += 1
        elif dtype == "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY" and not blocked:
            manual_export_packet_accept_count += 1

    latest_decision = decision_records[-1] if decision_records else None
    current_review_status = (latest_decision.get("decision_status")
                             if latest_decision else "PENDING_MANUAL_REVIEW")

    return {
        "history_id": _deterministic_id("hist", export_packet_id),
        "queue_item_id": queue_item_id,
        "export_packet_id": export_packet_id,
        "decision_records": list(decision_records),
        "latest_decision": latest_decision,
        "revision_count": revision_count,
        "rejection_count": rejection_count,
        "hold_count": hold_count,
        "internal_review_accept_count": internal_review_accept_count,
        "manual_export_packet_accept_count": manual_export_packet_accept_count,
        "current_review_status": current_review_status,
        "current_publish_status": "NOT_PUBLIC_POSTABLE",
        "approval_granted": False,
        "publish_ready": False,
        "advisory_only": True,
        "human_review_required": True,
        "append_only_semantics_note": APPEND_ONLY_NOTE,
    }


def append_decision(history: dict, queue_item: dict, decision_record: dict) -> dict:
    """Return a new history with the decision appended (append-only)."""
    records = list(history.get("decision_records", [])) + [decision_record]
    return build_history(queue_item, records)


def summarize_history(history: dict) -> dict:
    """Deterministic summary of a single review history."""
    return {
        "history_id": history.get("history_id"),
        "queue_item_id": history.get("queue_item_id"),
        "export_packet_id": history.get("export_packet_id"),
        "decision_count": len(history.get("decision_records", [])),
        "revision_count": history.get("revision_count", 0),
        "rejection_count": history.get("rejection_count", 0),
        "hold_count": history.get("hold_count", 0),
        "internal_review_accept_count": history.get("internal_review_accept_count", 0),
        "manual_export_packet_accept_count": history.get("manual_export_packet_accept_count", 0),
        "current_review_status": history.get("current_review_status"),
        "current_publish_status": "NOT_PUBLIC_POSTABLE",
        "approval_granted": False,
        "publish_ready": False,
    }


def validate_history(history: dict) -> dict:
    """Local validation of a review history."""
    warnings = []
    blockers = []

    records = history.get("decision_records", [])
    if not records:
        blockers.append("Review history has no decision records.")

    if history.get("approval_granted") or history.get("publish_ready"):
        blockers.append("Review history grants approval/publish authority.")
    if history.get("current_publish_status") != "NOT_PUBLIC_POSTABLE":
        blockers.append("Review history publish status is not NOT_PUBLIC_POSTABLE.")

    latest = history.get("latest_decision")
    if latest:
        # Latest decision must not contradict a BLOCKED snapshot.
        snap_blocked = (latest.get("audit_status_snapshot") == "BLOCKED"
                        or latest.get("citation_guardrail_status_snapshot") == "BLOCKED")
        accepted = latest.get("decision_status", "").startswith("ACCEPTED")
        if snap_blocked and accepted:
            blockers.append("Latest decision accepts a packet with BLOCKED audit/citation state.")
        if latest.get("approval_granted") or latest.get("publish_ready"):
            blockers.append("Latest decision grants publish authority.")

    # Each decision record must individually validate.
    for record in records:
        res = operator_decision.validate_decision_record(record)
        if res["status"] == "BLOCKED":
            blockers.extend(res["blockers"])
        warnings.extend(res["warnings"])

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}


def render_markdown_report(history: dict) -> str:
    """Render a deterministic markdown history report with mandatory banners."""
    summary = summarize_history(history)
    lines = []
    lines.append("# Operator Decision History (v0)")
    lines.append("")
    lines.append("> " + " | ".join(MARKDOWN_BANNERS))
    lines.append("")
    lines.append("## History Summary")
    lines.append(f"- history_id: {summary['history_id']}")
    lines.append(f"- queue_item_id: {summary['queue_item_id']}")
    lines.append(f"- export_packet_id: {summary['export_packet_id']}")
    lines.append(f"- decision_count: {summary['decision_count']}")
    lines.append(f"- revision_count: {summary['revision_count']}")
    lines.append(f"- rejection_count: {summary['rejection_count']}")
    lines.append(f"- hold_count: {summary['hold_count']}")
    lines.append(f"- internal_review_accept_count: {summary['internal_review_accept_count']}")
    lines.append(f"- manual_export_packet_accept_count: "
                 f"{summary['manual_export_packet_accept_count']}")
    lines.append(f"- current_review_status: {summary['current_review_status']}")
    lines.append("")
    lines.append("## Safety Posture")
    lines.append("- approval_granted=false")
    lines.append("- publish_ready=false")
    lines.append("- current_publish_status: NOT_PUBLIC_POSTABLE")
    lines.append("")
    lines.append("## Decision Records")
    for record in history.get("decision_records", []):
        lines.append(f"### {record.get('decision_id')}")
        lines.append(f"- decision_type: {record.get('decision_type')}")
        lines.append(f"- decision_status: {record.get('decision_status')}")
        lines.append(f"- audit_status_snapshot: {record.get('audit_status_snapshot')}")
        lines.append(f"- citation_guardrail_status_snapshot: "
                     f"{record.get('citation_guardrail_status_snapshot')}")
        lines.append(f"- no_public_post_reason: {record.get('no_public_post_reason')}")
        for b in record.get("decision_blockers", []):
            lines.append(f"  - BLOCKER: {b}")
        lines.append("")
    lines.append(f"_{history.get('append_only_semantics_note', '')}_")
    return "\n".join(lines)


def build_summary() -> dict:
    """Deterministic CLI summary describing the decision/history posture."""
    return {
        "status": "deterministic local operator decision capture and review history active",
        "local_only": True,
        "advisory_only": True,
        "decision_capture_enabled": True,
        "review_history_enabled": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "all_fixture_outputs_not_public_postable": True,
        "supported_decision_types": list(operator_decision.ALLOWED_DECISION_TYPES),
        "forbidden_decision_rules_enabled": True,
    }

