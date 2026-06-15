"""Network-free, env-free tests for the 0174CS reconciliation gate.

All tests inject a ledger dict or use tmp_path; none touch the network or env.
"""

import json

import pytest

from live_contentops import telegram_second_live_post_reconciliation_gate as gate


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _accepted_0174cr_ledger():
    """A faithful copy of the accepted 0174CR ledger, with the metadata bug."""
    return {
        "allowed_method": "sendMessage",
        "approval_hash_matches_payload": True,
        "approval_record_present": True,
        "autonomous_replies_enabled": False,
        "blocked_reasons": [],
        "credential_persisted": False,
        "date_present": True,
        "date_value_persisted": False,
        "dry_run_source_gate": "TELEGRAM_SECOND_SUPERVISED_POST_DRY_RUN_LEDGER_0174CQ",
        "gate": "TELEGRAM_SECOND_SUPERVISED_LIVE_POST_0174CR",
        "get_updates_enabled": False,
        "host_allowlist_passed": True,
        "live_publish_gate": "blocked_after_second_live_pilot",
        "message_id_present": True,
        "message_id_value_persisted": False,
        "message_sent": True,
        "method_allowlist_passed": True,
        "metrics_fetch_enabled": False,
        "next_gate_required_before_any_future_live_post": True,
        "no_retry": True,
        "one_time_live_override_class": "operator_approved_0174cr_only",
        "one_time_operator_go_present": True,
        "payload_hash":
            "2f7cd6d38aa84ef8a9c810d27a65bdd58fd87267d1f3742c219f2455ef9767b7",
        "payload_text": (
            "Capital Chronicle ContentOps second supervised Telegram pilot: "
            "human-approved publish controls remain gated. Local-first workflow "
            "validation continues. No financial advice, no trading calls, no "
            "automation."
        ),
        "payload_text_persisted": True,
        "platform": "telegram",
        "pre_live_implementation_commit":
            "0a38e91f1b5e6b4c94d2322ffa8b78d99449fbe3",
        "prior_chain": {
            "first_live_post_delivered_once": True,
            "first_post_pilot_ledger_persisted": True,
            "next_platform_selection_accepted": True,
            "second_dry_run_ledger_accepted": True,
            "telegram_identity_validated": True,
            "telegram_target_binding_validated": True,
        },
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "redaction_verified": True,
        "request_attempted": True,
        "request_budget": 1,
        "request_count": 1,
        "scheduler_enabled": False,
        "second_attempt_made": False,
        "send_message_attempted": True,
        "source_baseline_commit": "0a38e91f1b5e6b4c94d2322ffa8b78d99449fbe3",
        "status": "pass",
        "target_identifier_persisted": False,
        "task_label":
            "TASK_CONTENTOPS_0174CR_TELEGRAM_SECOND_SUPERVISED_LIVE_POST_"
            "OPERATOR_GO_GATE_V0",
        "telegram_response_ok_class": "true",
        "webhook_enabled": False,
    }


# --------------------------------------------------------------------------- #
# Preview vs write
# --------------------------------------------------------------------------- #
def test_preview_does_not_write(tmp_path):
    ledger_dir = tmp_path / "docs" / "credential_readiness" / "0174CR"
    ledger_dir.mkdir(parents=True)
    (ledger_dir / gate.PACKET_FILENAME)  # noop
    out = gate.run_reconciliation_gate(
        write=False, repo_root=str(tmp_path),
        ledger=_accepted_0174cr_ledger())
    assert out["status"] == "pass"
    assert out["ledger_written"] is False
    assert out["packet_written"] is False
    assert out["readme_written"] is False
    assert not (tmp_path / "docs" / "credential_readiness" / "0174CS").exists()


def test_write_creates_only_allowed_artifacts(tmp_path):
    # Seed the existing 0174CR ledger on disk so the corrected one overwrites it.
    ledger_dir = tmp_path / "docs" / "credential_readiness" / "0174CR"
    ledger_dir.mkdir(parents=True)
    ledger_path = ledger_dir / "telegram_second_supervised_live_post_ledger.json"
    ledger_path.write_text(gate.serialize(_accepted_0174cr_ledger()),
                           encoding="utf-8")
    out = gate.run_reconciliation_gate(write=True, repo_root=str(tmp_path))
    assert out["status"] == "pass"
    assert out["ledger_written"] is True
    assert out["packet_written"] is True
    assert out["readme_written"] is True
    cs_dir = tmp_path / "docs" / "credential_readiness" / "0174CS"
    created = sorted(p.name for p in cs_dir.iterdir())
    assert created == sorted([gate.PACKET_FILENAME, gate.README_FILENAME])


# --------------------------------------------------------------------------- #
# Correction correctness
# --------------------------------------------------------------------------- #
def test_correction_changes_only_allowed_keys():
    before = _accepted_0174cr_ledger()
    after = gate.apply_correction(before)
    ok, illegal = gate.correction_only_touches_allowed_keys(before, after)
    assert ok, illegal


def test_live_result_fields_remain_unchanged():
    before = _accepted_0174cr_ledger()
    after = gate.apply_correction(before)
    for key, expected in gate.IMMUTABLE_LIVE_FIELDS.items():
        assert after.get(key) == expected, key
    for key in gate.IMMUTABLE_CONTENT_FIELDS:
        assert after.get(key) == before.get(key), key


def test_canonical_pre_live_commit_is_corrected():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert after["pre_live_implementation_commit"] == gate.CORRECTED_PRE_LIVE_COMMIT


def test_original_incorrect_value_recorded_in_ledger():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert (after["original_pre_live_implementation_commit_recorded"]
            == gate.ORIGINAL_PRE_LIVE_COMMIT_RECORDED)
    assert after["reconciliation_reason"] == gate.CORRECTION_REASON
    assert after["live_result_fields_changed"] is False
    assert after["redaction_contract_preserved"] is True


