"""Test feedback summary packet assembly rules."""
from __future__ import annotations

from live_contentops import feedback_summary_packet_v6 as summary


def test_create_summary_packet():
    snapshots = [
        {
            "snapshot_id": "s1",
            "redaction_required": True,
            "blocked_reasons": []
        },
        {
            "snapshot_id": "s2",
            "redaction_required": False,
            "blocked_reasons": ["private_identifier_detected"]
        }
    ]
    clusters = [
        {
            "cluster_id": "c1",
            "cluster_label": "source_request"
        }
    ]
    candidates = [
        {
            "backlog_id": "b1",
            "source_cluster_id": "c1"
        }
    ]

    packet = summary.create_summary_packet(snapshots, clusters, candidates)

    assert packet["llm_provider_call_performed"] is False
    assert packet["provider_credentials_hydrated"] is False
    assert packet["human_review_required"] is True
    assert packet["publication_allowed"] is False
    assert packet["dispatch_allowed_now"] is False
    assert len(packet["unsafe_or_blocked_items"]) == 1
    assert packet["unsafe_or_blocked_items"][0]["snapshot_id"] == "s2"
    assert "private_identifier_detected" in packet["unsafe_or_blocked_items"][0]["blocked_reasons"]
    assert packet["redaction_status"]["snapshots_processed"] == 2
    assert packet["redaction_status"]["redaction_performed_on_count"] == 1
