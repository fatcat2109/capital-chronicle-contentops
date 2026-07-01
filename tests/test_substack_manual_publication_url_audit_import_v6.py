from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.substack_manual_publication_url_audit_import_v6 import (
    SubstackManualPublicationUrlAuditImportError,
    build_substack_manual_publication_url_audit_import_packet,
)

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs/automation/V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF/sample_substack_manual_export_operator_handoff_packet.json"
SAMPLE = ROOT / "docs/automation/V6_SUBSTACK_MANUAL_PUBLICATION_URL_AUDIT_IMPORT/sample_substack_manual_publication_url_audit_import_packet.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _build(**kwargs) -> dict:
    return build_substack_manual_publication_url_audit_import_packet(
        _read_json(HANDOFF),
        operator_supplied_publication_url=kwargs.get(
            "url", "https://capitalchronicle.substack.com/p/evaluate-historical-volatility-in-macro-calendar-commentaries"
        ),
        operator_supplied_publication_timestamp=kwargs.get("timestamp", "2026-07-01T05:00:00Z"),
    )


def test_committed_sample_matches_builder() -> None:
    assert _read_json(SAMPLE) == _build()


def test_packet_binds_handoff_export_evidence_and_article() -> None:
    handoff = _read_json(HANDOFF)
    packet = _build()
    assert packet["operator_handoff_packet_id"] == handoff["operator_handoff_packet_id"]
    assert packet["operator_handoff_hash"] == handoff["operator_handoff_hash"]
    assert packet["source_export_packet_id"] == handoff["source_export_packet_id"]
    assert packet["source_export_payload_hash"] == handoff["source_export_payload_hash"]
    assert packet["approval_export_evidence_packet_id"] == handoff["approval_export_evidence_packet_id"]
    assert packet["approval_export_evidence_hash"] == handoff["approval_export_evidence_hash"]
    assert packet["source_article_packet_id"] == handoff["source_article_packet_id"]
    assert packet["source_article_hash"] == handoff["source_article_hash"]
    assert packet["exact_payload_hash"] == handoff["exact_payload_hash"]


def test_safety_flags_and_operator_supplied_url_semantics() -> None:
    packet = _build(url="  https://capitalchronicle.substack.com/p/sample-proof  ")
    assert packet["operator_supplied_publication_url"] == "https://capitalchronicle.substack.com/p/sample-proof"
    assert packet["operator_supplied_publication_url_hash"]
    assert packet["operator_supplied_url_verification_status"] == "operator_supplied_not_network_verified"
    assert packet["publication_audit_status"] == "manual_url_imported_pending_operator_review"
    assert packet["url_network_verified"] is False
    assert packet["substack_api_used"] is False
    assert packet["provider_call_made"] is False
    assert packet["network_call_made"] is False
    assert packet["credential_read_made"] is False
    assert packet["env_value_read_made"] is False
    assert packet["browser_session_used"] is False
    assert packet["live_publish_performed_by_contentops"] is False
    assert packet["manual_publication_claim_operator_supplied"] is True
    assert packet["enabled_publish_send_dispatch_approve_controls"] is False


def test_rejects_non_https_and_control_whitespace_urls() -> None:
    with pytest.raises(SubstackManualPublicationUrlAuditImportError, match="operator_url_must_be_https"):
        _build(url="http://capitalchronicle.substack.com/p/sample")
    with pytest.raises(SubstackManualPublicationUrlAuditImportError, match="operator_url_contains_control_whitespace"):
        _build(url="https://capitalchronicle.substack.com/p/sample\nnext")


def test_rejects_secret_or_session_material() -> None:
    handoff = _read_json(HANDOFF)
    handoff["operator_instructions"] = ["cookie: secret"]
    with pytest.raises(SubstackManualPublicationUrlAuditImportError, match="forbidden_secret_or_session_material"):
        build_substack_manual_publication_url_audit_import_packet(
            handoff,
            operator_supplied_publication_url="https://capitalchronicle.substack.com/p/sample",
            operator_supplied_publication_timestamp="2026-07-01T05:00:00Z",
        )
