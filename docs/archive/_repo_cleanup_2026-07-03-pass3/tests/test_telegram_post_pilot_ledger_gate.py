"""Tests for the 0174CO Telegram post-pilot ledger gate (strictly local, no network)."""

import json
import re
from pathlib import Path

import pytest

from live_contentops import telegram_post_pilot_ledger_gate as gate

EXPECTED_HASH = "b9955db3a78d0738aa99f12e8889d70bae450395b9eae58e313fd70b9d73baa1"


# --------------------------------------------------------------------------- #
# Hash recompute + verification
# --------------------------------------------------------------------------- #
def test_recomputed_payload_hash_equals_expected():
    ok, recomputed = gate.verify_payload_hash()
    assert ok is True
    assert recomputed == EXPECTED_HASH


def test_hash_mismatch_blocks_and_writes_nothing(monkeypatch):
    monkeypatch.setattr(gate, "EXPECTED_PAYLOAD_HASH", "0" * 64)
    writes = []
    result = gate.run_post_pilot_ledger_gate(
        write=True, _writer=lambda p, t: writes.append((p, t)))
    assert result["status"] == "blocked"
    assert result["payload_hash_verified"] is False
    assert "payload_hash_mismatch_block_no_write" in result["blocked_reasons"]
    assert writes == []
    assert result["ledger_written"] is False


# --------------------------------------------------------------------------- #
# Write / preview behavior
# --------------------------------------------------------------------------- #
def test_default_no_write_path_creates_no_file():
    writes = []
    result = gate.run_post_pilot_ledger_gate(
        write=False, _writer=lambda p, t: writes.append((p, t)))
    assert result["status"] == "fail_closed"
    assert result["ledger_written"] is False
    assert writes == []
    assert "write_flag_absent_preview_only" in result["blocked_reasons"]


def test_explicit_write_flag_writes_ledger(tmp_path):
    writes = {}
    result = gate.run_post_pilot_ledger_gate(
        write=True, repo_root=str(tmp_path),
        _writer=lambda p, t: writes.__setitem__(p, t))
    assert result["status"] == "pass"
    assert result["ledger_written"] is True
    assert result["ledger_path"] == "docs/credential_readiness/0174CO/telegram_post_pilot_ledger_0174cn.json"
    assert len(writes) == 1
    # The written path ends with the expected ledger filename.
    written_path = next(iter(writes))
    assert written_path.endswith("telegram_post_pilot_ledger_0174cn.json")


def test_real_write_creates_file_at_expected_path(tmp_path):
    result = gate.run_post_pilot_ledger_gate(write=True, repo_root=str(tmp_path))
    assert result["status"] == "pass"
    target = tmp_path / "docs" / "credential_readiness" / "0174CO" / "telegram_post_pilot_ledger_0174cn.json"
    assert target.is_file()
    text = target.read_text(encoding="utf-8")
    assert text.endswith("\n")
    loaded = json.loads(text)
    assert loaded["ledger_gate"] == "TELEGRAM_POST_PILOT_LEDGER_0174CO"
    assert loaded["payload_hash"] == EXPECTED_HASH


# --------------------------------------------------------------------------- #
# Deterministic serialization
# --------------------------------------------------------------------------- #
def test_ledger_serialization_is_deterministic():
    ok, recomputed = gate.verify_payload_hash()
    ledger = gate.build_ledger_record(recomputed, ok)
    a = gate.serialize_ledger(ledger)
    b = gate.serialize_ledger(ledger)
    assert a == b
    assert a.endswith("\n")
    # sorted keys: re-dumping the parsed object with sort_keys must match (minus newline).
    assert json.loads(a) == ledger
    assert json.dumps(ledger, sort_keys=True, separators=(",", ":"), ensure_ascii=False) == a.rstrip("\n")


def test_ledger_checksum_stable():
    ok, recomputed = gate.verify_payload_hash()
    ledger = gate.build_ledger_record(recomputed, ok)
    serialized = gate.serialize_ledger(ledger)
    assert gate.ledger_checksum(serialized) == gate.ledger_checksum(serialized)
    assert re.fullmatch(r"[0-9a-f]{64}", gate.ledger_checksum(serialized))


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def test_redaction_scanner_clean_ledger_has_no_violations():
    ok, recomputed = gate.verify_payload_hash()
    ledger = gate.build_ledger_record(recomputed, ok)
    assert gate.scan_ledger_for_leaks(ledger) == []


def test_redaction_scanner_blocks_token_like_value():
    ledger = {"x": "123456789:AAH" + "a" * 32}
    violations = gate.scan_ledger_for_leaks(ledger)
    assert any(v.startswith("secret_like_value") for v in violations)


def test_redaction_scanner_blocks_raw_telegram_url():
    ledger = {"x": "https://api.telegram.org/botSOMETHING/sendMessage"}
    violations = gate.scan_ledger_for_leaks(ledger)
    assert any(v.startswith("telegram_url") for v in violations)


def test_redaction_scanner_blocks_raw_handle():
    ledger = {"x": "see @capitalchronicle channel"}
    violations = gate.scan_ledger_for_leaks(ledger)
    assert any(v.startswith("raw_handle") for v in violations)


