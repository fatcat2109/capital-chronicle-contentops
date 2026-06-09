"""Tests for the pre-alpha platform-specific manual export templates (Task 0110)."""

import json
import os

from live_contentops import pre_alpha_platform_manual_templates as pmt
from live_contentops import pre_alpha_manual_export_batch as meb

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _export_batch():
    """A clean 0107 manual export batch packet from its accepted default fixture."""
    return meb.build_from_config_file()


def test_schema_loads():
    schema = pmt.load_schema()
    assert schema["title"] == "PreAlphaPlatformManualTemplatePacket"
    assert "platform_template_records" in schema["properties"]


def test_pass_path_generation():
    packet = pmt.build_platform_manual_template_packet(_export_batch())
    assert packet["packet_status"] == "pass"
    assert packet["platform_manual_template_packet_id"]
    assert packet["created_at"] == "2026-01-01T00:00:00Z"
    assert packet["safety_audit"]["unsafe_flag_count"] == 0


def test_every_clean_export_maps_to_one_template_record():
    batch = _export_batch()
    clean = [
        ep for ep in batch["manual_export_packets"]
        if ep.get("export_status") == "prepared_for_operator_review"
        and ep.get("manual_copy_ready") is True
        and not ep.get("blocked_reasons")
    ]
    packet = pmt.build_platform_manual_template_packet(batch)
    assert len(packet["platform_template_records"]) == len(clean)
    rec_ids = {r["manual_export_packet_id"] for r in packet["platform_template_records"]}
    clean_ids = {ep["manual_export_packet_id"] for ep in clean}
    assert rec_ids == clean_ids


def test_blocked_export_preserved_not_templated_as_clean():
    batch = _export_batch()
    # Force the export packet(s) into a blocked state.
    for ep in batch["manual_export_packets"]:
        ep["export_status"] = "blocked"
        ep["manual_copy_ready"] = False
        ep["blocked_reasons"] = ["forced_blocked_for_test"]
    packet = pmt.build_platform_manual_template_packet(batch)
    assert len(packet["platform_template_records"]) == 0
    assert len(packet["unsupported_or_blocked_exports"]) >= 1
    for item in packet["unsupported_or_blocked_exports"]:
        assert item["reason"] in (
            "export_packet_not_clean",
            "unsupported_platform_family",
        )


def test_unknown_platform_family_fails_closed():
    batch = _export_batch()
    for ep in batch["manual_export_packets"]:
        ep["platform_family"] = "tiktok"
    packet = pmt.build_platform_manual_template_packet(batch)
    assert packet["packet_status"] == "blocked"
    assert any(
        "unsupported_platform_family" in r for r in packet["blocked_reasons"]
    )
    assert len(packet["platform_template_records"]) == 0


def test_source_attribution_and_limitations_preserved():
    packet = pmt.build_platform_manual_template_packet(_export_batch())
    for rec in packet["platform_template_records"]:
        has_sources = bool(rec["source_artifact_ids"])
        is_general = bool(rec["is_general_process_content"])
        assert has_sources or is_general
        assert isinstance(rec["limitations"], list)
        assert not rec["blocked_reasons"]


def test_final_operator_check_required_on_records():
    packet = pmt.build_platform_manual_template_packet(_export_batch())
    for rec in packet["platform_template_records"]:
        assert rec["operator_final_check_required"] is True
        assert rec["manual_publish_only"] is True
        assert "OPERATOR FINAL CHECK REQUIRED" in rec["copy_paste_text"]
        assert "NOT PUBLIC POSTABLE" in rec["copy_paste_text"]


def test_no_platform_api_payload_fields():
    packet = pmt.build_platform_manual_template_packet(_export_batch())
    blob = json.dumps(packet).lower()
    assert "platform_api_payload" not in blob
    assert "request_body" not in blob
    for rec in packet["platform_template_records"]:
        assert "platform_api_payload" not in rec
        assert "request_body" not in rec


def test_public_postable_and_publish_allowed_now_pinned_false():
    packet = pmt.build_platform_manual_template_packet(_export_batch())
    for rec in packet["platform_template_records"]:
        assert rec["public_postable"] is False
        assert rec["publish_allowed_now"] is False
        assert rec["platform_publish_allowed_now"] is False
        assert rec["platform_api_call_allowed"] is False
        assert rec["scheduler_allowed"] is False
        assert rec["metrics_ingestion_allowed"] is False
        assert rec["live_execution_allowed_now"] is False


def test_hard_boundary_flags_pinned():
    packet = pmt.build_platform_manual_template_packet(_export_batch())
    flags = packet["hard_boundary_flags"]
    assert flags["local_only"] is True
    assert flags["fixture_only"] is True
    assert flags["manual_copy_paste_only"] is True
    assert flags["operator_final_check_required"] is True
    assert flags["platform_api_call_allowed_now"] is False
    assert flags["provider_call_allowed_now"] is False
    assert flags["network_call_allowed_now"] is False
    assert flags["scheduler_allowed"] is False
    assert flags["automatic_metrics_ingestion_allowed"] is False
    assert flags["scraping_allowed"] is False
    assert flags["credential_or_env_read_allowed"] is False
    assert flags["live_execution_allowed_now"] is False
    assert flags["auto_publish"] is False
    assert flags["public_postable"] is False


def test_fail_closed_on_unsafe_source_export_batch_flag():
    batch = _export_batch()
    batch["packet_status"] = "blocked"
    packet = pmt.build_platform_manual_template_packet(batch)
    assert packet["packet_status"] == "blocked"
    assert "source_export_batch_packet_blocked" in packet["blocked_reasons"]


def test_deterministic_output():
    a = pmt.build_platform_manual_template_packet(_export_batch())
    b = pmt.build_platform_manual_template_packet(_export_batch())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_build_from_config_file_chains_off_0107():
    packet = pmt.build_from_config_file()
    assert packet["packet_status"] == "pass"
    assert packet["source_manual_export_batch_packet_id"]
    assert packet["source_refs"]


def test_template_format_matches_platform_family():
    packet = pmt.build_platform_manual_template_packet(_export_batch())
    expected = {
        "x": "short_form_plain_text",
        "threads": "short_form_plain_text",
        "linkedin": "professional_long_form",
        "newsletter": "newsletter_markdown",
        "generic": "generic_markdown",
    }
    for rec in packet["platform_template_records"]:
        assert rec["manual_template_format"] == expected[rec["platform_family"]]


def test_cli_summary_valid_json():
    out = pmt.summary()
    assert out["packet_status"] == "pass"
    assert out["platform_template_record_count"] >= 1
    assert out["unsafe_flag_count"] == 0
    assert out["platform_api_payload_generated"] is False
    assert out["current_platform_spec_verified"] is False
    assert json.loads(json.dumps(out))


def test_no_forbidden_imports_or_calls():
    """Static scan: the module introduces no network/env/provider/platform code."""
    path = os.path.join(
        REPO_ROOT, "live_contentops", "pre_alpha_platform_manual_templates.py"
    )
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
