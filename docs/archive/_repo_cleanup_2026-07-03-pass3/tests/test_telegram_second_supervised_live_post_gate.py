"""Network-free tests for the 0174CR Telegram second supervised live-post gate.

All tests use an injected ``_api_caller`` (or fail before any caller) so NO real
network request is ever made. A spy caller records call count to prove the
request budget of exactly one and no-retry semantics.
"""

import copy
import json

import pytest

from live_contentops import telegram_second_supervised_live_post_gate as gate
from live_contentops import telegram_supervised_post_dry_run_gate as dryrun


# --------------------------------------------------------------------------- #
# Helpers / fixtures
# --------------------------------------------------------------------------- #
class SpyCaller:
    """Records how many times it was called; returns a configurable response."""

    def __init__(self, response):
        self.response = response
        self.calls = 0
        self.methods = []

    def __call__(self, method, token, target, text, timeout_seconds):
        self.calls += 1
        self.methods.append(method)
        return self.response


def _ok_response():
    return {"ok": True, "transport_error": False,
            "message_id_present": True, "date_present": True,
            "chat_type": "channel"}


def _valid_dry_run_ledger():
    return {
        "status": "pass",
        "gate": gate.DRY_RUN_SOURCE_GATE,
        "would_send_message": True,
        "request_attempted": False,
        "live_network_attempted": False,
        "send_message_attempted": False,
        "message_sent": False,
        "request_budget": 0,
        "live_publish_gate": "blocked_after_second_dry_run",
        "next_gate_required_before_second_live_post": True,
    }


def _kwargs(**overrides):
    """Default happy-path kwargs with all preflight inputs injected."""
    base = dict(
        live_post_flag=True,
        operator_go_flag=True,
        write_ledger=False,
        repo_root=None,
        dry_run_ledger=_valid_dry_run_ledger(),
        existing_live_ledger={},
        # Inject env-free path by short-circuiting the env read with a fake repo
        # is not possible here; tests that reach the caller pass _api_caller and a
        # repo_root that has a .env. To stay fully network/env-free, the gate-level
        # blocking tests never reach the env read. Happy-path tests inject the
        # caller AND monkeypatch the env reader (see tests below).
    )
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# Fail-closed: flags
# --------------------------------------------------------------------------- #
def test_no_flags_fail_closed_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=False, operator_go_flag=False, _api_caller=spy)
    assert out["status"] == "fail_closed"
    assert spy.calls == 0
    assert "live_post_flag_absent_fail_closed" in out["blocked_reasons"]
    assert "operator_go_flag_absent_fail_closed" in out["blocked_reasons"]


def test_only_live_flag_fail_closed_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=False, _api_caller=spy)
    assert out["status"] == "fail_closed"
    assert spy.calls == 0


def test_only_operator_go_fail_closed_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=False, operator_go_flag=True, _api_caller=spy)
    assert out["status"] == "fail_closed"
    assert spy.calls == 0


# --------------------------------------------------------------------------- #
# Blocking gates (no caller invoked)
# --------------------------------------------------------------------------- #
def test_missing_dry_run_ledger_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=None, repo_root="/nonexistent_repo_root_xyz",
        existing_live_ledger={}, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "dry_run_0174cq_ledger_missing" in out["blocked_reasons"]


def test_invalid_dry_run_state_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    bad = _valid_dry_run_ledger()
    bad["would_send_message"] = False
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=bad, existing_live_ledger={}, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "dry_run_ledger_field_mismatch:would_send_message" in out["blocked_reasons"]


def test_payload_text_mismatch_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    payload = gate.build_default_payload()
    payload["content_text"] = "Some other text entirely, not the approved live payload."
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        payload=payload, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "payload_text_not_exact_second_live_text" in out["blocked_reasons"]


def test_forbidden_language_blocks_no_caller():
    # If the approved text constant were ever altered to include a signal word,
    # the forbidden-language scan must block. Simulate via a custom payload whose
    # text we also register as the exact text monkeypatched off — instead, prove
    # the scanner itself blocks signal words through the gate's own validator.
    ok, reasons = gate.check_forbidden_language(
        "We say buy now, sell later, with a price target and stop loss.")
    assert not ok
    assert reasons


def test_approval_missing_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        live_approval_record={}, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0


def test_approval_hash_mismatch_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    rec = gate.build_default_live_approval_record()
    rec["approved_payload_hash"] = "deadbeef"
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        live_approval_record=rec, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "live_approval_hash_mismatch" in out["blocked_reasons"]
    assert out["approval_hash_matches_payload"] is False


def test_approval_wrong_state_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    rec = gate.build_default_live_approval_record()
    rec["approval_state"] = "operator_approved_for_dry_run"
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        live_approval_record=rec, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert any(r.startswith("approval_state_not_second_live_post")
               for r in out["blocked_reasons"])


