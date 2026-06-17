"""Tests for the 0174UW/UX/UY Telegram operator cockpit read model + precheck.

Pure, LOCAL, deterministic. NO network / API / Telegram / env / credential read
and NO ``sendMessage``. Asserts the read-model sections, the next-send precheck
classifier across all mandated outcomes, and full redaction + determinism of the
cockpit packet/doc, all driven by the committed 0174UT console packet.
"""

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

cockpit = importlib.import_module(
    "live_contentops.telegram_operator_cockpit_read_model")
console = importlib.import_module(
    "live_contentops.telegram_operator_replay_console")

CONSOLE_PACKET_PATH = ROOT / cockpit.CONSOLE_PACKET_REL


def _console_packet():
    return json.loads(CONSOLE_PACKET_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Import posture / fixtures
# --------------------------------------------------------------------------- #
def test_import_has_no_side_effects():
    mod = importlib.reload(cockpit)
    assert mod.TASK_LABEL.startswith("TASK_CONTENTOPS_0174UW_UX_UY")


def test_committed_console_packet_exists():
    assert CONSOLE_PACKET_PATH.is_file()


# --------------------------------------------------------------------------- #
# Read model + sections
# --------------------------------------------------------------------------- #
def test_read_model_builds_from_committed_console_packet():
    rm = cockpit.build_operator_cockpit_read_model(_console_packet())
    assert rm["read_model_schema"] == cockpit.READ_MODEL_SCHEMA
    assert rm["provider"] == "telegram"
    assert rm["cockpit_read_model_checksum"]


def test_operational_truth_rail_has_reconciliation_ok():
    rm = cockpit.build_operator_cockpit_read_model(_console_packet())
    rail = rm["operational_truth_rail"]
    assert rail["reconciliation_status"] == console.RECON_OK


def test_operational_truth_rail_has_ledger_count_2():
    rm = cockpit.build_operator_cockpit_read_model(_console_packet())
    assert rm["operational_truth_rail"]["current_ledger_count"] == 2


def test_operational_truth_rail_has_last_send_sequence_3():
    rm = cockpit.build_operator_cockpit_read_model(_console_packet())
    rail = rm["operational_truth_rail"]
    assert rail["last_send_sequence"] == 3
    assert rail["last_send_succeeded"] is True


def test_evidence_chain_carries_console_request_response_checksums():
    cp = _console_packet()
    rm = cockpit.build_operator_cockpit_read_model(cp)
    chain = rm["evidence_chain_panel"]
    assert chain["replay_console_checksum"] == cp["console_packet_checksum"]
    last = cp["last_successful_send"]
    assert chain["last_request_checksum"] == last["request_checksum"]
    assert chain["last_response_checksum"] == last["response_checksum"]


def test_replay_guard_panel_contains_all_four_examples():
    rm = cockpit.build_operator_cockpit_read_model(_console_packet())
    panel = rm["replay_guard_panel"]
    assert (panel["exact_replay_example_outcome"]
            == console.ACTION_BLOCKED_EXACT_REPLAY)
    assert (panel["same_payload_no_gate_outcome"]
            == console.ACTION_REQUIRES_FRESH_GATE)
    assert (panel["same_payload_fresh_gate_outcome"]
            == console.ACTION_CLEAR_FOR_MANUAL_SEND)
    assert panel["new_payload_outcome"] == console.ACTION_CLEAR_FOR_MANUAL_SEND


def test_forbidden_affordance_panel_blocks_all_unsafe_affordances():
    rm = cockpit.build_operator_cockpit_read_model(_console_packet())
    p = rm["forbidden_affordance_panel"]
    assert p["no_auto_send"] is True
    assert p["no_scheduler"] is True
    assert p["no_retry_loop"] is True
    assert p["no_autonomous_reply"] is True
    assert p["no_webhook_polling"] is True
    assert p["no_live_ready_claim"] is True


def test_read_model_never_marks_live_or_auto_or_valid_for_live():
    rm = cockpit.build_operator_cockpit_read_model(_console_packet())
    assert rm["live_ready"] is False
    assert rm["auto_send_ready"] is False
    assert rm["valid_for_live_execution"] is False


# --------------------------------------------------------------------------- #
# Next-send precheck
# --------------------------------------------------------------------------- #
def _examples():
    return _console_packet()["candidate_console_examples"]


def test_missing_candidate_precheck_blocks_missing_candidate():
    pc = cockpit.build_next_send_precheck(_console_packet(), candidate=None)
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_BLOCKED_MISSING_CANDIDATE
    assert cockpit.BLOCKER_MISSING_CANDIDATE in pc["blockers"]


def test_unreconciled_console_blocks_unreconciled_ledger():
    cp = _console_packet()
    cp["reconciliation_outcome_class"] = (
        "ledger_reconciliation_blocked_manifest_not_advanced")
    pc = cockpit.build_next_send_precheck(
        cp, candidate=_examples()["d_new_payload_clear"])
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_BLOCKED_UNRECONCILED
    assert cockpit.BLOCKER_UNRECONCILED_LEDGER in pc["blockers"]


def test_exact_replay_precheck_blocks_exact_replay():
    pc = cockpit.build_next_send_precheck(
        _console_packet(), candidate=_examples()["a_exact_replay_blocked"])
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_BLOCKED_EXACT_REPLAY
    assert pc["next_allowed_action"] == console.ACTION_BLOCKED_EXACT_REPLAY


def test_same_payload_without_gate_requires_fresh_gate():
    pc = cockpit.build_next_send_precheck(
        _console_packet(),
        candidate=_examples()["b_same_payload_without_fresh_gate"])
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_REQUIRES_FRESH_GATE
    assert pc["next_allowed_action"] == console.ACTION_REQUIRES_FRESH_GATE


def test_same_payload_with_fresh_gate_clears_for_manual_gate():
    pc = cockpit.build_next_send_precheck(
        _console_packet(),
        candidate=_examples()["c_same_payload_with_fresh_gate"])
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_CLEAR
    assert pc["next_allowed_action"] == console.ACTION_CLEAR_FOR_MANUAL_SEND


def test_new_payload_with_fresh_gate_clears_for_manual_gate():
    pc = cockpit.build_next_send_precheck(
        _console_packet(), candidate=_examples()["d_new_payload_clear"])
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_CLEAR
    assert pc["next_allowed_action"] == console.ACTION_CLEAR_FOR_MANUAL_SEND


def test_forbidden_value_fail_closes_precheck():
    cp = _console_packet()
    bad_candidate = dict(_examples()["d_new_payload_clear"])
    bad_candidate["leaked_token"] = (
        "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00")
    pc = cockpit.build_next_send_precheck(cp, candidate=bad_candidate)
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_FAIL_CLOSED
    assert pc["forbidden_fields_detected"] is True


def test_forbidden_console_url_fail_closes_precheck():
    cp = _console_packet()
    cp["leaked_url"] = (
        "https://api.telegram.org/bot123456789:AaBbCc/sendMessage")
    pc = cockpit.build_next_send_precheck(
        cp, candidate=_examples()["d_new_payload_clear"])
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_FAIL_CLOSED


def test_precheck_raw_candidate_evidence_path():
    # A raw candidate evidence packet (no replay_guard_outcome_class) should be
    # run through the console against the reconstructed ledger and clear under a
    # fresh gate when it is a genuinely new payload.
    cp = _console_packet()
    new_candidate = console.build_candidate_evidence(
        destination_binding_checksum="9bf41c5012402b2a",
        send_text_checksum=console.compute_checksum({"k": "raw_new_payload"}),
        request_checksum="rawreq", credential_handle_id="8fb71e088c52dd65",
        live_test_sequence=4)
    pc = cockpit.build_next_send_precheck(
        cp, candidate=new_candidate,
        fresh_operator_gate_id="operator_cockpit_fresh_gate")
    assert pc["precheck_outcome_class"] == cockpit.PRECHECK_CLEAR


def test_precheck_never_marks_live_ready():
    pc = cockpit.build_next_send_precheck(
        _console_packet(), candidate=_examples()["d_new_payload_clear"])
    assert pc["classified_live_ready"] is False
    assert pc["classified_auto_send_ready"] is False
    assert pc["valid_for_live_execution"] is False
    assert pc["requires_separate_operator_send_gate"] is True


# --------------------------------------------------------------------------- #
# Packet + doc
# --------------------------------------------------------------------------- #
def _packet():
    return cockpit.build_cockpit_packet(_console_packet())


def test_cockpit_packet_is_deterministic():
    p1 = _packet()
    p2 = _packet()
    assert p1 == p2
    assert p1["cockpit_packet_checksum"]


def test_cockpit_packet_and_doc_scanner_clean():
    p = _packet()
    doc = cockpit.build_cockpit_doc(p)
    assert cockpit.scan_cockpit(p, doc) == []


def test_cockpit_packet_carries_headline_state():
    p = _packet()
    assert p["reconciliation_outcome"] == console.RECON_OK
    assert p["current_ledger_count"] == 2
    assert p["replay_console_checksum"] == _console_packet()[
        "console_packet_checksum"]
    assert p["cockpit_read_model_checksum"]


def test_cockpit_packet_precheck_examples_cover_all_outcomes():
    p = _packet()
    ex = p["precheck_examples"]
    assert (ex["exact_replay"]["precheck_outcome_class"]
            == cockpit.PRECHECK_BLOCKED_EXACT_REPLAY)
    assert (ex["same_payload_without_fresh_gate"]["precheck_outcome_class"]
            == cockpit.PRECHECK_REQUIRES_FRESH_GATE)
    assert (ex["same_payload_with_fresh_gate"]["precheck_outcome_class"]
            == cockpit.PRECHECK_CLEAR)
    assert (ex["new_payload"]["precheck_outcome_class"]
            == cockpit.PRECHECK_CLEAR)


def test_cockpit_packet_default_state_blocks_missing_candidate():
    # The committed packet's default cockpit state has no candidate selected.
    p = _packet()
    assert p["next_allowed_action"] == console.ACTION_BLOCKED_INVALID_CANDIDATE
    assert (p["next_send_precheck_panel"]["precheck_outcome_class"]
            == cockpit.PRECHECK_BLOCKED_MISSING_CANDIDATE)


def test_cockpit_packet_stores_no_secrets_and_not_live():
    p = _packet()
    blob = json.dumps(p)
    assert "api.telegram.org/bot" not in blob
    assert p["live_ready"] is False
    assert p["sendmessage_executed"] is False
    assert p["network_performed"] is False
    assert p["telegram_api_called"] is False
    assert p["credential_read"] is False
    assert p["env_read"] is False
    assert p["valid_for_live_execution"] is False
    assert p["is_read_only_cockpit"] is True


def test_build_from_repo_matches_explicit_packet():
    from_repo = cockpit.build_cockpit_packet_from_repo(ROOT)
    explicit = _packet()
    assert (from_repo["cockpit_packet_checksum"]
            == explicit["cockpit_packet_checksum"])


def test_write_artifacts_refuses_unsafe(tmp_path):
    import pytest
    p = _packet()
    doc = cockpit.build_cockpit_doc(p)
    written = cockpit.write_artifacts(tmp_path, p, doc)
    assert len(written) == 2
    bad = dict(p)
    bad["leaked"] = "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00"
    with pytest.raises(RuntimeError):
        cockpit.write_artifacts(tmp_path, bad, doc)
