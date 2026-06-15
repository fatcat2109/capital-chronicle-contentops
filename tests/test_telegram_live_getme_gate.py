import json

from live_contentops import telegram_live_getme_gate as g

# Clearly-fake synthetic values used ONLY in tests. Not real credentials.
FAKE_TOKEN = "111111:FAKEFAKEfakefakeFAKEfakefakeFAKEfake12"
FAKE_CHAT_ID = "-1009999999999"


def _write_env(tmp_path, body):
    (tmp_path / ".env").write_text(body, encoding="utf-8")
    return str(tmp_path)


def _token_env(tmp_path):
    return _write_env(tmp_path, f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\n")


def _empty_env(tmp_path):
    return _write_env(tmp_path, "SOMETHING_ELSE=1\n")


def _ok_caller(token, timeout_seconds):
    assert token == FAKE_TOKEN
    return {"ok": True, "is_bot": True, "has_id": True, "transport_error": False}


def _ok_not_bot_caller(token, timeout_seconds):
    return {"ok": True, "is_bot": False, "has_id": True, "transport_error": False}


def _auth_fail_caller(token, timeout_seconds):
    return {"ok": False, "is_bot": False, "has_id": False, "transport_error": False}


def _transport_error_caller(token, timeout_seconds):
    return {"ok": False, "is_bot": False, "has_id": False, "transport_error": True}


class _CountingCaller:
    def __init__(self, resp):
        self.resp = resp
        self.calls = 0

    def __call__(self, token, timeout_seconds):
        self.calls += 1
        return dict(self.resp)


# --- fail-closed -------------------------------------------------------------

def test_not_armed_skips_request(tmp_path):
    root = _token_env(tmp_path)
    s = g.run_getme_gate(armed=False, repo_root=root, _api_caller=_ok_caller)
    assert s["armed"] is False
    assert s["request_attempted"] is False
    assert s["request_count"] == 0
    assert s["status"] == "blocked"
    assert any("not_armed" in r for r in s["blocked_reasons"])


def test_env_unavailable_fails_closed(tmp_path):
    # tmp_path has no .env file at all
    s = g.run_getme_gate(armed=True, repo_root=str(tmp_path), _api_caller=_ok_caller)
    assert s["status"] == "blocked"
    assert s["request_attempted"] is False
    assert any("unavailable" in r for r in s["blocked_reasons"])


def test_token_absent_blocks(tmp_path):
    root = _empty_env(tmp_path)
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=_ok_caller)
    assert s["status"] == "blocked"
    assert s["request_attempted"] is False
    assert s["token_present"] is False
    assert any("token_absent" in r for r in s["blocked_reasons"])


# --- success / failure paths -------------------------------------------------

def test_armed_success_validates_identity(tmp_path):
    root = _token_env(tmp_path)
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=_ok_caller)
    assert s["status"] == "pass"
    assert s["response_ok"] is True
    assert s["bot_identity_validated"] is True
    assert s["request_count"] == 1
    assert s["host_allowlist_passed"] is True
    assert s["method_allowlist_passed"] is True


def test_ok_but_not_bot_blocks(tmp_path):
    root = _token_env(tmp_path)
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=_ok_not_bot_caller)
    assert s["status"] == "blocked"
    assert s["response_ok"] is True
    assert s["bot_identity_validated"] is False
    assert any("identity_not_confirmed" in r for r in s["blocked_reasons"])


def test_auth_failure_redacted(tmp_path):
    root = _token_env(tmp_path)
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=_auth_fail_caller)
    assert s["status"] == "blocked"
    assert s["response_ok"] is False
    blob = json.dumps(s)
    assert FAKE_TOKEN not in blob
    assert "api.telegram.org/bot" not in blob


def test_transport_error_redacted(tmp_path):
    root = _token_env(tmp_path)
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=_transport_error_caller)
    assert s["status"] == "blocked"
    assert any("transport_error" in r for r in s["blocked_reasons"])


# --- request budget ----------------------------------------------------------

def test_default_budget_one_call(tmp_path):
    root = _token_env(tmp_path)
    caller = _CountingCaller({"ok": False, "is_bot": False, "has_id": False, "transport_error": True})
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=caller)
    assert caller.calls == 1
    assert s["request_count"] == 1
    assert s["request_budget"] == 1


def test_second_attempt_capped_at_two(tmp_path):
    root = _token_env(tmp_path)
    caller = _CountingCaller({"ok": False, "is_bot": False, "has_id": False, "transport_error": True})
    s = g.run_getme_gate(armed=True, repo_root=root, allow_second_attempt=True, _api_caller=caller)
    assert caller.calls == 2
    assert s["request_count"] == 2
    assert s["request_budget"] == 2


def test_success_does_not_consume_second_attempt(tmp_path):
    root = _token_env(tmp_path)
    caller = _CountingCaller({"ok": True, "is_bot": True, "has_id": True, "transport_error": False})
    s = g.run_getme_gate(armed=True, repo_root=root, allow_second_attempt=True, _api_caller=caller)
    assert caller.calls == 1
    assert s["status"] == "pass"


# --- redaction + locked policy flags -----------------------------------------

def test_no_secret_or_url_emitted(tmp_path):
    root = _token_env(tmp_path)
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=_ok_caller)
    blob = json.dumps(s)
    assert FAKE_TOKEN not in blob
    assert "api.telegram.org/bot" not in blob


def test_locked_policy_flags_remain_false(tmp_path):
    root = _token_env(tmp_path)
    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=_ok_caller)
    assert s["posting_enabled"] is False
    assert s["send_message_enabled"] is False
    assert s["get_updates_enabled"] is False
    assert s["webhook_enabled"] is False
    assert s["channel_write_validated"] is False
    assert s["scheduler_enabled"] is False
    assert s["autonomous_replies_enabled"] is False
    assert s["metrics_fetch_enabled"] is False
    assert s["live_publish_gate"] == "blocked"
    assert s["manual_review_required"] is True
    assert s["next_gate_required_before_posting"] is True


def test_redaction_guard_scrubs_leaked_token(tmp_path):
    root = _token_env(tmp_path)

    def leaking_caller(token, timeout_seconds):
        # Simulate a buggy caller trying to surface a token-like string.
        return {"ok": True, "is_bot": True, "has_id": True,
                "transport_error": False, "leak": "999999:" + ("A" * 35)}

    s = g.run_getme_gate(armed=True, repo_root=root, _api_caller=leaking_caller)
    # The summary itself never stores caller extras, so no leak reaches output.
    blob = json.dumps(s)
    assert "999999:" not in blob


def test_method_allowlist_is_getme_only():
    assert g.ALLOWED_METHOD == "getMe"
    assert g.ALLOWED_METHOD not in g.FORBIDDEN_METHODS


def test_only_getme_token_passed_to_caller(tmp_path):
    root = _token_env(tmp_path)
    seen = {}

    def caller(token, timeout_seconds):
        seen["token"] = token
        seen["timeout"] = timeout_seconds
        return {"ok": True, "is_bot": True, "has_id": True, "transport_error": False}

    g.run_getme_gate(armed=True, repo_root=root, timeout_seconds=7, _api_caller=caller)
    assert seen["token"] == FAKE_TOKEN
    assert seen["timeout"] == 7
