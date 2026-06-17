"""Tests for 0174VF/VG/VH manual-gate-backed Telegram send runner."""

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "tools" / "telegram_run_manual_gate_backed_supervised_send.py"
MANUAL_GATE_PATH = REPO_ROOT / "docs/automation/0174VC_VD_VE/telegram_manual_gate_packet_builder_packet.json"
LEDGER_PACKET_PATH = REPO_ROOT / "docs/automation/0174UN_UO_UP/telegram_supervised_send_outcome_ledger_packet.json"
THIRD_PACKET_PATH = REPO_ROOT / "docs/automation/0174UQ_UR_US/telegram_ledger_guarded_supervised_send_proof_packet.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("manual_gate_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return load_runner()


@pytest.fixture(scope="module")
def manual_gate_packet():
    return json.loads(MANUAL_GATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def existing_entries(runner):
    ledger_packet = json.loads(LEDGER_PACKET_PATH.read_text(encoding="utf-8"))
    third_packet = json.loads(THIRD_PACKET_PATH.read_text(encoding="utf-8"))
    return runner.load_existing_ledger_entries(ledger_packet, third_packet)


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


def make_matching_gate(runner, packet, destination_checksum=None):
    p = copy.deepcopy(packet)
    captured = p["captured_approval_state"]
    rendered = runner.adapter.render_telegram_payload(
        approved_text=runner.SUPERVISED_TEST_MESSAGE,
        parse_mode=runner.adapter.PARSE_MODE_NONE)
    captured["approved_payload_checksum"] = rendered["send_text_checksum"]
    if destination_checksum is not None:
        captured["destination_binding_checksum"] = destination_checksum
    return p


def test_import_has_no_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('r', r'tools/telegram_run_manual_gate_backed_supervised_send.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('imported')"],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "imported"


def test_default_runner_does_not_read_env_or_network(runner, manual_gate_packet, existing_entries):
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=manual_gate_packet,
        operator_live_send_enabled=False,
        existing_ledger_entries=existing_entries,
        http_transport=transport)
    assert transport.calls == 0
    assert res["send_result"]["send_attempted"] is False
    assert runner.BLOCK_LIVE_NOT_ENABLED in res["send_result"]["blocked_reasons"]


def test_missing_manual_gate_packet_blocks_before_network(runner, existing_entries):
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=None,
        operator_live_send_enabled=True,
        token="token", destination="dest",
        existing_ledger_entries=existing_entries,
        http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_MISSING_MANUAL_GATE_PACKET in res["send_result"]["blocked_reasons"]


def test_unapproved_manual_gate_blocks_before_network(runner, manual_gate_packet, existing_entries):
    p = copy.deepcopy(manual_gate_packet)
    p["captured_approval_state"]["operator_approval_outcome_class"] = "operator_approval_waiting"
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination="dest",
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_MANUAL_GATE_NOT_APPROVED in res["send_result"]["blocked_reasons"]


def test_current_packet_approved_checksum_mismatch_blocks(runner, manual_gate_packet, existing_entries):
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=manual_gate_packet,
        operator_live_send_enabled=True,
        token="token", destination="dest",
        existing_ledger_entries=existing_entries,
        http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_APPROVED_PAYLOAD_MISMATCH in res["send_result"]["blocked_reasons"]
    assert res["candidate_evidence"]["send_text_checksum"] != manual_gate_packet[
        "captured_approval_state"]["approved_payload_checksum"]


def test_destination_binding_mismatch_blocks_before_network(runner, manual_gate_packet, existing_entries):
    p = make_matching_gate(runner, manual_gate_packet, destination_checksum="expected_dest")
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination="other_dest",
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_DESTINATION_BINDING_MISMATCH in res["send_result"]["blocked_reasons"]


def test_missing_operator_gate_hash_blocks_before_network(runner, manual_gate_packet, existing_entries):
    p = make_matching_gate(runner, manual_gate_packet)
    p["captured_approval_state"]["operator_gate_id_hash"] = None
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination="dest",
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_OPERATOR_GATE_HASH_MISSING in res["send_result"]["blocked_reasons"]


def test_exact_replay_blocks_before_network(runner, manual_gate_packet, existing_entries):
    dest = "dest"
    destsum = runner._fingerprint16(dest, runner.DEST_BINDING_DOMAIN)
    p = make_matching_gate(runner, manual_gate_packet, destination_checksum=destsum)
    probe = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=False,
        token="token", destination=dest,
        existing_ledger_entries=existing_entries, http_transport=CountingTransport())
    exact = runner.ledger.build_replay_keys(
        probe["candidate_evidence"],
        operator_gate_id=runner.gate.DEMO_FRESH_GATE_ID)["exact_run_replay_key"]
    existing = list(existing_entries) + [{
        "ledger_entry_checksum": "x",
        "exact_run_replay_key": exact,
        "stable_payload_replay_key": "not_used",
    }]
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination=dest,
        existing_ledger_entries=existing, http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_REPLAY_GUARD_NOT_CLEAR in res["send_result"]["blocked_reasons"]


def test_token_missing_blocks_before_network(runner, manual_gate_packet, existing_entries):
    p = make_matching_gate(runner, manual_gate_packet)
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token=None, destination="dest",
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_TOKEN_MISSING in res["send_result"]["blocked_reasons"]


