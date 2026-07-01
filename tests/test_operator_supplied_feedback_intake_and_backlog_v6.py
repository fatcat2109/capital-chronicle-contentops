"""Tests for operator-supplied feedback intake and backlog loop v6."""
from __future__ import annotations

import pytest

from live_contentops.operator_feedback_backlog_summary_v6 import build_operator_feedback_backlog_summary_packet
from live_contentops.operator_supplied_feedback_intake_v6 import build_operator_supplied_feedback_intake_packet


def test_feedback_intake_packet_is_manual_only_and_bound_to_registry_audit_index() -> None:
    packet = build_operator_supplied_feedback_intake_packet()

    assert packet["packet_kind"] == "operator_supplied_feedback_intake_v0"
    assert packet["intake_status"] == "operator_supplied_only"
    assert packet["feedback_count"] == 4
    assert packet["registry_packet_id"].startswith("manual_distribution_evidence_registry_")
    assert packet["audit_index_packet_id"].startswith("manual_distribution_registry_audit_index_")
    assert packet["network_call_made"] is False
    assert packet["provider_call_made"] is False
    assert packet["llm_provider_call_made"] is False
    assert packet["public_url_fetch_made"] is False
    assert packet["platform_api_used"] is False
    assert packet["live_publish_performed_by_contentops"] is False
    assert packet["forbidden_financial_advice_or_signal_wording_present"] is False
    assert packet["feedback_intake_packet_id"].endswith(packet["exact_payload_hash"][:16])
    for item in packet["feedback_items"]:
        assert item["operator_supplied_claim"] is True
        assert item["source_url_network_verified"] is False
        assert item["source_scraped"] is False
        assert item["source_api_used"] is False


def test_feedback_intake_rejects_signal_or_advice_wording() -> None:
    with pytest.raises(ValueError):
        build_operator_supplied_feedback_intake_packet([
            {
                "feedback_item_id": "bad",
                "source_platform": "manual_note",
                "source_kind": "manual_note",
                "operator_supplied_text": "This should be treated as financial advice.",
                "operator_supplied_timestamp": "2026-07-01T00:00:00Z",
                "source_url_text_optional": "",
                "sentiment_label": "neutral",
                "topic_tags": ["bad"],
            }
        ])


def test_backlog_summary_is_deterministic_review_only_no_llm() -> None:
    intake = build_operator_supplied_feedback_intake_packet()
    packet = build_operator_feedback_backlog_summary_packet(intake)

    assert packet["packet_kind"] == "operator_feedback_backlog_summary_v0"
    assert packet["summary_method"] == "deterministic_tag_grouping_no_llm"
    assert packet["backlog_status"] == "ready_for_operator_review_only"
    assert packet["feedback_intake_packet_id"] == intake["feedback_intake_packet_id"]
    assert packet["feedback_intake_hash"] == intake["exact_payload_hash"]
    assert packet["candidate_count"] >= 3
    assert packet["network_call_made"] is False
    assert packet["provider_call_made"] is False
    assert packet["llm_provider_call_made"] is False
    assert packet["public_url_fetch_made"] is False
    assert packet["platform_api_used"] is False
    assert packet["live_publish_performed_by_contentops"] is False
    assert packet["non_readiness_claims"] == {
        "live_readiness_claimed": False,
        "api_readiness_claimed": False,
        "llm_summary_claimed": False,
        "public_url_verification_claimed": False,
        "dispatch_readiness_claimed": False,
    }
    assert packet["backlog_summary_packet_id"].endswith(packet["exact_payload_hash"][:16])
    assert packet["backlog_candidates"] == sorted(
        packet["backlog_candidates"],
        key=lambda candidate: (-candidate["priority_score"], candidate["candidate_id"]),
    )
