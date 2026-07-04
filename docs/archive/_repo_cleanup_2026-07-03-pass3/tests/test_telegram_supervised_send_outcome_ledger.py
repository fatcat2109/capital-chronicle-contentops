"""Tests for the 0174UN/UO/UP Telegram supervised-send outcome ledger + guard.

Pure, LOCAL, deterministic. NO network / API / Telegram / env / credential read
and NO ``sendMessage`` -- the module under test contains none of those, and
these tests assert the redaction + replay-guard + immutable-append behavior
using the COMMITTED 0174UK_UL_UM evidence packet as the fixture.
"""

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ledger = importlib.import_module(
    "live_contentops.telegram_supervised_send_outcome_ledger")
adapter = importlib.import_module(
    "live_contentops.telegram_local_adapter_contract")

ACCEPTED_PACKET_PATH = (
    ROOT / "docs" / "automation" / "0174UK_UL_UM"
    / "telegram_single_supervised_sendmessage_proof_packet.json")

GATE_A = "operator_run_0174un_uo_up_gate_alpha"
GATE_B = "operator_run_0174un_uo_up_gate_bravo"


def _accepted_packet():
    """Load the committed accepted supervised-send evidence packet."""
    return json.loads(ACCEPTED_PACKET_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Import posture
# --------------------------------------------------------------------------- #
def test_import_has_no_side_effects():
    mod = importlib.reload(ledger)
    assert mod.TASK_LABEL.startswith("TASK_CONTENTOPS_0174UN_UO_UP")
    assert mod.METHOD_SUPERVISED_SEND == "sendMessage"


def test_accepted_fixture_packet_exists_and_has_required_fields():
    p = _accepted_packet()
    for field, _reason in ledger.REQUIRED_EVIDENCE_FIELDS:
        assert p.get(field), field


# --------------------------------------------------------------------------- #
# Ledger entry model
# --------------------------------------------------------------------------- #
def test_valid_evidence_builds_scanner_clean_ok_entry():
    entry = ledger.build_ledger_entry(_accepted_packet(), operator_gate_id=GATE_A)
    assert entry["ledger_entry_outcome_class"] == ledger.LEDGER_ENTRY_OK
    assert entry["ledger_entry_ok"] is True
    assert entry["status"] == adapter.Status.PASS
    assert ledger.scan_for_leaks(entry) == []
    assert ledger.scan_for_financial_advice(entry) == []
    assert entry["ledger_entry_checksum"]


def test_ledger_entry_has_non_null_response_checksum():
    entry = ledger.build_ledger_entry(_accepted_packet())
    assert entry["response_checksum"] is not None
    assert entry["response_shape_checksum"] is not None


def test_ledger_entry_carries_required_redacted_fields():
    entry = ledger.build_ledger_entry(_accepted_packet(), operator_gate_id=GATE_A)
    for field in (
        "source_task_label", "source_evidence_checksum", "send_outcome_class",
        "send_succeeded", "live_test_sequence", "credential_source_class",
        "destination_source_class", "destination_binding_checksum",
        "request_checksum", "response_checksum", "response_shape_checksum",
        "redacted_message_id_class", "provider_status_code_class",
        "response_status_class", "request_budget_used",
        "timestamp_placeholder_class", "operator_gate_id", "operator_gate_class",
        "ledger_entry_checksum",
    ):
        assert field in entry, field
    assert entry["operator_gate_id"] == GATE_A
    assert entry["operator_gate_class"] == ledger.OPERATOR_GATE_PRESENT_CLASS


def test_ledger_entry_stores_no_secrets():
    entry = ledger.build_ledger_entry(_accepted_packet(), operator_gate_id=GATE_A)
    blob = json.dumps(entry)
    assert "api.telegram.org/bot" not in blob
    assert entry["stores_no_token"] is True
    assert entry["stores_no_raw_destination"] is True
    assert entry["stores_no_raw_chat_id"] is True
    assert entry["stores_no_raw_response"] is True
    assert entry["stores_no_raw_url"] is True
    assert entry["stores_no_headers"] is True
    assert entry["stores_no_cookies"] is True
    assert entry["stores_no_username"] is True
    assert entry["stores_no_raw_provider_body"] is True


def test_ledger_entry_is_never_live_ready():
    entry = ledger.build_ledger_entry(_accepted_packet())
    assert entry["live_ready"] is False
    assert entry["auto_send_ready"] is False
    assert entry["valid_for_live_execution"] is False
    assert entry["sendmessage_executed"] is False
    assert entry["network_performed"] is False


# --------------------------------------------------------------------------- #
# Missing-checksum blocking
# --------------------------------------------------------------------------- #
def _packet_without(field):
    p = _accepted_packet()
    p[field] = None
    return p


def test_missing_response_checksum_blocks_entry():
    entry = ledger.build_ledger_entry(_packet_without("response_checksum"))
    assert entry["ledger_entry_outcome_class"] == ledger.LEDGER_ENTRY_BLOCKED
    assert ledger.BLOCK_MISSING_RESPONSE_CHECKSUM in entry["blocked_reasons"]


def test_missing_request_checksum_blocks_entry():
    entry = ledger.build_ledger_entry(_packet_without("request_checksum"))
    assert entry["ledger_entry_outcome_class"] == ledger.LEDGER_ENTRY_BLOCKED
    assert ledger.BLOCK_MISSING_REQUEST_CHECKSUM in entry["blocked_reasons"]


def test_missing_destination_binding_checksum_blocks_entry():
    entry = ledger.build_ledger_entry(
        _packet_without("destination_binding_checksum"))
    assert entry["ledger_entry_outcome_class"] == ledger.LEDGER_ENTRY_BLOCKED
    assert (ledger.BLOCK_MISSING_DESTINATION_BINDING_CHECKSUM
            in entry["blocked_reasons"])


def test_missing_evidence_checksum_blocks_entry():
    entry = ledger.build_ledger_entry(_packet_without("evidence_checksum"))
    assert entry["ledger_entry_outcome_class"] == ledger.LEDGER_ENTRY_BLOCKED
    assert ledger.BLOCK_MISSING_EVIDENCE_CHECKSUM in entry["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Fail-closed on forbidden values
# --------------------------------------------------------------------------- #
def test_forbidden_raw_token_fail_closes():
    p = _accepted_packet()
    p["leaked_token"] = "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00"
    entry = ledger.build_ledger_entry(p)
    assert entry["ledger_entry_outcome_class"] == ledger.LEDGER_ENTRY_FAIL_CLOSED
    assert entry["forbidden_fields_detected"] is True


def test_forbidden_raw_url_fail_closes_guard():
    p = _accepted_packet()
    p["leaked_url"] = "https://api.telegram.org/bot123456789:AaBbCc/sendMessage"
    state = ledger.build_replay_guard_state([], p)
    assert state["replay_guard_outcome_class"] == ledger.REPLAY_FAIL_CLOSED
    assert state["forbidden_fields_detected"] is True


def test_forbidden_raw_destination_fail_closes_guard():
    p = _accepted_packet()
    # A raw chat-id-looking secret field injected into the candidate packet.
    p["raw_chat_id"] = "-1001234567890"
    state = ledger.build_replay_guard_state([], p)
    assert state["replay_guard_outcome_class"] in (
        ledger.REPLAY_FAIL_CLOSED, ledger.REPLAY_BLOCKED_MISSING_EVIDENCE)


# --------------------------------------------------------------------------- #
# Replay keys
# --------------------------------------------------------------------------- #
def test_replay_keys_are_deterministic():
    p = _accepted_packet()
    k1 = ledger.build_replay_keys(p, operator_gate_id=GATE_A)
    k2 = ledger.build_replay_keys(p, operator_gate_id=GATE_A)
    assert k1 == k2
    assert k1["exact_run_replay_key"] != k1["stable_payload_replay_key"]


def test_exact_key_changes_with_gate_but_stable_key_does_not():
    p = _accepted_packet()
    a = ledger.build_replay_keys(p, operator_gate_id=GATE_A)
    b = ledger.build_replay_keys(p, operator_gate_id=GATE_B)
    assert a["exact_run_replay_key"] != b["exact_run_replay_key"]
    assert a["stable_payload_replay_key"] == b["stable_payload_replay_key"]


def test_replay_keys_contain_no_secrets():
    p = _accepted_packet()
    keys = ledger.build_replay_keys(p, operator_gate_id=GATE_A)
    blob = json.dumps(keys)
    # Keys are bare 16/64-hex checksums; assert they're not raw material.
    assert "api.telegram.org" not in blob
    assert ledger.scan_for_leaks(keys) == []


# --------------------------------------------------------------------------- #
# Replay decision
# --------------------------------------------------------------------------- #
def test_new_payload_is_clear_for_new_operator_gate():
    state = ledger.build_replay_guard_state(
        [], _accepted_packet(), operator_gate_id=GATE_A)
    assert state["replay_guard_outcome_class"] == ledger.REPLAY_CLEAR
    assert state["replay_guard_clear"] is True
    assert state["same_payload_under_fresh_gate"] is False
    # Even a clear guard never asserts live readiness.
    assert state["classified_live_ready"] is False
    assert state["classified_auto_send_ready"] is False
    assert state["requires_separate_operator_send_gate"] is True


def test_exact_replay_key_duplicate_blocks():
    p = _accepted_packet()
    entry = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    state = ledger.build_replay_guard_state(
        [entry], p, operator_gate_id=GATE_A)
    assert state["replay_guard_outcome_class"] == ledger.REPLAY_BLOCKED_EXACT
    assert state["exact_replay_key_matched"] is True


def test_stable_payload_duplicate_without_fresh_gate_requires_fresh_gate():
    p = _accepted_packet()
    # Existing entry recorded under gate A. Candidate has no gate => only the
    # stable payload key matches.
    entry = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    state = ledger.build_replay_guard_state([entry], p, operator_gate_id=None)
    assert (state["replay_guard_outcome_class"]
            == ledger.REPLAY_REQUIRES_FRESH_GATE)
    assert state["stable_payload_key_matched"] is True
    assert state["exact_replay_key_matched"] is False


def test_stable_payload_duplicate_with_fresh_gate_clears_with_flag():
    p = _accepted_packet()
    entry = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    # A genuinely different operator gate => exact key differs, stable matches.
    state = ledger.build_replay_guard_state([entry], p, operator_gate_id=GATE_B)
    assert state["replay_guard_outcome_class"] == ledger.REPLAY_CLEAR
    assert state["same_payload_under_fresh_gate"] is True
    assert state["stable_payload_key_matched"] is True
    assert state["exact_replay_key_matched"] is False


def test_missing_response_checksum_blocks_guard():
    state = ledger.build_replay_guard_state(
        [], _packet_without("response_checksum"))
    assert (state["replay_guard_outcome_class"]
            == ledger.REPLAY_BLOCKED_MISSING_EVIDENCE)


def test_missing_request_checksum_blocks_guard():
    state = ledger.build_replay_guard_state(
        [], _packet_without("request_checksum"))
    assert (state["replay_guard_outcome_class"]
            == ledger.REPLAY_BLOCKED_MISSING_EVIDENCE)


# --------------------------------------------------------------------------- #
# Immutable append helper
# --------------------------------------------------------------------------- #
def test_append_appends_when_guard_clear():
    p = _accepted_packet()
    entry = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    guard = ledger.build_replay_guard_state([], p, operator_gate_id=GATE_A)
    result = ledger.append_ledger_entry([], entry, guard)
    assert result["append_status_class"] == ledger.APPEND_OK
    assert result["appended"] is True
    assert result["ledger_entry_count"] == 1
    assert result["ledger_manifest_checksum"]


def test_append_does_not_mutate_input_list():
    p = _accepted_packet()
    entry = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    guard = ledger.build_replay_guard_state([], p, operator_gate_id=GATE_A)
    original = []
    result = ledger.append_ledger_entry(original, entry, guard)
    assert original == []  # untouched
    assert result["ledger"] is not original
    assert result["input_ledger_unchanged"] is True


def test_append_blocks_when_guard_blocked():
    p = _accepted_packet()
    entry = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    # A blocked guard (exact replay against a ledger already containing entry).
    blocked_guard = ledger.build_replay_guard_state(
        [entry], p, operator_gate_id=GATE_A)
    assert blocked_guard["replay_guard_clear"] is False
    result = ledger.append_ledger_entry([entry], entry, blocked_guard)
    assert result["appended"] is False
    assert (ledger.APPEND_BLOCKED_GUARD_NOT_CLEAR in result["blocked_reasons"]
            or ledger.APPEND_BLOCKED_DUPLICATE_ENTRY in result["blocked_reasons"])
    assert result["ledger_entry_count"] == 1


def test_duplicate_ledger_entry_checksum_does_not_append_twice():
    p = _accepted_packet()
    entry = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    clear_guard = ledger.build_replay_guard_state([], p, operator_gate_id=GATE_A)
    first = ledger.append_ledger_entry([], entry, clear_guard)
    # Attempt to append the SAME entry again into the now-populated ledger.
    second = ledger.append_ledger_entry(first["ledger"], entry, clear_guard)
    assert second["appended"] is False
    assert ledger.APPEND_BLOCKED_DUPLICATE_ENTRY in second["blocked_reasons"]
    assert second["ledger_entry_count"] == 1


def test_append_blocks_invalid_entry():
    p = _accepted_packet()
    bad_entry = ledger.build_ledger_entry(_packet_without("response_checksum"))
    guard = ledger.build_replay_guard_state([], p, operator_gate_id=GATE_A)
    result = ledger.append_ledger_entry([], bad_entry, guard)
    assert result["appended"] is False
    assert ledger.APPEND_BLOCKED_INVALID_ENTRY in result["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Determinism of build + append
# --------------------------------------------------------------------------- #
def test_build_and_append_are_deterministic():
    p = _accepted_packet()
    e1 = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    e2 = ledger.build_ledger_entry(p, operator_gate_id=GATE_A)
    assert e1 == e2
    g1 = ledger.build_replay_guard_state([], p, operator_gate_id=GATE_A)
    g2 = ledger.build_replay_guard_state([], p, operator_gate_id=GATE_A)
    assert g1 == g2
    a1 = ledger.append_ledger_entry([], e1, g1)["ledger_manifest_checksum"]
    a2 = ledger.append_ledger_entry([], e2, g2)["ledger_manifest_checksum"]
    assert a1 == a2


# --------------------------------------------------------------------------- #
# Packet + doc
# --------------------------------------------------------------------------- #
def test_ledger_packet_is_deterministic_and_scanner_clean():
    p = _accepted_packet()
    pkt1 = ledger.build_ledger_packet(p, operator_gate_id=GATE_A)
    pkt2 = ledger.build_ledger_packet(p, operator_gate_id=GATE_A)
    assert pkt1 == pkt2
    doc = ledger.build_ledger_doc(pkt1)
    assert ledger.scan_packet_and_doc(pkt1, doc) == []


def test_ledger_packet_records_replay_policy_decisions():
    pkt = ledger.build_ledger_packet(_accepted_packet(), operator_gate_id=GATE_A)
    policy = pkt["replay_policy"]
    assert policy["exact_resubmit_outcome_class"] == ledger.REPLAY_BLOCKED_EXACT
    assert (policy["same_payload_without_fresh_gate_outcome_class"]
            == ledger.REPLAY_REQUIRES_FRESH_GATE)
    assert pkt["seed_append_status_class"] == ledger.APPEND_OK
    assert pkt["ledger_entry_count"] == 1


def test_ledger_packet_has_non_null_checksums_and_keys():
    pkt = ledger.build_ledger_packet(_accepted_packet(), operator_gate_id=GATE_A)
    assert pkt["current_ledger_entry_checksum"]
    assert pkt["exact_run_replay_key"]
    assert pkt["stable_payload_replay_key"]
    assert pkt["ledger_manifest_checksum"]
    assert pkt["ledger_packet_checksum"]


def test_ledger_packet_stores_no_secrets_and_not_live():
    pkt = ledger.build_ledger_packet(_accepted_packet(), operator_gate_id=GATE_A)
    blob = json.dumps(pkt)
    assert "api.telegram.org/bot" not in blob
    assert pkt["live_ready"] is False
    assert pkt["sendmessage_executed"] is False
    assert pkt["network_performed"] is False
    assert pkt["telegram_api_called"] is False
    assert pkt["credential_read"] is False


def test_write_artifacts_refuses_unsafe(tmp_path):
    import pytest
    pkt = ledger.build_ledger_packet(_accepted_packet(), operator_gate_id=GATE_A)
    doc = ledger.build_ledger_doc(pkt)
    # Clean artifacts write fine.
    written = ledger.write_artifacts(tmp_path, pkt, doc)
    assert len(written) == 2
    # An injected raw token makes the writer refuse.
    bad = dict(pkt)
    bad["leaked"] = "123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00"
    with pytest.raises(RuntimeError):
        ledger.write_artifacts(tmp_path, bad, doc)
