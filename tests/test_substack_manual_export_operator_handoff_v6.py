from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.substack_manual_export_operator_handoff_v6 import (
    SubstackManualExportOperatorHandoffError,
    build_substack_manual_export_operator_handoff_packet,
)

ROOT = Path(__file__).resolve().parents[1]
EXPORT_SAMPLE = ROOT / "docs/automation/V6_SUBSTACK_MANUAL_EXPORT_ARTICLE_STUDIO/sample_substack_manual_export_article_studio_packet.json"
EVIDENCE_SAMPLE = ROOT / "docs/automation/V6_SUBSTACK_MANUAL_APPROVAL_EXPORT_EVIDENCE/sample_substack_manual_approval_export_evidence_packet.json"
SAMPLE = ROOT / "docs/automation/V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF/sample_substack_manual_export_operator_handoff_packet.json"


def _export() -> dict:
    return json.loads(EXPORT_SAMPLE.read_text(encoding="utf-8-sig"))


def _evidence() -> dict:
    return json.loads(EVIDENCE_SAMPLE.read_text(encoding="utf-8-sig"))


def _sample() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8-sig"))


def test_committed_sample_matches_builder() -> None:
    built = build_substack_manual_export_operator_handoff_packet(_export(), _evidence())
    assert _sample() == built
    assert built["operator_handoff_packet_id"].startswith("substack_manual_export_operator_handoff_")
    assert built["source_export_packet_id"] == "substack_manual_export_e556b07116d81110"
    assert built["source_export_payload_hash"] == "e556b07116d81110da7f8b96f5e5d39b80d65ce16c0c190eb51cdc9fdbd1f335"
    assert built["approval_export_evidence_packet_id"] == "substack_manual_approval_export_evidence_ba20cf65f42da369"
    assert built["approval_export_evidence_hash"] == "ba20cf65f42da3691a30690fc90be7f09ac0b446ced30920a5f489595d80ffb8"


def test_required_safety_flags_are_closed() -> None:
    packet = build_substack_manual_export_operator_handoff_packet(_export(), _evidence())
    assert packet["approval_status"] == "pending"
    assert packet["operator_handoff_status"] == "ready_for_manual_review"
    assert packet["manual_copy_only"] is True
    for key in ["live_publish_allowed", "live_publish_performed", "substack_api_used", "provider_call_made", "network_call_made", "credential_read_made", "env_value_read_made", "browser_session_used", "enabled_publish_send_dispatch_approve_controls"]:
        assert packet[key] is False
    assert packet["sample_scope"] == "sample_fixture_only"


def test_evidence_cards_cover_required_handoff_lane() -> None:
    packet = build_substack_manual_export_operator_handoff_packet(_export(), _evidence())
    card_types = {card["card_type"] for card in packet["evidence_cards"]}
    assert card_types == {"canonical_article_source", "manual_export_payload", "approval_export_evidence_packet", "manual_copy_checklist", "blocked_live_publish_state", "operator_handoff_packet"}
    checklist = {item["check_id"]: item for item in packet["manual_copy_checklist"]}
    assert checklist["confirm_manual_copy_only"]["status"] == "pending_review"
    assert checklist["confirm_export_payload"]["required"] is True


def test_no_secret_env_provider_webhook_or_session_material_serialized() -> None:
    serialized = json.dumps(build_substack_manual_export_operator_handoff_packet(_export(), _evidence()), sort_keys=True).lower()
    for term in ["https://discord.com/api/webhooks/", "discord_live_announcements_webhook=https", "sk-", "xoxb-", "ghp_", "bearer ", "cookie=", "localstorage=", "sessionstorage="]:
        assert term not in serialized


@pytest.mark.parametrize(("field", "value"), [("live_publish_allowed", True), ("live_publish_performed", True), ("provider_call_made", True), ("network_call_made", True), ("browser_session_used", True)])
def test_source_export_must_remain_closed(field: str, value: bool) -> None:
    export = copy.deepcopy(_export())
    export[field] = value
    with pytest.raises(SubstackManualExportOperatorHandoffError):
        build_substack_manual_export_operator_handoff_packet(export, _evidence())


def test_binding_mismatch_fails_closed() -> None:
    evidence = copy.deepcopy(_evidence())
    evidence["source_export_packet_id"] = "wrong"
    with pytest.raises(SubstackManualExportOperatorHandoffError):
        build_substack_manual_export_operator_handoff_packet(_export(), evidence)
