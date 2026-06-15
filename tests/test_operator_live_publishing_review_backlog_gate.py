"""Network-free tests for the 0174CT operator live-publishing review + backlog gate.

These tests never touch the network and never read env/credentials. The module
under test imports ONLY hashlib, json, os.path, re (asserted below), so there is
no transport or dotenv surface at all.
"""

import ast
import os

import pytest

from live_contentops import operator_live_publishing_review_backlog_gate as gate


# --------------------------------------------------------------------------- #
# Fixtures: redacted prior-ledger stand-ins (booleans/classes only)
# --------------------------------------------------------------------------- #
def _first_ledger():
    return {
        "request_count": 1,
        "request_budget": 1,
        "message_id_value_persisted": False,
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "status": "pass",
    }


def _second_ledger():
    return {
        "request_count": 1,
        "request_budget": 1,
        "no_retry": True,
        "second_attempt_made": False,
        "message_id_value_persisted": False,
        "raw_request_persisted": False,
        "raw_response_persisted": False,
        "status": "pass",
    }


def _run(**overrides):
    base = dict(
        write=False,
        first_ledger=_first_ledger(),
        second_ledger=_second_ledger(),
    )
    base.update(overrides)
    return gate.run_review_backlog_gate(**base)


# --------------------------------------------------------------------------- #
# Write behavior
# --------------------------------------------------------------------------- #
def test_default_preview_does_not_write(tmp_path):
    out = _run(repo_root=str(tmp_path))
    assert out["status"] == "pass"
    assert out["write_requested"] is False
    assert out["packet_written"] is False
    assert out["readme_written"] is False
    assert not (tmp_path / gate.PACKET_REL_DIR).exists()


def test_explicit_write_creates_packet_path(tmp_path):
    out = _run(write=True, repo_root=str(tmp_path))
    assert out["status"] == "pass"
    assert out["packet_written"] is True
    assert out["readme_written"] is True
    packet_path = tmp_path / gate.PACKET_REL_DIR / gate.PACKET_FILENAME
    readme_path = tmp_path / gate.PACKET_REL_DIR / gate.README_FILENAME
    assert packet_path.exists()
    assert readme_path.exists()
    # Deterministic serialization ends with a trailing newline.
    assert packet_path.read_text(encoding="utf-8").endswith("\n")


# --------------------------------------------------------------------------- #
# Packet content
# --------------------------------------------------------------------------- #
def test_packet_contains_accepted_chain_fields():
    packet = gate.build_packet(
        live_pilot_summary=gate.build_live_pilot_summary(
            _first_ledger(), _second_ledger()),
        status="pass", blocked_reasons=[])
    chain = packet["accepted_chain"]
    for key in (
        "telegram_identity_validated",
        "telegram_target_binding_validated",
        "first_dry_run_preflight_accepted",
        "first_live_post_delivered_once",
        "first_post_pilot_ledger_persisted",
        "next_platform_selection_accepted",
        "second_dry_run_ledger_accepted",
        "second_live_post_delivered_once",
        "second_live_post_ledger_reconciled",
        "test_isolation_repair_accepted",
    ):
        assert chain[key] is True, key


def test_packet_confirms_two_telegram_pilots():
    summary = gate.build_live_pilot_summary(_first_ledger(), _second_ledger())
    assert summary["telegram_live_pilot_count"] == 2
    assert summary["both_live_posts_redacted_ledgers_present"] is True
    assert summary["both_live_posts_request_count_one"] is True
    assert summary["both_live_posts_no_retry"] is True
    assert summary["both_live_posts_message_id_value_not_persisted"] is True
    assert summary["both_live_posts_raw_request_response_not_persisted"] is True
    assert summary["first_live_task"] == gate.FIRST_LIVE_TASK
    assert summary["second_live_task"] == gate.SECOND_LIVE_TASK


def test_packet_confirms_current_live_posting_state_blocked():
    posture = gate.build_current_operator_posture()
    assert posture["live_posting_state"] == \
        "blocked_until_new_explicit_task_and_operator_go"
    assert posture["immediate_recommendation"] == \
        "pause_additional_live_sends_and_review"
    for flag in ("global_scheduler_enabled", "webhook_enabled",
                 "get_updates_enabled", "autonomous_replies_enabled",
                 "metrics_fetch_enabled", "scraping_enabled",
                 "generic_publisher_enabled"):
        assert posture[flag] is False, flag


def test_packet_includes_all_four_backlog_items():
    backlog = gate.build_platform_requirements_backlog()
    assert set(backlog.keys()) == {
        "telegram_pause_and_review",
        "telegram_third_gate_later",
        "x_requirements_only",
        "linkedin_requirements_only",
    }


