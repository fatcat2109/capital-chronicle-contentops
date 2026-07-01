from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.substack_publication_audit_review_metrics_summary_v6 import (
    SubstackPublicationAuditReviewMetricsSummaryError,
    build_substack_publication_audit_review_metrics_summary_packet,
)

ROOT = Path(__file__).resolve().parents[1]
URL_AUDIT = ROOT / "docs/automation/V6_SUBSTACK_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_substack_manual_publication_url_audit_import_packet.json"
SAMPLE = ROOT / "docs/automation/V6_SUBSTACK_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY/sample_substack_publication_audit_review_metrics_summary_packet.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _build(**kwargs) -> dict:
    return build_substack_publication_audit_review_metrics_summary_packet(
        _read_json(URL_AUDIT),
        operator_supplied_views=kwargs.get("views", 1240),
        operator_supplied_opens=kwargs.get("opens", 820),
        operator_supplied_likes=kwargs.get("likes", 45),
        operator_supplied_comments=kwargs.get("comments", 8),
        operator_supplied_shares=kwargs.get("shares", 12),
        operator_supplied_restacks=kwargs.get("restacks", 3),
        operator_supplied_subscribers_delta=kwargs.get("subscribers_delta", 15),
        operator_supplied_notes=kwargs.get("notes", "Fixture metrics for evaluation purposes only."),
    )


def test_committed_sample_matches_builder() -> None:
    assert _read_json(SAMPLE) == _build()


def test_packet_binds_url_audit_and_handoff_hashes() -> None:
    url_audit = _read_json(URL_AUDIT)
    packet = _build()
    assert packet["publication_url_audit_packet_id"] == url_audit["publication_url_audit_packet_id"]
    assert packet["publication_url_audit_hash"] == url_audit["publication_url_audit_hash"]
    assert packet["operator_handoff_packet_id"] == url_audit["operator_handoff_packet_id"]
    assert packet["operator_handoff_hash"] == url_audit["operator_handoff_hash"]
    assert packet["source_export_packet_id"] == url_audit["source_export_packet_id"]
    assert packet["source_export_payload_hash"] == url_audit["source_export_payload_hash"]
    assert packet["approval_export_evidence_packet_id"] == url_audit["approval_export_evidence_packet_id"]
    assert packet["approval_export_evidence_hash"] == url_audit["approval_export_evidence_hash"]
    assert packet["source_article_packet_id"] == url_audit["source_article_packet_id"]
    assert packet["source_article_hash"] == url_audit["source_article_hash"]
    assert packet["exact_payload_hash"] == url_audit["exact_payload_hash"]
    assert packet["operator_supplied_publication_url"] == url_audit["operator_supplied_publication_url"]
    assert packet["operator_supplied_publication_url_hash"] == url_audit["operator_supplied_publication_url_hash"]
    assert packet["operator_supplied_publication_timestamp"] == url_audit["operator_supplied_publication_timestamp"]


def test_metrics_fixture_posture_and_provenance() -> None:
    packet = _build(views=100, opens=80)
    assert packet["manual_metrics"]["views"] == 100
    assert packet["manual_metrics"]["opens"] == 80
    assert packet["metrics_source"] == "operator_supplied_manual_entry"
    assert packet["metrics_network_verified"] is False
    assert packet["metrics_provider_api_used"] is False
    assert packet["url_network_verified"] is False
    assert packet["substack_api_used"] is False
    assert packet["provider_call_made"] is False
    assert packet["network_call_made"] is False
    assert packet["credential_read_made"] is False
    assert packet["env_value_read_made"] is False
    assert packet["browser_session_used"] is False
    assert packet["live_publish_performed_by_contentops"] is False
    assert packet["manual_publication_claim_operator_supplied"] is True
    assert packet["manual_metrics_claim_operator_supplied"] is True
    assert packet["enabled_publish_send_dispatch_approve_controls"] is False


def test_rejects_secret_or_session_material() -> None:
    url_audit = _read_json(URL_AUDIT)
    url_audit["operator_supplied_publication_url"] = "https://discord.com/api/webhooks/12345"
    with pytest.raises(SubstackPublicationAuditReviewMetricsSummaryError, match="forbidden_secret_or_session_material"):
        build_substack_publication_audit_review_metrics_summary_packet(url_audit)