def test_approval_missing_ack_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    rec = gate.build_default_live_approval_record()
    rec["understands_this_sends_live_message"] = False
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        live_approval_record=rec, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "ack_missing:understands_this_sends_live_message" in out["blocked_reasons"]


def test_kill_switch_missing_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        kill_switch_state={}, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0


def test_kill_switch_wrong_override_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    ks = gate.build_default_kill_switch_state()
    ks["one_time_live_override"] = "operator_approved_0174cn_only"
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        kill_switch_state=ks, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "one_time_live_override_not_0174cr_scoped" in out["blocked_reasons"]


def test_kill_switch_global_dispatch_not_blocked_blocks_no_caller():
    spy = SpyCaller(_ok_response())
    ks = gate.build_default_kill_switch_state()
    ks["global_live_dispatch"] = "active"
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        kill_switch_state=ks, _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "global_live_dispatch_not_blocked" in out["blocked_reasons"]


def test_existing_ledger_with_attempt_blocks_duplicate_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(),
        existing_live_ledger={"request_attempted": True, "message_sent": False},
        _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "existing_0174cr_ledger_blocks_resend" in out["blocked_reasons"]


def test_existing_ledger_with_message_sent_blocks_duplicate_no_caller():
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(),
        existing_live_ledger={"request_attempted": False, "message_sent": True},
        _api_caller=spy)
    assert out["status"] == "blocked"
    assert spy.calls == 0
    assert "existing_0174cr_ledger_blocks_resend" in out["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Happy path + response classes (env reader monkeypatched; injected caller)
# --------------------------------------------------------------------------- #
@pytest.fixture
def _fake_env(monkeypatch):
    """Make the redacted env reader return a present-but-fake token + target.

    The value never appears in output (only booleans/classes), and no network is
    touched because tests inject ``_api_caller``.
    """
    def fake_reader(repo_root, use_process_env=False):
        return ("TELEGRAM_BOT_TOKEN=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"
                "TELEGRAM_TARGET_CHAT_ID=-1000000000001\n",
                "REPO_LOCAL_DOTENV_REDACTED", True)
    monkeypatch.setattr(gate.readiness, "_read_repo_env_source", fake_reader)


def test_happy_path_calls_caller_exactly_once(_fake_env):
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        _api_caller=spy)
    assert out["status"] == "pass"
    assert spy.calls == 1
    assert spy.methods == ["sendMessage"]
    assert out["request_count"] == 1
    assert out["request_budget"] == 1
    assert out["message_sent"] is True
    assert out["telegram_response_ok_class"] == "true"
    assert out["message_id_present"] is True
    assert out["chat_type_class"] == "channel"


def test_request_budget_is_one_and_no_retry(_fake_env):
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        _api_caller=spy)
    assert out["request_budget"] == 1
    assert out["no_retry"] is True
    assert out["second_attempt_made"] is False
    assert spy.calls == 1


def test_response_ok_true_pass_with_redacted_classes(_fake_env):
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        _api_caller=spy)
    assert out["status"] == "pass"
    # Only redacted classes/booleans present.
    assert out["telegram_response_ok_class"] == "true"
    assert isinstance(out["message_id_present"], bool)
    assert isinstance(out["date_present"], bool)


def test_transport_error_blocks_with_one_call_no_retry(_fake_env):
    spy = SpyCaller({"ok": False, "transport_error": True,
                     "message_id_present": False, "date_present": False,
                     "chat_type": None})
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        _api_caller=spy)
    assert out["status"] == "blocked"
    assert out["request_count"] == 1
    assert spy.calls == 1
    assert out["telegram_response_ok_class"] == "transport_error"
    assert out["message_sent"] is False


def test_response_ok_false_blocks_with_one_call_no_retry(_fake_env):
    spy = SpyCaller({"ok": False, "transport_error": False,
                     "message_id_present": False, "date_present": False,
                     "chat_type": None})
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True,
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        _api_caller=spy)
    assert out["status"] == "blocked"
    assert out["request_count"] == 1
    assert spy.calls == 1
    assert out["telegram_response_ok_class"] == "false"
    assert out["message_sent"] is False


# --------------------------------------------------------------------------- #
# Ledger write + determinism
# --------------------------------------------------------------------------- #
def test_write_ledger_creates_only_expected_path(tmp_path, monkeypatch):
    def fake_reader(repo_root, use_process_env=False):
        return ("TELEGRAM_BOT_TOKEN=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"
                "TELEGRAM_TARGET_CHAT_ID=-1000000000001\n",
                "REPO_LOCAL_DOTENV_REDACTED", True)
    monkeypatch.setattr(gate.readiness, "_read_repo_env_source", fake_reader)
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True, write_ledger=True,
        repo_root=str(tmp_path),
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        _api_caller=spy)
    assert out["status"] == "pass"
    assert out["ledger_written"] is True
    out_path = tmp_path / gate.LEDGER_REL_DIR / gate.LEDGER_FILENAME
    assert out_path.exists()
    created = [p.name for p in (tmp_path / gate.LEDGER_REL_DIR).iterdir()]
    assert created == [gate.LEDGER_FILENAME]


