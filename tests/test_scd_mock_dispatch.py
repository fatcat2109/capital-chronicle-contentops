"""Tests for mock dispatch execution and redacted audit binding (SCD, 0174AT).

Local-only, deterministic, fail-closed. Verifies schema shape, per-object
validation states, mock-only/manual-only invariants, no-network/API/credential/
platform/browser/live flags, Telegram bot/sendMessage/chat_id/webhook blocking,
secret/token/endpoint blocking, manual-export citation/limitation requirements,
redacted audit binding proof requirements, run-report fail-closed precedence,
api_gate_required blocking, forbidden financial/signal language blocking, and
that the deterministic helpers create mock-only records inventing no platform
result, URL, credential, token, or endpoint. No network, providers, credentials,
platform APIs, webhooks, OAuth, or live behavior.
"""
import json
import os
from pathlib import Path

from live_contentops import scd_mock_dispatch as md

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "scd_mock_dispatch"


def _load(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Mock execution request -------------------------------------------------------

def test_request_pass():
    res = md.validate_mock_dispatch_execution_request(_load("request_pass.json"))
    assert res["validation_state"] == md.PASS, res


def test_request_blocked_gate_fail():
    res = md.validate_mock_dispatch_execution_request(_load("request_blocked_gate_fail.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_request_blocked_network_allowed():
    res = md.validate_mock_dispatch_execution_request(_load("request_blocked_network_allowed.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_request_review_required():
    res = md.validate_mock_dispatch_execution_request(_load("request_review_required.json"))
    assert res["validation_state"] == md.REVIEW_REQUIRED, res


def test_request_unknown_missing_ref():
    res = md.validate_mock_dispatch_execution_request(_load("request_unknown_missing_ref.json"))
    assert res["validation_state"] == md.UNKNOWN, res


def test_request_mock_only_required():
    req = _load("request_pass.json")
    req["mock_only"] = False
    res = md.validate_mock_dispatch_execution_request(req)
    assert res["validation_state"] == md.BLOCKED, res


# --- Mock execution record --------------------------------------------------------

def test_record_pass():
    res = md.validate_mock_dispatch_execution_record(_load("record_pass.json"))
    assert res["validation_state"] == md.PASS, res


def test_record_blocked_network():
    res = md.validate_mock_dispatch_execution_record(_load("record_blocked_network.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_record_blocked_credential():
    res = md.validate_mock_dispatch_execution_record(_load("record_blocked_credential.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_record_blocked_telegram():
    res = md.validate_mock_dispatch_execution_record(_load("record_blocked_telegram.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_record_blocked_live():
    res = md.validate_mock_dispatch_execution_record(_load("record_blocked_live.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_record_blocked_signal_language():
    res = md.validate_mock_dispatch_execution_record(_load("record_blocked_signal.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_record_unknown_missing_audit():
    res = md.validate_mock_dispatch_execution_record(_load("record_unknown_missing_audit.json"))
    assert res["validation_state"] == md.UNKNOWN, res


# --- Manual export packet ---------------------------------------------------------

def test_manual_export_pass():
    res = md.validate_manual_export_packet(_load("manual_export_pass.json"))
    assert res["validation_state"] == md.PASS, res


def test_manual_export_blocked_endpoint():
    res = md.validate_manual_export_packet(_load("manual_export_blocked_endpoint.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_manual_export_blocked_missing_content():
    res = md.validate_manual_export_packet(_load("manual_export_blocked_missing_content.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_manual_export_requires_citations_and_limitations():
    packet = _load("manual_export_pass.json")
    packet["citations_included"] = False
    res = md.validate_manual_export_packet(packet)
    assert res["validation_state"] == md.BLOCKED, res


# --- Redacted audit binding -------------------------------------------------------

def test_audit_binding_pass():
    res = md.validate_redacted_audit_binding_packet(_load("audit_binding_pass.json"))
    assert res["validation_state"] == md.PASS, res


def test_audit_binding_blocked_proof():
    res = md.validate_redacted_audit_binding_packet(_load("audit_binding_blocked_proof.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_audit_binding_blocked_on_network():
    binding = _load("audit_binding_pass.json")
    binding["network_accessed"] = True
    res = md.validate_redacted_audit_binding_packet(binding)
    assert res["validation_state"] == md.BLOCKED, res


# --- Run report -------------------------------------------------------------------

def test_run_report_pass():
    res = md.validate_mock_dispatch_run_report(_load("run_report_pass.json"))
    assert res["validation_state"] == md.PASS, res


def test_run_report_blocked_contradiction():
    res = md.validate_mock_dispatch_run_report(_load("run_report_blocked_contradiction.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_run_report_blocked_api_gate():
    res = md.validate_mock_dispatch_run_report(_load("run_report_blocked_api_gate.json"))
    assert res["validation_state"] == md.BLOCKED, res


def test_run_report_cannot_pass_with_non_pass_platform():
    report = _load("run_report_pass.json")
    report["per_platform_mock_results"].append({"platform_id": "telegram", "result": "REVIEW_REQUIRED"})
    res = md.validate_mock_dispatch_run_report(report)
    assert res["validation_state"] == md.BLOCKED, res


# --- Deterministic helpers --------------------------------------------------------

def test_create_mock_dispatch_record_invents_nothing():
    request = _load("request_pass.json")
    gate_result = {"validation_state": md.PASS, "redacted_audit_event_ref": "audit_pass_001"}
    record = md.create_mock_dispatch_record(request, gate_result)
    # All capability-used flags hard false.
    for flag in md.FORBIDDEN_USED_FLAGS:
        assert record[flag] is False, flag
    assert record["execution_mode"] == "mock_only"
    # Platform results only mirror supplied targets; no invented URL/endpoint.
    pids = [r["platform_id"] for r in record["platform_results"]]
    assert pids == request["platform_targets"]
    # Produced record passes its own validator.
    res = md.validate_mock_dispatch_execution_record(record)
    assert res["validation_state"] == md.PASS, res


def test_create_mock_dispatch_record_blocks_when_gate_not_pass():
    request = _load("request_pass.json")
    gate_result = {"validation_state": md.BLOCKED}
    record = md.create_mock_dispatch_record(request, gate_result)
    assert record["execution_state"] == "blocked"
    assert record["validation_state"] == md.BLOCKED


def test_create_manual_export_packet_is_safe():
    record = _load("record_pass.json")
    packet = md.create_manual_export_packet(record, ["payload_x_001"])
    assert packet["export_contains_credentials"] is False
    assert packet["export_contains_tokens"] is False
    assert packet["export_contains_platform_endpoint"] is False
    res = md.validate_manual_export_packet(packet)
    assert res["validation_state"] == md.PASS, res


def test_bind_redacted_audit_event_is_safe():
    record = _load("record_pass.json")
    audit_event = {"audit_event_id": "audit_pass_001", "related_packet_refs": ["mer_pass_001"]}
    binding = md.bind_redacted_audit_event(record, audit_event)
    for flag in ("network_accessed", "credential_accessed", "platform_api_called", "webhook_used", "live_execution"):
        assert binding[flag] is False, flag
    res = md.validate_redacted_audit_binding_packet(binding)
    assert res["validation_state"] == md.PASS, res


# --- Global flag invariants -------------------------------------------------------

def test_no_pass_fixture_grants_live_or_executable():
    for fname in os.listdir(FIXTURE_DIR):
        data = _load(fname)
        if data.get("validation_state") != "PASS":
            continue
        for flag in ("public_ready", "live_ready", "executable_dispatch", "live_eligibility"):
            assert data.get(flag) in (False, None), f"{fname}:{flag}"
        for flag in ("network_accessed", "credential_accessed", "platform_api_called",
                     "telegram_bot_used", "webhook_used", "live_execution", "public_post_created"):
            assert data.get(flag) in (False, None), f"{fname}:{flag}"
