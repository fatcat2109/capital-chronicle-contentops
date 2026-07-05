"""Tests for the pre-alpha operator dashboard packet (Task 0104).

Local-only, deterministic. No network/provider/LLM/platform/credential access.
"""

import json
import os

from live_contentops import pre_alpha_operator_dashboard as dash


def test_schema_loads():
    schema = dash.load_dashboard_schema()
    assert schema["title"] == "PreAlphaOperatorDashboardPacket"


def test_packet_generation_pass_path():
    packet = dash.build_dashboard_packet()
    assert packet["packet_status"] == "pass"
    assert packet["dashboard_packet_id"].startswith("dashboard_")
    assert packet["repo_posture"]["mode"] == "pre_alpha_local_only"
    for key in (
        "source_refs",
        "seed_library_summary",
        "editorial_calendar_summary",
        "blocked_content_summary",
        "pipeline_demo_summary",
        "manual_export_ledger_summary",
        "operator_next_actions",
        "hard_boundary_flags",
        "safety_audit",
    ):
        assert key in packet


def test_safe_and_blocked_seed_counts_surfaced():
    packet = dash.build_dashboard_packet()
    sl = packet["seed_library_summary"]
    assert sl["safe_seed_count"] == 3
    assert sl["blocked_seed_count"] == 1
    assert sl["total_seeds"] == 4
    cal = packet["editorial_calendar_summary"]
    assert cal["safe_item_count"] == 3
    assert cal["blocked_item_count"] == 1
    assert cal["manual_review_queue_count"] == 3


def test_blocked_reasons_preserved_not_dropped():
    packet = dash.build_dashboard_packet()
    bc = packet["blocked_content_summary"]
    assert bc["blocked_item_count"] == 1
    assert len(bc["blocked_items"]) == 1
    item = bc["blocked_items"][0]
    assert item["seed_id"] == "seed_blocked_signal_001"
    assert item["blocked_reasons"]


def test_hard_boundary_flags_pinned():
    packet = dash.build_dashboard_packet()
    flags = packet["hard_boundary_flags"]
    assert flags["local_only"] is True
    assert flags["fixture_only"] is True
    assert flags["manual_review_required"] is True
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



def test_dashboard_blocks_on_unsafe_flag():
    original = dict(dash._REQUIRED_FLAGS)
    try:
        bad = dash._hard_boundary_flags()
        bad["live_execution_allowed_now"] = True
        violations = dash._audit_flags(bad)
        assert any("live_execution_allowed_now" in v for v in violations)
    finally:
        dash._REQUIRED_FLAGS.clear()
        dash._REQUIRED_FLAGS.update(original)


def test_dashboard_blocks_on_unsafe_child_summary(monkeypatch):
    def fake_run(path=None):
        return {"demo_status": "weird", "stages_reached": [], "safety_violations": []}

    monkeypatch.setattr(dash.demo, "run_demo_from_file", fake_run)
    packet = dash.build_dashboard_packet()
    assert packet["packet_status"] == "blocked"
    assert any("pipeline_demo:unknown_status" in r for r in packet["blocked_reasons"])


def test_dashboard_blocks_on_demo_safety_violation(monkeypatch):
    def fake_run(path=None):
        return {
            "demo_status": "blocked",
            "stages_reached": ["seed"],
            "safety_violations": ["editorial_packet.public_postable=True"],
        }

    monkeypatch.setattr(dash.demo, "run_demo_from_file", fake_run)
    packet = dash.build_dashboard_packet()
    assert packet["packet_status"] == "blocked"
    assert any("pipeline_demo:" in r for r in packet["blocked_reasons"])


def test_deterministic_output():
    p1 = dash.build_dashboard_packet()
    p2 = dash.build_dashboard_packet()
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)


def test_operator_next_actions_present():
    packet = dash.build_dashboard_packet()
    actions = packet["operator_next_actions"]
    assert isinstance(actions, list)
    assert actions
    assert any("manual" in a.lower() for a in actions)


def test_cli_summary_valid_json_and_safe():
    s = dash.summary()
    assert json.loads(json.dumps(s)) == s
    assert s["local_only"] is True
    assert s["provider_call_made"] is False
    assert s["network_call_made"] is False
    assert s["credential_read"] is False
    assert s["public_postable_output"] is False
    assert s["scheduler_allowed"] is False
    assert s["metrics_ingestion_allowed"] is False
    assert s["packet_status"] == "pass"
    assert s["safe_seed_count"] == 3
    assert s["blocked_seed_count"] == 1
    assert s["unsafe_flag_count"] == 0


def test_no_forbidden_imports_in_module():
    path = os.path.join(
        os.path.dirname(__file__), "..", "live_contentops", "pre_alpha_operator_dashboard.py"
    )
    with open(os.path.abspath(path), "r", encoding="utf-8") as f:
        src = f.read()
    forbidden = [
        "import requests",
        "import httpx",
        "import aiohttp",
        "import urllib",
        "import socket",
        "import subprocess",
        "import openai",
        "import anthropic",
        "os.environ",
        "getenv",
        "dotenv",
        ".post(",
        "schedule(",
    ]
    for token in forbidden:
        assert token not in src, "forbidden token present: %s" % token
