"""Tests for ledger-3 fifth send runner."""

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "tools/telegram_run_ledger7_manual_gate_backed_ninth_send.py"
GATE_PACKET_PATH = REPO_ROOT / "docs/automation/0174WJ_WK_WL/telegram_ledger7_next_manual_gate_packet.json"
REMOTE_PACKET_PATH = REPO_ROOT / "docs/automation/0174WG_WH_WI/telegram_ledger7_remote_operator_loop_state_packet.json"


def load_module():
    spec = importlib.util.spec_from_file_location("ninth_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return load_module()


@pytest.fixture(scope="module")
def manual_gate():
    return json.loads(GATE_PACKET_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def remote_packet():
    return json.loads(REMOTE_PACKET_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def existing(runner, remote_packet):
    return runner.load_existing_ledger_entries(REPO_ROOT, remote_packet)


class CountingTransport:
    def __init__(self, result=None, exc=None):
        self.calls = 0
        self.result = result or (True, 200, {"has_message_id": True})
        self.exc = exc

    def __call__(self):
        self.calls += 1
        if self.exc:
            raise self.exc
        return self.result


def test_import_has_no_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('r', r'tools/telegram_run_ledger7_manual_gate_backed_ninth_send.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('imported')"],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "imported"


def test_default_runner_no_env_network(runner, manual_gate, remote_packet, existing):
    transport = CountingTransport()
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=False, existing_ledger_entries=existing,
        http_transport=transport)
    assert transport.calls == 0
    assert res["send_result"]["send_attempted"] is False
    assert runner.BLOCK_LIVE_NOT_ENABLED in res["send_result"]["blocked_reasons"]


def test_missing_packet_blocks_before_network(runner, remote_packet, existing):
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=None, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="t", destination="d",
        existing_ledger_entries=existing, http_transport=CountingTransport())
    assert res["send_result"]["send_attempted"] is False
    assert runner.BLOCK_MISSING_MANUAL_GATE_PACKET in res["send_result"]["blocked_reasons"]


def test_wrong_ledger_count_blocks(runner, manual_gate, remote_packet, existing):
    packet = copy.deepcopy(manual_gate)
    packet["source_current_ledger_count"] = 4
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=packet, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="t", destination="d",
        existing_ledger_entries=existing, http_transport=CountingTransport())
    assert runner.BLOCK_WRONG_LEDGER_COUNT in res["send_result"]["blocked_reasons"]


def test_unapproved_gate_blocks(runner, manual_gate, remote_packet, existing):
    packet = copy.deepcopy(manual_gate)
    packet["allowed_next_step"] = "manual_gate_blocked"
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=packet, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="t", destination="d",
        existing_ledger_entries=existing, http_transport=CountingTransport())
    assert runner.BLOCK_MANUAL_GATE_NOT_APPROVED in res["send_result"]["blocked_reasons"]


def test_payload_checksum_mismatch_blocks(runner, manual_gate, remote_packet, existing):
    packet = copy.deepcopy(manual_gate)
    packet["approved_payload_checksum"] = "bad"
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=packet, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="t", destination="d",
        existing_ledger_entries=existing, http_transport=CountingTransport())
    assert runner.BLOCK_APPROVED_PAYLOAD_MISMATCH in res["send_result"]["blocked_reasons"]


def test_destination_binding_mismatch_blocks(runner, manual_gate, remote_packet, existing):
    packet = copy.deepcopy(manual_gate)
    packet["destination_binding_checksum"] = "bad"
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=packet, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="t", destination="d",
        existing_ledger_entries=existing, http_transport=CountingTransport())
    assert runner.BLOCK_DESTINATION_BINDING_MISMATCH in res["send_result"]["blocked_reasons"]


def test_missing_operator_gate_hash_blocks(runner, manual_gate, remote_packet, existing):
    packet = copy.deepcopy(manual_gate)
    packet["operator_gate_id_hash"] = None
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=packet, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="t", destination="d",
        existing_ledger_entries=existing, http_transport=CountingTransport())
    assert runner.BLOCK_OPERATOR_GATE_HASH_MISSING in res["send_result"]["blocked_reasons"]


def test_exact_replay_blocks(runner, manual_gate, remote_packet, existing):
    transport = CountingTransport()
    # Existing ledger already contains the ledger-3 accepted exact replay key.
    accepted = remote_packet["remote_loop_state"]["accepted_ledger_entry"]
    packet = copy.deepcopy(manual_gate)
    packet["approved_payload_checksum"] = accepted["send_text_checksum"]
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=packet, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="t", destination="d",
        existing_ledger_entries=existing, http_transport=transport)
    assert transport.calls == 0
    assert res["send_result"]["send_attempted"] is False


def test_mocked_success_executes_exactly_one_transport_call(runner, manual_gate, remote_packet, existing):
    transport = CountingTransport()
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="token", destination="__approved_destination__",
        existing_ledger_entries=existing, http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["send_succeeded"] is True


def test_mocked_success_advances_ledger_7_to_8(runner, manual_gate, remote_packet, existing):
    transport = CountingTransport()
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="token", destination="__approved_destination__",
        existing_ledger_entries=existing, http_transport=transport)
    assert len(existing) == 7
    assert res["append"]["ledger_entry_count"] == 8


def test_provider_error_one_call_no_retry(runner, manual_gate, remote_packet, existing):
    transport = CountingTransport(result=(False, 500, {"has_message_id": False}))
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="token", destination="__approved_destination__",
        existing_ledger_entries=existing, http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["outcome_class"] == runner.SEND_PROVIDER_ERROR


def test_network_exception_one_call_no_retry(runner, manual_gate, remote_packet, existing):
    transport = CountingTransport(exc=RuntimeError("network down"))
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="token", destination="__approved_destination__",
        existing_ledger_entries=existing, http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["outcome_class"] == runner.SEND_NETWORK_ERROR


def test_proof_doc_deterministic_and_scanner_clean(runner, manual_gate, remote_packet, existing):
    transport1 = CountingTransport()
    res1 = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="token", destination="__approved_destination__",
        existing_ledger_entries=existing, http_transport=transport1)
    p1 = runner.build_proof_packet(res1, old_manifest="old")
    d1 = runner.build_proof_doc(p1)
    transport2 = CountingTransport()
    res2 = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=True, token="token", destination="__approved_destination__",
        existing_ledger_entries=existing, http_transport=transport2)
    p2 = runner.build_proof_packet(res2, old_manifest="old")
    d2 = runner.build_proof_doc(p2)
    assert p1 == p2
    assert d1 == d2
    assert runner.scan_proof(p1, d1) == []


def test_write_artifacts_refuses_unsafe_doc(tmp_path, runner, manual_gate, remote_packet, existing):
    res = runner.run_ledger7_manual_gate_backed_send(
        manual_gate_packet=manual_gate, remote_loop_packet=remote_packet,
        operator_live_send_enabled=False, existing_ledger_entries=existing)
    packet = runner.build_proof_packet(res)
    doc = runner.build_proof_doc(packet) + "\nhttps://api.telegram.org/bot123456:AA\n"
    with pytest.raises(RuntimeError):
        runner.write_artifacts(tmp_path, packet, doc)

