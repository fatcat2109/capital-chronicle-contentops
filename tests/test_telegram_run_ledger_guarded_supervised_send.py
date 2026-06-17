"""Tests for the 0174UQ/UR/US ledger-backed replay-guarded supervised send.

Pure, LOCAL, deterministic. Every test that touches the send path injects a
MOCK transport, so NO real network / Telegram / ``.env`` / credential access
ever happens here. The tests assert: the deterministic replay-guard preflight,
fresh-gate enforcement, exactly-one-send execution (with no retry), the
immutable ledger append, and full redaction of token/destination/raw material.
"""

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runner = importlib.import_module(
    "tools.telegram_run_ledger_guarded_supervised_send")
ledger = importlib.import_module(
    "live_contentops.telegram_supervised_send_outcome_ledger")
adapter = importlib.import_module(
    "live_contentops.telegram_local_adapter_contract")

FAKE_TOKEN = "FAKE-OPERATOR-TOKEN-7f3a"
FAKE_DEST = "FAKE-TEST-CHANNEL-9q2b"
GATE_A = "operator_gate_test_alpha"
GATE_B = "operator_gate_test_bravo"


class _TransportSpy:
    """A mock transport recording call count. NEVER touches the network."""

    def __init__(self, result=None, raises=None):
        self.calls = 0
        self._result = result
        self._raises = raises

    def __call__(self):
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        return self._result


def _ok_spy():
    return _TransportSpy(result=(True, 200, {"has_message_id": True}))


def _err_spy():
    return _TransportSpy(result=(False, 400, {"has_message_id": False}))


def _boom_spy():
    return _TransportSpy(raises=RuntimeError("network boom"))


def _run(**kwargs):
    kwargs.setdefault("token", FAKE_TOKEN)
    kwargs.setdefault("destination", FAKE_DEST)
    kwargs.setdefault("existing_ledger_entries", [])
    return runner.run_ledger_guarded_send(**kwargs)


def _entry_from_same_payload(gate):
    """An OK ledger entry built from the SAME third-send payload under ``gate``."""
    res = _run(fresh_operator_gate_id=gate, http_transport=_ok_spy())
    return ledger.build_ledger_entry(res["final_evidence"], operator_gate_id=gate)


def _prior_entry_different_payload(gate="prior_gate"):
    """An OK ledger entry for a DIFFERENT payload (distinct stable key)."""
    text = "Capital Chronicle ContentOps prior placeholder entry. No market advice."
    rendered = adapter.render_telegram_payload(
        approved_text=text, parse_mode=adapter.PARSE_MODE_NONE)
    enforcer = adapter.enforce_capability()
    one_req = adapter.build_one_request_object(
        rendered, enforcer, credential_handle_id="aaaaaaaaaaaaaaaa",
        destination_binding_id="bbbbbbbbbbbbbbbb")
    cand = runner.build_candidate_evidence_packet(
        rendered, one_req, credential_handle_id="aaaaaaaaaaaaaaaa",
        destination_binding_checksum="cccccccccccccccc",
        credential_source_class=runner.CREDENTIAL_SOURCE_DOTENV,
        destination_source_class=runner.DESTINATION_SOURCE_DOTENV_TEST_CHANNEL,
        destination_present_redacted=True)
    return ledger.build_ledger_entry(cand, operator_gate_id=gate)


# --------------------------------------------------------------------------- #
# Import posture
# --------------------------------------------------------------------------- #
def test_import_has_no_side_effects():
    mod = importlib.reload(runner)
    assert mod.TASK_LABEL.startswith("TASK_CONTENTOPS_0174UQ_UR_US")
    assert mod.LIVE_TEST_SEQUENCE == 3
    assert mod.REQUEST_BUDGET == 1


def test_message_is_the_deterministic_third_test_message():
    assert "test 3" in runner.SUPERVISED_TEST_MESSAGE
    assert "No market advice." in runner.SUPERVISED_TEST_MESSAGE


