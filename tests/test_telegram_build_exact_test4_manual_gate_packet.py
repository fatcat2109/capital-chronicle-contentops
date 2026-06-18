"""Tests for exact test-4 manual gate packet builder."""

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "tools" / "telegram_build_exact_test4_manual_gate_packet.py"
RUNNER_PATH = REPO_ROOT / "tools" / "telegram_run_manual_gate_backed_supervised_send.py"
VC_PACKET_PATH = REPO_ROOT / "docs/automation/0174VC_VD_VE/telegram_manual_gate_packet_builder_packet.json"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return load_module("exact_test4_builder", BUILDER_PATH)


@pytest.fixture(scope="module")
def runner():
    return load_module("manual_gate_runner_for_exact", RUNNER_PATH)


@pytest.fixture(scope="module")
def exact_packet(builder):
    return builder.build_exact_test4_manual_gate_packet(
        destination="dest", existing_ledger_entries=[])


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
        [sys.executable, "-c", "import importlib.util; s=importlib.util.spec_from_file_location('b', r'tools/telegram_build_exact_test4_manual_gate_packet.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('imported')"],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "imported"


def test_exact_builder_produces_approved_packet(builder, exact_packet):
    captured = exact_packet["captured_approval_state"]
    assert exact_packet["allowed_next_step"] == builder.gate.NEXT_STEP_APPROVED_FOR_RUNNER
    assert captured["operator_approval_outcome_class"] == builder.gate.APPROVAL_CAPTURED
    assert captured["approval_captured"] is True


def test_approved_payload_equals_runner_rendered_test4(builder, runner, exact_packet):
    rendered = runner.adapter.render_telegram_payload(
        approved_text=runner.SUPERVISED_TEST_MESSAGE,
        parse_mode=runner.adapter.PARSE_MODE_NONE)
    assert exact_packet["approved_payload_checksum"] == rendered["send_text_checksum"]
    assert exact_packet["approved_payload_checksum_matches"] is True


def test_default_vc_demo_packet_still_mismatches_test4(runner):
    vc_packet = json.loads(VC_PACKET_PATH.read_text(encoding="utf-8"))
    rendered = runner.adapter.render_telegram_payload(
        approved_text=runner.SUPERVISED_TEST_MESSAGE,
        parse_mode=runner.adapter.PARSE_MODE_NONE)
    assert vc_packet["captured_approval_state"]["approved_payload_checksum"] != rendered[
        "send_text_checksum"]


def test_exact_packet_has_no_raw_gate_id_or_note(builder, exact_packet):
    blob = builder.serialize(exact_packet)
    assert builder.gate.DEMO_FRESH_GATE_ID not in blob
    assert "operator approved" not in blob.lower()
    assert exact_packet["stores_no_raw_operator_gate_id"] is True
    assert exact_packet["stores_no_raw_approval_note"] is True


def test_exact_packet_stores_no_secret_or_raw_transport_fields(builder, exact_packet):
    blob = builder.serialize(exact_packet)
    forbidden = ["123456:aa", "https://api.telegram.org/bot", "authorization: bearer"]
    assert all(item not in blob.lower() for item in forbidden)
    for key in ("stores_no_token", "stores_no_raw_destination", "stores_no_raw_response",
                "stores_no_raw_url", "stores_no_headers", "stores_no_cookies"):
        assert exact_packet[key] is True


def test_dry_runner_exact_packet_no_payload_mismatch(builder, runner, exact_packet):
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=exact_packet,
        operator_live_send_enabled=False,
        existing_ledger_entries=[])
    assert runner.BLOCK_APPROVED_PAYLOAD_MISMATCH not in res["send_result"]["blocked_reasons"]
    assert runner.BLOCK_LIVE_NOT_ENABLED in res["send_result"]["blocked_reasons"]
    assert res["send_result"]["send_attempted"] is False


