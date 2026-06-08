"""Local-only deterministic grounded packet review queue (v0).

Takes exported grounded editorial packets and places them into a deterministic
local operator review queue with audit status, review gates, blockers,
warnings, manual decision placeholders, and no-public-post enforcement.

This module performs NO network, provider, LLM, search, or platform calls.
Every queue item is advisory-only and explicitly NOT PUBLIC POSTABLE. No
auto-approval and no auto-selection of final public copy ever occurs.
"""

import hashlib

from . import packet_audit

QUEUE_STATUSES = [
    "PENDING_REVIEW",
    "BLOCKED",
    "NEEDS_REVISION",
    "APPROVED_FOR_MANUAL_EXPORT_ONLY",
]

MARKDOWN_BANNERS = [
    "LOCAL ONLY",
    "ADVISORY ONLY",
    "REVIEW QUEUE",
    "HUMAN REVIEW REQUIRED",
    "NOT PUBLIC POSTABLE",
    "NO PROVIDER CALL",
    "NO SEARCH CALL",
    "NO PLATFORM ACTION",
]


def _deterministic_id(prefix: str, seed: str) -> str:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def _derive_queue_status(audit: dict) -> str:
    """Map an audit result to a queue status. Never auto-approves.

    Fixture/demo/synthetic packets can at most reach
    APPROVED_FOR_MANUAL_EXPORT_ONLY, which is NOT publish authority.
    """
    if audit.get("blocker_count", 0) > 0:
        return "BLOCKED"
    if audit.get("warning_count", 0) > 0:
        return "NEEDS_REVISION"
    return "PENDING_REVIEW"


def build_queue_item(packet: dict) -> dict:
    """Build one deterministic review-queue item from an exported packet."""
    source_id = packet.get("source_fixture_id") or "export_fixture"
    export_packet_id = packet.get("export_packet_id") or _deterministic_id("export", source_id)

    audit = packet_audit.audit_packet(packet)
    queue_status = _derive_queue_status(audit)

    nps = packet.get("no_public_post_status", {})
    no_public_post_reason = None
    reasons = nps.get("reasons", [])
    if reasons:
        no_public_post_reason = "; ".join(
            f"[{r.get('component')}] {r.get('reason')}" for r in reasons
        )
    if not no_public_post_reason:
        no_public_post_reason = "Synthetic/demo/fixture packet - not public postable."

    operator_review = {
        "reviewer_id": None,
        "selected_preview_id": None,
        "decision": "PENDING_MANUAL_REVIEW",
        "operator_notes": "",
        "reviewed_at": None,
        "approval_status": "NOT_APPROVED",
        "publish_status": "NOT_PUBLIC_POSTABLE",
    }

    return {
        "queue_item_id": _deterministic_id("queue", export_packet_id),
        "export_packet_id": export_packet_id,
        "source_fixture_id": source_id,
        "content_type": packet.get("content_type", "post"),
        "target_platforms": packet.get("target_platforms", []),
        "created_at": "DETERMINISTIC_TIMESTAMP",
        "queue_status": queue_status,
        "audit_status": audit.get("audit_status"),
        "blocker_count": audit.get("blocker_count", 0),
        "warning_count": audit.get("warning_count", 0),
        "blockers": audit.get("blockers", []),
        "warnings": audit.get("warnings", []),
        "audit_detail": audit,
        "review_required": True,
        "manual_decision_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "no_public_post_reason": no_public_post_reason,
        "operator_review": operator_review,
    }


def build_queue(packets: list) -> list:
    """Build a deterministic review queue from a list of exported packets."""
    return [build_queue_item(p) for p in packets]


def summarize_queue(queue: list) -> dict:
    """Deterministic queue summary. publish_ready_count is always 0."""
    counts = {s: 0 for s in QUEUE_STATUSES}
    manual_decision_required_count = 0
    publish_ready_count = 0
    for item in queue:
        status = item.get("queue_status")
        if status in counts:
            counts[status] += 1
        if item.get("manual_decision_required"):
            manual_decision_required_count += 1
        if item.get("publish_ready"):
            publish_ready_count += 1

    return {
        "status": "deterministic local grounded packet review queue active",
        "queue_length": len(queue),
        "pending_review_count": counts["PENDING_REVIEW"],
        "blocked_count": counts["BLOCKED"],
        "needs_revision_count": counts["NEEDS_REVISION"],
        "approved_for_manual_export_only_count": counts["APPROVED_FOR_MANUAL_EXPORT_ONLY"],
        "manual_decision_required_count": manual_decision_required_count,
        "publish_ready_count": publish_ready_count,
        "queue_status_counts": counts,
        "live_actions_disabled": True,
        "advisory_only": True,
        "all_fixture_outputs_not_public_postable": True,
    }


def render_markdown_report(queue: list) -> str:
    """Render a deterministic markdown queue report with mandatory banners."""
    summary = summarize_queue(queue)
    lines = []
    lines.append("# Grounded Packet Review Queue (v0)")
    lines.append("")
    lines.append("> " + " | ".join(MARKDOWN_BANNERS))
    lines.append("")
    lines.append("## Queue Summary")
    lines.append(f"- queue_length: {summary['queue_length']}")
    lines.append(f"- pending_review_count: {summary['pending_review_count']}")
    lines.append(f"- blocked_count: {summary['blocked_count']}")
    lines.append(f"- needs_revision_count: {summary['needs_revision_count']}")
    lines.append(f"- manual_decision_required_count: {summary['manual_decision_required_count']}")
    lines.append(f"- publish_ready_count: {summary['publish_ready_count']}")
    lines.append("")
    lines.append("## Safety Posture")
    lines.append("- approval_granted=false")
    lines.append("- publish_ready=false")
    lines.append("- provider_call_allowed=false")
    lines.append("- search_call_allowed=false")
    lines.append("- platform_action_allowed=false")
    lines.append("- human_review_required=true")
    lines.append("")
    lines.append("## Queue Items")
    for item in queue:
        lines.append(f"### {item.get('queue_item_id')}")
        lines.append(f"- export_packet_id: {item.get('export_packet_id')}")
        lines.append(f"- queue_status: {item.get('queue_status')}")
        lines.append(f"- audit_status: {item.get('audit_status')}")
        lines.append(f"- blocker_count: {item.get('blocker_count')}")
        lines.append(f"- warning_count: {item.get('warning_count')}")
        lines.append(f"- citation_guardrail_status: "
                     f"{item.get('audit_detail', {}).get('citation_guardrail_status')}")
        lines.append(f"- no_public_post_reason: {item.get('no_public_post_reason')}")
        lines.append(f"- decision: {item.get('operator_review', {}).get('decision')}")
        for b in item.get("blockers", []):
            lines.append(f"  - BLOCKER: {b}")
        for w in item.get("warnings", []):
            lines.append(f"  - WARNING: {w}")
        lines.append("")
    return "\n".join(lines)


def build_summary() -> dict:
    """Deterministic CLI summary describing the review queue posture."""
    return {
        "status": "deterministic local grounded packet review queue active",
        "local_only": True,
        "advisory_only": True,
        "review_queue_enabled": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "all_fixture_outputs_not_public_postable": True,
        "queue_status_counts": {s: 0 for s in QUEUE_STATUSES},
        "audit_rules_enabled": True,
    }