def test_each_backlog_item_has_required_fields():
    backlog = gate.build_platform_requirements_backlog()
    required = (
        "objective", "allowed_now", "forbidden_now", "required_before_live",
        "credential_policy", "account_binding_policy", "approval_policy",
        "redaction_policy", "test_policy", "blockers", "recommended_priority",
    )
    for name, item in backlog.items():
        for field in required:
            assert field in item, f"{name} missing {field}"


def test_packet_top_level_safety_booleans_true():
    packet = gate.build_packet(
        live_pilot_summary=gate.build_live_pilot_summary(
            _first_ledger(), _second_ledger()),
        status="pass", blocked_reasons=[])
    for flag in ("no_live_call_performed", "no_credentials_read",
                 "no_env_read", "no_account_binding_performed",
                 "no_oauth_flow_performed", "no_posting_performed",
                 "no_scheduler_created", "no_webhook_created",
                 "no_reply_dm_created", "no_metrics_fetched",
                 "no_scraping_performed", "redaction_verified"):
        assert packet[flag] is True, flag
    assert packet["gate"] == "OPERATOR_LIVE_PUBLISHING_REVIEW_BACKLOG_0174CT"
    assert packet["next_recommended_task"] == gate.NEXT_RECOMMENDED_TASK


def test_missing_prior_ledgers_downgrade_attestations_not_crash(tmp_path):
    out = gate.run_review_backlog_gate(
        write=False, repo_root=str(tmp_path),
        first_ledger=None, second_ledger=None)
    # Still passes (review packet is self-contained) but the cross-pilot
    # attestations are False when ledgers are absent.
    assert out["status"] == "pass"
    summary = out["live_pilot_summary"]
    assert summary["both_live_posts_redacted_ledgers_present"] is False
    assert summary["both_live_posts_request_count_one"] is False


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
    bad = {"x": "follow @capitalchronicle today"}
    assert any(v.startswith("raw_handle")
               for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_long_numeric_id():
    bad = {"x": "chat is -1001234567890 here"}
    assert any(v.startswith("long_digits_possible_id")
               for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_linkedin_urn():
    bad = {"x": "owner is urn:li:organization:12345"}
    assert any(v.startswith("linkedin_urn")
               for v in gate.scan_ledger_for_leaks(bad))


def test_redaction_scanner_blocks_forbidden_raw_keys():
    for k in gate._FORBIDDEN_KEYS:
        bad = {k: "whatever"}
        assert any(v == f"forbidden_key:{k}"
                   for v in gate.scan_ledger_for_leaks(bad)), k


def test_forbidden_keys_include_account_and_urn_keys():
    for k in ("account_id", "account_handle", "organization_id",
              "person_urn", "organization_urn"):
        assert k in gate._FORBIDDEN_KEYS, k


def test_real_packet_passes_redaction_scan():
    packet = gate.build_packet(
        live_pilot_summary=gate.build_live_pilot_summary(
            _first_ledger(), _second_ledger()),
        status="pass", blocked_reasons=[])
    assert gate.scan_ledger_for_leaks(packet) == []


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_deterministic_serialization():
    packet = gate.build_packet(
        live_pilot_summary=gate.build_live_pilot_summary(
            _first_ledger(), _second_ledger()),
        status="pass", blocked_reasons=[])
    s1 = gate.serialize(packet)
    s2 = gate.serialize(packet)
    assert s1 == s2
    assert s1.endswith("\n")
    import json
    parsed = json.loads(s1)
    assert list(parsed.keys()) == sorted(parsed.keys())


# --------------------------------------------------------------------------- #
# No network / no env imports (static source analysis)
# --------------------------------------------------------------------------- #
def _module_source():
    path = gate.__file__
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def test_module_has_no_network_imports():
    tree = ast.parse(_module_source())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imported.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    for forbidden in ("urllib", "requests", "httpx", "socket", "http",
                      "dotenv"):
        assert forbidden not in imported, forbidden


def test_module_has_no_env_reads():
    src = _module_source()
    assert "os.environ" not in src
    assert "os.getenv" not in src
    assert "getenv" not in src


def test_module_imports_only_allowed_stdlib():
    tree = ast.parse(_module_source())
    top = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                top.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # `import sys` is local to main(); allowed.
            if node.module:
                top.add(node.module.split(".")[0])
    # `sys` may appear as a local import inside main(); allow it.
    allowed = {"hashlib", "json", "os", "re", "sys"}
    assert top <= allowed, top - allowed


# --------------------------------------------------------------------------- #
# CLI dispatch
# --------------------------------------------------------------------------- #
def test_cli_main_runs_and_is_local(capsys):
    rc = gate.main(argv=[])
    assert rc == 0
    out = capsys.readouterr().out
    assert "OPERATOR_LIVE_PUBLISHING_REVIEW_BACKLOG_0174CT" in out
    assert "blocked_until_new_explicit_task_and_operator_go" in out
