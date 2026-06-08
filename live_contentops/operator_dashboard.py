"""Local-only deterministic operator dashboard (v0).

Builds a compact, advisory operator-facing dashboard summary and markdown report
over the local packet registry and review ledger. Surfaces packet status,
blockers, review state, decisions, not-public-post posture, and ledger lineage
WITHOUT granting any publishing authority.

Performs NO network, provider, LLM, search, or platform calls.
"""

from . import packet_registry_query as rq

MARKDOWN_BANNERS = [
    "LOCAL ONLY",
    "ADVISORY ONLY",
    "OPERATOR DASHBOARD",
    "PACKET REGISTRY QUERY",
    "HUMAN REVIEW REQUIRED",
    "NOT PUBLIC POSTABLE",
    "NO PROVIDER CALL",
    "NO SEARCH CALL",
    "NO PLATFORM ACTION",
]


def build_dashboard(registry_records: list, ledger: list) -> dict:
    """Deterministic operator dashboard summary over registry/ledger data."""
    items = rq.build_query_items(registry_records, ledger)

    blocked_count = sum(1 for i in items if i.get("queue_status") == "BLOCKED")
    pending_review_count = sum(1 for i in items if i.get("queue_status") == "PENDING_REVIEW")
    needs_revision_count = sum(1 for i in items if i.get("queue_status") == "NEEDS_REVISION")

    held = sum(1 for e in ledger if e.get("event_type") == "HELD_FOR_REAL_ARTIFACT")
    internal = sum(1 for e in ledger if e.get("event_type") == "INTERNAL_REVIEW_ACCEPTED")
    manual = sum(1 for e in ledger if e.get("event_type") == "MANUAL_EXPORT_PACKET_ACCEPTED")

    no_public_post_count = sum(1 for i in items if i.get("no_public_post_reason"))
    missing_issue_count = sum(
        1 for i in items
        if i.get("source_reference_status") == "MISSING"
        or i.get("limitation_visibility_status") == "MISSING"
    )
    citation_blocked_count = sum(
        1 for i in items if i.get("citation_guardrail_status") == "BLOCKED"
    )

    highest = rq.highest_priority_items(items)

    return {
        "status": "deterministic local operator dashboard active",
        "local_only": True,
        "advisory_only": True,
        "dashboard_enabled": True,
        "registry_record_count": len(registry_records),
        "ledger_entry_count": len(ledger),
        "blocked_count": blocked_count,
        "pending_review_count": pending_review_count,
        "needs_revision_count": needs_revision_count,
        "held_for_real_artifact_count": held,
        "internal_review_accept_count": internal,
        "manual_export_packet_accept_count": manual,
        "publish_ready_count": 0,
        "approval_granted_count": 0,
        "no_public_post_count": no_public_post_count,
        "missing_source_or_limitation_issue_count": missing_issue_count,
        "citation_guardrail_blocked_count": citation_blocked_count,
        "provider_call_allowed_count": 0,
        "search_call_allowed_count": 0,
        "platform_action_allowed_count": 0,
        "all_fixture_outputs_not_public_postable": True,
        "highest_priority_items": [
            {
                "registry_record_id": i.get("registry_record_id"),
                "queue_status": i.get("queue_status"),
                "audit_status": i.get("audit_status"),
                "latest_decision_status": i.get("latest_decision_status"),
                "blocker_count": i.get("blocker_count", 0),
            }
            for i in highest
        ],
    }


