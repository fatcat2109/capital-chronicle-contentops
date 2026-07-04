"""Tests for final X CDP pre-click rehearsal dry run."""
from __future__ import annotations

import json

from live_contentops.x_cdp_final_pre_click_rehearsal_dry_run_v6 import (
    BLOCKED_STATUS,
    PASS_STATUS,
    build_final_pre_click_rehearsal_packet,
    build_fixture_evidence_bundle,
    main,
)
from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import EXPECTED_GO_PHRASE, build_go_phrase_gate_packet
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import build_prelive_post_packet

PAYLOAD = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
COMMAND_LINE = r"msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"


def _chain():
    prelive = build_prelive_post_packet(payload_text=PAYLOAD, cdp_port=9223, command_line=COMMAND_LINE)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        kill_switch_snapshot=default_kill_switch_snapshot(),
        rollback_checklist=default_rollback_checklist(),
    )
    return prelive, gate, auth


def test_final_rehearsal_ready_but_non_executable():
    packet = build_final_pre_click_rehearsal_packet(*(), prelive_packet=_chain()[0], go_gate_packet=_chain()[1], authorization_packet=_chain()[2])
    assert packet["final_rehearsal_status"] == PASS_STATUS
    assert packet["ready_for_separate_exact_live_task"] is True
    assert packet["separate_exact_live_task_required"] is True
    assert packet["blocked_before_live_click"] is True
    assert packet["live_click_allowed"] is False
    assert packet["live_click_performed"] is False
    assert packet["approval_ledger_entry_created"] is False
    assert packet["executable_outbox_entry_created"] is False
    assert packet["publication_registry_record_appended"] is False
    assert packet["public_url_capture_performed"] is False
    assert packet["raw_go_phrase_stored"] is False


def test_final_rehearsal_blocks_authorization_id_mismatch():
    prelive, gate, auth = _chain()
    packet = build_final_pre_click_rehearsal_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        authorization_packet={**auth, "authorization_packet_id": "x_live_click_auth_wrong"},
    )
    assert packet["final_rehearsal_status"] == BLOCKED_STATUS
    assert "authorization_packet_id_recomputed_match" in packet["blocked_reasons"]
    assert packet["live_click_allowed"] is False


def test_final_rehearsal_blocks_missing_capture_plan():
    prelive, gate, auth = _chain()
    packet = build_final_pre_click_rehearsal_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        authorization_packet={**auth, "post_click_capture_plan": None},
    )
    assert packet["final_rehearsal_status"] == BLOCKED_STATUS
    assert "post_click_capture_plan_present" in packet["blocked_reasons"]
    assert "post_click_capture_plan_non_executable_now" in packet["blocked_reasons"]


def test_final_rehearsal_blocks_disabled_kill_switch():
    prelive, gate, auth = _chain()
    packet = build_final_pre_click_rehearsal_packet(
        prelive_packet=prelive,
        go_gate_packet=gate,
        authorization_packet={**auth, "kill_switch_snapshot": {**auth["kill_switch_snapshot"], "live_click_enabled_now": True}},
    )
    assert "kill_switch_blocks_live_click_now" in packet["blocked_reasons"]
    assert packet["final_rehearsal_status"] == BLOCKED_STATUS


def test_fixture_bundle_covers_ready_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["approved_case_ready_for_separate_exact_live_task"] is True
    assert bundle["all_cases_blocked_before_click"] is True
    assert bundle["raw_go_phrase_stored_anywhere"] is False
    assert bundle["case_count"] >= 7
    statuses = {case["final_rehearsal_status"] for case in bundle["cases"].values()}
    assert PASS_STATUS in statuses
    assert BLOCKED_STATUS in statuses


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
    assert printed["approved_case_ready_for_separate_exact_live_task"] is True
    assert written == printed