def test_mocked_live_success_executes_one_call_and_advances_ledger(builder, runner, exact_packet):
    existing = builder.load_existing_entries(REPO_ROOT)
    transport = CountingTransport()
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=exact_packet,
        operator_live_send_enabled=True,
        token="token", destination="dest",
        existing_ledger_entries=existing,
        http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["send_succeeded"] is True
    assert res["append"]["ledger_entry_count"] == 3
    assert res["manual_gate_revalidated"] is True


def test_provider_error_one_call_no_retry(builder, runner, exact_packet):
    transport = CountingTransport(result=(False, 500, {"has_message_id": False}))
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=exact_packet,
        operator_live_send_enabled=True,
        token="token", destination="dest",
        existing_ledger_entries=builder.load_existing_entries(REPO_ROOT),
        http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["outcome_class"] == runner.SEND_PROVIDER_ERROR


def test_network_exception_one_call_no_retry(builder, runner, exact_packet):
    transport = CountingTransport(exc=RuntimeError("boom"))
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=exact_packet,
        operator_live_send_enabled=True,
        token="token", destination="dest",
        existing_ledger_entries=builder.load_existing_entries(REPO_ROOT),
        http_transport=transport)
    assert transport.calls == 1
    assert res["send_result"]["outcome_class"] == runner.SEND_NETWORK_ERROR


def test_proof_packet_doc_scanner_clean(builder, exact_packet):
    doc = builder.build_doc(exact_packet)
    assert builder.scan_packet(exact_packet, doc) == []


def test_no_live_network_in_builder_tests(builder, exact_packet):
    assert exact_packet["no_retry"] is True
    assert exact_packet["no_scheduler"] is True
    assert exact_packet["no_webhook"] is True
    assert exact_packet["no_polling"] is True
    assert exact_packet["no_get_updates"] is True
    assert exact_packet["no_second_send_path"] is True


def test_packet_checksum_is_deterministic(builder):
    a = builder.build_exact_test4_manual_gate_packet(
        destination="dest", existing_ledger_entries=[])
    b = builder.build_exact_test4_manual_gate_packet(
        destination="dest", existing_ledger_entries=[])
    assert a == b
    assert builder.build_doc(a) == builder.build_doc(b)


def test_destination_checksum_matches_runner_policy(builder, runner, exact_packet):
    expected = runner._fingerprint16("dest", runner.DEST_BINDING_DOMAIN)
    assert exact_packet["destination_binding_checksum"] == expected
    assert exact_packet["destination_binding_checksum_matches"] is True


def test_copy_runner_proof_to_vi(tmp_path, builder):
    vf = tmp_path / builder.runner.DOC_REL_DIR
    vf.mkdir(parents=True)
    (vf / builder.runner.PACKET_FILENAME).write_text("{}", encoding="utf-8")
    (vf / builder.runner.DOC_FILENAME).write_text("doc", encoding="utf-8")
    written = builder.copy_runner_proof_to_vi(tmp_path)
    assert len(written) == 2
    assert (tmp_path / builder.DOC_REL_DIR / builder.RUNNER_PACKET_FILENAME).is_file()
    assert (tmp_path / builder.DOC_REL_DIR / builder.RUNNER_DOC_FILENAME).is_file()


def test_manual_gate_packet_nested_for_runner(builder, runner, exact_packet):
    blockers, captured = runner.validate_manual_gate_packet(exact_packet)
    assert blockers == []
    assert captured["approved_payload_checksum"] == exact_packet["approved_payload_checksum"]
    assert captured["manual_gate_packet_checksum"] == exact_packet["manual_gate_packet_checksum"]


def test_mutated_payload_blocks_runner(builder, runner, exact_packet):
    packet = copy.deepcopy(exact_packet)
    packet["captured_approval_state"]["approved_payload_checksum"] = "bad"
    res = runner.run_manual_gate_backed_send(
        manual_gate_packet=packet,
        operator_live_send_enabled=False,
        existing_ledger_entries=[])
    assert runner.BLOCK_APPROVED_PAYLOAD_MISMATCH in res["send_result"]["blocked_reasons"]