def test_redaction_scanner_blocks_forbidden_keys():
    for key in ("token", "chat_id", "channel_id", "channel_username",
                "bot_id", "bot_username", "message_id", "raw_response",
                "raw_request", "raw_url", "date"):
        violations = gate.scan_ledger_for_leaks({key: "x"})
        assert f"forbidden_key:{key}" in violations, key


def test_redaction_scanner_blocks_long_digit_id():
    violations = gate.scan_ledger_for_leaks({"x": "1234567890"})
    assert any(v.startswith("long_digits_possible_id") for v in violations)


def test_redaction_scanner_allows_payload_hash_and_commit():
    ledger = {"payload_hash": EXPECTED_HASH, "source_live_commit": gate.SOURCE_LIVE_COMMIT}
    assert gate.scan_ledger_for_leaks(ledger) == []


def test_write_blocked_when_ledger_would_leak(tmp_path, monkeypatch):
    real_builder = gate.build_ledger_record

    def leaky_builder(payload_hash, verified):
        rec = real_builder(payload_hash, verified)
        rec["leak_field"] = "contact @leakyhandle now"
        return rec

    monkeypatch.setattr(gate, "build_ledger_record", leaky_builder)
    writes = []
    result = gate.run_post_pilot_ledger_gate(
        write=True, repo_root=str(tmp_path),
        _writer=lambda p, t: writes.append((p, t)))
    assert result["status"] == "blocked"
    assert result["redaction_scan_passed"] is False
    assert writes == []


# --------------------------------------------------------------------------- #
# Ledger field contract + lock state
# --------------------------------------------------------------------------- #
def test_ledger_record_contract_fields_present_and_disabled():
    ok, recomputed = gate.verify_payload_hash()
    ledger = gate.build_ledger_record(recomputed, ok)

    assert ledger["task_label"].startswith("TASK_CONTENTOPS_0174CO_")
    assert ledger["ledger_gate"] == "TELEGRAM_POST_PILOT_LEDGER_0174CO"
    assert ledger["source_live_commit"] == "71bcd9cb79fe6039290145d438969987b2728222"
    assert ledger["platform"] == "telegram"
    assert ledger["live_result_class"] == "delivered_once_redacted"
    assert ledger["request_count"] == 1
    assert ledger["request_budget"] == 1
    assert ledger["allowed_method"] == "sendMessage"
    assert ledger["message_sent"] is True
    assert ledger["telegram_response_ok_class"] == "true"
    assert ledger["message_id_present"] is True
    assert ledger["payload_hash"] == EXPECTED_HASH
    assert ledger["payload_hash_verified"] is True
    assert ledger["approval_hash_matches_payload"] is True

    # Persistence-suppression flags.
    for f in ("message_id_value_persisted", "date_value_persisted",
              "target_identifier_persisted", "raw_response_persisted",
              "raw_request_persisted", "credential_persisted"):
        assert ledger[f] is False, f

    # Chain proof.
    for f in ("chain_0174ck_identity_validated", "chain_0174cl_target_binding_validated",
              "chain_0174cm_dry_run_preflight_validated", "chain_0174cn_live_send_passed"):
        assert ledger[f] is True, f

    # Post-pilot lock state.
    assert ledger["post_pilot_live_publish_gate"] == "blocked_after_one_time_pilot"
    assert ledger["next_gate_required_before_next_live_post"] is True
    for f in ("scheduler_enabled", "webhook_enabled", "get_updates_enabled",
              "autonomous_replies_enabled", "metrics_fetch_enabled",
              "live_dispatch_enabled_after_pilot"):
        assert ledger[f] is False, f


def test_message_id_value_is_never_persisted():
    ok, recomputed = gate.verify_payload_hash()
    ledger = gate.build_ledger_record(recomputed, ok)
    assert "message_id_value" not in ledger
    assert "message_id" not in ledger  # only message_id_present is allowed
    assert ledger["message_id_present"] is True
    assert ledger["message_id_value_persisted"] is False


def test_roadmap_stub_fields():
    stub = gate.build_roadmap_stub()
    assert stub["next_platform_binding_candidate"] == (
        "x_or_linkedin_or_telegram_second_gate_pending_operator_choice")
    assert "new explicit task" in stub["requirement_before_next_live_send"]
    for f in ("no_autonomous_publishing", "no_scheduler", "no_reply_dm",
              "no_metrics_fetch", "no_scraping"):
        assert stub[f] is True, f


def test_summary_wrapper_matches_run():
    a = gate.summary(write=False, _writer=lambda p, t: None)
    assert a["ledger_gate"] == "TELEGRAM_POST_PILOT_LEDGER_0174CO"
    assert a["network_performed"] is False
    assert a["env_read_performed"] is False


# --------------------------------------------------------------------------- #
# No network / no env in the module source
# --------------------------------------------------------------------------- #
def test_module_has_no_network_imports():
    src = Path(gate.__file__).read_text(encoding="utf-8")
    forbidden = re.compile(r"import\s+(requests|httpx|urllib|socket|dotenv)")
    assert not forbidden.search(src)


def test_module_has_no_env_reads():
    src = Path(gate.__file__).read_text(encoding="utf-8")
    assert not re.search(r"os\.(environ|getenv)", src)
