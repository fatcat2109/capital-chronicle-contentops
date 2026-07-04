"""Tests for X CDP exact live-click execution outcome."""
from __future__ import annotations

import json

from live_contentops.x_cdp_exact_live_click_authorization_v6 import build_exact_live_click_authorization
from live_contentops.x_cdp_exact_live_click_execution_v6 import (
    BLOCKED_STATUS,
    EXECUTED_STATUS,
    build_exact_live_click_execution,
    build_fixture_evidence_bundle,
    main,
)
from live_contentops.x_cdp_exact_live_click_execution_prep_v6 import build_execution_prep_packet
from live_contentops.x_cdp_exact_separate_live_click_authorization_request_v6 import build_exact_live_click_authorization_request
from live_contentops.x_cdp_exact_separate_live_click_scope_decision_v6 import build_scope_decision_packet
from live_contentops.x_cdp_final_pre_click_rehearsal_dry_run_v6 import build_final_pre_click_rehearsal_packet
from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import EXPECTED_GO_PHRASE, build_go_phrase_gate_packet
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import build_prelive_post_packet

PAYLOAD = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
COMMAND_LINE = r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
URL = "https://x.com/capitalchronicle/status/1234567890123456789"


def _authorization(scope_decision="approve_future_scope"):
    prelive = build_prelive_post_packet(payload_text=PAYLOAD, cdp_port=9223, command_line=COMMAND_LINE)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        kill_switch_snapshot=default_kill_switch_snapshot(),
        rollback_checklist=default_rollback_checklist(),
    )
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
    decision = build_scope_decision_packet(authorization_request_packet=request, scope_decision=scope_decision)
    prep = build_execution_prep_packet(scope_decision_packet=decision)
    return build_exact_live_click_authorization(execution_prep_packet=prep)


def _execute(auth=None, **overrides):
    auth = _authorization() if auth is None else auth
    kwargs = {
        "authorization_packet": auth,
        "operator_confirmed_click_performed": True,
        "captured_public_x_url": URL,
        "operator_confirmed_payload_hash": auth["payload_hash"],
        "operator_confirmed_account_destination": "@capitalchronicle on X",
        "operator_confirmed_kill_switch_available_before_click": True,
    }
    kwargs.update(overrides)
    return build_exact_live_click_execution(**kwargs)


def test_authorized_click_with_captured_public_url_executes_outcome():
    packet = _execute()
    assert packet["execution_status"] == EXECUTED_STATUS
    assert packet["live_click_performed"] is True
    assert packet["public_url_capture_performed"] is True
    assert packet["captured_public_x_url"] == URL
    assert packet["registry_append_ready"] is True
    assert packet["publication_registry_record_appended"] is False
    assert packet["browser_or_cdp_probe_performed"] is False
    assert packet["x_api_used"] is False


def test_missing_click_confirmation_blocks():
    packet = _execute(operator_confirmed_click_performed=False)
    assert packet["execution_status"] == BLOCKED_STATUS
    assert packet["live_click_performed"] is False
    assert "operator_click_confirmed" in packet["blocked_reasons"]


def test_missing_or_non_status_public_url_blocks():
    missing = _execute(captured_public_x_url="")
    wrong = _execute(captured_public_x_url="https://x.com/capitalchronicle")
    assert missing["execution_status"] == BLOCKED_STATUS
    assert wrong["execution_status"] == BLOCKED_STATUS
    assert "captured_public_x_url_valid" in missing["blocked_reasons"]
    assert "captured_public_x_url_valid" in wrong["blocked_reasons"]


def test_authorization_not_ready_blocks():
    denied = _authorization("deny")
    packet = _execute(auth=denied, operator_confirmed_payload_hash=denied.get("payload_hash", ""))
    assert packet["execution_status"] == BLOCKED_STATUS
    assert "authorization_status_authorized" in packet["blocked_reasons"]


def test_payload_hash_mismatch_blocks():
    packet = _execute(operator_confirmed_payload_hash="0" * 64)
    assert packet["execution_status"] == BLOCKED_STATUS
    assert "operator_payload_hash_confirmed" in packet["blocked_reasons"]


def test_prior_registry_append_blocks():
    packet = _execute(auth={**_authorization(), "publication_registry_record_appended": True})
    assert packet["execution_status"] == BLOCKED_STATUS
    assert "prior_registry_not_appended" in packet["blocked_reasons"]


def test_fixture_bundle_covers_executed_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    statuses = {case["execution_status"] for case in bundle["cases"].values()}
    assert bundle["ready_case_executed_with_captured_public_url"] is True
    assert {EXECUTED_STATUS, BLOCKED_STATUS}.issubset(statuses)
    assert bundle["registry_append_performed"] is False
    assert bundle["raw_go_phrase_stored_anywhere"] is False


def test_cli_requires_dry_run(capsys):
    code = main(["--fixture-bundle"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_performed"] is False


def test_cli_fixture_evidence_writes_json(tmp_path, capsys):
    path = tmp_path / "evidence.json"
    code = main(["--dry-run", "--fixture-bundle", "--write-evidence", str(path)])
    printed = json.loads(capsys.readouterr().out)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert code == 0
    assert printed["ready_case_executed_with_captured_public_url"] is True
    assert written == printed
