"""Tests for the pre-alpha manual publish record packet generator (Task 0108).

Local-only, deterministic. Proves valid explicit records advance exactly one
ledger to manually_published; missing records stay export_prepared; invalid /
duplicate / unknown-targeting records are blocked; blocked exports never become
manually_published; URL+timestamp are required; metrics are operator-supplied
only; hard-boundary flags stay pinned; output is deterministic; and no
network/env/provider/platform/scheduler/posting/scraping/metrics-ingestion
imports or calls were added.
"""

import copy
import json
import os

import pytest

from live_contentops import pre_alpha_manual_publish_record as mpr

MODULE_PATH = mpr.__file__


def _export_packet(suffix, status="prepared_for_operator_review",
                   blocked=False, copy_ready=True):
    """Build a minimal clean (or blocked) manual export packet for tests."""
    return {
        "manual_export_packet_id": "manual_export_%s" % suffix,
        "approval_packet_id": "approval_%s" % suffix,
        "draft_id": "draft_%s" % suffix,
        "platform_family": "x",
        "content_type": "build_in_public",
        "export_status": status,
        "export_text": "Process note about building Capital Chronicle carefully.",
        "export_format": "copy_paste_text",
        "source_artifact_ids": [],
        "is_general_process_content": True,
        "limitations": ["general/process content only"],
        "manual_publish_only": True,
        "final_operator_check_required": True,
        "manual_copy_ready": copy_ready,
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "platform_api_call_allowed": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "blocked_reasons": ["x"] if blocked else [],
        "audit_refs": [],
    }


def _export_batch(export_packets, status="pass"):
    return {
        "manual_export_batch_packet_id": "export_batch_001",
        "manual_export_packets": list(export_packets),
        "packet_status": status,
    }


def _record(suffix, url="https://example.invalid/p/%s", ts="2026-01-02T09:00:00Z",
            metrics=None):
    return {
        "manual_export_packet_id": "manual_export_%s" % suffix,
        "manual_publish_url": (url % suffix) if "%s" in url else url,
        "manual_publish_timestamp": ts,
        "manual_metrics": metrics,
    }


# --------------------------------------------------------------------------- #
# Schema + pass path
# --------------------------------------------------------------------------- #

def test_schema_loads():
    schema = mpr.load_record_schema()
    assert schema["title"] == "PreAlphaManualPublishRecordPacket"
    assert "packet_status" in schema["required"]


def test_pass_path_record_packet_generation():
    batch = _export_batch([_export_packet("a")])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a")])
    assert packet["packet_status"] == "pass"
    assert packet["recorded_publish_count"] == 1
    assert packet["not_recorded_count"] == 0
    assert packet["blocked_record_count"] == 0


def test_valid_record_advances_exactly_one_ledger_to_manually_published():
    batch = _export_batch([_export_packet("a"), _export_packet("b")])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a")])
    published = [
        le for le in packet["updated_content_ledger_entries"]
        if le["lifecycle_status"] == "manually_published"
    ]
    assert len(published) == 1
    assert published[0]["manual_export_packet_id"] == "manual_export_a"
    assert published[0]["manual_publish_url"].startswith("https://example.invalid")


def test_missing_record_stays_export_prepared():
    batch = _export_batch([_export_packet("a"), _export_packet("b")])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a")])
    assert packet["not_recorded_count"] == 1
    not_recorded = packet["not_recorded_export_report"][0]
    assert not_recorded["manual_export_packet_id"] == "manual_export_b"
    assert not_recorded["lifecycle_status"] == "export_prepared"


def test_invalid_record_missing_url_is_blocked():
    batch = _export_batch([_export_packet("a")])
    rec = _record("a")
    rec["manual_publish_url"] = ""
    packet = mpr.build_manual_publish_record_packet(batch, [rec])
    assert packet["packet_status"] == "blocked"
    assert packet["blocked_record_count"] == 1
    assert packet["blocked_record_report"][0]["reason"] == "missing_manual_publish_url"


def test_missing_timestamp_is_blocked():
    batch = _export_batch([_export_packet("a")])
    rec = _record("a")
    rec["manual_publish_timestamp"] = ""
    packet = mpr.build_manual_publish_record_packet(batch, [rec])
    assert packet["packet_status"] == "blocked"
    assert packet["blocked_record_report"][0]["reason"] == "missing_manual_publish_timestamp"


def test_duplicate_record_fails_closed():
    batch = _export_batch([_export_packet("a")])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a"), _record("a")])
    assert packet["packet_status"] == "blocked"
    reasons = [r["reason"] for r in packet["blocked_record_report"]]
    assert "duplicate_record_for_export_packet" in reasons
    # First record still recorded exactly once.
    assert packet["recorded_publish_count"] == 1


# --------------------------------------------------------------------------- #
# Blocked exports / metrics / boundaries
# --------------------------------------------------------------------------- #

