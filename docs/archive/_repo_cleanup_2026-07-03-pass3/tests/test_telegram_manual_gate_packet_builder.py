"""Tests for 0174VC/VD/VE Telegram manual gate packet builder + approval capture.

Pure, LOCAL, deterministic. NO network / API / Telegram / env / credential read
and NO ``sendMessage``. Asserts: candidate packet build + determinism, the
default no-candidate waiting state, fail-closed on forbidden values, the worked
clear candidate, the full approval-capture fail-closed precedence, manual-gate
next-step derivation, redaction (no raw gate id / note / secrets), and that
nothing is ever classified live-ready / auto-send-ready / dispatch.
"""

import json
import pathlib

import pytest

from live_contentops import telegram_manual_gate_packet_builder as builder
from live_contentops import telegram_operator_cockpit_html_render as render
from live_contentops import telegram_operator_replay_console as console

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RENDER_PACKET_PATH = REPO_ROOT / builder.RENDER_PACKET_REL
CONSOLE_PACKET_PATH = REPO_ROOT / builder.CONSOLE_PACKET_REL


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def render_packet():
    return json.loads(RENDER_PACKET_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def console_packet():
    return json.loads(CONSOLE_PACKET_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def clear_candidate(render_packet, console_packet):
    evidence = builder.build_demo_clear_candidate_evidence()
    return builder.build_manual_gate_candidate_packet(
        render_packet, candidate_evidence_packet=evidence,
        fresh_operator_gate_id=builder.DEMO_FRESH_GATE_ID,
        console_packet=console_packet)


# --------------------------------------------------------------------------- #
# Candidate packet: default no-candidate state
# --------------------------------------------------------------------------- #
def test_default_candidate_is_waiting(render_packet, console_packet):
    pkt = builder.build_manual_gate_candidate_packet(
        render_packet, console_packet=console_packet)
    assert pkt["manual_gate_candidate_outcome_class"] == builder.CANDIDATE_WAITING
    assert pkt["candidate_present"] is False
    assert builder.BLOCKER_MISSING_CANDIDATE in pkt["blockers"]
    assert pkt["precheck_clear_for_manual_gate"] is False
    assert pkt["status"] == render.readmodel.console.adapter.Status.BLOCKED


def test_candidate_packet_is_deterministic(render_packet, console_packet):
    a = builder.build_manual_gate_candidate_packet(
        render_packet, console_packet=console_packet)
    b = builder.build_manual_gate_candidate_packet(
        render_packet, console_packet=console_packet)
    assert a == b
    assert a["manual_gate_candidate_checksum"] == b[
        "manual_gate_candidate_checksum"]


def test_candidate_binds_source_render_checksum(render_packet, console_packet):
    pkt = builder.build_manual_gate_candidate_packet(
        render_packet, console_packet=console_packet)
    assert pkt["source_cockpit_render_checksum"] == render_packet[
        "render_packet_checksum"]
    assert pkt["source_replay_console_checksum"] == console_packet[
        "console_packet_checksum"]


# --------------------------------------------------------------------------- #
# Candidate packet: worked clear candidate
# --------------------------------------------------------------------------- #
def test_clear_candidate_precheck_clear(clear_candidate):
    assert clear_candidate["manual_gate_candidate_outcome_class"] == (
        builder.CANDIDATE_PRECHECK_CLEAR)
    assert clear_candidate["precheck_clear_for_manual_gate"] is True
    assert clear_candidate["candidate_present"] is True
    assert clear_candidate["blockers"] == []
    assert clear_candidate["status"] == render.readmodel.console.adapter.Status.PASS


def test_clear_candidate_carries_replay_keys(clear_candidate):
    assert clear_candidate["stable_payload_replay_key"]
    assert clear_candidate["exact_run_replay_key"]
    # Brand-new payload => stable key must NOT match the recorded send.
    assert clear_candidate["replay_guard_outcome_class"] == (
        console.ledger.REPLAY_CLEAR)


def test_clear_candidate_stores_gate_hash_not_raw(clear_candidate):
    # The raw demo gate id must never appear; only a hash + class.
    assert clear_candidate["fresh_operator_gate_id_hash"]
    assert clear_candidate["fresh_operator_gate_id_hash"] != (
        builder.DEMO_FRESH_GATE_ID)
    assert clear_candidate["fresh_operator_gate_class"] == (
        builder.OPERATOR_GATE_PRESENT_CLASS)
    assert builder.DEMO_FRESH_GATE_ID not in builder.serialize(clear_candidate)


# --------------------------------------------------------------------------- #
# Candidate packet: fail-closed on forbidden value
# --------------------------------------------------------------------------- #
def test_candidate_fail_closed_on_forbidden(render_packet, console_packet):
    bad = {"bot_token": "123456:AAH-REAL-LOOKING-TOKEN-VALUE-xyz"}
    pkt = builder.build_manual_gate_candidate_packet(
        render_packet, candidate_evidence_packet=bad,
        console_packet=console_packet)
    assert pkt["manual_gate_candidate_outcome_class"] == (
        builder.CANDIDATE_FAIL_CLOSED)
    assert pkt["forbidden_fields_detected"] is True
    assert builder.BLOCKER_FORBIDDEN_VALUE in pkt["blockers"]


# --------------------------------------------------------------------------- #
# Approval capture: precedence
# --------------------------------------------------------------------------- #
def test_approval_waiting_when_none(clear_candidate):
    cap = builder.capture_operator_approval(clear_candidate, None)
    assert cap["operator_approval_outcome_class"] == builder.APPROVAL_WAITING
    assert cap["approval_captured"] is False


def test_approval_waiting_when_not_approved(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    approval["approved"] = False
    cap = builder.capture_operator_approval(clear_candidate, approval)
    assert cap["operator_approval_outcome_class"] == builder.APPROVAL_WAITING


def test_approval_blocked_when_precheck_not_clear(render_packet, console_packet):
    waiting = builder.build_manual_gate_candidate_packet(
        render_packet, console_packet=console_packet)
    approval = builder.build_demo_operator_approval(waiting)
    approval["operator_gate_id"] = builder.DEMO_FRESH_GATE_ID
    cap = builder.capture_operator_approval(waiting, approval)
    assert cap["operator_approval_outcome_class"] == (
        builder.APPROVAL_BLOCKED_PRECHECK_NOT_CLEAR)


def test_approval_blocked_missing_gate(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    approval["operator_gate_id"] = None
    cap = builder.capture_operator_approval(clear_candidate, approval)
    assert cap["operator_approval_outcome_class"] == (
        builder.APPROVAL_BLOCKED_MISSING_GATE)


def test_approval_blocked_payload_mismatch(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    approval["approved_payload_checksum"] = "deadbeef"
    cap = builder.capture_operator_approval(clear_candidate, approval)
    assert cap["operator_approval_outcome_class"] == (
        builder.APPROVAL_BLOCKED_PAYLOAD_MISMATCH)


def test_approval_blocked_destination_mismatch(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    approval["destination_binding_checksum"] = "deadbeef"
    cap = builder.capture_operator_approval(clear_candidate, approval)
    assert cap["operator_approval_outcome_class"] == (
        builder.APPROVAL_BLOCKED_DESTINATION_MISMATCH)


def test_approval_captured_happy_path(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    cap = builder.capture_operator_approval(clear_candidate, approval)
    assert cap["operator_approval_outcome_class"] == builder.APPROVAL_CAPTURED
    assert cap["approval_captured"] is True
    assert cap["is_dispatch"] is False
    assert cap["classified_live_ready"] is False
    assert cap["approved_payload_checksum_matches"] is True
    assert cap["destination_binding_checksum_matches"] is True


def test_approval_fail_closed_on_forbidden(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    approval["leaked"] = "https://api.telegram.org/bot123:secret/sendMessage"
    cap = builder.capture_operator_approval(clear_candidate, approval)
    assert cap["operator_approval_outcome_class"] == builder.APPROVAL_FAIL_CLOSED


# --------------------------------------------------------------------------- #
# Approval capture: redaction of note + gate id
# --------------------------------------------------------------------------- #
def test_approval_stores_gate_hash_not_raw(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    cap = builder.capture_operator_approval(clear_candidate, approval)
    assert cap["operator_gate_id_hash"] != builder.DEMO_FRESH_GATE_ID
    assert builder.DEMO_FRESH_GATE_ID not in builder.serialize(cap)


def test_approval_note_class_is_symbolic_only(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    approval["approval_note_class"] = "send the money now to my account please"
    cap = builder.capture_operator_approval(clear_candidate, approval)
    # Non-symbolic prose must be replaced by the safe default class.
    assert cap["approval_note_class"] == builder.DEFAULT_NOTE_CLASS
    assert "send the money now" not in builder.serialize(cap)


# --------------------------------------------------------------------------- #
# Manual gate packet: next-step derivation
# --------------------------------------------------------------------------- #
def test_manual_gate_waiting_for_candidate(render_packet, console_packet):
    cand = builder.build_manual_gate_candidate_packet(
        render_packet, console_packet=console_packet)
    cap = builder.capture_operator_approval(cand, None)
    gate = builder.build_manual_gate_packet(cand, cap)
    assert gate["allowed_next_step"] == builder.NEXT_STEP_WAITING_FOR_CANDIDATE


def test_manual_gate_waiting_for_approval(clear_candidate):
    cap = builder.capture_operator_approval(clear_candidate, None)
    gate = builder.build_manual_gate_packet(clear_candidate, cap)
    assert gate["allowed_next_step"] == builder.NEXT_STEP_WAITING_FOR_APPROVAL


def test_manual_gate_approved_for_runner(clear_candidate):
    approval = builder.build_demo_operator_approval(clear_candidate)
    cap = builder.capture_operator_approval(clear_candidate, approval)
    gate = builder.build_manual_gate_packet(clear_candidate, cap)
    assert gate["allowed_next_step"] == builder.NEXT_STEP_APPROVED_FOR_RUNNER
    assert gate["requires_separate_send_runner"] is True
    assert gate["is_dispatch"] is False
    assert gate["classified_live_ready"] is False
    assert gate["valid_for_live_execution"] is False


def test_manual_gate_blocked_on_failed_candidate(render_packet, console_packet):
    bad = {"bot_token": "123456:AAH-REAL-LOOKING-TOKEN-VALUE-xyz"}
    cand = builder.build_manual_gate_candidate_packet(
        render_packet, candidate_evidence_packet=bad,
        console_packet=console_packet)
    cap = builder.capture_operator_approval(cand, None)
    gate = builder.build_manual_gate_packet(cand, cap)
    assert gate["allowed_next_step"] == builder.NEXT_STEP_BLOCKED


# --------------------------------------------------------------------------- #
# Artifact packet + doc
# --------------------------------------------------------------------------- #
def test_artifact_packet_scenarios(render_packet, console_packet):
    pkt = builder.build_artifact_packet(render_packet, console_packet)
    assert pkt["default_state"]["allowed_next_step"] == (
        builder.NEXT_STEP_WAITING_FOR_CANDIDATE)
    assert pkt["worked_candidate_state"]["allowed_next_step"] == (
        builder.NEXT_STEP_WAITING_FOR_APPROVAL)
    assert pkt["captured_approval_state"]["allowed_next_step"] == (
        builder.NEXT_STEP_APPROVED_FOR_RUNNER)
    assert pkt["captured_approval_state"]["approval_captured"] is True


def test_artifact_packet_deterministic(render_packet, console_packet):
    a = builder.build_artifact_packet(render_packet, console_packet)
    b = builder.build_artifact_packet(render_packet, console_packet)
    assert a == b
    assert a["artifact_packet_checksum"] == b["artifact_packet_checksum"]


def test_artifact_doc_is_scanner_clean(render_packet, console_packet):
    pkt = builder.build_artifact_packet(render_packet, console_packet)
    doc = builder.build_artifact_doc(pkt)
    assert builder.scan_manual_gate(pkt, doc) == []


def test_artifact_packet_safety_flags(render_packet, console_packet):
    pkt = builder.build_artifact_packet(render_packet, console_packet)
    for flag in ("network_performed", "telegram_api_called", "credential_read",
                 "env_read", "dotenv_read", "sendmessage_executed",
                 "dispatch_performed", "live_ready", "auto_send_ready",
                 "valid_for_live_execution"):
        assert pkt[flag] is False, flag
    assert pkt["is_local_only"] is True
    assert pkt["requires_separate_operator_send_gate"] is True


def test_build_from_repo_matches_direct(render_packet, console_packet):
    direct = builder.build_artifact_packet(render_packet, console_packet)
    from_repo = builder.build_artifact_from_repo(REPO_ROOT)
    assert from_repo["artifact_packet_checksum"] == direct[
        "artifact_packet_checksum"]


# --------------------------------------------------------------------------- #
# Write artifacts (into a tmp dir; never the repo) + refusal on leak
# --------------------------------------------------------------------------- #
def test_write_artifacts_round_trip(tmp_path, render_packet, console_packet):
    pkt = builder.build_artifact_packet(render_packet, console_packet)
    doc = builder.build_artifact_doc(pkt)
    written = builder.write_artifacts(tmp_path, pkt, doc)
    assert len(written) == 2
    for path in written:
        assert pathlib.Path(path).is_file()


def test_write_artifacts_refuses_on_leak(tmp_path):
    leaky = {"bot_token": "123456:AAH-REAL-LOOKING-TOKEN-VALUE-xyz"}
    with pytest.raises(RuntimeError):
        builder.write_artifacts(tmp_path, leaky, "doc")
