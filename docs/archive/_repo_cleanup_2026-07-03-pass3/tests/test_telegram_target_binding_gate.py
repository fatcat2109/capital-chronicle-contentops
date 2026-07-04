import json

from live_contentops import telegram_target_binding_gate as g

# Clearly-fake synthetic values used ONLY in tests. Not real credentials.
FAKE_TOKEN = "111111:FAKEFAKEfakefakeFAKEfakefakeFAKEfake12"
FAKE_CHANNEL_ID = "-1009999999999"
FAKE_HANDLE = "@somefakechannelhandle"
FAKE_BOT_UID = 424242


def _write_env(tmp_path, body):
    (tmp_path / ".env").write_text(body, encoding="utf-8")
    return str(tmp_path)


def _full_env(tmp_path, target=FAKE_CHANNEL_ID):
    return _write_env(
        tmp_path,
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={target}\n",
    )


def _token_only_env(tmp_path):
    return _write_env(tmp_path, f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\n")


def _empty_env(tmp_path):
    return _write_env(tmp_path, "SOMETHING_ELSE=1\n")


class _ScriptedCaller:
    """Injectable caller returning scripted redacted responses keyed by method.

    Records the ordered list of methods called and the bot_user_id forwarded to
    getChatMember, so tests can assert the exact bounded 3-request sequence.
    """

    def __init__(self, *, me=None, chat=None, member=None):
        self.me = me if me is not None else {
            "ok": True, "transport_error": False, "bot_user_id": FAKE_BOT_UID}
        self.chat = chat if chat is not None else {
            "ok": True, "transport_error": False, "chat_type": "channel"}
        self.member = member if member is not None else {
            "ok": True, "transport_error": False,
            "member_status": "administrator", "can_post_messages": True}
        self.calls = []
        self.seen_user_id = None
        self.seen_token = None
        self.seen_target = None

    def __call__(self, method, token, target, timeout_seconds, bot_user_id=None):
        self.calls.append(method)
        self.seen_token = token
        self.seen_target = target
        if method == "getMe":
            return dict(self.me)
        if method == "getChat":
            return dict(self.chat)
        if method == "getChatMember":
            self.seen_user_id = bot_user_id
            return dict(self.member)
        return {"ok": False, "transport_error": True}


# --- fail-closed -------------------------------------------------------------

def test_not_armed_skips_request(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=False, repo_root=root, _api_caller=caller)
    assert s["armed"] is False
    assert s["request_attempted"] is False
    assert s["request_count"] == 0
    assert s["status"] == "fail_closed"
    assert caller.calls == []
    assert any("not_armed" in r for r in s["blocked_reasons"])


def test_env_unavailable_fails_closed(tmp_path):
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=str(tmp_path), _api_caller=caller)
    assert s["status"] == "fail_closed"
    assert s["request_attempted"] is False
    assert caller.calls == []
    assert any("unavailable" in r for r in s["blocked_reasons"])


def test_token_absent_fails_closed(tmp_path):
    root = _write_env(tmp_path, f"TELEGRAM_TARGET_CHAT_ID={FAKE_CHANNEL_ID}\n")
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "fail_closed"
    assert caller.calls == []
    assert any("token_absent" in r for r in s["blocked_reasons"])


def test_target_slot_absent_fails_closed(tmp_path):
    root = _token_only_env(tmp_path)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "fail_closed"
    assert s["target_slot_present"] is False
    assert caller.calls == []
    assert any("target_slot_absent" in r for r in s["blocked_reasons"])


def test_target_invalid_shape_fails_closed(tmp_path):
    root = _full_env(tmp_path, target="not a valid target!!")
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "fail_closed"
    assert s["target_identifier_shape_class"] == g.TARGET_INVALID
    assert caller.calls == []
    assert any("invalid_shape" in r for r in s["blocked_reasons"])


# --- success path ------------------------------------------------------------

