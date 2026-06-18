"""Tests for 0174VL/VM/VN remote operator loop state."""

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "live_contentops" / "telegram_remote_operator_loop_state.py"
PROOF_PATH = REPO_ROOT / "docs/automation/0174VI_VJ_VK/telegram_exact_test4_send_proof_packet.json"
GATE_PATH = REPO_ROOT / "docs/automation/0174VI_VJ_VK/telegram_exact_test4_manual_gate_packet.json"
LEDGER_PATH = REPO_ROOT / "docs/automation/0174UN_UO_UP/telegram_supervised_send_outcome_ledger_packet.json"
THIRD_PATH = REPO_ROOT / "docs/automation/0174UQ_UR_US/telegram_ledger_guarded_supervised_send_proof_packet.json"


def load_module():
    spec = importlib.util.spec_from_file_location("remote_loop", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def remote_loop():
    return load_module()


@pytest.fixture(scope="module")
def proof():
    return json.loads(PROOF_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gate_packet():
    return json.loads(GATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def state(remote_loop, proof, gate_packet):
    return remote_loop.build_remote_operator_loop_state(
        proof, gate_packet,
        previous_ledger_packet=json.loads(LEDGER_PATH.read_text(encoding="utf-8")),
        previous_success_proofs=[json.loads(THIRD_PATH.read_text(encoding="utf-8"))])


def test_import_has_no_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('r', r'live_contentops/telegram_remote_operator_loop_state.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('imported')"],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "imported"


def test_accepts_committed_exact_test4_proof(remote_loop, proof):
    rec = remote_loop.reconcile_exact_test4_send_proof(proof)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_OK
    assert rec["reconciled"] is True


def test_blocks_missing_proof(remote_loop):
    rec = remote_loop.reconcile_exact_test4_send_proof(None)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_MISSING


def test_blocks_send_not_succeeded(remote_loop, proof):
    p = copy.deepcopy(proof)
    p["send_succeeded"] = False
    rec = remote_loop.reconcile_exact_test4_send_proof(p)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_SEND_NOT_SUCCEEDED


def test_blocks_manual_gate_not_revalidated(remote_loop, proof):
    p = copy.deepcopy(proof)
    p["manual_gate_revalidated"] = False
    rec = remote_loop.reconcile_exact_test4_send_proof(p)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_GATE_NOT_REVALIDATED


def test_blocks_ledger_not_advanced(remote_loop, proof):
    p = copy.deepcopy(proof)
    p["ledger_entry_count"] = 2
    rec = remote_loop.reconcile_exact_test4_send_proof(p)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_LEDGER_NOT_ADVANCED


def test_blocks_manifest_not_advanced(remote_loop, proof):
    p = copy.deepcopy(proof)
    p["new_ledger_manifest_checksum"] = p["old_ledger_manifest_checksum"]
    rec = remote_loop.reconcile_exact_test4_send_proof(p)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_MANIFEST_NOT_ADVANCED


def test_blocks_missing_response_checksum(remote_loop, proof):
    p = copy.deepcopy(proof)
    p["response_checksum"] = None
    rec = remote_loop.reconcile_exact_test4_send_proof(p)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_LEDGER_NOT_ADVANCED


def test_fail_closes_forbidden_raw_token_url_destination(remote_loop, proof):
    p = copy.deepcopy(proof)
    p["raw_url"] = "https://api.telegram.org/bot123456:AA/sendMessage"
    p["raw_destination"] = "@capitalchronicle"
    p["token"] = "123456:AA"
    rec = remote_loop.reconcile_exact_test4_send_proof(p)
    assert rec["reconciliation_outcome_class"] == remote_loop.RECONCILE_FAIL_CLOSED


def test_builds_state_with_ledger_count_3_and_sequence_4(state):
    assert state["current_ledger_count"] == 3
    assert state["last_successful_send_sequence"] == 4
    assert state["reconciled"] is True


def test_state_has_old_new_manifest_checksums_and_they_differ(state):
    assert state["previous_ledger_manifest_checksum"]
    assert state["current_ledger_manifest_checksum"]
    assert state["previous_ledger_manifest_checksum"] != state["current_ledger_manifest_checksum"]


def test_state_stores_no_raw_secrets(remote_loop, state):
    blob = remote_loop.serialize(state).lower()
    assert "https://api.telegram.org/bot" not in blob
    assert "123456:aa" not in blob
    assert state["stores_no_token"] is True
    assert state["stores_no_raw_destination"] is True
    assert state["stores_no_raw_response"] is True
    assert state["stores_no_raw_url"] is True


def test_next_gate_missing_candidate_waits(remote_loop, state):
    nxt = remote_loop.build_next_gate_precheck_state(state)
    assert nxt["next_gate_outcome_class"] == remote_loop.NEXT_WAITING


def test_exact_replay_blocks(remote_loop, proof, state):
    candidate = remote_loop._candidate_from_proof(proof)
    nxt = remote_loop.build_next_gate_precheck_state(
        state, candidate, fresh_operator_gate_id="exact_test4_operator_gate")
    assert nxt["next_gate_outcome_class"] == remote_loop.NEXT_BLOCKED_EXACT


def test_same_payload_without_fresh_gate_requires_gate(remote_loop, proof, state):
    candidate = remote_loop._candidate_from_proof(
        proof, sequence=5, response_suffix="same_payload")
    nxt = remote_loop.build_next_gate_precheck_state(state, candidate)
    assert nxt["next_gate_outcome_class"] == remote_loop.NEXT_REQUIRES_FRESH_GATE


def test_same_payload_with_fresh_gate_clears(remote_loop, proof, state):
    candidate = remote_loop._candidate_from_proof(
        proof, sequence=5, response_suffix="same_payload")
    nxt = remote_loop.build_next_gate_precheck_state(
        state, candidate, fresh_operator_gate_id="fresh_next_gate")
    assert nxt["next_gate_outcome_class"] == remote_loop.NEXT_CLEAR


def test_new_payload_with_fresh_gate_clears(remote_loop, proof, state):
    candidate = remote_loop._new_payload_candidate_from_proof(proof)
    nxt = remote_loop.build_next_gate_precheck_state(
        state, candidate, fresh_operator_gate_id="fresh_next_gate")
    assert nxt["next_gate_outcome_class"] == remote_loop.NEXT_CLEAR


def test_unreconciled_loop_blocks(remote_loop, state):
    bad = copy.deepcopy(state)
    bad["reconciled"] = False
    nxt = remote_loop.build_next_gate_precheck_state(
        bad, {"evidence_checksum": "x"}, fresh_operator_gate_id="fresh")
    assert nxt["next_gate_outcome_class"] == remote_loop.NEXT_BLOCKED_UNRECONCILED


def test_artifact_packet_doc_deterministic_and_scanner_clean(remote_loop, proof, gate_packet):
    p1 = remote_loop.build_artifact_packet(proof, gate_packet)
    p2 = remote_loop.build_artifact_packet(proof, gate_packet)
    assert p1 == p2
    d1 = remote_loop.build_artifact_doc(p1)
    d2 = remote_loop.build_artifact_doc(p2)
    assert d1 == d2
    assert remote_loop.scan_artifact(p1, d1) == []


def test_write_artifacts_refuses_unsafe_packet_doc(tmp_path, remote_loop, proof, gate_packet):
    packet = remote_loop.build_artifact_packet(proof, gate_packet)
    doc = remote_loop.build_artifact_doc(packet) + "\nhttps://api.telegram.org/bot123456:AA\n"
    with pytest.raises(RuntimeError):
        remote_loop.write_artifacts(tmp_path, packet, doc)


def test_no_network_api_env_credential_read_or_sendmessage(remote_loop, proof, gate_packet):
    packet = remote_loop.build_artifact_packet(proof, gate_packet)
    assert packet["network_performed"] is False
    assert packet["platform_api_called"] is False
    assert packet["telegram_api_called"] is False
    assert packet["credential_read"] is False
    assert packet["env_read"] is False
    assert packet["dotenv_read"] is False
    assert packet["sendmessage_executed"] is False


def test_build_artifact_from_repo(remote_loop):
    packet = remote_loop.build_artifact_from_repo(REPO_ROOT)
    assert packet["reconciliation_outcome_class"] == remote_loop.RECONCILE_OK
    assert packet["current_ledger_count"] == 3
    assert packet["next_gate_examples"]["no_candidate"]["next_gate_outcome_class"] == remote_loop.NEXT_WAITING


def test_write_artifacts_success(tmp_path, remote_loop, proof, gate_packet):
    packet = remote_loop.build_artifact_packet(proof, gate_packet)
    doc = remote_loop.build_artifact_doc(packet)
    written = remote_loop.write_artifacts(tmp_path, packet, doc)
    assert len(written) == 2
    assert pathlib.Path(written[0]).is_file()
    assert pathlib.Path(written[1]).is_file()

