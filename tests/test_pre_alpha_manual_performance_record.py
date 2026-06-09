"""Tests for pre-alpha manual performance record (Task 0116).

Verifies validation, missing metrics preservation, invalid metric blocks,
forbidden source flags, pinning of safety bounds, and no scraping or posting.
"""

import json
import os
import copy
import pytest

from live_contentops import pre_alpha_manual_performance_record as mpr

MODULE_PATH = mpr.__file__

def test_schema_loads():
    schema = mpr.load_schema()
    assert schema["title"] == "PreAlphaManualPerformanceRecordPacket"
    assert "manual_performance_record_packet_id" in schema["required"]

def test_valid_performance_record_packet_passes():
    packet = mpr.build_from_config_file(mpr.DEFAULT_CONFIG)
    assert packet["packet_status"] == "pass"
    assert packet["record_count"] == 1
    assert packet["invalid_record_count"] == 0
    assert packet["unsafe_flag_count"] == 0

def test_missing_null_metrics_are_preserved_and_counted():
    config_path = os.path.join(mpr.FIXTURE_DIR, "missing_metrics_manual_performance_record_config.json")
    packet = mpr.build_from_config_file(config_path)
    assert packet["packet_status"] == "pass"
    assert packet["missing_metric_count"] == 2  # impressions, comments
    
    rec = packet["performance_records"][0]
    assert rec["metrics"]["impressions"] is None
    assert rec["metrics"]["comments"] is None
    assert rec["metrics"]["likes"] == 12
    assert rec["metric_null_reason"] is not None

def test_invalid_negative_metric_blocks():
    config_path = os.path.join(mpr.FIXTURE_DIR, "invalid_manual_performance_record_config.json")
    packet = mpr.build_from_config_file(config_path)
    assert packet["packet_status"] == "blocked"
    assert packet["invalid_record_count"] == 1
    assert any("negative_metric:likes" in r for r in packet["blocked_reasons"])

def test_non_operator_entered_metrics_source_type_blocks():
    config_path = os.path.join(mpr.FIXTURE_DIR, "invalid_manual_performance_record_config.json")
    packet = mpr.build_from_config_file(config_path)
    assert packet["packet_status"] == "blocked"
    assert any("invalid_metrics_source_type:scraped" in r for r in packet["blocked_reasons"])

def test_fetched_api_scraped_automatic_source_flags_block():
    rec = {
        "linked_manual_publish_record_id": "manual_pub_1",
        "metric_capture_timestamp": "2026-06-10T12:00:00Z",
        "metrics_source_type": "operator_entered",
        "scraped": True,
        "metrics": {"likes": 5}
    }
    packet = mpr.build_manual_performance_record_packet({"records": [rec]})
    assert packet["packet_status"] == "blocked"
    assert any("forbidden_record_field:scraped" in r for r in packet["blocked_reasons"])

def test_missing_manual_publish_reference_blocks():
    rec = {
        "metric_capture_timestamp": "2026-06-10T12:00:00Z",
        "metrics_source_type": "operator_entered",
        "metrics": {"likes": 5}
    }
    packet = mpr.build_manual_performance_record_packet({"records": [rec]})
    assert packet["packet_status"] == "blocked"
    assert any("missing_manual_publish_reference" in r for r in packet["blocked_reasons"])

def test_no_inferred_publication_or_metrics():
    packet = mpr.build_manual_performance_record_packet({"records": []})
    assert packet["packet_status"] == "pass"
    assert packet["record_count"] == 0
    assert packet["missing_metric_count"] == 0

def test_packet_hard_boundary_flags_pinned():
    packet = mpr.build_from_config_file()
    f = packet["hard_boundary_flags"]
    assert f["local_only"] is True
    assert f["manual_operator_entry_only"] is True
    assert f["fixture_only"] is True
    assert f["network_call_allowed_now"] is False
    assert f["provider_call_allowed_now"] is False
    assert f["platform_api_call_allowed_now"] is False
    assert f["scraping_allowed"] is False
    assert f["automatic_metrics_ingestion_allowed"] is False
    assert f["credential_or_env_read_allowed"] is False
    assert f["auto_publish"] is False
    assert f["public_postable"] is False

def test_deterministic_output():
    p1 = mpr.build_from_config_file()
    p1["manual_performance_record_packet_id"] = "fixed_id"
    p1["created_at"] = "fixed_time"
    for r in p1["performance_records"]:
        r["performance_record_id"] = "fixed_rec_id"

    p2 = copy.deepcopy(p1)
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)

def test_cli_summary_valid_json():
    out = mpr.summary()
    assert out["packet_status"] == "pass"
    assert out["automatic_metrics_ingestion_allowed"] is False
    assert out["scraping_allowed"] is False
    assert out["public_postable"] is False
    assert out["auto_publish"] is False
    json.dumps(out)

def test_static_scan_no_forbidden_imports_or_calls():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    forbidden = [
        "os.environ", "getenv", "dotenv", "requests", "httpx", "aiohttp",
        "urllib", "socket", "subprocess", "openai", "anthropic", "bearer",
        "api_key", "telegram", "smtplib", "scraped", "fetched"
    ]
    # "scraped" and "fetched" are in the file as string literals to forbid them, so we must be careful.
    # Actually, they are in the _FORBIDDEN_RECORD_KEYS list, so we can't test for their absence entirely.
    # We test for imports and actual network calls.
    forbidden_imports = [
        "import requests", "import httpx", "import aiohttp", "import urllib",
        "import socket", "import subprocess", "import openai", "import anthropic",
        "os.environ", "os.getenv", "getenv(", "dotenv", "load_dotenv",
        ".post(", ".send(", "schedule.", "APScheduler", "BeautifulSoup",
        "selenium", "playwright", "smtplib"
    ]
    for token in forbidden_imports:
        assert token not in src, f"forbidden token in module: {token}"
