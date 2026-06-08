"""Local-only deterministic review ledger (v0).

Append-only-style local ledger of packet lifecycle events spanning export,
audit, queue, operator decisions, and review history. No ledger event grants
publishing authority. Synthetic/demo/fixture content stays NOT PUBLIC POSTABLE.

Performs NO network, provider, LLM, search, or platform calls.
"""

import hashlib

SUPPORTED_EVENT_TYPES = [
    "PACKET_EXPORTED",
    "AUDIT_COMPLETED",
    "QUEUE_ITEM_CREATED",
    "OPERATOR_DECISION_RECORDED",
    "REVIEW_HISTORY_UPDATED",
    "REGISTRY_RECORD_UPDATED",
    "BLOCKER_DETECTED",
    "REVISION_REQUESTED",
    "HELD_FOR_REAL_ARTIFACT",
    "INTERNAL_REVIEW_ACCEPTED",
    "MANUAL_EXPORT_PACKET_ACCEPTED",
]

AUTHORITY_BOUNDARY_NOTE = (
    "Local advisory event only. Grants no approval, publish, platform, "
    "scheduling, or execution authority. Content remains NOT PUBLIC POSTABLE."
)


def _deterministic_id(prefix: str, seed: str) -> str:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def build_ledger_entry(registry_record: dict, event_type: str, **kwargs) -> dict:
    """Build one deterministic ledger entry for a lifecycle event."""
    registry_record_id = registry_record.get("registry_record_id", "unknown_registry")
    export_packet_id = registry_record.get("export_packet_id", "unknown_export_packet")
    queue_item_id = registry_record.get("queue_item_id", "unknown_queue_item")
    history_id = registry_record.get("history_id", "unknown_history")

    seed = f"{registry_record_id}:{event_type}:{kwargs.get('seq', 0)}"

    return {
        "ledger_entry_id": _deterministic_id("led", seed),
        "registry_record_id": registry_record_id,
        "export_packet_id": export_packet_id,
        "queue_item_id": queue_item_id,
        "history_id": history_id,
        "event_type": event_type,
        "event_timestamp": "DETERMINISTIC_TIMESTAMP",
        "event_source": kwargs.get("event_source", "local_workflow"),
        "event_summary": kwargs.get("event_summary", ""),
        "blocker_count": kwargs.get("blocker_count", 0),
        "warning_count": kwargs.get("warning_count", 0),
        "decision_type": kwargs.get("decision_type"),
        "decision_status": kwargs.get("decision_status"),
        "publish_status": "NOT_PUBLIC_POSTABLE",
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "authority_boundary_note": AUTHORITY_BOUNDARY_NOTE,
    }


def build_ledger(registry_record: dict, packet: dict, queue_item: dict, history: dict) -> list:
    """Build a deterministic, ordered lifecycle ledger for one packet."""
    entries = []
    audit_detail = queue_item.get("audit_detail", {})

    entries.append(build_ledger_entry(
        registry_record, "PACKET_EXPORTED", seq=0,
        event_source="editorial_packet_export",
        event_summary=f"Exported packet {registry_record.get('export_packet_id')}.",
    ))
    entries.append(build_ledger_entry(
        registry_record, "AUDIT_COMPLETED", seq=1,
        event_source="packet_audit",
        event_summary=f"Audit status {queue_item.get('audit_status')}.",
        blocker_count=audit_detail.get("blocker_count", 0),
        warning_count=audit_detail.get("warning_count", 0),
    ))
    entries.append(build_ledger_entry(
        registry_record, "QUEUE_ITEM_CREATED", seq=2,
        event_source="packet_review_queue",
        event_summary=f"Queue status {queue_item.get('queue_status')}.",
        blocker_count=queue_item.get("blocker_count", 0),
        warning_count=queue_item.get("warning_count", 0),
    ))

    if queue_item.get("blocker_count", 0) > 0:
        entries.append(build_ledger_entry(
            registry_record, "BLOCKER_DETECTED", seq=3,
            event_source="packet_audit",
            event_summary="One or more blockers detected; packet remains not public postable.",
            blocker_count=queue_item.get("blocker_count", 0),
        ))

    seq = 10
    for record in history.get("decision_records", []):
        entries.append(build_ledger_entry(
            registry_record, "OPERATOR_DECISION_RECORDED", seq=seq,
            event_source="operator_decision",
            event_summary=f"Operator recorded {record.get('decision_type')}.",
            decision_type=record.get("decision_type"),
            decision_status=record.get("decision_status"),
        ))
        seq += 1
        event = _decision_event_type(record)
        if event:
            entries.append(build_ledger_entry(
                registry_record, event, seq=seq,
                event_source="operator_decision",
                event_summary=f"{event} (advisory, not public approval).",
                decision_type=record.get("decision_type"),
                decision_status=record.get("decision_status"),
            ))
            seq += 1

    entries.append(build_ledger_entry(
        registry_record, "REVIEW_HISTORY_UPDATED", seq=seq,
        event_source="review_history",
        event_summary=f"Latest review status {history.get('current_review_status')}.",
    ))
    entries.append(build_ledger_entry(
        registry_record, "REGISTRY_RECORD_UPDATED", seq=seq + 1,
        event_source="packet_registry",
        event_summary="Registry record indexed.",
    ))
    return entries


def _decision_event_type(record: dict):
    """Map a non-blocked decision to a ledger event type."""
    if record.get("decision_status") == "BLOCKED":
        return None
    return {
        "REQUEST_REVISION": "REVISION_REQUESTED",
        "HOLD_FOR_REAL_ARTIFACT": "HELD_FOR_REAL_ARTIFACT",
        "ACCEPT_FOR_INTERNAL_REVIEW_ONLY": "INTERNAL_REVIEW_ACCEPTED",
        "ACCEPT_FOR_MANUAL_EXPORT_PACKET_ONLY": "MANUAL_EXPORT_PACKET_ACCEPTED",
    }.get(record.get("decision_type"))


