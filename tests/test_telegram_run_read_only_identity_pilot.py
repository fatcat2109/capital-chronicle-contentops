"""Tests for the 0174UH/UI/UJ operator runner.

These tests NEVER perform a real network call and NEVER read a real token: every
test injects a mock ``env_reader`` and/or a mock ``http_transport``. They assert
the runner is dry-run safe, fails closed on a missing credential, emits a fully
redacted scanner-clean evidence packet/doc, performs at most one ``getMe``, and
contains no posting / retry / scheduler behavior. They also assert importing the
module has no side effects.
"""

import importlib
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from live_contentops import telegram_read_only_identity_pilot as pilot
from tools import telegram_run_read_only_identity_pilot as runner

GOOD_TOKEN = "123456789:" + ("A" * 35)  # plausible shape; never a real secret
GATE = runner.OPERATOR_GATE_ID


# --------------------------------------------------------------------------- #
# Mock transports (mirror the accepted pilot test shape)
# --------------------------------------------------------------------------- #
def _ok_transport():
    return (True, 200, {"has_id": True, "has_username": True})


def _provider_error_transport():
    return (False, 401, {"has_id": False, "has_username": False})


def _exploding_transport():
    raise AssertionError("transport must not be called in dry-run/blocked paths")


def _raising_transport():
    raise RuntimeError("simulated network failure")


def _good_env_reader(name):
    assert name == pilot.ALLOWED_ENV_VAR
    return GOOD_TOKEN


def _missing_env_reader(name):
    assert name == pilot.ALLOWED_ENV_VAR
    return None


# --------------------------------------------------------------------------- #
# Import has no side effects
# --------------------------------------------------------------------------- #
def test_import_has_no_side_effects():
    captured = io.StringIO()
    with redirect_stdout(captured):
        importlib.reload(runner)
    assert captured.getvalue() == ""


# --------------------------------------------------------------------------- #
# Dry-run path: no env read, no network
# --------------------------------------------------------------------------- #
def test_dry_run_does_no_env_read_or_network():
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=False,
        env_reader=_exploding_env_reader, http_transport=_exploding_transport)
    assert proof["env_read_performed"] is False
    assert proof["credential_proof_outcome_class"] == \
        pilot.CREDENTIAL_PROOF_NOT_HYDRATED
    assert identity["identity_proof_outcome_class"] == pilot.PILOT_NOT_RUN_DRY_RUN
    assert identity["network_performed"] is False
    assert identity["read_only_request_performed"] is False


def _exploding_env_reader(name):
    raise AssertionError("env must not be read in dry-run")


# --------------------------------------------------------------------------- #
# Missing credential -> redacted blocked packet, no retry, no network
# --------------------------------------------------------------------------- #
def test_missing_credential_produces_redacted_blocked_packet():
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=_missing_env_reader, http_transport=_exploding_transport)
    assert pilot.BLOCK_CREDENTIAL_MISSING in proof["blocked_reasons"]
    assert identity["identity_proof_outcome_class"] == pilot.PILOT_BLOCKED
    assert identity["read_only_request_performed"] is False

    packet = runner.build_evidence_packet(
        plan, proof, identity, audit, start_head="h", final_head="h",
        origin_head="h", git_status_summary="changed_entries=0",
        real_getme_attempted=True)
    assert packet["credential_env_var_present_redacted"] is False
    assert packet["request_budget_used"] == 0
    assert packet["no_sendmessage"] is True
    # Packet + doc must be scanner-clean.
    doc = runner.build_evidence_doc(packet)
    assert runner.scan_evidence(packet, doc) == []


