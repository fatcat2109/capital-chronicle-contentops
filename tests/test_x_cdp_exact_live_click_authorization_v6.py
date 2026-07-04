"""Tests for X CDP exact live-click authorization."""
from __future__ import annotations

import json

from live_contentops.x_cdp_exact_live_click_authorization_v6 import (
    AUTHORIZED_STATUS,
    BLOCKED_STATUS,
    build_exact_live_click_authorization,
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


def _prep(scope_decision="approve_future_scope"):
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
    return build_execution_prep_packet(scope_decision_packet=decision)


def test_ready_execution_prep_authorizes_exact_one_click_but_does_not_execute():
    packet = build_exact_live_click_authorization(execution_prep_packet=_prep())
    assert packet["authorization_status"] == AUTHORIZED_STATUS
    assert packet["exact_live_click_authorized_for_one_operator_supervised_click"] is True
    assert packet["authorization_scope"] == "one_payload_one_account_one_destination_one_x_post_click"
    assert packet["live_execution_task_required"] is True
    assert packet["browser_or_cdp_probe_performed"] is False
    assert packet["live_click_performed"] is False
    assert packet["publication_registry_record_appended"] is False
    assert packet["public_url_capture_performed"] is False
    assert packet["raw_go_phrase_stored"] is False


def test_denied_and_deferred_prep_block_authorization():
    for decision in ("deny", "defer"):
        packet = build_exact_live_click_authorization(execution_prep_packet=_prep(decision))
        assert packet["authorization_status"] == BLOCKED_STATUS
        assert packet["exact_live_click_authorized_for_one_operator_supervised_click"] is False
        assert "execution_prep_status_ready" in packet["blocked_reasons"]


def test_authorization_blocks_execution_prep_identity_mismatch():
    packet = build_exact_live_click_authorization(execution_prep_packet={**_prep(), "execution_prep_id": "x_execution_prep_wrong"})
    assert packet["authorization_status"] == BLOCKED_STATUS
    assert "execution_prep_id_recomputed_match" in packet["blocked_reasons"]


def test_authorization_blocks_prior_live_or_registry_flags():
    live = build_exact_live_click_authorization(execution_prep_packet={**_prep(), "live_click_performed": True})
    registry = build_exact_live_click_authorization(execution_prep_packet={**_prep(), "publication_registry_record_appended": True})
    assert live["authorization_status"] == BLOCKED_STATUS
    assert registry["authorization_status"] == BLOCKED_STATUS
    assert "no_prior_live_write_or_registry_append" in live["blocked_reasons"]
    assert "no_prior_live_write_or_registry_append" in registry["blocked_reasons"]


def test_fixture_bundle_covers_authorized_and_blocked_cases():
    bundle = build_fixture_evidence_bundle()
    assert bundle["ready_case_authorized"] is True
    assert bundle["live_action_performed"] is False
    assert bundle["raw_go_phrase_stored_anywhere"] is False
    statuses = {case["authorization_status"] for case in bundle["cases"].values()}
    assert {AUTHORIZED_STATUS, BLOCKED_STATUS}.issubset(statuses)


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
    assert printed["ready_case_authorized"] is True
    assert written == printed