# --------------------------------------------------------------------------- #
# Default no-live mode + preflight blocking (NO network)
# --------------------------------------------------------------------------- #
def test_default_no_live_does_not_network():
    spy = _ok_spy()
    res = runner.run_ledger_guarded_send(
        operator_live_send_enabled=False, fresh_operator_gate_id=None,
        token=None, destination=None, existing_ledger_entries=[],
        http_transport=spy)
    assert spy.calls == 0
    assert res["send_result"]["send_attempted"] is False
    assert runner.BLOCK_LIVE_NOT_ENABLED in res["send_result"]["blocked_reasons"]


def test_missing_fresh_gate_blocks_before_network():
    spy = _ok_spy()
    res = _run(fresh_operator_gate_id=None, http_transport=spy)
    assert spy.calls == 0
    assert runner.BLOCK_FRESH_GATE_MISSING in res["send_result"]["blocked_reasons"]


def test_missing_token_blocks_before_network():
    spy = _ok_spy()
    res = runner.run_ledger_guarded_send(
        fresh_operator_gate_id=GATE_A, token=None, destination=FAKE_DEST,
        existing_ledger_entries=[], http_transport=spy)
    assert spy.calls == 0
    assert runner.BLOCK_CREDENTIAL_MISSING in res["send_result"]["blocked_reasons"]