# --------------------------------------------------------------------------- #
# Live success via injected mock transport -> redacted ok packet
# --------------------------------------------------------------------------- #
def test_live_success_via_mock_transport_redacted():
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=_good_env_reader, http_transport=_ok_transport)
    assert identity["identity_proof_outcome_class"] == pilot.PILOT_OK
    assert identity["getme_ok"] is True
    assert identity["read_only_request_performed"] is True

    packet = runner.build_evidence_packet(
        plan, proof, identity, audit, start_head=runner.REQUIRED_BASELINE_COMMIT,
        final_head=runner.REQUIRED_BASELINE_COMMIT,
        origin_head=runner.REQUIRED_BASELINE_COMMIT,
        git_status_summary="changed_entries=2", real_getme_attempted=True)
    assert packet["baseline_matched"] is True
    assert packet["credential_env_var_present_redacted"] is True
    assert packet["request_budget_used"] == 1
    assert packet["getme_ok"] is True
    assert packet["bot_identity_presence_class"] == \
        pilot.BOT_IDENTITY_PRESENT_CLASS
    assert packet["provider_status_code_class"] == \
        pilot.PROVIDER_CODE_SUCCESS_CLASS
    # No-secret + no-posting proofs.
    assert packet["stores_no_token"] is True
    assert packet["stores_no_raw_response"] is True
    assert packet["stores_no_raw_url"] is True
    assert packet["stores_no_headers"] is True
    assert packet["stores_no_cookies"] is True
    assert packet["no_sendmessage"] is True
    assert packet["no_posting"] is True
    assert packet["no_auto_retry"] is True
    assert packet["no_scheduler"] is True
    assert packet["no_webhook"] is True
    assert packet["no_polling"] is True
    assert packet["next_recommended_task"] == runner.NEXT_RECOMMENDED_TASK


def test_provider_error_via_mock_transport_redacted():
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=_good_env_reader, http_transport=_provider_error_transport)
    assert identity["identity_proof_outcome_class"] == pilot.PILOT_PROVIDER_ERROR
    packet = runner.build_evidence_packet(
        plan, proof, identity, audit, start_head="h", final_head="h",
        origin_head="h", git_status_summary="changed_entries=0",
        real_getme_attempted=True)
    assert packet["getme_ok"] is False
    assert packet["request_budget_used"] == 1
    assert packet["provider_status_code_class"] == \
        pilot.PROVIDER_CODE_CLIENT_ERROR_CLASS
    doc = runner.build_evidence_doc(packet)
    assert runner.scan_evidence(packet, doc) == []


def test_network_exception_fails_closed_redacted():
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=_good_env_reader, http_transport=_raising_transport)
    assert identity["identity_proof_outcome_class"] == pilot.PILOT_NETWORK_BLOCKED
    packet = runner.build_evidence_packet(
        plan, proof, identity, audit, start_head="h", final_head="h",
        origin_head="h", git_status_summary="changed_entries=0",
        real_getme_attempted=True)
    doc = runner.build_evidence_doc(packet)
    assert runner.scan_evidence(packet, doc) == []


# --------------------------------------------------------------------------- #
# Exactly one request
# --------------------------------------------------------------------------- #
def test_executes_exactly_one_request():
    calls = {"n": 0}

    def counting_transport():
        calls["n"] += 1
        return (True, 200, {"has_id": True, "has_username": True})

    runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=_good_env_reader, http_transport=counting_transport)
    assert calls["n"] == 1


# --------------------------------------------------------------------------- #
# Evidence packet/doc never carry token or raw response material
# --------------------------------------------------------------------------- #
def test_evidence_is_scanner_clean_and_tokenless():
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=_good_env_reader, http_transport=_ok_transport)
    packet = runner.build_evidence_packet(
        plan, proof, identity, audit, start_head="h", final_head="h",
        origin_head="h", git_status_summary="changed_entries=0",
        real_getme_attempted=True)
    doc = runner.build_evidence_doc(packet)
    blob = json.dumps(packet) + doc
    assert GOOD_TOKEN not in blob
    assert "123456789:" not in blob
    assert runner.scan_evidence(packet, doc) == []
    assert runner.scan_for_financial_advice_safe(packet, doc) == []


# --------------------------------------------------------------------------- #
# write_evidence refuses to write unsafe content + writes clean content
# --------------------------------------------------------------------------- #
def test_write_evidence_writes_clean_artifacts(tmp_path):
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=_good_env_reader, http_transport=_ok_transport)
    packet = runner.build_evidence_packet(
        plan, proof, identity, audit, start_head="h", final_head="h",
        origin_head="h", git_status_summary="changed_entries=0",
        real_getme_attempted=True)
    doc = runner.build_evidence_doc(packet)
    written = runner.write_evidence(tmp_path, packet, doc)
    assert len(written) == 2
    for path in written:
        assert Path(path).is_file()