def test_destination_missing_blocks_before_network(runner, manual_gate_packet, existing_entries):
    p = make_matching_gate(runner, manual_gate_packet)
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination=None,
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 0
    assert runner.BLOCK_DESTINATION_MISSING in res["send_result"]["blocked_reasons"]


def test_success_path_executes_exactly_one_mocked_transport(runner, manual_gate_packet, existing_entries):
    dest = "dest"
    dest_checksum = runner._fingerprint16(dest, runner.DEST_BINDING_DOMAIN)
    p = make_matching_gate(runner, manual_gate_packet, destination_checksum=dest_checksum)
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination=dest,
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["send_succeeded"] is True
    assert res["send_result"]["budget_used"] == 1
    assert res["append"]["ledger_entry_count"] == 3


def test_provider_error_one_call_no_retry(runner, manual_gate_packet, existing_entries):
    dest = "dest"
    p = make_matching_gate(
        runner, manual_gate_packet,
        destination_checksum=runner._fingerprint16(dest, runner.DEST_BINDING_DOMAIN))
    transport = CountingTransport(result=(False, 500, {"has_message_id": False}))
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination=dest,
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["send_succeeded"] is False
    assert res["send_result"]["outcome_class"] == runner.SEND_PROVIDER_ERROR


def test_network_exception_one_call_no_retry(runner, manual_gate_packet, existing_entries):
    dest = "dest"
    p = make_matching_gate(
        runner, manual_gate_packet,
        destination_checksum=runner._fingerprint16(dest, runner.DEST_BINDING_DOMAIN))
    transport = CountingTransport(exc=RuntimeError("boom"))
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination=dest,
        existing_ledger_entries=existing_entries, http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["send_succeeded"] is False
    assert res["send_result"]["outcome_class"] == runner.SEND_NETWORK_ERROR


def test_response_checksum_non_null_for_attempted(runner, manual_gate_packet, existing_entries):
    dest = "dest"
    p = make_matching_gate(
        runner, manual_gate_packet,
        destination_checksum=runner._fingerprint16(dest, runner.DEST_BINDING_DOMAIN))
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=p, operator_live_send_enabled=True,
        token="token", destination=dest,
        existing_ledger_entries=existing_entries, http_transport=CountingTransport())
    assert res["final_evidence"]["response_checksum"]
    assert res["final_evidence"]["response_shape_checksum"]


def test_redacted_proof_and_doc_scanner_clean(runner, manual_gate_packet, existing_entries):
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=manual_gate_packet,
        operator_live_send_enabled=False,
        existing_ledger_entries=existing_entries,
        http_transport=CountingTransport())
    packet = runner.build_proof_packet(
        res, old_manifest="old", start_head="h", final_head="h", origin_head="h",
        git_status_summary="changed_entries=0")
    doc = runner.build_proof_doc(packet)
    assert runner.scan_proof(packet, doc) == []
    blob = runner.serialize(packet) + doc
    forbidden = ["123456:AA", "https://api.telegram.org/bot", "setWebhook", "getUpdates"]
    assert "operator_demo_fresh_gate_for_manual_packet" not in blob
    assert "raw_approval_note" in blob  # safety proof key only
    assert all(item not in blob for item in forbidden)


def test_no_extra_behavior_flags(runner, manual_gate_packet, existing_entries):
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=manual_gate_packet,
        operator_live_send_enabled=False,
        existing_ledger_entries=existing_entries)
    packet = runner.build_proof_packet(res)
    for key in ("no_retry", "no_scheduler", "no_webhook", "no_polling",
                "no_get_updates", "no_media", "no_edit", "no_delete",
                "no_second_send_path"):
        assert packet[key] is True


def test_packet_doc_deterministic(runner, manual_gate_packet, existing_entries):
    a = runner.run_manual_gate_backed_send(
        manual_gate_packet=manual_gate_packet,
        operator_live_send_enabled=False,
        existing_ledger_entries=existing_entries)
    b = runner.run_manual_gate_backed_send(
        manual_gate_packet=manual_gate_packet,
        operator_live_send_enabled=False,
        existing_ledger_entries=existing_entries)
    pa = runner.build_proof_packet(a, old_manifest="old")
    pb = runner.build_proof_packet(b, old_manifest="old")
    assert pa == pb
    assert runner.build_proof_doc(pa) == runner.build_proof_doc(pb)


def test_load_dotenv_reads_only_allowed_keys(tmp_path, runner):
    env = tmp_path / ".env"
    env.write_text(
        "TELEGRAM_BOT_TOKEN=abc\nTEST_TELEGRAM_CHANNEL=def\nOTHER_SECRET=ghi\n",
        encoding="utf-8")
    token, destination = runner.load_dotenv_values(env)
    assert token == "abc"
    assert destination == "def"


def test_main_current_packet_writes_blocked_proof_no_live():
    result = subprocess.run(
        [sys.executable, "tools/telegram_run_manual_gate_backed_supervised_send.py"],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert result.returncode == 0
    assert "REAL_SENDMESSAGE_ATTEMPTED False" in result.stdout
    assert "approved_payload_checksum_mismatch" in result.stdout


def test_source_has_no_forbidden_paths():
    text = RUNNER_PATH.read_text(encoding="utf-8")
    assert "getUpdates" not in text
    assert "setWebhook" not in text
    assert "for attempt" not in text
    assert "while " not in text
    assert "media" not in text.lower().replace("no_media", "")
    assert "delete" not in text.lower().replace("no_delete", "")