def test_missing_destination_blocks_before_network():
    spy = _ok_spy()
    res = runner.run_ledger_guarded_send(
        fresh_operator_gate_id=GATE_A, token=FAKE_TOKEN, destination=None,
        existing_ledger_entries=[], http_transport=spy)
    assert spy.calls == 0
    assert runner.BLOCK_DESTINATION_MISSING in res["send_result"]["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Replay-guard preflight states
# --------------------------------------------------------------------------- #
def test_stable_payload_without_fresh_gate_blocks_before_network():
    prior = _entry_from_same_payload(GATE_A)
    spy = _ok_spy()
    res = runner.run_ledger_guarded_send(
        fresh_operator_gate_id=None, token=FAKE_TOKEN, destination=FAKE_DEST,
        existing_ledger_entries=[prior], http_transport=spy)
    assert spy.calls == 0
    assert (res["preflight_guard"]["replay_guard_outcome_class"]
            == ledger.REPLAY_REQUIRES_FRESH_GATE)


def test_stable_payload_with_fresh_gate_clears_and_records_flag():
    prior = _entry_from_same_payload(GATE_A)
    spy = _ok_spy()
    res = _run(fresh_operator_gate_id=GATE_B,
               existing_ledger_entries=[prior], http_transport=spy)
    assert spy.calls == 1
    assert (res["preflight_guard"]["replay_guard_outcome_class"]
            == ledger.REPLAY_CLEAR)
    assert res["post_guard"]["same_payload_under_fresh_gate"] is True


def test_exact_replay_with_same_gate_blocks_before_network():
    prior = _entry_from_same_payload(GATE_A)
    spy = _ok_spy()
    res = _run(fresh_operator_gate_id=GATE_A,
               existing_ledger_entries=[prior], http_transport=spy)
    assert spy.calls == 0
    assert (res["preflight_guard"]["replay_guard_outcome_class"]
            == ledger.REPLAY_BLOCKED_EXACT)


def test_candidate_missing_request_checksum_blocks_guard():
    rendered = adapter.render_telegram_payload(
        approved_text=runner.SUPERVISED_TEST_MESSAGE,
        parse_mode=adapter.PARSE_MODE_NONE)
    one_req = adapter.build_one_request_object(
        rendered, adapter.enforce_capability(),
        credential_handle_id="h", destination_binding_id="d")
    cand = runner.build_candidate_evidence_packet(
        rendered, one_req, credential_handle_id="h",
        destination_binding_checksum="cccccccccccccccc",
        credential_source_class=runner.CREDENTIAL_SOURCE_DOTENV,
        destination_source_class=runner.DESTINATION_SOURCE_DOTENV_TEST_CHANNEL,
        destination_present_redacted=True)
    cand["request_checksum"] = None
    state = ledger.build_replay_guard_state([], cand, operator_gate_id=GATE_A)
    assert (state["replay_guard_outcome_class"]
            == ledger.REPLAY_BLOCKED_MISSING_EVIDENCE)


# --------------------------------------------------------------------------- #
# Exactly-one-send execution (no retry)
# --------------------------------------------------------------------------- #
def test_success_path_executes_exactly_one_call():
    spy = _ok_spy()
    res = _run(fresh_operator_gate_id=GATE_A, http_transport=spy)
    assert spy.calls == 1
    assert res["send_result"]["send_succeeded"] is True
    assert res["send_result"]["budget_used"] == 1


def test_provider_error_path_one_call_no_retry():
    spy = _err_spy()
    res = _run(fresh_operator_gate_id=GATE_A, http_transport=spy)
    assert spy.calls == 1
    assert res["send_result"]["send_succeeded"] is False
    assert res["send_result"]["outcome_class"] == runner.SEND_PROVIDER_ERROR


def test_network_exception_path_one_call_no_retry():
    spy = _boom_spy()
    res = _run(fresh_operator_gate_id=GATE_A, http_transport=spy)
    assert spy.calls == 1
    assert res["send_result"]["send_succeeded"] is False
    assert res["send_result"]["outcome_class"] == runner.SEND_NETWORK_BLOCKED


def test_response_checksum_non_null_for_attempted_send():
    for spy in (_ok_spy(), _err_spy(), _boom_spy()):
        res = _run(fresh_operator_gate_id=GATE_A, http_transport=spy)
        assert res["final_evidence"]["response_checksum"] is not None


def test_blocked_before_network_response_checksum_may_be_null():
    res = _run(fresh_operator_gate_id=None, http_transport=_ok_spy())
    assert res["final_evidence"]["response_checksum"] is None


# --------------------------------------------------------------------------- #
# Immutable ledger append
# --------------------------------------------------------------------------- #
def test_ledger_append_creates_new_manifest_count_two():
    prior = _prior_entry_different_payload()
    res = _run(fresh_operator_gate_id=GATE_A,
               existing_ledger_entries=[prior], http_transport=_ok_spy())
    assert res["append"]["appended"] is True
    assert res["append"]["ledger_entry_count"] == 2
    assert res["append"]["ledger_manifest_checksum"]
    # The input list of prior entries is never mutated.
    assert res["existing_ledger_entries"] == [prior]


def test_duplicate_ledger_entry_checksum_does_not_append_twice():
    res = _run(fresh_operator_gate_id=GATE_A, http_transport=_ok_spy())
    entry = res["ledger_entry"]
    populated = res["append"]["ledger"]
    second = ledger.append_ledger_entry(populated, entry, res["post_guard"])
    assert second["appended"] is False
    assert ledger.APPEND_BLOCKED_DUPLICATE_ENTRY in second["blocked_reasons"]
    assert second["ledger_entry_count"] == len(populated)


def test_blocked_send_does_not_append():
    res = _run(fresh_operator_gate_id=None, http_transport=_ok_spy())
    assert res["append"]["appended"] is False


# --------------------------------------------------------------------------- #
# Redaction + scanner-clean evidence
# --------------------------------------------------------------------------- #
def test_token_and_destination_never_serialized():
    token = "SENTINEL-TOKEN-abc123"
    dest = "SENTINEL-DEST-xyz789"
    res = runner.run_ledger_guarded_send(
        fresh_operator_gate_id=GATE_A, token=token, destination=dest,
        existing_ledger_entries=[], http_transport=_ok_spy())
    packet = runner.build_proof_packet(
        res, accepted_ledger_packet={}, start_head="x", final_head="x",
        origin_head="x", git_status_summary="changed_entries=0")
    blob = json.dumps([res["candidate_evidence"], res["final_evidence"],
                       res["ledger_entry"], packet])
    assert token not in blob
    assert dest not in blob


def test_emitted_packet_and_doc_scanner_clean():
    res = _run(fresh_operator_gate_id=GATE_A, http_transport=_ok_spy())
    packet = runner.build_proof_packet(
        res, accepted_ledger_packet={}, start_head="x", final_head="x",
        origin_head="x", git_status_summary="changed_entries=0")
    doc = runner.build_proof_doc(packet)
    assert runner.scan_evidence(packet, doc) == []
    assert runner.scan_for_financial_advice_safe(packet, doc) == []


def test_proof_packet_has_no_raw_material_and_safety_proofs():
    res = _run(fresh_operator_gate_id=GATE_A, http_transport=_ok_spy())
    packet = runner.build_proof_packet(
        res, accepted_ledger_packet={}, start_head="x", final_head="x",
        origin_head="x", git_status_summary="changed_entries=0")
    blob = json.dumps(packet)
    assert "api.telegram.org/bot" not in blob
    assert packet["stores_no_token"] is True
    assert packet["stores_no_raw_destination"] is True
    assert packet["stores_no_raw_response"] is True
    assert packet["stores_no_raw_url"] is True
    assert packet["stores_no_headers"] is True
    assert packet["stores_no_cookies"] is True
    assert packet["stores_no_raw_chat_id"] is True


def test_proof_packet_no_extra_behavior_proofs():
    res = _run(fresh_operator_gate_id=GATE_A, http_transport=_ok_spy())
    packet = runner.build_proof_packet(
        res, accepted_ledger_packet={}, start_head="x", final_head="x",
        origin_head="x", git_status_summary="changed_entries=0")
    assert packet["no_retry"] is True
    assert packet["no_scheduler"] is True
    assert packet["no_webhook"] is True
    assert packet["no_polling"] is True
    assert packet["no_get_updates"] is True
    assert packet["no_media_edit_delete"] is True
    assert packet["no_second_send_path"] is True


def test_proof_packet_records_replay_and_ledger_fields():
    prior = _prior_entry_different_payload()
    accepted = {"current_ledger_entry_checksum": prior["ledger_entry_checksum"],
                "ledger_manifest_checksum": "old_manifest_checksum_placeholder"}
    res = _run(fresh_operator_gate_id=GATE_A,
               existing_ledger_entries=[prior], http_transport=_ok_spy())
    packet = runner.build_proof_packet(
        res, accepted_ledger_packet=accepted, start_head="x", final_head="x",
        origin_head="x", git_status_summary="changed_entries=0")
    assert packet["replay_guard_outcome_class"] == ledger.REPLAY_CLEAR
    assert packet["exact_run_replay_key"]
    assert packet["stable_payload_replay_key"]
    assert packet["previous_ledger_entry_checksum"] == prior["ledger_entry_checksum"]
    assert packet["new_ledger_entry_checksum"]
    assert packet["new_ledger_manifest_checksum"]
    assert packet["appended"] is True
    assert packet["ledger_entry_count"] == 2


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_runs_are_deterministic():
    r1 = _run(fresh_operator_gate_id=GATE_A, http_transport=_ok_spy())
    r2 = _run(fresh_operator_gate_id=GATE_A, http_transport=_ok_spy())
    assert r1["final_evidence"] == r2["final_evidence"]
    assert (r1["ledger_entry"]["ledger_entry_checksum"]
            == r2["ledger_entry"]["ledger_entry_checksum"])


def test_fresh_gate_id_is_part_of_exact_run_replay_key():
    a = _run(fresh_operator_gate_id=GATE_A, http_transport=_ok_spy())
    b = _run(fresh_operator_gate_id=GATE_B, http_transport=_ok_spy())
    assert (a["post_guard"]["exact_run_replay_key"]
            != b["post_guard"]["exact_run_replay_key"])
    assert (a["post_guard"]["stable_payload_replay_key"]
            == b["post_guard"]["stable_payload_replay_key"])
