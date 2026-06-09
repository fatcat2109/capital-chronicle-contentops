"""Tests for the local-only pre-alpha manual export packet + content ledger (Task 0099)."""

import json
import os

import pytest

from live_contentops import pre_alpha_manual_export as mex

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_manual_export"
)


def _load(name):
    with open(os.path.join(FIXTURE_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


_NON_PUBLISH_FLAGS = [
    "public_postable",
    "publish_allowed_now",
    "platform_publish_allowed_now",
    "live_execution_allowed_now",
    "platform_api_call_allowed",
    "scheduler_allowed",
    "metrics_ingestion_allowed",
]


def _assert_export_locked(packet):
    for flag in _NON_PUBLISH_FLAGS:
        assert packet[flag] is False, flag
    assert packet["manual_publish_only"] is True
    assert packet["final_operator_check_required"] is True


def test_valid_export_x_prepared():
    out = mex.build_from_input_file(os.path.join(FIXTURE_DIR, "valid_manual_export_x.json"))
    pkt = out["export_packet"]
    assert pkt["export_status"] == "prepared_for_operator_review"
    assert pkt["manual_copy_ready"] is True
    assert pkt["blocked_reasons"] == []
    assert pkt["export_format"] == "copy_paste_text"
    assert pkt["export_text"] != ""
    _assert_export_locked(pkt)


def test_valid_export_linkedin_prepared():
    out = mex.build_from_input_file(
        os.path.join(FIXTURE_DIR, "valid_manual_export_linkedin.json")
    )
    pkt = out["export_packet"]
    assert pkt["export_status"] == "prepared_for_operator_review"
    assert pkt["manual_copy_ready"] is True
    assert pkt["platform_family"] == "linkedin"
    _assert_export_locked(pkt)


def test_valid_ledger_entry_manual_published():
    out = mex.build_from_input_file(
        os.path.join(FIXTURE_DIR, "valid_content_ledger_entry.json")
    )
    entry = out["ledger_entry"]
    assert entry["lifecycle_status"] == "manually_published"
    assert entry["manual_publish_url"] == "https://operator-recorded.example/post/abc123"
    assert entry["manual_publish_timestamp"] == "2026-01-02T00:00:00Z"
    assert entry["public_postable"] is False
    assert entry["publish_allowed_now"] is False
    assert entry["platform_publish_allowed_now"] is False
    assert entry["live_execution_allowed_now"] is False
    assert entry["scheduler_allowed"] is False


def test_ledger_defaults_url_null_without_manual_record():
    pkt = mex.build_export_packet(_load("valid_manual_export_x.json")["approval_packet"])
    entry = mex.build_ledger_entry(pkt)
    assert entry["lifecycle_status"] == "export_prepared"
    assert entry["manual_publish_url"] is None
    assert entry["manual_publish_timestamp"] is None
    assert entry["manual_metrics"] is None


@pytest.mark.parametrize(
    "name,expected_substring",
    [
        ("invalid_publish_allowed_now.json", "approval_publish_allowed_now_must_be_false"),
        ("invalid_live_execution_allowed_now.json", "approval_live_execution_allowed_now_must_be_false"),
        ("invalid_missing_final_operator_check.json", "approval_final_operator_check_required_must_be_true"),
        ("invalid_unapproved_packet.json", "approval_packet_not_approved"),
        ("invalid_signal_language_export.json", "export_text_forbidden_language"),
    ],
)
def test_invalid_fixtures_block(name, expected_substring):
    out = mex.build_from_input_file(os.path.join(FIXTURE_DIR, name))
    pkt = out["export_packet"]
    assert pkt["export_status"] == "blocked"
    assert pkt["manual_copy_ready"] is False
    assert pkt["export_text"] == ""
    assert any(expected_substring in r for r in pkt["blocked_reasons"]), pkt["blocked_reasons"]
    _assert_export_locked(pkt)



def test_blocked_export_yields_blocked_ledger():
    out = mex.build_from_input_file(
        os.path.join(FIXTURE_DIR, "invalid_unapproved_packet.json")
    )
    entry = out["ledger_entry"]
    assert entry["lifecycle_status"] == "blocked"
    assert entry["manual_publish_url"] is None


def test_manual_record_cannot_publish_blocked_export():
    blocked = mex.build_export_packet({})  # empty -> blocked
    entry = mex.build_ledger_entry(
        blocked, {"manual_publish_url": "https://x.example/p/1"}
    )
    assert entry["lifecycle_status"] == "blocked"
    assert entry["manual_publish_url"] is None


def test_missing_source_and_general_marker_blocks():
    ap = _load("valid_manual_export_x.json")["approval_packet"]
    ap["is_general_process_content"] = False
    ap["source_artifact_ids"] = []
    pkt = mex.build_export_packet(ap)
    assert pkt["export_status"] == "blocked"
    assert any(
        "missing_source_artifact_ids_or_general_process_marker" in r
        for r in pkt["blocked_reasons"]
    )


def test_artifact_backed_without_general_marker_ok():
    ap = _load("valid_manual_export_x.json")["approval_packet"]
    ap["is_general_process_content"] = False
    ap["source_artifact_ids"] = ["cc_artifact_123"]
    pkt = mex.build_export_packet(ap)
    assert pkt["export_status"] == "prepared_for_operator_review"


def test_summary_safe_posture():
    s = mex.summary()
    assert s["local_only"] is True
    assert s["platform_api_call_allowed"] is False
    assert s["scheduler_allowed"] is False
    assert s["metrics_ingestion_allowed"] is False
    assert s["auto_publish"] is False
    assert s["network_call_made"] is False
    assert s["credential_read"] is False
    assert s["fake_alpha_output"] is False
    assert s["public_postable_output"] is False
    assert s["manual_publish_url_default_null"] is True


def test_schemas_load():
    assert mex.load_export_packet_schema()["title"] == "PreAlphaManualExportPacket"
    assert mex.load_ledger_entry_schema()["title"] == "PreAlphaContentLedgerEntry"
