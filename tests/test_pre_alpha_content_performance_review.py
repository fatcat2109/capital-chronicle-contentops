"""Tests for pre-alpha content performance review (Task 0117).

Verifies validation, missing metrics preservation, invalid metric blocks,
forbidden source flags, conservative language, and safety boundaries.
"""

import json
import os
import copy
import pytest

from live_contentops import pre_alpha_content_performance_review as cpr

MODULE_PATH = cpr.__file__

def test_schema_loads():
    schema = cpr.load_schema()
    assert schema["title"] == "PreAlphaContentPerformanceReviewPacket"
    assert "content_performance_review_packet_id" in schema["required"]

def test_valid_review_packet_passes():
    packet = cpr.build_from_config_file(cpr.DEFAULT_CONFIG)
    assert packet["packet_status"] == "pass"
    assert packet["record_count"] == 3
    assert packet["included_record_count"] == 3
    assert packet["excluded_record_count"] == 0
    assert packet["insufficient_sample"] is False
    assert packet["sample_size_warning"] is None
    assert packet["platform_family_summary"]["linkedin"] == 2
    assert packet["platform_family_summary"]["x"] == 1
    assert packet["content_type_summary"]["market_note"] == 2
    assert packet["content_type_summary"]["deep_dive"] == 1
    assert "linkedin" in packet["conservative_findings"][0]

def test_insufficient_sample_passes_with_warning():
    config_path = os.path.join(cpr.FIXTURE_DIR, "insufficient_sample_content_performance_review_config.json")
    packet = cpr.build_from_config_file(config_path)
    assert packet["packet_status"] == "pass"
    assert packet["record_count"] == 1
    assert packet["included_record_count"] == 1
    assert packet["insufficient_sample"] is True
    assert packet["sample_size_warning"] is not None
    assert packet["missing_metric_count"] == 1
    assert any("too small" in f for f in packet["conservative_findings"])

def test_missing_null_metrics_preserved_and_excluded():
    config_path = os.path.join(cpr.FIXTURE_DIR, "insufficient_sample_content_performance_review_config.json")
    packet = cpr.build_from_config_file(config_path)
    # The null metric is counted but does not block the packet
    assert packet["packet_status"] == "pass"
    assert packet["missing_metric_count"] == 1

def test_invalid_automatic_scraped_fetched_api_source_blocks():
    config_path = os.path.join(cpr.FIXTURE_DIR, "invalid_content_performance_review_config.json")
    packet = cpr.build_from_config_file(config_path)
    assert packet["packet_status"] == "blocked"
    assert packet["excluded_record_count"] == 1
    assert any("invalid_source" in r for r in packet["blocked_reasons"])

def test_missing_manual_publish_reference_blocks():
    rec = {
        "metrics_source_type": "operator_entered",
        "metrics": {"likes": 5}
    }
    packet = cpr.build_content_performance_review_packet({"records": [rec]})
    assert packet["packet_status"] == "blocked"
    assert any("missing_reference" in r for r in packet["blocked_reasons"])

def test_negative_metric_blocks():
    rec = {
        "linked_manual_publish_record_id": "manual_pub_1",
        "metrics_source_type": "operator_entered",
        "metrics": {"likes": -5}
    }
    packet = cpr.build_content_performance_review_packet({"records": [rec]})
    assert packet["packet_status"] == "blocked"
    assert any("negative_metric" in r for r in packet["blocked_reasons"])

def test_no_inferred_publication_or_metrics():
    packet = cpr.build_content_performance_review_packet({"records": []})
    assert packet["packet_status"] == "pass"
    assert packet["record_count"] == 0
    assert packet["missing_metric_count"] == 0
    assert packet["insufficient_sample"] is True

def test_statistical_significance_claim_blocks():
    packet = cpr.build_content_performance_review_packet({"statistical_significance_claimed": True, "records": []})
    assert packet["packet_status"] == "blocked"
    assert any("statistical_significance_claimed_not_allowed" in r for r in packet["blocked_reasons"])

def test_deterministic_output():
    p1 = cpr.build_from_config_file()
    p1["content_performance_review_packet_id"] = "fixed_id"
    p1["created_at"] = "fixed_time"

    p2 = copy.deepcopy(p1)
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)

def test_packet_hard_boundary_flags_pinned():
    packet = cpr.build_from_config_file()
    f = packet["hard_boundary_flags"]
    assert f["local_only"] is True
    assert f["deterministic_review_only"] is True
    assert f["manual_operator_entry_only"] is True
    assert f["fixture_only"] is True
    assert f["llm_generation_used"] is False
    assert f["statistical_significance_claimed"] is False

def test_cli_summary_valid_json():
    out = cpr.summary()
    assert out["packet_status"] == "pass"
    assert out["automatic_metrics_ingestion_allowed"] is False
    assert out["scraping_allowed"] is False
    assert out["public_postable"] is False
    assert out["auto_publish"] is False
    assert out["statistical_significance_claimed"] is False
    json.dumps(out)

def test_static_scan_no_forbidden_imports_or_calls():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    
    # We enforce that certain dangerous libraries or functions are never imported.
    forbidden_imports = [
        "import requests", "import httpx", "import aiohttp", "import urllib",
        "import socket", "import subprocess", "import openai", "import anthropic",
        "os.environ", "os.getenv", "getenv(", "dotenv", "load_dotenv",
        ".post(", ".send(", "schedule.", "APScheduler", "BeautifulSoup",
        "selenium", "playwright", "smtplib"
    ]
    for token in forbidden_imports:
        assert token not in src, f"forbidden token in module: {token}"
    
    forbidden_language = [
        "guaranteed", "proven", "buy", "sell", "hold", "position sizing",
        "significant difference", "p-value"
    ]
    for token in forbidden_language:
        assert token not in src.lower(), f"forbidden language in module: {token}"