def test_channel_admin_can_post_passes(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "pass"
    assert caller.calls == ["getMe", "getChat", "getChatMember"]
    assert s["request_count"] == 3
    assert s["request_budget"] == 3
    assert s["host_allowlist_passed"] is True
    assert s["method_allowlist_passed"] is True
    assert s["target_chat_reachable"] is True
    assert s["target_chat_type_class"] == g.CHAT_TYPE_CHANNEL
    assert s["bot_membership_checked"] is True
    assert s["bot_member_status_class"] == g.STATUS_ADMINISTRATOR
    assert s["can_post_messages_class"] == g.CPM_TRUE
    assert s["future_supervised_publish_possible_after_remaining_gates"] is True


def test_channel_creator_passes_without_cpm(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(member={
        "ok": True, "transport_error": False,
        "member_status": "creator", "can_post_messages": None})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "pass"
    assert s["bot_member_status_class"] == g.STATUS_CREATOR
    assert s["can_post_messages_class"] == g.CPM_TRUE
    assert s["future_supervised_publish_possible_after_remaining_gates"] is True


def test_handle_target_accepted_shape(tmp_path):
    root = _full_env(tmp_path, target=FAKE_HANDLE)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["target_identifier_shape_class"] == g.TARGET_PRESENT
    assert s["status"] == "pass"


# --- channel-only semantics --------------------------------------------------

def test_non_channel_supergroup_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(
        chat={"ok": True, "transport_error": False, "chat_type": "supergroup"},
        member={"ok": True, "transport_error": False,
                "member_status": "administrator", "can_post_messages": None})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert s["target_chat_type_class"] == g.CHAT_TYPE_SUPERGROUP
    assert s["can_post_messages_class"] == g.CPM_NOT_APPLICABLE
    assert s["future_supervised_publish_possible_after_remaining_gates"] is False
    assert "target_type_not_channel_for_supervised_channel_publish_gate" in s["blocked_reasons"]


def test_non_channel_private_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(
        chat={"ok": True, "transport_error": False, "chat_type": "private"},
        member={"ok": True, "transport_error": False,
                "member_status": "member", "can_post_messages": None})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert s["target_chat_type_class"] == g.CHAT_TYPE_PRIVATE
    assert s["can_post_messages_class"] == g.CPM_NOT_APPLICABLE
    assert "target_type_not_channel_for_supervised_channel_publish_gate" in s["blocked_reasons"]


def test_non_channel_group_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(
        chat={"ok": True, "transport_error": False, "chat_type": "group"})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert s["target_chat_type_class"] == g.CHAT_TYPE_GROUP
    assert s["future_supervised_publish_possible_after_remaining_gates"] is False


# --- channel permission shortfalls -------------------------------------------

def test_channel_admin_without_post_permission_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(member={
        "ok": True, "transport_error": False,
        "member_status": "administrator", "can_post_messages": False})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert s["can_post_messages_class"] == g.CPM_FALSE
    assert s["future_supervised_publish_possible_after_remaining_gates"] is False
    assert any("channel_post_permission_absent" in r for r in s["blocked_reasons"])


def test_channel_admin_cpm_unavailable_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(member={
        "ok": True, "transport_error": False,
        "member_status": "administrator", "can_post_messages": None})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert s["can_post_messages_class"] == g.CPM_UNAVAILABLE
    assert s["future_supervised_publish_possible_after_remaining_gates"] is False


def test_channel_plain_member_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(member={
        "ok": True, "transport_error": False,
        "member_status": "member", "can_post_messages": None})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert s["can_post_messages_class"] == g.CPM_NOT_APPLICABLE
    assert any("not_channel_poster" in r for r in s["blocked_reasons"])


# --- API error paths (redacted) ----------------------------------------------

def test_getme_failure_blocks_before_getchat(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(me={"ok": False, "transport_error": True})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert caller.calls == ["getMe"]
    assert s["request_count"] == 1
    assert any("getme" in r for r in s["blocked_reasons"])


def test_getme_missing_uid_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(me={"ok": True, "transport_error": False, "bot_user_id": None})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert caller.calls == ["getMe"]
    assert any("bot_user_id_unavailable" in r for r in s["blocked_reasons"])


def test_getchat_unreachable_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(chat={"ok": False, "transport_error": False})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert caller.calls == ["getMe", "getChat"]
    assert s["target_chat_reachable"] is False
    assert any("unreachable" in r for r in s["blocked_reasons"])


def test_getchat_transport_error_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(chat={"ok": False, "transport_error": True})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert any("getchat_transport_error" in r for r in s["blocked_reasons"])


def test_getchatmember_failure_blocks(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller(member={"ok": False, "transport_error": True})
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["status"] == "blocked"
    assert caller.calls == ["getMe", "getChat", "getChatMember"]
    assert s["bot_membership_checked"] is False
    assert any("getchatmember_transport_error" in r for r in s["blocked_reasons"])


# --- request budget / wiring -------------------------------------------------

def test_bot_user_id_forwarded_to_getchatmember(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller()
    g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert caller.seen_user_id == FAKE_BOT_UID
    assert caller.seen_token == FAKE_TOKEN


def test_budget_never_exceeds_three(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert len(caller.calls) <= 3
    assert s["request_count"] <= 3


# --- redaction + locked policy flags -----------------------------------------

def test_no_secret_url_or_handle_emitted(tmp_path):
    root = _full_env(tmp_path, target=FAKE_HANDLE)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    blob = json.dumps(s)
    assert FAKE_TOKEN not in blob
    assert FAKE_HANDLE not in blob
    assert "api.telegram.org/bot" not in blob


def test_channel_id_not_emitted(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    blob = json.dumps(s)
    assert FAKE_CHANNEL_ID not in blob


def test_locked_policy_flags_remain_false(tmp_path):
    root = _full_env(tmp_path)
    caller = _ScriptedCaller()
    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=caller)
    assert s["posting_enabled"] is False
    assert s["send_message_enabled"] is False
    assert s["get_updates_enabled"] is False
    assert s["webhook_enabled"] is False
    assert s["scheduler_enabled"] is False
    assert s["autonomous_replies_enabled"] is False
    assert s["metrics_fetch_enabled"] is False
    assert s["live_publish_gate"] == "blocked"
    assert s["next_gate_required_before_posting"] is True


def test_redaction_guard_scrubs_leaked_handle(tmp_path):
    root = _full_env(tmp_path)

    def leaking_caller(method, token, target, timeout_seconds, bot_user_id=None):
        if method == "getMe":
            return {"ok": True, "transport_error": False, "bot_user_id": FAKE_BOT_UID}
        if method == "getChat":
            # Simulate a buggy caller surfacing a raw handle into a field.
            return {"ok": True, "transport_error": False, "chat_type": "@leakedhandle"}
        return {"ok": True, "transport_error": False,
                "member_status": "administrator", "can_post_messages": True}

    s = g.run_target_binding_gate(armed=True, repo_root=root, _api_caller=leaking_caller)
    blob = json.dumps(s)
    assert "@leakedhandle" not in blob


def test_method_allowlist_contains_only_read_methods():
    assert g.ALLOWED_METHODS == ("getMe", "getChat", "getChatMember")
    for m in g.ALLOWED_METHODS:
        assert m not in g.FORBIDDEN_METHODS
    for forbidden in ("sendMessage", "getUpdates", "setWebhook", "banChatMember"):
        assert forbidden in g.FORBIDDEN_METHODS


def test_timeout_forwarded(tmp_path):
    root = _full_env(tmp_path)
    seen = {}

    def caller(method, token, target, timeout_seconds, bot_user_id=None):
        seen["timeout"] = timeout_seconds
        if method == "getMe":
            return {"ok": True, "transport_error": False, "bot_user_id": FAKE_BOT_UID}
        if method == "getChat":
            return {"ok": True, "transport_error": False, "chat_type": "channel"}
        return {"ok": True, "transport_error": False,
                "member_status": "creator", "can_post_messages": True}

    g.run_target_binding_gate(armed=True, repo_root=root, timeout_seconds=7, _api_caller=caller)
    assert seen["timeout"] == 7
