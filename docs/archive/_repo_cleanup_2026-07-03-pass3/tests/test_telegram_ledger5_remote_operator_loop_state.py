"""Tests for 0174VU/VV/VW ledger-5 remote operator loop state."""

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "live_contentops" / "telegram_ledger5_remote_operator_loop_state.py"
FIFTH_PROOF_PATH = REPO_ROOT / "docs/automation/0174WA_WB_WC/telegram_ledger4_sixth_send_proof_packet.json"
MANUAL_GATE_PATH = REPO_ROOT / "docs/automation/0174VX_VY_VZ/telegram_ledger4_next_manual_gate_packet.json"
PREVIOUS_LOOP_PATH = REPO_ROOT / "docs/automation/0174VU_VV_VW/telegram_ledger4_remote_operator_loop_state_packet.json"


def load_module():
    spec = importlib.util.spec_from_file_location("ledger5_loop", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ledger5():
    return load_module()


@pytest.fixture(scope="module")
def proof():
    return json.loads(FIFTH_PROOF_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manual_gate():
    return json.loads(MANUAL_GATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def previous_loop():
    return json.loads(PREVIOUS_LOOP_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def state(ledger5, proof, manual_gate, previous_loop):
    return ledger5.build_ledger5_remote_operator_loop_state(
        proof, manual_gate, previous_loop_state_packet=previous_loop)


def test_import_has_no_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('m', r'live_contentops/telegram_ledger5_remote_operator_loop_state.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('imported')"],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "imported"


def test_accept_committed_sixth_proof(ledger5, proof, previous_loop):
    rec = ledger5.reconcile_sixth_send_proof(proof, previous_loop)
    assert rec["reconciliation_outcome_class"] == ledger5.RECONCILE_OK


def test_block_missing_proof(ledger5):
    rec = ledger5.reconcile_sixth_send_proof(None)
    assert rec["reconciliation_outcome_class"] == ledger5.RECONCILE_MISSING


def test_block_send_not_succeeded(ledger5, proof):
    p = copy.deepcopy(proof)
    p["send_succeeded"] = False
    rec = ledger5.reconcile_sixth_send_proof(p)
    assert rec["reconciliation_outcome_class"] == ledger5.RECONCILE_SEND_NOT_SUCCEEDED


def test_block_manual_gate_not_revalidated(ledger5, proof):
    p = copy.deepcopy(proof)
    p["manual_gate_revalidated"] = False
    rec = ledger5.reconcile_sixth_send_proof(p)
    assert rec["reconciliation_outcome_class"] == ledger5.RECONCILE_GATE_NOT_REVALIDATED


def test_block_ledger_not_advanced(ledger5, proof):
    p = copy.deepcopy(proof)
    p["ledger_entry_count"] = 4
    rec = ledger5.reconcile_sixth_send_proof(p)
    assert rec["reconciliation_outcome_class"] == ledger5.RECONCILE_LEDGER_NOT_ADVANCED


def test_block_manifest_not_advanced(ledger5, proof):
    p = copy.deepcopy(proof)
    p["new_ledger_manifest_checksum"] = p["old_ledger_manifest_checksum"]
    rec = ledger5.reconcile_sixth_send_proof(p)
    assert rec["reconciliation_outcome_class"] == ledger5.RECONCILE_MANIFEST_NOT_ADVANCED


def test_fail_close_raw_token_url_destination(ledger5, proof):
    p = copy.deepcopy(proof)
    p["raw_url"] = "https://api.telegram.org/bot123456:AA/sendMessage"
    p["token"] = "123456:AA"
    p["raw_destination"] = "@capitalchronicle"
    rec = ledger5.reconcile_sixth_send_proof(p)
    assert rec["reconciliation_outcome_class"] == ledger5.RECONCILE_FAIL_CLOSED


def test_state_has_ledger_count_4_and_sequence_5(state):
    assert state["current_ledger_count"] == 5
    assert state["last_successful_send_sequence"] == 6
    assert state["reconciled"] is True


def test_exact_replay_blocks(ledger5, proof, state):
    candidate = ledger5._candidate_from_proof(proof)
    pre = ledger5.build_next_gate_precheck_state(
        state, candidate, fresh_operator_gate_id=ledger5.SIXTH_GATE_ID)
    assert pre["next_gate_outcome_class"] == ledger5.loop3.NEXT_BLOCKED_EXACT


def test_same_payload_without_gate_requires_fresh_gate(ledger5, proof, state):
    candidate = ledger5._candidate_from_proof(proof, sequence=6, response_suffix="same_payload")
    pre = ledger5.build_next_gate_precheck_state(state, candidate)
    assert pre["next_gate_outcome_class"] == ledger5.loop3.NEXT_REQUIRES_FRESH_GATE


def test_fresh_gate_clears(ledger5, proof, state):
    candidate = ledger5._new_payload_candidate_from_proof(proof)
    pre = ledger5.build_next_gate_precheck_state(
        state, candidate, fresh_operator_gate_id="fresh")
    assert pre["next_gate_outcome_class"] == ledger5.loop3.NEXT_CLEAR


def test_packet_doc_deterministic_and_scanner_clean(ledger5, proof, manual_gate, previous_loop):
    p1 = ledger5.build_artifact_packet(proof, manual_gate, previous_loop_state_packet=previous_loop)
    p2 = ledger5.build_artifact_packet(proof, manual_gate, previous_loop_state_packet=previous_loop)
    assert p1 == p2
    d1 = ledger5.build_artifact_doc(p1)
    d2 = ledger5.build_artifact_doc(p2)
    assert d1 == d2
    assert ledger5.scan_artifact(p1, d1) == []


def test_write_artifacts_refuses_unsafe_output(tmp_path, ledger5, proof, manual_gate, previous_loop):
    packet = ledger5.build_artifact_packet(proof, manual_gate, previous_loop_state_packet=previous_loop)
    doc = ledger5.build_artifact_doc(packet) + "\nhttps://api.telegram.org/bot123456:AA\n"
    with pytest.raises(RuntimeError):
        ledger5.write_artifacts(tmp_path, packet, doc)


def test_no_live_env_network_flags(ledger5, proof, manual_gate, previous_loop):
    packet = ledger5.build_artifact_packet(proof, manual_gate, previous_loop_state_packet=previous_loop)
    assert packet["network_performed"] is False
    assert packet["telegram_api_called"] is False
    assert packet["env_read"] is False
    assert packet["credential_read"] is False
    assert packet["sendmessage_executed"] is False


def test_build_artifact_from_repo(ledger5):
    packet = ledger5.build_artifact_from_repo(REPO_ROOT)
    assert packet["reconciliation_outcome_class"] == ledger5.RECONCILE_OK
    assert packet["current_ledger_count"] == 5
    assert packet["last_successful_send_sequence"] == 6