def test_blocked_export_cannot_become_manually_published():
    # A blocked export packet is not eligible; a record targeting it is blocked.
    batch = _export_batch([_export_packet("a", status="blocked", blocked=True)])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a")])
    assert packet["packet_status"] == "blocked"
    assert packet["eligible_export_packet_count"] == 0
    published = [
        le for le in packet["updated_content_ledger_entries"]
        if le["lifecycle_status"] == "manually_published"
    ]
    assert published == []
    reasons = [r["reason"] for r in packet["blocked_record_report"]]
    assert "references_unknown_or_blocked_export_packet" in reasons


def test_record_targeting_unknown_export_is_blocked():
    batch = _export_batch([_export_packet("a")])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("zzz")])
    assert packet["packet_status"] == "blocked"
    assert packet["blocked_record_report"][0]["reason"] == (
        "references_unknown_or_blocked_export_packet"
    )


def test_metrics_fixture_supplied_only_and_may_be_null():
    batch = _export_batch([_export_packet("a"), _export_packet("b")])
    records = [
        _record("a", metrics=None),
        _record("b", metrics={"views": 10, "likes": 2}),
    ]
    packet = mpr.build_manual_publish_record_packet(batch, records)
    assert packet["packet_status"] == "pass"
    by_id = {
        le["manual_export_packet_id"]: le
        for le in packet["updated_content_ledger_entries"]
    }
    assert by_id["manual_export_a"]["manual_metrics"] is None
    assert by_id["manual_export_b"]["manual_metrics"] == {"views": 10, "likes": 2}


def test_no_automatic_metrics_ingestion():
    batch = _export_batch([_export_packet("a")])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a")])
    assert packet["safety_audit"]["automatic_metrics_ingestion_count"] == 0
    assert packet["hard_boundary_flags"]["automatic_metrics_ingestion_allowed"] is False
    assert packet["hard_boundary_flags"]["scraping_allowed"] is False


def test_forbidden_record_field_is_blocked():
    batch = _export_batch([_export_packet("a")])
    rec = _record("a")
    rec["platform_api_payload"] = {"endpoint": "/post"}
    packet = mpr.build_manual_publish_record_packet(batch, [rec])
    assert packet["packet_status"] == "blocked"
    assert packet["blocked_record_report"][0]["reason"] == (
        "forbidden_record_field:platform_api_payload"
    )


def test_hard_boundary_flags_pinned():
    batch = _export_batch([_export_packet("a")])
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a")])
    f = packet["hard_boundary_flags"]
    assert f["local_only"] is True
    assert f["fixture_only"] is True
    assert f["manual_recordkeeping_only"] is True
    assert f["manual_operator_record_required"] is True
    for flag in (
        "platform_api_call_allowed_now", "provider_call_allowed_now",
        "network_call_allowed_now", "scheduler_allowed",
        "automatic_metrics_ingestion_allowed", "scraping_allowed",
        "credential_or_env_read_allowed", "live_execution_allowed_now",
        "auto_publish",
    ):
        assert f[flag] is False
    assert packet["safety_audit"]["unsafe_flag_count"] == 0


def test_fail_closed_on_blocked_source_export_batch():
    batch = _export_batch([_export_packet("a")], status="blocked")
    packet = mpr.build_manual_publish_record_packet(batch, [_record("a")])
    assert packet["packet_status"] == "blocked"
    assert "source_manual_export_batch_packet_blocked" in packet["blocked_reasons"]


def test_deterministic_output():
    batch = _export_batch([_export_packet("a"), _export_packet("b")])
    records = [_record("a")]
    p1 = mpr.build_manual_publish_record_packet(copy.deepcopy(batch), copy.deepcopy(records))
    p2 = mpr.build_manual_publish_record_packet(copy.deepcopy(batch), copy.deepcopy(records))
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)


def test_chains_off_0107_default_fixture():
    packet = mpr.build_from_config_file()
    assert packet["packet_status"] in ("pass", "blocked")
    assert packet["source_manual_export_batch_packet_id"] is not None
    # No ledger entry may carry an unsafe publish flag regardless of status.
    for le in packet["updated_content_ledger_entries"]:
        assert le["public_postable"] is False
        assert le["publish_allowed_now"] is False
        assert le["platform_publish_allowed_now"] is False
        assert le["live_execution_allowed_now"] is False


def test_cli_summary_valid_json():
    out = mpr.summary()
    assert out["local_only"] is True
    assert out["manual_recordkeeping_only"] is True
    assert out["automatic_metrics_ingestion_allowed"] is False
    assert out["platform_api_call_allowed_now"] is False
    assert out["scheduler_allowed"] is False
    # JSON-serializable
    json.dumps(out)


def test_static_scan_no_forbidden_imports_or_calls():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    forbidden = [
        "os.environ", "getenv", "dotenv", "requests", "httpx", "aiohttp",
        "urllib", "socket", "subprocess", "openai", "anthropic", "bearer",
        "api_key", "telegram", "smtplib",
    ]
    for token in forbidden:
        assert token not in src, "forbidden token in module: %s" % token


