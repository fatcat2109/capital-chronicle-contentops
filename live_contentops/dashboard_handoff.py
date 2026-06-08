"""Local-only deterministic packet dashboard export and operator handoff (v0).

Exports a readable, deterministic handoff/report bundle from the packet registry
query and operator dashboard layers. Helps an operator inspect packet counts,
highest-priority items, blockers, review status, decision history, ledger
lineage, and next-operator-action placeholders.

Performs NO network, provider, LLM, search, or platform calls. Every export is
advisory-only and explicitly NOT PUBLIC POSTABLE. It creates no public-postable
content, no publish-ready drafts, no platform exports, and no schedules.
"""

import hashlib

from . import operator_dashboard as dash
from . import packet_registry_query as rq

EXPORT_FORMATS_SUPPORTED = ["json_compatible_dict", "markdown_report"]

# Local manual-review placeholders only. None grant publish authority.
NEXT_OPERATOR_ACTION_PLACEHOLDERS = [
    "REVIEW_BLOCKERS",
    "REQUEST_REVISION",
    "HOLD_FOR_REAL_ARTIFACT",
    "ACCEPT_FOR_INTERNAL_REVIEW_ONLY",
    "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY",
]

MARKDOWN_BANNERS = [
    "LOCAL ONLY",
    "ADVISORY ONLY",
    "OPERATOR HANDOFF",
    "PACKET DASHBOARD EXPORT",
    "HUMAN REVIEW REQUIRED",
    "NOT PUBLIC POSTABLE",
    "NO PROVIDER CALL",
    "NO SEARCH CALL",
    "NO PLATFORM ACTION",
]


def _deterministic_id(prefix: str, seed: str) -> str:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def build_handoff_export(registry_records: list, ledger: list) -> dict:
    """Build a deterministic operator handoff export bundle."""
    dashboard = dash.build_dashboard(registry_records, ledger)
    items = rq.build_query_items(registry_records, ledger)
    registry_summary = rq_summary(items)

    blocker_summary = [
        {
            "registry_record_id": i.get("registry_record_id"),
            "blocker_count": i.get("blocker_count", 0),
            "audit_status": i.get("audit_status"),
            "citation_guardrail_status": i.get("citation_guardrail_status"),
        }
        for i in items if i.get("blocker_count", 0) > 0
    ]
    warning_summary = [
        {
            "registry_record_id": i.get("registry_record_id"),
            "warning_count": i.get("warning_count", 0),
            "source_reference_status": i.get("source_reference_status"),
            "limitation_visibility_status": i.get("limitation_visibility_status"),
        }
        for i in items
        if i.get("warning_count", 0) > 0
        or i.get("source_reference_status") == "MISSING"
        or i.get("limitation_visibility_status") == "MISSING"
    ]
    review_status_summary = [
        {
            "registry_record_id": i.get("registry_record_id"),
            "queue_status": i.get("queue_status"),
            "latest_decision_status": i.get("latest_decision_status"),
        }
        for i in items
    ]
    decision_history_summary = [
        {
            "registry_record_id": i.get("registry_record_id"),
            "latest_decision_type": i.get("latest_decision_type"),
            "latest_decision_status": i.get("latest_decision_status"),
            "note": "advisory, not public approval",
        }
        for i in items
    ]
    ledger_event_summary = [
        {
            "registry_record_id": e.get("registry_record_id"),
            "event_type": e.get("event_type"),
            "event_summary": e.get("event_summary"),
            "publish_status": e.get("publish_status"),
        }
        for e in ledger
    ]

    seed = ":".join(r.get("registry_record_id", "") for r in registry_records)
    return {
        "handoff_id": _deterministic_id("handoff", seed or "empty"),
        "generated_at": "DETERMINISTIC_TIMESTAMP",
        "dashboard_summary": dashboard,
        "registry_query_summary": registry_summary,
        "highest_priority_items": dashboard["highest_priority_items"],
        "blocker_summary": blocker_summary,
        "warning_summary": warning_summary,
        "review_status_summary": review_status_summary,
        "decision_history_summary": decision_history_summary,
        "ledger_event_summary": ledger_event_summary,
        "next_operator_action_placeholders": list(NEXT_OPERATOR_ACTION_PLACEHOLDERS),
        "safety_posture": {
            "advisory_only": True,
            "local_only": True,
            "human_review_required": True,
            "approval_granted": False,
            "publish_ready": False,
            "provider_call_allowed": False,
            "search_call_allowed": False,
            "platform_action_allowed": False,
            "all_fixture_outputs_not_public_postable": True,
        },
        "export_formats_supported": list(EXPORT_FORMATS_SUPPORTED),
        "advisory_only": True,
        "local_only": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "all_fixture_outputs_not_public_postable": True,
    }


def rq_summary(items: list) -> dict:
    """Compact registry query summary for the handoff bundle."""
    return {
        "item_count": len(items),
        "with_blockers": sum(1 for i in items if i.get("blocker_count", 0) > 0),
        "with_warnings": sum(1 for i in items if i.get("warning_count", 0) > 0),
        "not_public_postable_count": sum(1 for i in items if i.get("no_public_post_reason")),
        "supported_filters": list(rq.SUPPORTED_FILTERS),
        "supported_groupings": list(rq.SUPPORTED_GROUPINGS),
    }



