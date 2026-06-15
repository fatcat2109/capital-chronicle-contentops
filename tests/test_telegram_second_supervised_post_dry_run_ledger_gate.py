"""Network-free tests for the 0174CQ Telegram second supervised dry-run ledger gate."""

import json
import os

import pytest

from live_contentops import telegram_second_supervised_post_dry_run_ledger_gate as gate


# --------------------------------------------------------------------------- #
# Preview / write behavior
# --------------------------------------------------------------------------- #
def test_default_preview_does_not_write(tmp_path):
    out_dir = tmp_path / gate.LEDGER_REL_DIR
    summary = gate.run_gate(write=False, repo_root=str(tmp_path))
    assert summary["status"] == "pass"
    assert summary["write_requested"] is False
    assert summary["ledger_written"] is False
    assert not out_dir.exists()


def test_explicit_write_creates_expected_ledger_path(tmp_path):
    summary = gate.run_gate(write=True, repo_root=str(tmp_path))
    assert summary["status"] == "pass"
    assert summary["ledger_written"] is True
    out_path = tmp_path / gate.LEDGER_REL_DIR / gate.LEDGER_FILENAME
    assert out_path.exists()
    # Only the ledger artifact is created under the 0174CQ dir.
    created = list((tmp_path / gate.LEDGER_REL_DIR).iterdir())
    assert [p.name for p in created] == [gate.LEDGER_FILENAME]


def test_write_mode_writes_only_ledger_no_other_dirs(tmp_path):
    gate.run_gate(write=True, repo_root=str(tmp_path))
    # docs/credential_readiness/0174CQ is the only path branch created.
    cr = tmp_path / "docs" / "credential_readiness"
    assert [p.name for p in cr.iterdir()] == ["0174CQ"]


# --------------------------------------------------------------------------- #
# Determinism + hashing
# --------------------------------------------------------------------------- #
def test_deterministic_json_serialization():
    ledger, _ = gate.build_ledger()
    s1 = gate.serialize_ledger(ledger)
    s2 = gate.serialize_ledger(ledger)
    assert s1 == s2
    assert s1.endswith("\n")
    # sorted keys
    parsed = json.loads(s1)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_payload_hash_stable_and_approval_hash_matches():
    payload = gate.build_second_dry_run_payload()
    h1 = gate.compute_payload_hash(payload)
    h2 = gate.compute_payload_hash(gate.build_second_dry_run_payload())
    assert h1 == h2
    approval = gate.build_approval_record(h1)
    ok, reasons = gate.validate_approval_record(approval, h1)
    assert ok, reasons
    assert approval["approved_payload_hash"] == h1


def test_approval_hash_mismatch_detected():
    ok, reasons = gate.validate_approval_record(
        gate.build_approval_record("deadbeef"), "not_the_same_hash")
    assert not ok
    assert "approval_hash_mismatch" in reasons


def test_ledger_checksum_stable():
    ledger, _ = gate.build_ledger()
    assert gate.compute_ledger_checksum(ledger) == gate.compute_ledger_checksum(ledger)


# --------------------------------------------------------------------------- #
# Forbidden-language blocks before pass
# --------------------------------------------------------------------------- #
def test_forbidden_language_blocks_before_ledger_pass():
    # The 0174CM scanner must flag a signal word; ledger must not be 'pass'.
    ok, reasons = gate.cm_gate.check_forbidden_language(
        "We say buy now and sell later with a price target.")
    assert not ok
    assert reasons


def test_real_payload_passes_forbidden_language():
    ok, reasons = gate.cm_gate.check_forbidden_language(
        gate.SECOND_DRY_RUN_PAYLOAD_TEXT)
    assert ok, reasons


def test_payload_text_states_local_only_dry_run_no_live_send():
    ok, reasons = gate.validate_payload_text(gate.SECOND_DRY_RUN_PAYLOAD_TEXT)
    assert ok, reasons


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def test_redaction_scanner_blocks_token_like_value():
    bad = {"x": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789ab"}
    assert any(v.startswith("secret_like_value") for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_raw_telegram_url():
    bad = {"x": "https://api.telegram.org/botXXXX/sendMessage"}
    assert any(v.startswith("telegram_url") for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_raw_handle():
    bad = {"x": "post to @capitalchronicle now"}
    assert any(v.startswith("raw_handle") for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_long_numeric_id():
    bad = {"x": "chat is -1001234567890 here"}
    assert any(v.startswith("long_digits_possible_id") for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_forbidden_raw_keys():
    for k in ("token", "bot_token", "chat_id", "channel_id", "channel_username",
              "bot_id", "bot_username", "message_id", "date", "raw_url",
              "raw_request", "raw_response", "target_identifier", "target_value",
              "access_token", "refresh_token", "client_secret", "api_key"):
        bad = {k: "whatever"}
        assert any(v == f"forbidden_key:{k}" for v in gate.scan_ledger_for_leaks(bad)), k


def test_real_ledger_passes_redaction_scan():
    ledger, _ = gate.build_ledger()
    assert gate.scan_ledger_for_leaks(ledger) == []


def test_known_safe_identifiers_not_flagged():
    assert gate._is_known_safe_identifier(gate.SOURCE_BASELINE_COMMIT)
    assert gate._is_known_safe_identifier("a" * 64)


# --------------------------------------------------------------------------- #
# No network / no env imports
# --------------------------------------------------------------------------- #
def test_module_has_no_network_imports():
    import inspect
    src = inspect.getsource(gate)
    for banned in ("import urllib", "import requests", "import httpx",
                   "import socket", "import dotenv", "from dotenv"):
        assert banned not in src, banned


def test_module_has_no_env_reads():
    import inspect
    src = inspect.getsource(gate)
    assert "environ" not in src
    assert "getenv" not in src


# --------------------------------------------------------------------------- #
# Live-behavior invariants
# --------------------------------------------------------------------------- #
def test_ledger_live_flags_disabled():
    ledger, _ = gate.build_ledger()
    assert ledger["request_attempted"] is False
    assert ledger["live_network_attempted"] is False
    assert ledger["send_message_attempted"] is False
    assert ledger["message_sent"] is False
    assert ledger["would_send_message"] is True
    assert ledger["request_budget"] == 0


def test_ledger_no_live_behavior_flags_all_true():
    ledger, _ = gate.build_ledger()
    for k in ("no_live_call_performed", "no_credentials_read", "no_env_read",
              "no_account_binding_performed", "no_oauth_flow_performed",
              "no_token_exchange_performed", "no_posting_performed",
              "no_scheduler_created", "no_webhook_created", "no_reply_dm_created",
              "no_metrics_fetched", "no_scraping_performed"):
        assert ledger[k] is True, k


def test_ledger_publish_gate_stays_blocked():
    ledger, _ = gate.build_ledger()
    assert ledger["live_publish_gate"] == "blocked_after_second_dry_run"
    assert ledger["next_gate_required_before_second_live_post"] is True
    assert ledger["status"] == "pass"


def test_prior_chain_all_true():
    ledger, _ = gate.build_ledger()
    for k, v in ledger["prior_chain"].items():
        assert v is True, k
