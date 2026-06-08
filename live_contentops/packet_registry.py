"""Local-only deterministic packet registry (v0).

Indexes grounded editorial packets, review queue items, audits, operator
decisions, and review histories into deterministic local registry records.
Makes the offline workflow traceable WITHOUT granting publishing authority.

Performs NO network, provider, LLM, search, or platform calls. Every registry
record is advisory-only and explicitly NOT PUBLIC POSTABLE.
"""

import hashlib


def _deterministic_id(prefix: str, seed: str) -> str:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def build_registry_record(packet: dict, queue_item: dict, history: dict) -> dict:
    """Build one deterministic registry record from the workflow layers."""
    export_packet_id = (packet.get("export_packet_id")
                        or queue_item.get("export_packet_id")
                        or "unknown_export_packet")
    queue_item_id = queue_item.get("queue_item_id", "unknown_queue_item")
    history_id = history.get("history_id", "unknown_history")
    source_id = (packet.get("source_fixture_id")
                 or queue_item.get("source_fixture_id")
                 or queue_item.get("source_draft_id")
                 or "export_fixture")

    audit_detail = queue_item.get("audit_detail", {})
    latest_decision = history.get("latest_decision") or {}
    latest_decision_status = latest_decision.get("decision_status", "PENDING_MANUAL_REVIEW")

    no_public_post_reason = (queue_item.get("no_public_post_reason")
                             or "Synthetic/demo/fixture packet - not public postable.")

    return {
        "registry_record_id": _deterministic_id("reg", export_packet_id),
        "export_packet_id": export_packet_id,
        "queue_item_id": queue_item_id,
        "history_id": history_id,
        "source_fixture_id": source_id,
        "content_type": queue_item.get("content_type", "post"),
        "target_platforms": queue_item.get("target_platforms", []),
        "packet_status": "REGISTERED",
        "queue_status": queue_item.get("queue_status", "PENDING_REVIEW"),
        "latest_decision_status": latest_decision_status,
        "audit_status": queue_item.get("audit_status", "UNKNOWN"),
        "citation_guardrail_status": audit_detail.get("citation_guardrail_status", "UNKNOWN"),
        "source_reference_status": audit_detail.get("source_reference_status", "UNKNOWN"),
        "limitation_visibility_status": audit_detail.get("limitation_visibility_status", "UNKNOWN"),
        "created_at": "DETERMINISTIC_TIMESTAMP",
        "updated_at": "DETERMINISTIC_TIMESTAMP",
        "no_public_post_reason": no_public_post_reason,
        "advisory_only": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }


def validate_registry_record(record: dict) -> dict:
    """Local validation of a single registry record."""
    warnings = []
    blockers = []

    for key in ("export_packet_id", "queue_item_id", "history_id"):
        if not record.get(key):
            blockers.append(f"Registry record missing {key}.")

    if record.get("approval_granted") or record.get("publish_ready"):
        blockers.append("Registry record grants approval/publish authority.")
    if record.get("platform_action_allowed") or record.get("provider_call_allowed") \
            or record.get("search_call_allowed"):
        blockers.append("Registry record grants provider/search/platform authority.")
    if not record.get("no_public_post_reason"):
        blockers.append("Registry record missing no_public_post_reason.")

    # A BLOCKED audit/citation status must not be paired with an accepted status.
    blocked = (record.get("audit_status") == "BLOCKED"
               or record.get("citation_guardrail_status") == "BLOCKED")
    if blocked and str(record.get("latest_decision_status", "")).startswith("ACCEPTED"):
        blockers.append("Registry record hides BLOCKED audit/citation behind an accepted status.")

    # Source/limitation problems must remain visible.
    if record.get("source_reference_status") == "MISSING":
        warnings.append("Registry record notes missing source references.")
    if record.get("limitation_visibility_status") == "MISSING":
        warnings.append("Registry record notes missing limitations.")

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}