def test_preview_does_not_write(tmp_path, monkeypatch):
    def fake_reader(repo_root, use_process_env=False):
        return ("TELEGRAM_BOT_TOKEN=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"
                "TELEGRAM_TARGET_CHAT_ID=-1000000000001\n",
                "REPO_LOCAL_DOTENV_REDACTED", True)
    monkeypatch.setattr(gate.readiness, "_read_repo_env_source", fake_reader)
    spy = SpyCaller(_ok_response())
    out = gate.run_second_supervised_live_post_gate(
        live_post_flag=True, operator_go_flag=True, write_ledger=False,
        repo_root=str(tmp_path),
        dry_run_ledger=_valid_dry_run_ledger(), existing_live_ledger={},
        _api_caller=spy)
    assert out["ledger_written"] is False
    assert not (tmp_path / gate.LEDGER_REL_DIR).exists()


def test_ledger_serialization_deterministic():
    ledger = gate.build_ledger(
        payload_hash=gate.compute_payload_hash(gate.build_default_payload()),
        approval_ok=True, response_class="true", request_attempted=True,
        request_count=1, send_message_attempted=True, message_sent=True,
        message_id_present=True, date_present=True, chat_type_class="channel",
        pre_live_commit=gate.SOURCE_BASELINE_COMMIT, status="pass",
        blocked_reasons=[])
    s1 = gate.serialize_ledger(ledger)
    s2 = gate.serialize_ledger(ledger)
    assert s1 == s2
    assert s1.endswith("\n")
    parsed = json.loads(s1)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_ledger_never_persists_id_date_target_credential():
    ledger = gate.build_ledger(
        payload_hash=gate.compute_payload_hash(gate.build_default_payload()),
        approval_ok=True, response_class="true", request_attempted=True,
        request_count=1, send_message_attempted=True, message_sent=True,
        message_id_present=True, date_present=True, chat_type_class="channel",
        pre_live_commit=gate.SOURCE_BASELINE_COMMIT, status="pass",
        blocked_reasons=[])
    assert ledger["message_id_value_persisted"] is False
    assert ledger["date_value_persisted"] is False
    assert ledger["target_identifier_persisted"] is False
    assert ledger["raw_request_persisted"] is False
    assert ledger["raw_response_persisted"] is False
    assert ledger["credential_persisted"] is False
    # And the redaction scanner passes on the real ledger.
    assert gate.scan_ledger_for_leaks(ledger) == []


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
    for k in gate._FORBIDDEN_KEYS:
        bad = {k: "whatever"}
        assert any(v == f"forbidden_key:{k}" for v in gate.scan_ledger_for_leaks(bad)), k


def test_known_safe_identifiers_not_flagged():
    assert gate._is_known_safe_identifier(gate.SOURCE_BASELINE_COMMIT)
    assert gate._is_known_safe_identifier("a" * 64)


# --------------------------------------------------------------------------- #
# Payload + exact text + forbidden-language on the real approved text
# --------------------------------------------------------------------------- #
def test_exact_payload_text_matches_constant():
    payload = gate.build_default_payload()
    assert payload["content_text"] == gate.SECOND_LIVE_PAYLOAD_TEXT


def test_real_payload_passes_forbidden_language():
    ok, reasons = gate.check_forbidden_language(gate.SECOND_LIVE_PAYLOAD_TEXT)
    assert ok, reasons


def test_real_payload_under_telegram_limit():
    assert len(gate.SECOND_LIVE_PAYLOAD_TEXT) <= gate.TELEGRAM_TEXT_LIMIT


def test_payload_text_does_not_say_no_live_send():
    # Distinct from the 0174CQ dry-run text which says "no live send".
    assert "no live send" not in gate.SECOND_LIVE_PAYLOAD_TEXT.lower()


# --------------------------------------------------------------------------- #
# Forbidden methods never built
# --------------------------------------------------------------------------- #
def test_allowed_method_is_send_message_only():
    assert gate.ALLOWED_METHOD == "sendMessage"
    assert gate.ALLOWED_METHOD not in gate.FORBIDDEN_METHODS


def test_forbidden_methods_include_all_disallowed():
    for m in ("getMe", "getChat", "getChatMember", "getUpdates", "setWebhook",
              "deleteWebhook", "getWebhookInfo", "sendPhoto", "sendMediaGroup",
              "copyMessage", "forwardMessage", "editMessageText", "deleteMessage",
              "pinChatMessage", "sendPoll", "sendChatAction"):
        assert m in gate.FORBIDDEN_METHODS, m


def test_default_caller_rejects_forbidden_method_without_network():
    # Calling the real default caller with a forbidden method must short-circuit
    # to a transport_error WITHOUT performing a network request.
    resp = gate._default_api_caller("getMe", "tok", "tgt", "text", 1)
    assert resp["transport_error"] is True
    assert resp["ok"] is False