def validate_ledger(ledger: list, known_registry_ids: set) -> dict:
    """Local validation of a ledger against known registry record ids."""
    warnings = []
    blockers = []

    for entry in ledger:
        if entry.get("event_type") not in SUPPORTED_EVENT_TYPES:
            blockers.append(f"Unknown ledger event type: {entry.get('event_type')}")
        if entry.get("registry_record_id") not in known_registry_ids:
            blockers.append(
                f"Ledger entry references unknown registry record: "
                f"{entry.get('registry_record_id')}"
            )
        if entry.get("approval_granted") or entry.get("publish_ready"):
            blockers.append("Ledger event grants approval/publish authority.")
        if entry.get("platform_action_allowed") or entry.get("provider_call_allowed") \
                or entry.get("search_call_allowed"):
            blockers.append("Ledger event grants provider/search/platform authority.")
        if entry.get("publish_status") != "NOT_PUBLIC_POSTABLE":
            blockers.append("Ledger event publish status is not NOT_PUBLIC_POSTABLE.")

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}



def summarize_registry(registry_records: list, ledger: list) -> dict:
    """Deterministic registry + ledger summary."""
    pending_review_count = 0
    blocked_count = 0
    needs_revision_count = 0
    for record in registry_records:
        qs = record.get("queue_status")
        if qs == "PENDING_REVIEW":
            pending_review_count += 1
        elif qs == "BLOCKED":
            blocked_count += 1
        elif qs == "NEEDS_REVISION":
            needs_revision_count += 1

    held = sum(1 for e in ledger if e.get("event_type") == "HELD_FOR_REAL_ARTIFACT")
    internal = sum(1 for e in ledger if e.get("event_type") == "INTERNAL_REVIEW_ACCEPTED")
    manual = sum(1 for e in ledger if e.get("event_type") == "MANUAL_EXPORT_PACKET_ACCEPTED")

    return {
        "status": "deterministic local review ledger and packet registry active",
        "registry_record_count": len(registry_records),
        "ledger_entry_count": len(ledger),
        "pending_review_count": pending_review_count,
        "blocked_count": blocked_count,
        "needs_revision_count": needs_revision_count,
        "held_for_real_artifact_count": held,
        "internal_review_accept_count": internal,
        "manual_export_packet_accept_count": manual,
        "publish_ready_count": 0,
        "approval_granted_count": 0,
        "all_fixture_outputs_not_public_postable": True,
        "live_actions_disabled": True,
        "advisory_only": True,
    }


MARKDOWN_BANNERS = [
    "LOCAL ONLY",
    "ADVISORY ONLY",
    "PACKET REGISTRY",
    "REVIEW LEDGER",
    "HUMAN REVIEW REQUIRED",
    "NOT PUBLIC POSTABLE",
    "NO PROVIDER CALL",
    "NO SEARCH CALL",
    "NO PLATFORM ACTION",
]


def render_markdown_report(registry_records: list, ledger: list) -> str:
    """Render a deterministic markdown registry/ledger report with banners."""
    summary = summarize_registry(registry_records, ledger)
    lines = []
    lines.append("# Review Ledger and Packet Registry (v0)")
    lines.append("")
    lines.append("> " + " | ".join(MARKDOWN_BANNERS))
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- registry_record_count: {summary['registry_record_count']}")
    lines.append(f"- ledger_entry_count: {summary['ledger_entry_count']}")
    lines.append(f"- pending_review_count: {summary['pending_review_count']}")
    lines.append(f"- blocked_count: {summary['blocked_count']}")
    lines.append(f"- needs_revision_count: {summary['needs_revision_count']}")
    lines.append(f"- held_for_real_artifact_count: {summary['held_for_real_artifact_count']}")
    lines.append(f"- internal_review_accept_count: {summary['internal_review_accept_count']}")
    lines.append(f"- manual_export_packet_accept_count: "
                 f"{summary['manual_export_packet_accept_count']}")
    lines.append("")
    lines.append("## Safety Posture")
    lines.append("- approval_granted=false")
    lines.append("- publish_ready=false")
    lines.append("- current_publish_status: NOT_PUBLIC_POSTABLE")
    lines.append("")
    lines.append("## Registry Records")
    for record in registry_records:
        lines.append(f"### {record.get('registry_record_id')}")
        lines.append(f"- export_packet_id: {record.get('export_packet_id')}")
        lines.append(f"- queue_status: {record.get('queue_status')}")
        lines.append(f"- audit_status: {record.get('audit_status')}")
        lines.append(f"- citation_guardrail_status: {record.get('citation_guardrail_status')}")
        lines.append(f"- latest_decision_status: {record.get('latest_decision_status')}")
        lines.append(f"- no_public_post_reason: {record.get('no_public_post_reason')}")
        lines.append("")
    lines.append("## Ledger Entries")
    for entry in ledger:
        lines.append(f"- [{entry.get('event_type')}] {entry.get('event_summary')}")
    return "\n".join(lines)


def build_summary() -> dict:
    """Deterministic CLI summary describing the registry/ledger posture."""
    return {
        "status": "deterministic local review ledger and packet registry active",
        "local_only": True,
        "advisory_only": True,
        "packet_registry_enabled": True,
        "review_ledger_enabled": True,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "all_fixture_outputs_not_public_postable": True,
        "registry_record_count": 0,
        "ledger_entry_count": 0,
        "supported_event_types": list(SUPPORTED_EVENT_TYPES),
        "validation_rules_enabled": True,
    }

