"""Local-only deterministic packet registry query utilities (v0).

Filter, sort, and group registry records and review-ledger entries. Helps an
operator inspect packet status, blockers, review state, and ledger lineage
WITHOUT granting any publishing authority.

Performs NO network, provider, LLM, search, or platform calls. Every query
result is advisory-only and explicitly NOT PUBLIC POSTABLE.
"""

# Supported filter keys (advisory inspection only).
SUPPORTED_FILTERS = [
    "packet_status",
    "queue_status",
    "latest_decision_status",
    "audit_status",
    "content_type",
    "target_platform",
    "source_fixture_id",
    "source_draft_id",
    "has_blockers",
    "has_warnings",
    "publish_ready",
    "approval_granted",
    "not_public_postable",
    "decision_type",
    "event_type",
]

SUPPORTED_GROUPINGS = [
    "status_severity",
    "content_type",
    "target_platform",
    "latest_decision_status",
    "blocker_count",
]

# Lower number = higher severity (sorted first).
STATUS_SEVERITY_ORDER = {
    "BLOCKED": 0,
    "NEEDS_REVISION": 1,
    "PENDING_REVIEW": 2,
    "HELD_FOR_REAL_ARTIFACT": 3,
    "ACCEPTED_INTERNAL_REVIEW_ONLY": 4,
    "ACCEPTED_MANUAL_EXPORT_PACKET_ONLY": 5,
}


def _latest_ledger_for_record(record_id: str, ledger: list):
    entries = [e for e in ledger if e.get("registry_record_id") == record_id]
    return entries[-1] if entries else None


def _latest_decision_event(record_id: str, ledger: list):
    decision_events = [
        e for e in ledger
        if e.get("registry_record_id") == record_id and e.get("decision_type")
    ]
    return decision_events[-1] if decision_events else None


def build_query_item(record: dict, ledger: list) -> dict:
    """Build a deterministic, advisory query-result item for a registry record."""
    record_id = record.get("registry_record_id")
    latest_entry = _latest_ledger_for_record(record_id, ledger)
    latest_decision_entry = _latest_decision_event(record_id, ledger)

    return {
        "registry_record_id": record_id,
        "export_packet_id": record.get("export_packet_id"),
        "queue_item_id": record.get("queue_item_id"),
        "history_id": record.get("history_id"),
        "content_type": record.get("content_type"),
        "target_platforms": record.get("target_platforms", []),
        "packet_status": record.get("packet_status"),
        "queue_status": record.get("queue_status"),
        "latest_decision_status": record.get("latest_decision_status"),
        "audit_status": record.get("audit_status"),
        "citation_guardrail_status": record.get("citation_guardrail_status"),
        "source_reference_status": record.get("source_reference_status"),
        "limitation_visibility_status": record.get("limitation_visibility_status"),
        "blocker_count": _blocker_count(record_id, ledger),
        "warning_count": _warning_count(record_id, ledger),
        "latest_event_type": latest_entry.get("event_type") if latest_entry else None,
        "latest_decision_type": (latest_decision_entry.get("decision_type")
                                 if latest_decision_entry else None),
        "no_public_post_reason": record.get("no_public_post_reason"),
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }


def _blocker_count(record_id: str, ledger: list) -> int:
    return max((e.get("blocker_count", 0)
                for e in ledger if e.get("registry_record_id") == record_id), default=0)


def _warning_count(record_id: str, ledger: list) -> int:
    return max((e.get("warning_count", 0)
                for e in ledger if e.get("registry_record_id") == record_id), default=0)


def build_query_items(registry_records: list, ledger: list) -> list:
    return [build_query_item(r, ledger) for r in registry_records]


