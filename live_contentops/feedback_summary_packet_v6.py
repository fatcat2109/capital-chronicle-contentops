"""V6 Feedback Summary Packet.

Combines snapshots, clusters, backlog candidates into an LLM-summary-ready packet without calling any remote providers.
"""
from __future__ import annotations

import hashlib
from typing import Any


def create_summary_packet(
    snapshots: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    backlog_candidates: list[dict[str, Any]]
) -> dict[str, Any]:
    """Assembles all community feedback components into a deterministic, summary-ready packet."""
    snap_ids = [s.get("snapshot_id") for s in snapshots]

    # Collect blocked items
    unsafe_or_blocked_items = []
    for s in snapshots:
        if s.get("blocked_reasons", []):
            unsafe_or_blocked_items.append({
                "snapshot_id": s.get("snapshot_id"),
                "blocked_reasons": s.get("blocked_reasons")
            })

    # Summary packet ID
    hasher = hashlib.sha256(f"{','.join(sorted(snap_ids))}".encode("utf-8"))
    summary_packet_id = f"summary_packet_{hasher.hexdigest()[:12]}"

    # Count of redacted vs unredacted snapshots
    redaction_count = 0
    for s in snapshots:
        if s.get("redaction_required") is True:
            redaction_count += 1

    redaction_status = {
        "snapshots_processed": len(snapshots),
        "redaction_performed_on_count": redaction_count,
        "policy": "NO_SECRET_VALUES_NO_IDS_NO_URLS"
    }

    packet = {
        "summary_packet_id": summary_packet_id,
        "input_snapshot_refs": sorted(snap_ids),
        "redaction_status": redaction_status,
        "clusters": clusters,
        "backlog_candidates": backlog_candidates,
        "unsafe_or_blocked_items": unsafe_or_blocked_items,
        "llm_provider_call_performed": False,
        "provider_credentials_hydrated": False,
        "human_review_required": True,
        "publication_allowed": False,
        "dispatch_allowed_now": False
    }

    return packet
