"""Tests for operator feedback backlog V5 adapter codegen/check guardrail."""
from __future__ import annotations

import json
import re
from pathlib import Path

from live_contentops.operator_feedback_backlog_v5_adapter_codegen_v6 import (
    ROOT,
    build_operator_feedback_backlog_v5_adapter_text,
    check_operator_feedback_backlog_v5_adapter_in_sync,
)

ADAPTER_PATH = ROOT / "ui/contentops_v5/src/data/operatorFeedbackBacklogAdapter.ts"
INTAKE_PACKET_PATH = ROOT / "docs/automation/V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG/operator_supplied_feedback_intake_packet.json"
BACKLOG_PACKET_PATH = ROOT / "docs/automation/V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG/operator_feedback_backlog_summary_packet.json"


def _extract_const_json(adapter_text: str, export_name: str) -> dict:
    match = re.search(rf"export const {export_name} = (.*?) as const;", adapter_text, re.S)
    assert match, export_name
    return json.loads(match.group(1))


def test_generated_adapter_matches_committed_adapter() -> None:
    assert build_operator_feedback_backlog_v5_adapter_text() == ADAPTER_PATH.read_text(encoding="utf-8")
    assert check_operator_feedback_backlog_v5_adapter_in_sync()["adapter_in_sync"] is True


def test_generated_adapter_hashes_match_committed_packets() -> None:
    text = build_operator_feedback_backlog_v5_adapter_text()
    generated_intake = _extract_const_json(text, "operatorSuppliedFeedbackIntakePacket")
    generated_backlog = _extract_const_json(text, "operatorFeedbackBacklogSummaryPacket")
    committed_intake = json.loads(INTAKE_PACKET_PATH.read_text(encoding="utf-8"))
    committed_backlog = json.loads(BACKLOG_PACKET_PATH.read_text(encoding="utf-8"))

    assert generated_intake["exact_payload_hash"] == committed_intake["exact_payload_hash"]
    assert generated_intake["feedback_intake_packet_id"] == committed_intake["feedback_intake_packet_id"]
    assert generated_backlog["feedback_intake_hash"] == committed_intake["exact_payload_hash"]
    assert generated_backlog["exact_payload_hash"] == committed_backlog["exact_payload_hash"]
    assert generated_backlog["backlog_summary_packet_id"] == committed_backlog["backlog_summary_packet_id"]
    status = check_operator_feedback_backlog_v5_adapter_in_sync()
    assert status["intake_hash_matches"] is True
    assert status["backlog_hash_matches"] is True


def test_generated_adapter_remains_review_only_and_no_llm() -> None:
    text = build_operator_feedback_backlog_v5_adapter_text()
    backlog = _extract_const_json(text, "operatorFeedbackBacklogSummaryPacket")
    assert backlog["summary_method"] == "deterministic_tag_grouping_no_llm"
    assert backlog["backlog_status"] == "ready_for_operator_review_only"
    assert all(value is False for value in backlog["non_readiness_claims"].values())
    lowered = text.lower()
    for phrase in [
        "ready for live",
        "api ready",
        "dispatch ready",
        "public url verified",
        "platform auth ready",
        "llm synthesis",
    ]:
        assert phrase not in lowered


def test_generated_adapter_has_no_external_platform_urls_or_enabled_live_controls() -> None:
    text = build_operator_feedback_backlog_v5_adapter_text().lower()
    for phrase in ["https://", "http://", "substack.com", "linkedin.com", "x.com", "twitter.com"]:
        assert phrase not in text
    assert '"enabled_publish_send_dispatch_approve_controls": true' not in text
    for field in [
        "llm_provider_call_made",
        "provider_call_made",
        "platform_api_used",
        "public_url_fetch_made",
        "browser_session_used",
        "env_value_read_made",
        "credential_read_made",
        "live_publish_performed_by_contentops",
    ]:
        assert f'"{field}": true' not in text


def test_generated_adapter_output_is_deterministic() -> None:
    assert build_operator_feedback_backlog_v5_adapter_text() == build_operator_feedback_backlog_v5_adapter_text()
    assert check_operator_feedback_backlog_v5_adapter_in_sync() == check_operator_feedback_backlog_v5_adapter_in_sync()