def test_write_evidence_refuses_unsafe(tmp_path):
    bad_packet = {"leak_field": "bot_token=" + ("Z" * 40)}
    bad_doc = "ok"
    with pytest.raises(RuntimeError):
        runner.write_evidence(tmp_path, bad_packet, bad_doc)


# --------------------------------------------------------------------------- #
# main() prints only redacted classes, never the token
# --------------------------------------------------------------------------- #
def test_main_output_is_redacted(monkeypatch, tmp_path):
    # Force the runner to use a mock transport + env reader and write under
    # tmp_path, so no real network/env/token is touched and the repo is clean.
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    real_run = runner.run_identity_proof

    def fake_run(**kwargs):
        return real_run(
            operator_live_read_only_enabled=True,
            env_reader=_good_env_reader, http_transport=_ok_transport)

    monkeypatch.setattr(runner, "run_identity_proof", fake_run)
    monkeypatch.setattr(runner, "_head", lambda ref="HEAD": "deadbeef")
    monkeypatch.setattr(runner, "_git_status_summary",
                        lambda: "changed_entries=0")

    captured = io.StringIO()
    with redirect_stdout(captured):
        rc = runner.main([])
    out = captured.getvalue()
    assert rc == 0
    assert GOOD_TOKEN not in out
    assert "EVIDENCE_SCAN_CLEAN" in out
    assert "REAL_GETME_ATTEMPTED True" in out


# --------------------------------------------------------------------------- #
# Optional --from-dotenv credential source (runner-side only)
# --------------------------------------------------------------------------- #
def test_load_dotenv_token_reads_only_token_key(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'TELEGRAM_BOT_TOKEN="' + GOOD_TOKEN + '"\n'
        'TEST_TELEGRAM_CHANNEL="-100123"\n'
        '# a comment line\n'
        '{\n'
        '  "type": "service_account",\n'
        '  "private_key": "-----BEGIN PRIVATE KEY-----\\nABC\\n"\n'
        '}\n',
        encoding="utf-8")
    assert runner.load_dotenv_token(env_file) == GOOD_TOKEN


def test_load_dotenv_token_missing_file_or_key(tmp_path):
    assert runner.load_dotenv_token(tmp_path / "nope.env") is None
    env_file = tmp_path / ".env"
    env_file.write_text('TEST_TELEGRAM_CHANNEL="-100"\n', encoding="utf-8")
    assert runner.load_dotenv_token(env_file) is None


def test_make_dotenv_credentials_routes_only_allowed_var():
    env_reader, transport = runner.make_dotenv_credentials(
        GOOD_TOKEN, timeout_seconds=5)
    assert env_reader(pilot.ALLOWED_ENV_VAR) == GOOD_TOKEN
    assert env_reader("SOME_OTHER_VAR") is None
    assert callable(transport)


def test_make_dotenv_credentials_missing_token_fail_closed():
    env_reader, transport = runner.make_dotenv_credentials(None)
    assert env_reader(pilot.ALLOWED_ENV_VAR) is None
    # The fail-closed transport must never be invoked; the pilot blocks first.
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=env_reader, http_transport=transport)
    assert identity["read_only_request_performed"] is False
    assert pilot.BLOCK_CREDENTIAL_MISSING in proof["blocked_reasons"]


def test_dotenv_sourced_live_path_is_scanner_clean(tmp_path):
    # Use the dotenv-derived env_reader with an injected OK transport so no real
    # network occurs, and confirm the evidence stays tokenless + scanner-clean
    # and is labeled with the dotenv credential source.
    env_reader, _ = runner.make_dotenv_credentials(GOOD_TOKEN)
    plan, proof, identity, audit = runner.run_identity_proof(
        operator_live_read_only_enabled=True,
        env_reader=env_reader, http_transport=_ok_transport)
    packet = runner.build_evidence_packet(
        plan, proof, identity, audit, start_head="h", final_head="h",
        origin_head="h", git_status_summary="changed_entries=0",
        real_getme_attempted=True,
        credential_source_class=runner.CREDENTIAL_SOURCE_DOTENV)
    doc = runner.build_evidence_doc(packet)
    blob = json.dumps(packet) + doc
    assert GOOD_TOKEN not in blob
    assert packet["credential_source_class"] == runner.CREDENTIAL_SOURCE_DOTENV
    assert runner.scan_evidence(packet, doc) == []
    assert runner.scan_for_financial_advice_safe(packet, doc) == []
