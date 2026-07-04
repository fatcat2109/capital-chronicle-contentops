"""Tests for X CDP exact separate live-click scope decision dry run."""
from __future__ import annotations

import json

from live_contentops.x_cdp_exact_separate_live_click_authorization_request_v6 import build_exact_live_click_authorization_request
from live_contentops.x_cdp_exact_separate_live_click_scope_decision_v6 import (
    APPROVED_FUTURE_STATUS,
    BLOCKED_STATUS,
    DEFERRED_STATUS,
    DENIED_STATUS,
    build_fixture_evidence_bundle,
    build_scope_decision_packet,
    main,
)
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


def _request():
    prelive = build_prelive_post_packet(payload_text=PAYLOAD, cdp_port=9223, command_line=COMMAND_LINE)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        kill_switch_snapshot=default_kill_switch_snapshot(),
        rollback_checklist=default_rollback_checklist(),
    )
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    return build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)


def test_denied_scope_decision_is_non_executable():
    packet = build_scope_decision_packet(authorization_request_packet=_request(), scope_decision="deny")
    assert packet["scope_decision_status"] == DENIED_STATUS
    assert packet["approval_decision_record_created"] is True
    assert packet["future_exact_live_task_eligible_for_consideration"] is False
    assert packet["live_click_allowed_now"] is False
    assert packet["live_click_allowed"] is False
    assert packet["live_click_performed"] is False
    assert packet["publication_registry_record_appended"] is False
    assert packet["public_url_capture_performed"] is False


def test_deferred_scope_decision_is_non_executable():
    packet = build_scope_decision_packet(authorization_request_packet=_request(), scope_decision="defer")
    assert packet["scope_decision_status"] == DEFERRED_STATUS
    assert packet["future_exact_live_task_required"] is True
    assert packet["explicit_future_live_authorization_still_required"] is True
    assert packet["future_exact_live_task_eligible_for_consideration"] is False
    assert packet["live_click_performed"] is False


def test_approve_future_scope_still_does_not_click():
    packet = build_scope_decision_packet(authorization_request_packet=_request(), scope_decision="approve_future_scope")
    assert packet["scope_decision_status"] == APPROVED_FUTURE_STATUS
    assert packet["future_exact_live_task_eligible_for_consideration"] is True
    assert packet["fresh_profile_guard_required_in_future_task"] is True
    assert packet["operator_visible_account_destination_recheck_required"] is True
    assert packet["post_click_public_url_capture_required_before_registry_append"] is True
    assert packet["live_click_allowed_now"] is False
    assert packet["live_click_allowed"] is False
    assert packet["live_click_performed"] is False


def test_scope_decision_blocks_authorization_request_id_mismatch():
    request = _request()
    packet = build_scope_decision_packet(
        authorization_request_packet={**request, "authorization_request_id": "x_exact_live_request_wrong"},
        scope_decision="approve_future_scope",
    )
    assert packet["scope_decision_status"] == BLOCKED_STATUS
    assert "authorization_request_id_recomputed_match" in packet["blocked_reasons"]
    assert packet["future_exact_live_task_eligible_for_consideration"] is False


def test_scope_decision_blocks_capture_plan_now_executable():
    request = _request()
    packet = build_scope_decision_packet(
        authorization_request_packet={
            **request,
            "post_click_capture_plan": {**request["post_click_capture_plan"], "public_url_fetch_allowed": True},
        },
        scope_decision="approve_future_scope",
    )
    assert packet["scope_decision_status"] == BLOCKED_STATUS
    assert "post_click_capture_plan_non_executable_now" in packet["blocked_reasons"]


def test_fixture_bundle_covers_decisions_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["approved_future_case_eligible_for_consideration"] is True
    assert bundle["all_cases_blocked_before_click"] is True
    assert bundle["raw_go_phrase_stored_anywhere"] is False
    assert bundle["case_count"] >= 7
    statuses = {case["scope_decision_status"] for case in bundle["cases"].values()}
    assert {DENIED_STATUS, DEFERRED_STATUS, APPROVED_FUTURE_STATUS, BLOCKED_STATUS}.issubset(statuses)


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
    assert printed["approved_future_case_eligible_for_consideration"] is True
    assert written == printed
