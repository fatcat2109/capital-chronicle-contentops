"""Tests for the Task 0105 pre-alpha editorial batch review packet (local-only)."""

import json
import os

import pytest

from live_contentops import pre_alpha_editorial_batch_review as batch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEED_LIBRARY = os.path.join(
    REPO_ROOT, "fixtures", "pre_alpha_seed_library",
    "valid_seed_library_with_one_blocked.json",
)
CONFIG = os.path.join(
    REPO_ROOT, "fixtures", "pre_alpha_editorial_batch_review", "valid_batch_config.json",
)

# The shared fixture library has 3 safe seeds and 1 blocked (signal) seed.
SAFE_SEED_IDS = {
    "seed_macro_edu_001",
    "seed_build_in_public_001",
    "seed_data_sufficiency_001",
}
BLOCKED_SEED_ID = "seed_blocked_signal_001"


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def library():
    return _load(SEED_LIBRARY)


@pytest.fixture
def config():
    return _load(CONFIG)


def test_schema_loads():
    schema = batch.load_batch_schema()
    assert schema["title"]
    assert "hard_boundary_flags" in schema["properties"]


def test_pass_path_packet_generation(library, config):
    packet = batch.build_batch_review_packet(library, config)
    assert packet["packet_status"] == "pass"
    assert packet["blocked_reasons"] == []
    assert packet["batch_review_packet_id"]
    assert packet["created_at"] == "2026-01-01T00:00:00Z"


def test_safe_seeds_become_review_queue_items(library, config):
    packet = batch.build_batch_review_packet(library, config)
    assert set(packet["selected_safe_seed_ids"]) == SAFE_SEED_IDS
    assert len(packet["review_queue_items"]) >= len(SAFE_SEED_IDS)
    for item in packet["review_queue_items"]:
        assert item["review_status"] == "needs_manual_review"
        assert item["reviewer_required"] is True
        assert item["publish_allowed_now"] is False


def test_blocked_seeds_preserved_with_reasons(library, config):
    packet = batch.build_batch_review_packet(library, config)
    assert BLOCKED_SEED_ID in packet["blocked_seed_ids"]
    report_ids = {r["seed_id"] for r in packet["blocked_content_report"]}
    assert BLOCKED_SEED_ID in report_ids
    for report in packet["blocked_content_report"]:
        if report["seed_id"] == BLOCKED_SEED_ID:
            assert report["blocked_reasons"], "blocked reasons must not be empty"


def test_no_approval_export_or_ledger_objects_created(library, config):
    packet = batch.build_batch_review_packet(library, config)
    flags = packet["hard_boundary_flags"]
    assert flags["approval_packet_created"] is False
    assert flags["manual_export_packet_created"] is False
    assert flags["content_ledger_publish_status_changed"] is False
    # No approval/export/ledger objects must appear anywhere in the packet.
    blob = json.dumps(packet)
    assert "approval_packet_id" not in blob
    assert "manual_export_packet_id" not in blob
    assert "content_ledger_entry_id" not in blob


def test_hard_boundary_flags_pinned(library, config):
    packet = batch.build_batch_review_packet(library, config)
    flags = packet["hard_boundary_flags"]
    assert flags["local_only"] is True
    assert flags["fixture_only"] is True
    assert flags["manual_review_required"] is True
    assert flags["reviewer_required"] is True
    assert flags["auto_approval"] is False
    assert flags["public_postable"] is False
    assert flags["provider_call_allowed_now"] is False
    assert flags["network_call_allowed_now"] is False
    assert flags["platform_api_call_allowed_now"] is False
    assert flags["scheduler_allowed"] is False
    assert flags["metrics_ingestion_allowed"] is False
    assert flags["live_execution_allowed_now"] is False
    assert flags["credential_or_env_read_allowed"] is False
    assert packet["safety_audit"]["unsafe_flag_count"] == 0


def test_fail_closed_on_unsafe_flag(monkeypatch, library, config):
    # Simulate a tampered/unsafe flag set: the packet must fail closed.
    bad = dict(batch._REQUIRED_FLAGS)
    bad["public_postable"] = True
    monkeypatch.setattr(batch, "_hard_boundary_flags", lambda: bad)
    packet = batch.build_batch_review_packet(library, config)
    assert packet["packet_status"] == "blocked"
    assert any("public_postable" in r for r in packet["blocked_reasons"])
    assert packet["safety_audit"]["unsafe_flag_count"] >= 1


def test_fail_closed_on_renderer_guardrail_failure(monkeypatch, library, config):
    # If a "safe" planned seed renders blocked, it must be surfaced as blocked,
    # never silently kept, and the packet must fail closed.
    real_render = batch.render_review_packet

    def fake_render(editorial_packet, *a, **k):
        result = real_render(editorial_packet, *a, **k)
        if editorial_packet.get("input_seed_id") == "seed_macro_edu_001":
            result = dict(result)
            result["guardrail_status"] = "blocked"
            result["blocked_reasons"] = ["forced_block"]
        return result

    monkeypatch.setattr(batch, "render_review_packet", fake_render)
    packet = batch.build_batch_review_packet(library, config)
    assert packet["packet_status"] == "blocked"
    assert "seed_macro_edu_001" in packet["blocked_seed_ids"]
    assert "seed_macro_edu_001" not in packet["selected_safe_seed_ids"]
    assert any("seed_macro_edu_001" in r for r in packet["blocked_reasons"])


def test_deterministic_output(library, config):
    a = batch.build_batch_review_packet(library, config)
    b = batch.build_batch_review_packet(library, config)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_build_from_files_default():
    packet = batch.build_batch_review_packet_from_files()
    assert packet["packet_status"] == "pass"
    assert packet["seed_library_summary"]["total_seeds"] == 4


def test_cli_summary_valid_json():
    out = batch.summary()
    # Must be JSON-serializable and pin the non-publishing posture.
    serialized = json.dumps(out)
    assert json.loads(serialized)
    assert out["local_only"] is True
    assert out["fixture_only"] is True
    assert out["provider_call_made"] is False
    assert out["network_call_made"] is False
    assert out["credential_read"] is False
    assert out["public_postable_output"] is False
    assert out["approval_packet_created"] is False
    assert out["manual_export_packet_created"] is False
    assert out["content_ledger_publish_status_changed"] is False
    assert out["platform_api_call_allowed_now"] is False
    assert out["live_execution_allowed_now"] is False
    assert out["scheduler_allowed"] is False
    assert out["metrics_ingestion_allowed"] is False
    assert out["packet_status"] == "pass"
    assert out["selected_safe_seed_count"] == 3
    assert out["blocked_seed_count"] == 1


def test_static_scan_no_forbidden_capability():
    """The module must not import network/provider/env/platform/scheduler libs."""
    module_path = os.path.join(
        REPO_ROOT, "live_contentops", "pre_alpha_editorial_batch_review.py"
    )
    with open(module_path, "r", encoding="utf-8") as f:
        src = f.read().lower()
    forbidden = [
        "import requests", "import httpx", "import aiohttp", "import urllib",
        "import socket", "import subprocess", "import openai", "import anthropic",
        "import telegram", "import smtplib", "import webbrowser",
        "os.environ", "os.getenv", "getenv(", "load_dotenv", "dotenv",
        "requests.", "httpx.", "aiohttp.", "urlopen", "socket.",
        "subprocess.", "smtplib.", "webbrowser.",
    ]
    for token in forbidden:
        assert token not in src, "forbidden token present: %s" % token