def validate_dashboard(dashboard: dict, items: list, known_registry_ids: set) -> dict:
    """Block/warn if the dashboard would weaken guardrail posture."""
    warnings = []
    blockers = []

    if dashboard.get("publish_ready_count", 0) != 0:
        blockers.append("Dashboard reports publish_ready items.")
    if dashboard.get("approval_granted_count", 0) != 0:
        blockers.append("Dashboard reports approval-granted items.")
    if dashboard.get("platform_action_allowed_count", 0) != 0 \
            or dashboard.get("provider_call_allowed_count", 0) != 0 \
            or dashboard.get("search_call_allowed_count", 0) != 0:
        blockers.append("Dashboard reports provider/search/platform authority.")
    if not dashboard.get("all_fixture_outputs_not_public_postable"):
        blockers.append("Dashboard does not affirm not-public-postable status.")

    # A blocked citation count must be surfaced, not hidden.
    item_blocked = sum(1 for i in items if i.get("citation_guardrail_status") == "BLOCKED")
    if item_blocked != dashboard.get("citation_guardrail_blocked_count", 0):
        blockers.append("Dashboard hides citation guardrail BLOCKED count.")

    query_validation = rq.validate_query_items(items, known_registry_ids)
    blockers.extend(query_validation["blockers"])
    warnings.extend(query_validation["warnings"])

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}


def render_markdown_report(registry_records: list, ledger: list) -> str:
    """Render a deterministic markdown operator dashboard with banners."""
    dashboard = build_dashboard(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    lines = []
    lines.append("# Operator Dashboard (v0)")
    lines.append("")
    lines.append("> " + " | ".join(MARKDOWN_BANNERS))
    lines.append("")
    lines.append("## Summary Counts")
    lines.append(f"- registry_record_count: {dashboard['registry_record_count']}")
    lines.append(f"- ledger_entry_count: {dashboard['ledger_entry_count']}")
    lines.append(f"- blocked_count: {dashboard['blocked_count']}")
    lines.append(f"- pending_review_count: {dashboard['pending_review_count']}")
    lines.append(f"- needs_revision_count: {dashboard['needs_revision_count']}")
    lines.append(f"- held_for_real_artifact_count: {dashboard['held_for_real_artifact_count']}")
    lines.append(f"- internal_review_accept_count: {dashboard['internal_review_accept_count']}")
    lines.append(f"- manual_export_packet_accept_count: "
                 f"{dashboard['manual_export_packet_accept_count']}")
    lines.append(f"- citation_guardrail_blocked_count: "
                 f"{dashboard['citation_guardrail_blocked_count']}")
    lines.append("")
    lines.append("## Safety Posture")
    lines.append("- approval_granted=false")
    lines.append("- publish_ready=false")
    lines.append("- current_publish_status: NOT_PUBLIC_POSTABLE")
    lines.append("")
    lines.append("## Highest-Priority Items")
    for i in dashboard["highest_priority_items"]:
        lines.append(f"- {i['registry_record_id']}: queue={i['queue_status']} "
                     f"audit={i['audit_status']} decision={i['latest_decision_status']} "
                     f"blockers={i['blocker_count']}")
    lines.append("")
    lines.append("## Blockers / Warnings")
    for item in items:
        if item.get("blocker_count", 0) or item.get("warning_count", 0):
            lines.append(f"- {item['registry_record_id']}: "
                         f"blockers={item.get('blocker_count', 0)} "
                         f"warnings={item.get('warning_count', 0)}")
    lines.append("")
    lines.append("## Manual Decision Status")
    for item in items:
        lines.append(f"- {item['registry_record_id']}: "
                     f"latest_decision_status={item.get('latest_decision_status')} "
                     f"(advisory, not public approval)")
    lines.append("")
    lines.append("## Ledger Event Summary")
    for entry in ledger:
        lines.append(f"- [{entry.get('event_type')}] {entry.get('event_summary')}")
    lines.append("")
    lines.append("## Next Operator Action")
    lines.append("- PLACEHOLDER: manual human review required; no automated action taken.")
    return "\n".join(lines)


def build_summary() -> dict:
    """Deterministic CLI summary describing the dashboard/query posture."""
    return {
        "status": "deterministic local packet registry query and operator dashboard active",
        "local_only": True,
        "advisory_only": True,
        "query_enabled": True,
        "dashboard_enabled": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "all_fixture_outputs_not_public_postable": True,
        "registry_record_count": 0,
        "ledger_entry_count": 0,
        "supported_filters": list(rq.SUPPORTED_FILTERS),
        "supported_groupings": list(rq.SUPPORTED_GROUPINGS),
        "safety_validation_enabled": True,
    }

