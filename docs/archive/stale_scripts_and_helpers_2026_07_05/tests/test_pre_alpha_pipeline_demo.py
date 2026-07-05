"""Tests for the 0101 pre-alpha end-to-end local demo packet."""

import json
import os

import pytest

from live_contentops import pre_alpha_pipeline_demo as demo

FIXTURE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "fixtures",
    "pre_alpha_pipeline_demo",
    "valid_end_to_end_demo_input.json",
)


def _load_seed():
    with open(os.path.abspath(FIXTURE), "r", encoding="utf-8") as f:
        return json.load(f)


def test_demo_passes_end_to_end_from_seed_to_ledger():
    packet = demo.run_demo_from_file()
    assert packet["demo_status"] == "pass"
    assert packet["blocked_reasons"] == []
    assert packet["safety_violations"] == []
    # Every pipeline stage must be reached.
    for stage in (
        "seed",
        "editorial_packet",
        "rendered_packet",
        "review_queue",
        "approval_packet",
        "manual_export_packet",
        "content_ledger_entry",
    ):
        assert stage in packet["stages_reached"]


def test_demo_records_every_stage_object():
    packet = demo.run_demo_from_file()
    stages = packet["stages"]
    assert stages["editorial_packet"]["guardrail_status"] == "pass"
    assert stages["rendered_packet"]["guardrail_status"] == "pass"
    assert len(stages["review_queue_items"]) >= 1
    assert len(stages["item_traces"]) >= 1
    trace = stages["item_traces"][0]
    assert trace["approval_packet"]["approval_status"] == "approved_manual_publish_prep"
    assert trace["export_packet"]["export_status"] == "prepared_for_operator_review"
    assert trace["ledger_entry"]["lifecycle_status"] == "export_prepared"


def test_all_no_publish_no_live_flags_remain_pinned_false():
    packet = demo.run_demo_from_file()
    pinned = [
        "public_postable",
        "publish_allowed_now",
        "platform_publish_allowed_now",
        "live_execution_allowed_now",
        "provider_call_made",
        "network_call_made",
        "platform_api_call_allowed",
        "scheduler_allowed",
        "metrics_ingestion_allowed",
    ]
    for flag in pinned:
        assert packet[flag] is False, flag
    assert packet["manual_review_required"] is True
    assert packet["final_operator_check_required"] is True
    # Per-stage audit must show no flag anywhere set to anything but False.
    assert packet["safety_violations"] == []
    for entry in packet["safety_audit"]:
        for flag, value in entry["flags"].items():
            assert value is False, "%s.%s" % (entry["stage"], flag)


def test_ledger_publish_fields_default_null():
    packet = demo.run_demo_from_file()
    for trace in packet["stages"]["item_traces"]:
        ledger = trace["ledger_entry"]
        assert ledger["manual_publish_url"] is None
        assert ledger["manual_publish_timestamp"] is None
        assert ledger["manual_metrics"] is None
        assert ledger["lifecycle_status"] != "manually_published"


def test_unsafe_signal_language_seed_cannot_pass_demo():
    seed = _load_seed()
    # Inject a forbidden trade-direction claim into the key points.
    seed["key_points"] = [
        "Our model says buy the dip now; this is a strong signal to go long."
    ]
    packet = demo.run_demo(seed)
    assert packet["demo_status"] == "blocked"
    assert packet["blocked_reasons"]
    # No item should reach a clean approval/export.
    for trace in packet["stages"].get("item_traces", []):
        assert trace["approval_packet"]["approval_status"] != "approved_manual_publish_prep" or \
            trace["export_packet"]["export_status"] == "blocked"


def test_fake_alpha_market_note_seed_cannot_pass_demo():
    seed = _load_seed()
    seed["content_type"] = "market_note"
    seed["content_source_type"] = "general_process"
    seed["title"] = "Capital Chronicle alpha forecast says SP500 hits 7000"
    seed["key_points"] = [
        "Our Capital Chronicle alpha model guarantees the index will rise 12%."
    ]
    packet = demo.run_demo(seed)
    assert packet["demo_status"] == "blocked"
    assert packet["blocked_reasons"]


def test_public_postable_seed_attempt_does_not_flip_pinned_flags():
    seed = _load_seed()
    # An adversarial input that tries to assert publishability must not change
    # the pinned demo posture.
    seed["public_postable"] = True
    seed["publish_allowed_now"] = True
    seed["live_execution_allowed_now"] = True
    packet = demo.run_demo(seed)
    assert packet["public_postable"] is False
    assert packet["publish_allowed_now"] is False
    assert packet["live_execution_allowed_now"] is False
    assert packet["safety_violations"] == []


def test_summary_reports_pinned_false_and_real_demo_status():
    s = demo.summary()
    assert s["local_only"] is True
    assert s["fixture_only"] is True
    assert s["public_postable"] is False
    assert s["live_execution_allowed_now"] is False
    assert s["provider_call_made"] is False
    assert s["network_call_made"] is False
    assert s["scheduler_allowed"] is False
    assert s["metrics_ingestion_allowed"] is False
    assert s["auto_approval"] is False
    assert s["default_demo_status"] == "pass"
    assert s["default_demo_safety_violations"] == []


def test_demo_module_makes_no_network_or_env_access():
    # Static guarantee: the module imports no network/provider/credential libs.
    src_path = os.path.join(
        os.path.dirname(__file__), "..", "live_contentops", "pre_alpha_pipeline_demo.py"
    )
    with open(os.path.abspath(src_path), "r", encoding="utf-8") as f:
        src = f.read()
    for forbidden in ("import requests", "import urllib", "import socket",
                      "os.environ", "getenv", "dotenv", "open(\".env"):
        assert forbidden not in src, forbidden