def render_markdown_report(registry_records: list, ledger: list) -> str:
    """Render a deterministic markdown operator handoff report with banners."""
    export = build_handoff_export(registry_records, ledger)
    d = export["dashboard_summary"]
    lines = []
    lines.append("# Operator Handoff - Packet Dashboard Export (v0)")
    lines.append("")
    lines.append("> " + " | ".join(MARKDOWN_BANNERS))
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- handoff_id: {export['handoff_id']}")
    lines.append(f"- registry_record_count: {d['registry_record_count']}")
    lines.append(f"- ledger_entry_count: {d['ledger_entry_count']}")
    lines.append(f"- blocked_count: {d['blocked_count']}")
    lines.append("")
    lines.append("## Current Safety Posture")
    lines.append("- approval_granted=false")
    lines.append("- publish_ready=false")
    lines.append("- provider_call_allowed=false")
    lines.append("- search_call_allowed=false")
    lines.append("- platform_action_allowed=false")
    lines.append("- human_review_required=true")
    lines.append("- current_publish_status: NOT_PUBLIC_POSTABLE")
    lines.append("")
    lines.append("## Counts")
    lines.append(f"- pending_review_count: {d['pending_review_count']}")
    lines.append(f"- needs_revision_count: {d['needs_revision_count']}")
    lines.append(f"- held_for_real_artifact_count: {d['held_for_real_artifact_count']}")
    lines.append(f"- internal_review_accept_count: {d['internal_review_accept_count']}")
    lines.append(f"- manual_export_packet_accept_count: "
                 f"{d['manual_export_packet_accept_count']}")
    lines.append(f"- citation_guardrail_blocked_count: {d['citation_guardrail_blocked_count']}")
    lines.append("")
    lines.append("## Highest-Priority Packets")
    for i in export["highest_priority_items"]:
        lines.append(f"- {i['registry_record_id']}: queue={i['queue_status']} "
                     f"audit={i['audit_status']} decision={i['latest_decision_status']} "
                     f"blockers={i['blocker_count']}")
    lines.append("")
    lines.append("## Blockers and Warnings")
    for b in export["blocker_summary"]:
        lines.append(f"- BLOCKER {b['registry_record_id']}: count={b['blocker_count']} "
                     f"audit={b['audit_status']} citation={b['citation_guardrail_status']}")
    for w in export["warning_summary"]:
        lines.append(f"- WARNING {w['registry_record_id']}: count={w['warning_count']} "
                     f"source={w['source_reference_status']} "
                     f"limitations={w['limitation_visibility_status']}")
    lines.append("")
    lines.append("## Review / Decision History")
    for h in export["decision_history_summary"]:
        lines.append(f"- {h['registry_record_id']}: "
                     f"latest_decision_type={h['latest_decision_type']} "
                     f"status={h['latest_decision_status']} ({h['note']})")
    lines.append("")
    lines.append("## Ledger Lineage")
    for e in export["ledger_event_summary"]:
        lines.append(f"- [{e['event_type']}] {e['event_summary']} "
                     f"(publish_status={e['publish_status']})")
    lines.append("")
    lines.append("## Next Operator Actions")
    for action in export["next_operator_action_placeholders"]:
        lines.append(f"- {action} (local manual-review placeholder; grants no publish authority)")
    lines.append("")
    lines.append("## Non-Publishing Boundary")
    lines.append("This handoff is a LOCAL ADVISORY artifact only. It is NOT PUBLIC "
                 "POSTABLE. Manual export packet acceptance is a local-review artifact "
                 "decision and does NOT grant public approval, publish authority, "
                 "scheduling, or platform action.")
    return "\n".join(lines)



def validate_handoff_export(export: dict, items: list, known_registry_ids: set) -> dict:
    """Block/warn if the handoff export would weaken guardrail posture."""
    warnings = []
    blockers = []

    required_components = [
        "dashboard_summary", "registry_query_summary", "highest_priority_items",
        "blocker_summary", "warning_summary", "review_status_summary",
        "decision_history_summary", "ledger_event_summary",
        "next_operator_action_placeholders", "safety_posture",
    ]
    present = [c for c in required_components if export.get(c) is not None]
    if len(present) == 0:
        blockers.append("Handoff export has zero required components.")

    if export.get("approval_granted") or export.get("publish_ready"):
        blockers.append("Handoff export grants approval/publish authority.")
    if export.get("platform_action_allowed") or export.get("provider_call_allowed") \
            or export.get("search_call_allowed"):
        blockers.append("Handoff export grants provider/search/platform authority.")
    if not export.get("all_fixture_outputs_not_public_postable"):
        blockers.append("Handoff export does not affirm not-public-postable status.")

    d = export.get("dashboard_summary", {})
    if d.get("registry_record_count", 0) == 0 or d.get("ledger_entry_count", 0) == 0:
        blockers.append("Handoff demo path has zero registry records or ledger entries.")

    item_blocked = sum(1 for i in items if i.get("citation_guardrail_status") == "BLOCKED")
    if item_blocked != d.get("citation_guardrail_blocked_count", 0):
        blockers.append("Handoff export hides citation guardrail BLOCKED count.")

    dash_validation = dash.validate_dashboard(d, items, known_registry_ids)
    blockers.extend(dash_validation["blockers"])
    warnings.extend(dash_validation["warnings"])

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}


def build_summary() -> dict:
    """Deterministic CLI summary describing the handoff/export posture."""
    return {
        "status": "deterministic local packet dashboard export and operator handoff active",
        "local_only": True,
        "advisory_only": True,
        "handoff_export_enabled": True,
        "machine_readable_export_enabled": True,
        "markdown_report_enabled": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "all_fixture_outputs_not_public_postable": True,
        "fixture_backed_demo_record_count": 0,
        "fixture_backed_demo_ledger_entry_count": 0,
        "export_formats_supported": list(EXPORT_FORMATS_SUPPORTED),
        "validation_rules_enabled": True,
    }

