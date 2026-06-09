"""Tests for the pre-alpha daily operator content run packet (Task 0111).

Local-only, deterministic. Verifies the run packet composes the accepted
0103-0110 generators, reconciles counts, preserves blocked/not-ready items,
pins hard-boundary flags, fails closed on unsafe child flags or unexpected
child blocks, and never implies publish readiness or platform API payloads.
"""

import json
import os

from live_contentops import pre_alpha_daily_operator_content_run as run_mod


def _packet():
    return run_mod.build_daily_operator_content_run_packet({})


def test_schema_loads():
    schema = run_mod.load_schema()
    assert schema["title"] == "PreAlphaDailyOperatorContentRunPacket"
    assert "hard_boundary_flags" in schema["properties"]


def test_pass_path_generation():
    packet = _packet()
    assert packet["packet_status"] == "pass"
    assert packet["blocked_reasons"] == []
    for key in (
        "daily_operator_content_run_packet_id",
        "created_at",
        "run_label",
        "source_packet_ids",
        "seed_and_calendar_summary",
        "dashboard_summary",
        "review_batch_summary",
        "decision_batch_summary",
        "export_batch_summary",
        "platform_template_summary",
        "manual_publish_record_summary",
        "ready_for_operator_copy_paste_count",
        "blocked_or_not_ready_count",
        "operator_action_queue",
        "blocked_content_report",
        "final_operator_checklist",
        "hard_boundary_flags",
        "safety_audit",
    ):
        assert key in packet


def test_source_packet_ids_reconcile():
    packet = _packet()
    ids = packet["source_packet_ids"]
    assert ids["batch_review_packet_id"] == packet["review_batch_summary"]["batch_review_packet_id"]
    assert ids["manual_decision_batch_packet_id"] == packet["decision_batch_summary"]["manual_decision_batch_packet_id"]
    assert ids["manual_export_batch_packet_id"] == packet["export_batch_summary"]["manual_export_batch_packet_id"]
    assert ids["platform_manual_template_packet_id"] == packet["platform_template_summary"]["platform_manual_template_packet_id"]
    assert ids["manual_publish_record_packet_id"] == packet["manual_publish_record_summary"]["manual_publish_record_packet_id"]


def test_ready_and_not_ready_counts_reconcile():
    packet = _packet()
    tmpl = packet["platform_template_summary"]
    assert packet["ready_for_operator_copy_paste_count"] == tmpl["platform_template_record_count"]
    rec = packet["manual_publish_record_summary"]
    exp = packet["export_batch_summary"]
    review = packet["review_batch_summary"]
    expected_not_ready = (
        review["blocked_seed_count"]
        + exp["non_exported_decision_count"]
        + tmpl["unsupported_or_blocked_count"]
        + rec["blocked_record_count"]
        + rec["not_recorded_count"]
    )
    assert packet["blocked_or_not_ready_count"] == expected_not_ready


def test_blocked_items_preserved_with_reasons():
    packet = _packet()
    report = packet["blocked_content_report"]
    assert len(report) > 0
    for item in report:
        assert "stage" in item


def test_revision_and_rejected_not_marked_ready():
    packet = _packet()
    dec = packet["decision_batch_summary"]
    assert dec["revision_requested_count"] >= 1
    assert dec["rejected_count"] >= 1
    assert packet["ready_for_operator_copy_paste_count"] == dec["approval_packet_count"]


def test_platform_templates_remain_manual_copy_paste_only():
    tmpl = run_mod.templates.build_platform_manual_template_packet(
        run_mod.export_batch.build_from_config_file()
    )
    for rec in tmpl["platform_template_records"]:
        assert rec["public_postable"] is False
        assert rec["platform_api_call_allowed"] is False
        assert rec["manual_publish_only"] is True
        assert rec["operator_final_check_required"] is True


def test_final_operator_checklist_present():
    packet = _packet()
    assert len(packet["final_operator_checklist"]) >= 3
    joined = " ".join(packet["final_operator_checklist"]).lower()
    assert "manual" in joined
    assert "posts for you" in joined or "never posts" in joined


def test_no_platform_api_payload_fields():
    packet = _packet()
    blob = json.dumps(packet)
    assert "platform_api_payload" not in blob


def test_public_postable_and_auto_publish_pinned_false():
    packet = _packet()
    flags = packet["hard_boundary_flags"]
    assert flags["public_postable"] is False
    assert flags["auto_publish"] is False
    assert flags["auto_approval"] is False


def test_hard_boundary_flags_pinned():
    packet = _packet()
    flags = packet["hard_boundary_flags"]
    for flag, expected in run_mod._REQUIRED_FLAGS.items():
        assert flags[flag] is expected
    assert packet["safety_audit"]["unsafe_flag_count"] == 0


def test_fail_closed_on_unsafe_flag(monkeypatch):
    bad = dict(run_mod._REQUIRED_FLAGS)
    bad["public_postable"] = True
    monkeypatch.setattr(run_mod, "_hard_boundary_flags", lambda: dict(bad))
    packet = _packet()
    assert packet["packet_status"] == "blocked"
    assert any("public_postable" in r for r in packet["blocked_reasons"])


def test_fail_closed_on_unexpected_child_block(monkeypatch):
    blocked_child = {
        "packet_status": "blocked",
        "manual_export_batch_packet_id": "export_blocked",
        "manual_export_packets": [],
        "content_ledger_entries": [],
        "non_exported_decision_report": [],
    }
    monkeypatch.setattr(
        run_mod.export_batch, "build_from_config_file",
        lambda *a, **k: blocked_child,
    )
    packet = _packet()
    assert packet["packet_status"] == "blocked"
    assert any(
        "child_packet_blocked:export_batch" in r for r in packet["blocked_reasons"]
    )


def test_deterministic_output():
    a = json.dumps(_packet(), sort_keys=True)
    b = json.dumps(_packet(), sort_keys=True)
    assert a == b


def test_cli_summary_valid_json():
    out = run_mod.summary()
    assert out["packet_status"] == "pass"
    assert out["local_only"] is True
    assert out["network_call_made"] is False
    assert out["provider_call_made"] is False
    assert out["platform_api_call_allowed_now"] is False
    assert out["scheduler_allowed"] is False
    assert out["automatic_metrics_ingestion_allowed"] is False
    assert out["scraping_allowed"] is False
    assert out["credential_read"] is False
    assert out["auto_publish"] is False
    assert out["auto_approval"] is False
    json.loads(json.dumps(out))


def test_static_scan_no_forbidden_imports_or_calls():
    """Module must not import network/provider/platform/scheduler libs or read
    env, post, scrape, or ingest metrics."""
    path = os.path.join(
        os.path.dirname(run_mod.__file__),
        "pre_alpha_daily_operator_content_run.py",
    )
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    forbidden = [
        "import requests", "import httpx", "import aiohttp", "import urllib",
        "import socket", "import subprocess", "import openai", "import anthropic",
        "os.environ", "os.getenv", "getenv(", "dotenv", "load_dotenv",
        ".post(", ".send(", "schedule.", "APScheduler", "BeautifulSoup",
        "selenium", "playwright", "smtplib",
    ]
    for token in forbidden:
        assert token not in src, "forbidden token in module: %s" % token


def test_config_file_build_matches_default():
    from_file = run_mod.build_from_config_file()
    assert from_file["packet_status"] == "pass"
    assert from_file["run_label"] == "default_daily_run"

