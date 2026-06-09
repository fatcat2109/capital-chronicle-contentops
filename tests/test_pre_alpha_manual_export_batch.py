"""Tests for the pre-alpha manual export batch packet generator (Task 0107)."""

import json
import os

from live_contentops import pre_alpha_manual_export_batch as meb
from live_contentops import pre_alpha_manual_decision_batch as mdb

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _decision_batch():
    """A clean 0106 decision batch packet from its accepted default fixture."""
    return mdb.build_from_config_file()


def test_batch_schema_loads():
    schema = meb.load_batch_schema()
    assert schema["title"] == "PreAlphaManualExportBatchPacket"
    assert "manual_export_packets" in schema["properties"]


def test_pass_path_generation():
    packet = meb.build_manual_export_batch_packet(_decision_batch())
    assert packet["packet_status"] == "pass"
    assert packet["manual_export_batch_packet_id"]
    assert packet["created_at"] == "2026-01-01T00:00:00Z"
    assert packet["safety_audit"]["unsafe_flag_count"] == 0


def test_only_clean_approvals_produce_export_packets():
    packet = meb.build_manual_export_batch_packet(_decision_batch())
    assert packet["approved_decision_count"] == 1
    assert len(packet["manual_export_packets"]) == 1
    ep = packet["manual_export_packets"][0]
    assert ep["export_status"] == "prepared_for_operator_review"
    assert ep["manual_copy_ready"] is True


def test_revision_reject_blocked_preserved_not_exported():
    packet = meb.build_manual_export_batch_packet(_decision_batch())
    statuses = {r["decision_status"] for r in packet["non_exported_decision_report"]}
    assert "revision_requested" in statuses
    assert "rejected" in statuses
    exported_drafts = {ep["draft_id"] for ep in packet["manual_export_packets"]}
    for r in packet["non_exported_decision_report"]:
        assert r["draft_id"] not in exported_drafts


def test_every_export_packet_maps_to_one_ledger_entry():
    packet = meb.build_manual_export_batch_packet(_decision_batch())
    assert len(packet["manual_export_packets"]) == len(packet["content_ledger_entries"])
    for ep, le in zip(packet["manual_export_packets"], packet["content_ledger_entries"]):
        assert le["manual_export_packet_id"] == ep["manual_export_packet_id"]
        assert le["approval_packet_id"] == ep["approval_packet_id"]


def test_no_manually_published_ledger_state():
    packet = meb.build_manual_export_batch_packet(_decision_batch())
    for le in packet["content_ledger_entries"]:
        assert le["lifecycle_status"] in ("export_prepared", "blocked")
        assert le["lifecycle_status"] != "manually_published"


def test_manual_url_timestamp_metrics_null_by_default():
    packet = meb.build_manual_export_batch_packet(_decision_batch())
    for le in packet["content_ledger_entries"]:
        assert le["manual_publish_url"] is None
        assert le["manual_publish_timestamp"] is None
        assert le["manual_metrics"] is None


def test_hard_boundary_flags_pinned():
    packet = meb.build_manual_export_batch_packet(_decision_batch())
    flags = packet["hard_boundary_flags"]
    assert flags["local_only"] is True
    assert flags["fixture_only"] is True
    assert flags["manual_review_required"] is True
    assert flags["final_operator_check_required"] is True
    assert flags["auto_publish"] is False
    assert flags["public_postable"] is False
    assert flags["platform_api_call_allowed_now"] is False
    assert flags["scheduler_allowed"] is False
    assert flags["metrics_ingestion_allowed"] is False
    assert flags["provider_call_allowed_now"] is False
    assert flags["network_call_allowed_now"] is False
    assert flags["live_execution_allowed_now"] is False
    assert flags["credential_or_env_read_allowed"] is False
    assert flags["manually_published_created"] is False
    assert flags["manual_publish_url_default_null"] is True
    assert flags["manual_metrics_default_null"] is True


def test_fail_closed_on_unsafe_source_decision_batch_flag():
    batch = _decision_batch()
    batch["packet_status"] = "blocked"
    packet = meb.build_manual_export_batch_packet(batch)
    assert packet["packet_status"] == "blocked"
    assert "source_decision_batch_packet_blocked" in packet["blocked_reasons"]


def test_fail_closed_on_unsafe_export_packet_flag():
    batch = _decision_batch()
    for ap in batch["approval_packets"]:
        ap["approved_text"] = "We will buy and sell signals; entry now."
    packet = meb.build_manual_export_batch_packet(batch)
    assert packet["packet_status"] == "blocked"
    assert any("export_packet_blocked" in r for r in packet["blocked_reasons"])


def test_approved_decision_without_clean_approval_blocks():
    batch = _decision_batch()
    batch["approval_packets"] = []
    packet = meb.build_manual_export_batch_packet(batch)
    assert packet["packet_status"] == "blocked"
    assert any("missing_clean_approval" in r for r in packet["blocked_reasons"])
    assert len(packet["manual_export_packets"]) == 0


def test_deterministic_output():
    a = meb.build_manual_export_batch_packet(_decision_batch())
    b = meb.build_manual_export_batch_packet(_decision_batch())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_build_from_config_file_chains_off_0106():
    packet = meb.build_from_config_file()
    assert packet["packet_status"] == "pass"
    assert packet["source_manual_decision_batch_packet_id"]
    assert packet["source_refs"]


def test_cli_summary_valid_json():
    out = meb.summary()
    assert out["packet_status"] == "pass"
    assert out["manual_export_packet_count"] == 1
    assert out["content_ledger_entry_count"] == 1
    assert out["manually_published_count"] == 0
    assert out["unsafe_flag_count"] == 0
    assert json.loads(json.dumps(out))


def test_no_forbidden_imports_or_calls():
    """Static scan: the module introduces no network/env/provider/platform code."""
    path = os.path.join(REPO_ROOT, "live_contentops", "pre_alpha_manual_export_batch.py")
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    forbidden = [
        "os.environ",
        "getenv",
        "dotenv",
        "import requests",
        "import httpx",
        "import aiohttp",
        "import urllib",
        "import socket",
        "import subprocess",
        "import openai",
        "import anthropic",
        "bearer",
        "api_key",
    ]
    for token in forbidden:
        assert token not in src, "forbidden token in module: %s" % token

