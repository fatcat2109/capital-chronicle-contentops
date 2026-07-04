"""Tests for ledger-3 next manual gate packet builder."""

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "tools/telegram_build_ledger5_next_manual_gate_packet.py"
REMOTE_PACKET_PATH = REPO_ROOT / "docs/automation/0174WA_WB_WC/telegram_ledger5_remote_operator_loop_state_packet.json"


def load_module():
    spec = importlib.util.spec_from_file_location("ledger5_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return load_module()


@pytest.fixture(scope="module")
def remote_packet():
    return json.loads(REMOTE_PACKET_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built(builder, remote_packet):
    return builder.build_ledger5_next_manual_gate_packet(
        remote_packet, operator_gate_id="fresh_test_gate")


def test_import_has_no_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('b', r'tools/telegram_build_ledger5_next_manual_gate_packet.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('imported')"],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "imported"


def test_source_validation_accepts_committed_packet(builder, remote_packet):
    res = builder.validate_ledger5_remote_loop_state_for_next_gate(remote_packet)
    assert res["ledger5_source_validation_outcome_class"] == builder.LEDGER5_SOURCE_OK


def test_source_validation_blocks_missing_packet(builder):
    res = builder.validate_ledger5_remote_loop_state_for_next_gate(None)
    assert res["ledger5_source_validation_outcome_class"] == builder.LEDGER5_SOURCE_MISSING


def test_source_validation_blocks_unreconciled(builder, remote_packet):
    packet = copy.deepcopy(remote_packet)
    packet["remote_loop_state"]["reconciled"] = False
    res = builder.validate_ledger5_remote_loop_state_for_next_gate(packet)
    assert res["ledger5_source_validation_outcome_class"] == builder.LEDGER5_SOURCE_UNRECONCILED


def test_source_validation_blocks_wrong_ledger_count(builder, remote_packet):
    packet = copy.deepcopy(remote_packet)
    packet["current_ledger_count"] = 4
    res = builder.validate_ledger5_remote_loop_state_for_next_gate(packet)
    assert res["ledger5_source_validation_outcome_class"] == builder.LEDGER5_SOURCE_WRONG_COUNT


def test_source_validation_fail_closes_raw_token_url_destination(builder, remote_packet):
    packet = copy.deepcopy(remote_packet)
    packet["raw_url"] = "https://api.telegram.org/bot123456:AA/sendMessage"
    packet["token"] = "123456:AA"
    packet["raw_destination"] = "@capitalchronicle"
    res = builder.validate_ledger5_remote_loop_state_for_next_gate(packet)
    assert res["ledger5_source_validation_outcome_class"] == builder.LEDGER5_SOURCE_FAIL_CLOSED


def test_candidate_evidence_uses_sequence_7(builder, remote_packet):
    ev = builder.build_ledger5_next_candidate_evidence(remote_packet)
    assert ev["live_test_sequence"] == 7


def test_candidate_evidence_message_checksum_matches_adapter(builder, remote_packet):
    ev = builder.build_ledger5_next_candidate_evidence(remote_packet)
    rendered = builder.adapter.render_telegram_payload(
        approved_text=builder.TEST7_MESSAGE,
        parse_mode=builder.adapter.PARSE_MODE_NONE)
    assert ev["send_text_checksum"] == rendered["send_text_checksum"]


def test_next_gate_precheck_clears_new_payload_with_fresh_gate(builder, remote_packet):
    ev = builder.build_ledger5_next_candidate_evidence(remote_packet)
    pre = builder.loop.build_next_gate_precheck_state(
        remote_packet["remote_loop_state"], ev, fresh_operator_gate_id="fresh")
    assert pre["next_gate_outcome_class"] == builder.loop.loop3.NEXT_CLEAR


def test_exact_replay_example_still_blocks(builder, remote_packet):
    pre = remote_packet["next_gate_examples"]["exact_replay"]
    assert pre["next_gate_outcome_class"] == builder.loop.loop3.NEXT_BLOCKED_EXACT


def test_same_payload_without_gate_still_requires_fresh_gate(builder, remote_packet):
    pre = remote_packet["next_gate_examples"]["same_payload_without_gate"]
    assert pre["next_gate_outcome_class"] == builder.loop.loop3.NEXT_REQUIRES_FRESH_GATE


def test_manual_gate_builder_requires_fresh_operator_gate(builder, remote_packet):
    res = builder.build_ledger5_next_manual_gate_packet(remote_packet, operator_gate_id=None)
    assert res["status"] == builder.adapter.Status.BLOCKED
    assert res["captured_approval"]["operator_approval_outcome_class"] != builder.gate.APPROVAL_CAPTURED


def test_manual_gate_packet_captured_when_fresh_gate_present(builder, built):
    assert built["status"] == builder.adapter.Status.PASS
    assert built["captured_approval"]["operator_approval_outcome_class"] == builder.gate.APPROVAL_CAPTURED
    assert built["manual_gate_packet"]["allowed_next_step"] == builder.gate.NEXT_STEP_APPROVED_FOR_RUNNER


def test_approved_payload_checksum_equals_candidate_send_text_checksum(built):
    assert built["captured_approval"]["approved_payload_checksum"] == built[
        "candidate_evidence"]["send_text_checksum"]


def test_destination_binding_checksum_matches_candidate(built):
    assert built["captured_approval"]["destination_binding_checksum"] == built[
        "candidate_evidence"]["destination_binding_checksum"]


def test_raw_operator_gate_id_never_serialized(builder, built):
    blob = builder.serialize(built)
    assert "fresh_test_gate" not in blob
    assert "ledger5_next_manual_gate_transient_local_gate_v1" not in blob


def test_raw_approval_note_never_serialized(builder, built):
    blob = builder.serialize(built).lower()
    assert "operator approved" not in blob
    assert built["manual_gate_packet"]["stores_no_raw_approval_note"] is True


def test_packet_doc_deterministic_and_scanner_clean(builder, remote_packet):
    p1, r1 = builder.build_builder_artifact_packet(remote_packet, operator_gate_id="fresh")
    p2, r2 = builder.build_builder_artifact_packet(remote_packet, operator_gate_id="fresh")
    assert p1 == p2
    assert r1 == r2
    d1 = builder.build_builder_doc(p1)
    m1 = builder.build_manual_gate_doc(r1["manual_gate_packet"])
    assert builder.scan_artifact(p1, d1) == []
    assert builder.scan_artifact(r1["manual_gate_packet"], m1) == []


def test_write_artifacts_refuses_unsafe_packet_doc(tmp_path, builder, remote_packet):
    packet, result = builder.build_builder_artifact_packet(remote_packet, operator_gate_id="fresh")
    doc = builder.build_builder_doc(packet) + "\nhttps://api.telegram.org/bot123456:AA\n"
    manual = result["manual_gate_packet"]
    manual_doc = builder.build_manual_gate_doc(manual)
    with pytest.raises(RuntimeError):
        builder.write_artifacts(tmp_path, packet, doc, manual, manual_doc)


def test_no_network_api_env_credential_read_or_sendmessage(builder, remote_packet):
    packet, result = builder.build_builder_artifact_packet(remote_packet, operator_gate_id="fresh")
    manual = result["manual_gate_packet"]
    for obj in (packet, manual):
        assert obj["network_performed"] is False
        assert obj["platform_api_called"] is False
        assert obj["telegram_api_called"] is False
        assert obj["credential_read"] is False
        assert obj["env_read"] is False
        assert obj["dotenv_read"] is False
        assert obj["sendmessage_executed"] is False


def test_write_artifacts_success(tmp_path, builder, remote_packet):
    packet, result = builder.build_builder_artifact_packet(remote_packet, operator_gate_id="fresh")
    doc = builder.build_builder_doc(packet)
    manual = result["manual_gate_packet"]
    manual_doc = builder.build_manual_gate_doc(manual)
    written = builder.write_artifacts(tmp_path, packet, doc, manual, manual_doc)
    assert len(written) == 4
    for path in written:
        assert pathlib.Path(path).is_file()


def test_builder_artifact_core_fields(builder, remote_packet):
    packet, result = builder.build_builder_artifact_packet(remote_packet, operator_gate_id="fresh")
    assert packet["source_validation_outcome_class"] == builder.LEDGER5_SOURCE_OK
    assert packet["source_current_ledger_count"] == 5
    assert packet["next_gate_precheck_outcome_class"] == builder.loop.loop3.NEXT_CLEAR
    assert packet["manual_gate_packet_checksum"] == result["manual_gate_packet"]["manual_gate_packet_checksum"]
    assert packet["live_test_sequence"] == 7

