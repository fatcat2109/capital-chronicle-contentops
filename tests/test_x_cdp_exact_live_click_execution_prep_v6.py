"""Tests for X CDP exact live-click execution prep dry run."""
from __future__ import annotations

import json

from live_contentops.x_cdp_exact_live_click_execution_prep_v6 import (
    BLOCKED_STATUS,
    READY_STATUS,
    build_execution_prep_packet,
    build_fixture_evidence_bundle,
    main,
)
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


def _scope(scope_decision="approve_future_scope"):
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
    return build_scope_decision_packet(authorization_request_packet=request, scope_decision=scope_decision)


def test_approved_future_scope_becomes_execution_authorization_ready_not_live():
    packet = build_execution_prep_packet(scope_decision_packet=_scope())
    assert packet["execution_prep_status"] == READY_STATUS
    assert packet["ready_for_exact_live_execution_authorization_task"] is True
    assert packet["exact_live_authorization_task_required"] is True
    assert packet["fresh_profile_guard_required_before_click"] is True
    assert packet["operator_visible_account_destination_recheck_required_before_click"] is True
    assert packet["kill_switch_recheck_required_before_click"] is True
    assert packet["live_click_allowed_now"] is False
    assert packet["live_click_allowed"] is False
    assert packet["live_click_performed"] is False
    assert packet["publication_registry_record_appended"] is False
    assert packet["public_url_capture_performed"] is False


def test_denied_and_deferred_scope_are_blocked():
    for decision in ("deny", "defer"):
        packet = build_execution_prep_packet(scope_decision_packet=_scope(decision))
        assert packet["execution_prep_status"] == BLOCKED_STATUS
        assert packet["ready_for_exact_live_execution_authorization_task"] is False
        assert "scope_decision_status_approved_for_future" in packet["blocked_reasons"]
        assert "future_exact_live_task_eligible" in packet["blocked_reasons"]


def test_execution_prep_blocks_scope_decision_id_mismatch():
    packet = build_execution_prep_packet(scope_decision_packet={**_scope(), "scope_decision_id": "x_scope_decision_wrong"})
    assert packet["execution_prep_status"] == BLOCKED_STATUS
    assert "scope_decision_id_recomputed_match" in packet["blocked_reasons"]


def test_execution_prep_blocks_live_or_registry_flags():
    live = build_execution_prep_packet(scope_decision_packet={**_scope(), "live_click_performed": True})
    registry = build_execution_prep_packet(scope_decision_packet={**_scope(), "publication_registry_record_appended": True})
    assert live["execution_prep_status"] == BLOCKED_STATUS
    assert registry["execution_prep_status"] == BLOCKED_STATUS
    assert "still_blocks_live_click_now" in live["blocked_reasons"]
    assert "registry_and_public_url_not_written" in registry["blocked_reasons"]


def test_fixture_bundle_covers_ready_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["approved_case_ready_for_authorization_task"] is True
    assert bundle["all_cases_blocked_before_click"] is True
    assert bundle["raw_go_phrase_stored_anywhere"] is False
    assert bundle["case_count"] >= 6
    statuses = {case["execution_prep_status"] for case in bundle["cases"].values()}
    assert {READY_STATUS, BLOCKED_STATUS}.issubset(statuses)


def test_cli_requires_dry_run(capsys):
    code = main(["--fixture-bundle"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False


def test_cli_fixture_evidence_writes_json(tmp_path, capsys):
    path = tmp_path / "evidence.json"
    code = main(["--dry-run", "--fixture-bundle", "--write-evidence", str(path)])
    printed = json.loads(capsys.readouterr().out)
    written = json.loads(path.read_text(encoding="utf-8"))
    assert code == 0
    assert printed["approved_case_ready_for_authorization_task"] is True
    assert written == printed