def test_packet_records_original_incorrect_value(tmp_path):
    ledger_dir = tmp_path / "docs" / "credential_readiness" / "0174CR"
    ledger_dir.mkdir(parents=True)
    (ledger_dir / "telegram_second_supervised_live_post_ledger.json").write_text(
        gate.serialize(_accepted_0174cr_ledger()), encoding="utf-8")
    gate.run_reconciliation_gate(write=True, repo_root=str(tmp_path))
    packet_path = (tmp_path / "docs" / "credential_readiness" / "0174CS"
                   / gate.PACKET_FILENAME)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert (packet["original_pre_live_implementation_commit_recorded"]
            == gate.ORIGINAL_PRE_LIVE_COMMIT_RECORDED)
    assert (packet["corrected_pre_live_implementation_commit"]
            == gate.CORRECTED_PRE_LIVE_COMMIT)


# --------------------------------------------------------------------------- #
# Post-live lock + immutable accepted values
# --------------------------------------------------------------------------- #
def test_post_live_lock_state_remains_blocked():
    out = gate.run_reconciliation_gate(
        write=False, repo_root="/nope", ledger=_accepted_0174cr_ledger())
    rm = out["operator_roadmap"]
    assert rm["live_posting_state"] == "blocked_until_new_explicit_task_and_operator_go"
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert after["live_publish_gate"] == "blocked_after_second_live_pilot"
    assert after["next_gate_required_before_any_future_live_post"] is True


def test_request_count_remains_one():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert after["request_count"] == 1


def test_request_budget_remains_one():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert after["request_budget"] == 1


def test_no_retry_remains_true():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert after["no_retry"] is True


def test_second_attempt_made_remains_false():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert after["second_attempt_made"] is False


def test_persist_flags_remain_false():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    for key in ("message_id_value_persisted", "date_value_persisted",
                "raw_request_persisted", "raw_response_persisted",
                "credential_persisted"):
        assert after[key] is False, key


# --------------------------------------------------------------------------- #
# Blocking: tampered live fields block correction write
# --------------------------------------------------------------------------- #
def test_tampered_live_field_blocks():
    bad = _accepted_0174cr_ledger()
    bad["message_sent"] = False
    out = gate.run_reconciliation_gate(
        write=False, repo_root="/nope", ledger=bad)
    assert out["status"] == "blocked"
    assert any(r.startswith("live_field_mismatch:message_sent")
               for r in out["blocked_reasons"])


def test_missing_ledger_blocks(tmp_path):
    out = gate.run_reconciliation_gate(write=False, repo_root=str(tmp_path))
    assert out["status"] == "blocked"
    assert "ledger_0174cr_missing_or_unparseable" in out["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def test_redaction_scanner_blocks_token_like_value():
    bad = {"x": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789ab"}
    assert any(v.startswith("secret_like_value")
               for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_raw_telegram_url():
    bad = {"x": "https://api.telegram.org/botXXXX/sendMessage"}
    assert any(v.startswith("telegram_url")
               for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_raw_handle():
    bad = {"x": "post to @capitalchronicle now"}
    assert any(v.startswith("raw_handle")
               for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_long_numeric_id():
    bad = {"x": "chat is -1001234567890 here"}
    assert any(v.startswith("long_digits_possible_id")
               for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_forbidden_raw_keys():
    for k in gate._FORBIDDEN_KEYS:
        bad = {k: "whatever"}
        assert any(v == f"forbidden_key:{k}"
                   for v in gate.scan_ledger_for_leaks(bad)), k


def test_known_safe_identifiers_not_flagged():
    assert gate._is_known_safe_identifier(gate.SOURCE_BASELINE_COMMIT)
    assert gate._is_known_safe_identifier(gate.CORRECTED_PRE_LIVE_COMMIT)
    assert gate._is_known_safe_identifier(gate.ORIGINAL_PRE_LIVE_COMMIT_RECORDED)
    assert gate._is_known_safe_identifier("a" * 40)
    assert gate._is_known_safe_identifier("a" * 64)


def test_real_packet_passes_redaction_scan():
    packet = gate.build_reconciliation_packet(
        ledger=gate.apply_correction(_accepted_0174cr_ledger()),
        correction_applied=True, live_fields_ok=True,
        current_ledger_checksum="a" * 64, status="pass", blocked_reasons=[])
    assert gate.scan_ledger_for_leaks(packet) == []


def test_corrected_ledger_passes_redaction_scan():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    assert gate.scan_ledger_for_leaks(after) == []


# --------------------------------------------------------------------------- #
# No network imports / no env reads (static source checks)
# --------------------------------------------------------------------------- #
def test_module_has_no_network_imports():
    import inspect
    src = inspect.getsource(gate)
    for bad in ("import urllib", "import requests", "import httpx",
                "import socket", "import dotenv", "from urllib",
                "from requests", "from httpx", "from socket"):
        assert bad not in src, bad


def test_module_has_no_env_reads():
    import inspect
    src = inspect.getsource(gate)
    assert "os.environ" not in src
    assert "os.getenv" not in src


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_serialization_deterministic():
    after = gate.apply_correction(_accepted_0174cr_ledger())
    s1 = gate.serialize(after)
    s2 = gate.serialize(after)
    assert s1 == s2
    assert s1.endswith("\n")
    parsed = json.loads(s1)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_roadmap_next_task_is_0174ct():
    rm = gate.build_operator_roadmap()
    assert rm["recommended_next_task"] == (
        "TASK_CONTENTOPS_0174CT_OPERATOR_LIVE_PUBLISHING_REVIEW_AND_"
        "PLATFORM_REQUIREMENTS_BACKLOG_V0")