def filter_items(items: list, filters: dict) -> list:
    """Deterministically filter advisory query items. Read-only inspection."""
    result = list(items)
    for key, value in (filters or {}).items():
        if key == "target_platform":
            result = [i for i in result if value in (i.get("target_platforms") or [])]
        elif key in ("source_fixture_id", "source_draft_id"):
            result = [i for i in result if i.get("registry_record_id") and value
                      in (i.get("export_packet_id") or i.get("registry_record_id") or "")
                      or i.get(key) == value]
        elif key == "has_blockers":
            result = [i for i in result if (i.get("blocker_count", 0) > 0) == bool(value)]
        elif key == "has_warnings":
            result = [i for i in result if (i.get("warning_count", 0) > 0) == bool(value)]
        elif key == "not_public_postable":
            # All items are not public postable; this filter never returns postable items.
            result = [i for i in result if bool(i.get("no_public_post_reason")) == bool(value)]
        elif key == "decision_type":
            result = [i for i in result if i.get("latest_decision_type") == value]
        elif key == "event_type":
            result = [i for i in result if i.get("latest_event_type") == value]
        else:
            result = [i for i in result if i.get(key) == value]
    return result


def _severity_key(item: dict):
    queue = STATUS_SEVERITY_ORDER.get(item.get("queue_status"), 90)
    decision = STATUS_SEVERITY_ORDER.get(item.get("latest_decision_status"), 90)
    severity = min(queue, decision)
    # Tie-break deterministically by blocker_count desc then record id.
    return (severity, -item.get("blocker_count", 0), item.get("registry_record_id") or "")


def sort_items(items: list, by: str = "status_severity") -> list:
    """Deterministic sorting of advisory query items."""
    if by == "status_severity":
        return sorted(items, key=_severity_key)
    if by == "blocker_count":
        return sorted(items, key=lambda i: (-i.get("blocker_count", 0),
                                            i.get("registry_record_id") or ""))
    if by == "content_type":
        return sorted(items, key=lambda i: (i.get("content_type") or "",
                                            i.get("registry_record_id") or ""))
    if by == "latest_decision_status":
        return sorted(items, key=lambda i: (i.get("latest_decision_status") or "",
                                            i.get("registry_record_id") or ""))
    if by == "target_platform":
        return sorted(items, key=lambda i: ((i.get("target_platforms") or [""])[0],
                                            i.get("registry_record_id") or ""))
    return sorted(items, key=lambda i: i.get("registry_record_id") or "")


def group_items(items: list, by: str = "status_severity") -> dict:
    """Deterministic grouping of advisory query items into ordered buckets."""
    groups = {}
    for item in sort_items(items, by if by in ("blocker_count", "status_severity") else "status_severity"):
        if by == "status_severity":
            key = item.get("queue_status") or "UNKNOWN"
        elif by == "content_type":
            key = item.get("content_type") or "UNKNOWN"
        elif by == "target_platform":
            key = (item.get("target_platforms") or ["UNKNOWN"])[0]
        elif by == "latest_decision_status":
            key = item.get("latest_decision_status") or "UNKNOWN"
        elif by == "blocker_count":
            key = str(item.get("blocker_count", 0))
        else:
            key = "ALL"
        groups.setdefault(key, []).append(item)
    return groups


def highest_priority_items(items: list, limit: int = 5) -> list:
    """Return the highest-severity items first (BLOCKED before lower risk)."""
    return sort_items(items, "status_severity")[:limit]


def validate_query_items(items: list, known_registry_ids: set) -> dict:
    """Block/warn on any query result that weakens guardrail posture."""
    warnings = []
    blockers = []
    for item in items:
        if item.get("publish_ready"):
            blockers.append("Query result marks publish_ready=true.")
        if item.get("approval_granted") or item.get("platform_action_allowed"):
            blockers.append("Query result grants approval/platform action.")
        if item.get("provider_call_allowed") or item.get("search_call_allowed"):
            blockers.append("Query result grants provider/search authority.")
        if not item.get("no_public_post_reason"):
            blockers.append("Query result item lacks no_public_post_reason.")
        # Hidden BLOCKED audit/citation behind an accepted status.
        blocked = (item.get("audit_status") == "BLOCKED"
                   or item.get("citation_guardrail_status") == "BLOCKED")
        if blocked and str(item.get("latest_decision_status", "")).startswith("ACCEPTED"):
            blockers.append("Query result hides BLOCKED audit/citation behind accepted status.")
        if item.get("source_reference_status") == "MISSING":
            warnings.append("Query result notes missing source references.")
        if item.get("limitation_visibility_status") == "MISSING":
            warnings.append("Query result notes missing limitations.")
        if known_registry_ids is not None and item.get("registry_record_id") not in known_registry_ids:
            blockers.append("Query result references unknown registry record.")

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}

