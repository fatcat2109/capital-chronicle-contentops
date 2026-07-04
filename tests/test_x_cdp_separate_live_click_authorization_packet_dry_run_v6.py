"""Tests for X CDP separate live-click authorization packet dry run."""
from __future__ import annotations

import json

from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import (
    EXPECTED_GO_PHRASE,
    build_go_phrase_gate_packet,
)
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    BLOCKED_STATUS,
    PASS_STATUS,
    build_fixture_evidence_bundle,
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
    main,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import build_prelive_post_packet

PAYLOAD = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
COMMAND_LINE = r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"


def _chain():
    prelive = build_prelive_post_packet(payload_text=PAYLOAD, cdp_port=9223, command_line=COMMAND_LINE)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    packet = build_live_click_authorization_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        kill_switch_snapshot=default_kill_switch_snapshot(),
        rollback_checklist=default_rollback_checklist(),
    )
    return prelive, gate, packet


def test_authorization_packet_ready_but_non_executable():
    _, _, packet = _chain()
    assert packet["authorization_packet_status"] == PASS_STATUS
    assert packet["ready_for_exact_separate_live_task"] is True
    assert packet["separate_exact_live_task_required"] is True
    assert packet["live_click_allowed"] is False
    assert packet["live_click_performed"] is False
    assert packet["approval_ledger_entry_created"] is False
    assert packet["executable_outbox_entry_created"] is False
    assert packet["publication_registry_record_appended"] is False
    assert packet["public_url_capture_performed"] is False


def test_authorization_packet_includes_post_click_capture_expectations_only():
    _, _, packet = _chain()
    plan = packet["post_click_capture_plan"]
    assert plan["expected_capture_method_after_future_click"] == "x_cdp_post_detail_after_click"
    assert plan["public_url_capture_required_after_future_click"] is True
    assert plan["registry_append_allowed_now"] is False
    assert plan["public_url_fetch_allowed"] is False


def test_go_gate_mismatch_blocks():
    prelive, gate, _ = _chain()
    packet = build_live_click_authorization_packet(
        prelive_packet=prelive,
        go_gate_packet={**gate, "go_gate_packet_id": "x_go_gate_wrong"},
        kill_switch_snapshot=default_kill_switch_snapshot(),
        rollback_checklist=default_rollback_checklist(),
    )
    assert packet["authorization_packet_status"] == BLOCKED_STATUS
    assert "go_gate_packet_id_recomputed_match" in packet["blocked_reasons"]
    assert packet["live_click_allowed"] is False


def test_payload_hash_mismatch_blocks():
    prelive, gate, _ = _chain()
    packet = build_live_click_authorization_packet(
        prelive_packet={**prelive, "payload_hash": "0" * 64},
        go_gate_packet=gate,
        kill_switch_snapshot=default_kill_switch_snapshot(),
        rollback_checklist=default_rollback_checklist(),
    )
    assert packet["authorization_packet_status"] == BLOCKED_STATUS
    assert "payload_hash_recomputed_match" in packet["blocked_reasons"]
    assert "go_gate_references_same_payload_hash" in packet["blocked_reasons"]


def test_kill_switch_and_rollback_missing_block():
    prelive, gate, _ = _chain()
    no_kill = build_live_click_authorization_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        rollback_checklist=default_rollback_checklist(),
    )
    no_rollback = build_live_click_authorization_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        kill_switch_snapshot=default_kill_switch_snapshot(),
        rollback_checklist=[],
    )
    assert "kill_switch_snapshot_present" in no_kill["blocked_reasons"]
    assert "rollback_checklist_present" in no_rollback["blocked_reasons"]


def test_fixture_bundle_covers_ready_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["approved_case_ready_for_separate_live_task"] is True
    assert bundle["all_cases_blocked_before_click"] is True
    assert bundle["raw_go_phrase_stored_anywhere"] is False
    assert bundle["case_count"] >= 6
    statuses = {case["authorization_packet_status"] for case in bundle["cases"].values()}
    assert PASS_STATUS in statuses
    assert BLOCKED_STATUS in statuses


def test_cli_requires_dry_run(capsys):
    code = main(["--fixture-bundle"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["status"] == "blocked_dry_run_flag_required"
    assert payload["live_click_allowed"] is False
