import pytest

from live_contentops import telegram_readonly_channel_binding_permission_proof as gate


class FakeCaller:
    def __init__(self):
        self.calls = []

    def __call__(self, method, token, params=None):
        self.calls.append((method, params))
        if method == "getMe":
            return gate.TelegramReadonlyRawResultEnvelope(
                ok=True,
                method=method,
                status_code=200,
                body={"ok": True, "result": {"id": 123456789, "is_bot": True}},
            )
        if method == "getChat":
            return gate.TelegramReadonlyRawResultEnvelope(
                ok=True,
                method=method,
                status_code=200,
                body={"ok": True, "result": {"id": -1001234567890, "type": "channel"}},
            )
        if method == "getChatMember":
            return gate.TelegramReadonlyRawResultEnvelope(
                ok=True,
                method=method,
                status_code=200,
                body={
                    "ok": True,
                    "result": {
                        "status": "administrator",
                        "can_post_messages": True,
                    },
                },
            )
        raise AssertionError(method)


def test_probe_plan_is_exact_three_readonly_methods():
    plan = gate.build_telegram_readonly_probe_plan()

    assert plan.allowed_host == "api.telegram.org"
    assert plan.allowed_methods == ("getMe", "getChat", "getChatMember")
    assert plan.request_budget_max == 3
    assert plan.retry_allowed is False
    assert plan.raw_response_persisted is False
    assert plan.token_persisted is False
    assert plan.live_write_allowed_now is False
    assert [step.telegram_method for step in plan.steps] == ["getMe", "getChat", "getChatMember"]
    assert all(step.read_only for step in plan.steps)
    assert not any(step.write_allowed for step in plan.steps)


@pytest.mark.parametrize("method", ["sendMessage", "sendPhoto", "editMessageText", "deleteMessage", "pinChatMessage"])
def test_write_methods_fail_closed(method):
    with pytest.raises(gate.TelegramReadonlyProofError):
        gate.validate_telegram_readonly_allowlist(method)


def test_host_mismatch_fails_closed():
    with pytest.raises(gate.TelegramReadonlyProofError):
        gate.validate_telegram_readonly_allowlist("getMe", host="evil.example")


def test_request_budget_cannot_exceed_three():
    gate.validate_telegram_readonly_request_budget(3)
    with pytest.raises(gate.TelegramReadonlyProofError):
        gate.validate_telegram_readonly_request_budget(4)


def test_chat_and_member_classification():
    assert gate.classify_telegram_chat_type({"type": "channel"}) == "telegram_channel_confirmed_redacted"
    assert gate.classify_telegram_chat_type({"type": "private"}) == "telegram_private_not_channel_redacted"

    membership, is_admin, can_post = gate.classify_telegram_member_permission(
        {"status": "administrator", "can_post_messages": True}
    )
    assert membership == "bot_channel_administrator_confirmed_redacted"
    assert is_admin is True
    assert can_post is True

    membership, is_admin, can_post = gate.classify_telegram_member_permission({"status": "member"})
    assert membership == "bot_channel_member_not_admin_redacted"
    assert is_admin is False
    assert can_post is False


def test_redacted_live_readonly_success_keeps_write_locked():
    fake = FakeCaller()
    result = gate.run_telegram_readonly_channel_binding_permission_proof(
        operator_go=True,
        execution_requested=True,
        token_provider=lambda: "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
        chat_provider=lambda: "@CapitalChronicleExample",
        api_caller=fake,
    )

    assert [call[0] for call in fake.calls] == ["getMe", "getChat", "getChatMember"]
    assert result["status"] == "pass_redacted_readonly_proof"
    assert result["request_count"] == 3
    assert result["channel_binding_status"] == "channel_binding_confirmed_redacted"
    assert result["channel_permission_status"] == "can_post_messages_confirmed_redacted"
    assert result["live_write_allowed_now"] is False
    assert result["send_permission_unlocked_now"] is False
    gate.assert_no_telegram_secret_output(result)


def test_default_no_flags_does_not_call_live_api():
    def fail_api(*_args, **_kwargs):
        raise AssertionError("api should not be called")

    result = gate.run_telegram_readonly_channel_binding_permission_proof(api_caller=fail_api)

    assert result["status"] == "blocked"
    assert result["request_count"] == 0
    assert "operator_go_required" in result["blockers"]
    assert "execution_flag_required" in result["blockers"]


@pytest.mark.parametrize(
    "payload",
    [
        {"token": "redacted"},
        {"value": "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"},
        {"value": "https://api.telegram.org/bot123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi/getMe"},
        {"chat_id": "redacted"},
        {"value": "@RawHandle"},
        {"value": "-1001234567890"},
    ],
)
def test_secret_shape_scanner_blocks_sensitive_outputs(payload):
    with pytest.raises(gate.TelegramReadonlyProofError):
        gate.assert_no_telegram_secret_output(payload)
