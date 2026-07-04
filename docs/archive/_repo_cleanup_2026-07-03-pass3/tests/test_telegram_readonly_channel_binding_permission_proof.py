import pytest

from live_contentops import telegram_readonly_channel_binding_permission_proof as gate


class ScriptedCaller:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, token, params=None):
        self.calls.append((method, params))
        if not self.responses:
            raise AssertionError("unexpected API call")
        response = self.responses.pop(0)
        if callable(response):
            return response(method, params)
        return response


def env(**values):
    return values


def ok(method, result):
    return gate.TelegramReadonlyRawResultEnvelope(True, method, 200, {"ok": True, "result": result})


def fail(method):
    return gate.TelegramReadonlyRawResultEnvelope(False, method, 400, None, "error_redacted")


def success_responses(member=None):
    return [
        ok("getMe", {"id": 123456789, "is_bot": True}),
        ok("getChat", {"id": -1001234567890, "type": "channel"}),
        ok("getChatMember", member or {"status": "administrator", "can_post_messages": True}),
    ]


def run_with(responses, env_values=None):
    caller = ScriptedCaller(responses)
    result = gate.run_telegram_readonly_channel_binding_permission_proof(
        operator_go=True,
        execution_requested=True,
        env_provider=lambda: env_values or env(TELEGRAM_BOT_TOKEN="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi", TELEGRAM_CHANNEL_ID="@CapitalChronicleExample"),
        api_caller=caller,
    )
    return result, caller


def test_probe_plan_is_exact_three_readonly_methods_with_params():
    plan = gate.build_telegram_readonly_probe_plan()

    assert plan.allowed_host == "api.telegram.org"
    assert plan.allowed_methods == ("getMe", "getChat", "getChatMember")
    assert plan.param_allowlist == {"getMe": (), "getChat": ("chat_id",), "getChatMember": ("chat_id", "user_id")}
    assert plan.request_budget_max == 3
    assert plan.timeout_seconds == 10
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
        gate.validate_telegram_readonly_allowlist(method, params={})


def test_host_mismatch_fails_closed():
    with pytest.raises(gate.TelegramReadonlyProofError):
        gate.validate_telegram_readonly_allowlist("getMe", host="evil.example", params=None)


def test_param_allowlist_accepts_exact_shapes():
    gate.validate_telegram_readonly_allowlist("getMe", params=None)
    gate.validate_telegram_readonly_allowlist("getMe", params={})
    gate.validate_telegram_readonly_allowlist("getChat", params={"chat_id": "present"})
    gate.validate_telegram_readonly_allowlist("getChatMember", params={"chat_id": "present", "user_id": "present"})


@pytest.mark.parametrize(
    "method,params",
    [
        ("getMe", {"chat_id": "x"}),
        ("getChat", {}),
        ("getChat", {"chat_id": "x", "extra": "y"}),
        ("getChatMember", {"chat_id": "x"}),
        ("getChatMember", {"chat_id": "x", "user_id": "y", "extra": "z"}),
        ("getChat", {"chat_id": "x", "token": "bad"}),
        ("getChat", {"chat_id": "x", "raw_url": "bad"}),
        ("getChat", {"chat_id": "x", "authorization_header": "bad"}),
    ],
)
def test_param_allowlist_rejects_missing_extra_and_secret_params(method, params):
    with pytest.raises(gate.TelegramReadonlyProofError):
        gate.validate_telegram_readonly_allowlist(method, params=params)


def test_request_budget_cannot_exceed_three():
    gate.validate_telegram_readonly_request_budget(3)
    with pytest.raises(gate.TelegramReadonlyProofError):
        gate.validate_telegram_readonly_request_budget(4)


def test_missing_operator_go_blocks_before_network():
    def fail_api(*_args, **_kwargs):
        raise AssertionError("api should not be called")

    result = gate.run_telegram_readonly_channel_binding_permission_proof(
        execution_requested=True,
        env_provider=lambda: env(TELEGRAM_BOT_TOKEN="x", TELEGRAM_CHANNEL_ID="y"),
        api_caller=fail_api,
    )

    assert result["result_classification"] == gate.BLOCKED_OPERATOR_GO_REQUIRED
    assert result["request_budget_used"] == 0


def test_missing_execution_flag_blocks_before_network():
    def fail_api(*_args, **_kwargs):
        raise AssertionError("api should not be called")

    result = gate.run_telegram_readonly_channel_binding_permission_proof(
        operator_go=True,
        env_provider=lambda: env(TELEGRAM_BOT_TOKEN="x", TELEGRAM_CHANNEL_ID="y"),
        api_caller=fail_api,
    )

    assert result["result_classification"] == gate.BLOCKED_EXECUTION_FLAG_REQUIRED
    assert result["request_budget_used"] == 0


def test_missing_telegram_bot_token_blocks_before_network():
    def fail_api(*_args, **_kwargs):
        raise AssertionError("api should not be called")

    result = gate.run_telegram_readonly_channel_binding_permission_proof(
        operator_go=True,
        execution_requested=True,
        env_provider=lambda: env(TELEGRAM_CHANNEL_ID="present"),
        api_caller=fail_api,
    )

    assert result["result_classification"] == gate.BLOCKED_MISSING_CREDENTIAL
    assert result["request_budget_used"] == 0
    assert result["credential_key_presence"]["TELEGRAM_BOT_TOKEN"] is False


def test_missing_telegram_channel_id_blocks_before_getchat():
    def fail_api(*_args, **_kwargs):
        raise AssertionError("api should not be called")

    result = gate.run_telegram_readonly_channel_binding_permission_proof(
        operator_go=True,
        execution_requested=True,
        env_provider=lambda: env(TELEGRAM_BOT_TOKEN="present"),
        api_caller=fail_api,
    )

    assert result["result_classification"] == gate.BLOCKED_MISSING_CHANNEL_ID
    assert result["request_budget_used"] == 0
    assert result["channel_key_presence"]["TELEGRAM_CHANNEL_ID"] is False


def test_aliases_selected_only_if_primary_missing_key_name_only():
    result, caller = run_with(
        success_responses(),
        env(TELEGRAM_BOT_API_TOKEN="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi", TELEGRAM_CHAT_ID="@CapitalChronicleExample"),
    )

    assert result["result_classification"] == gate.PASS_READONLY_PROOF
    assert result["selected_credential_key_name"] == "TELEGRAM_BOT_API_TOKEN"
    assert result["selected_channel_key_name"] == "TELEGRAM_CHAT_ID"
    assert "123456:" not in str(result)
    assert "@CapitalChronicleExample" not in str(result)
    assert [call[0] for call in caller.calls] == ["getMe", "getChat", "getChatMember"]


def test_primary_key_preferred_over_alias():
    result, _caller = run_with(
        success_responses(),
        env(
            TELEGRAM_BOT_TOKEN="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
            TELEGRAM_BOT_API_TOKEN="123456:aliasABCDEFGHIJKLMNOPQRSTUVWXYZ",
            TELEGRAM_CHANNEL_ID="@CapitalChronicleExample",
            TELEGRAM_CHAT_ID="@AliasChannel",
        ),
    )

    assert result["selected_credential_key_name"] == "TELEGRAM_BOT_TOKEN"
    assert result["selected_channel_key_name"] == "TELEGRAM_CHANNEL_ID"


def test_getme_failure_stops_before_getchat():
    result, caller = run_with([fail("getMe")])

    assert result["result_classification"] == gate.BLOCKED_GETME_FAILED
    assert [call[0] for call in caller.calls] == ["getMe"]
    assert result["request_budget_used"] == 1


def test_getme_success_without_bot_id_stops_before_getchatmember():
    result, caller = run_with([ok("getMe", {"is_bot": True})])

    assert result["result_classification"] == gate.BLOCKED_GETME_FAILED
    assert [call[0] for call in caller.calls] == ["getMe"]
    assert result["request_budget_used"] == 1


def test_getchat_failure_stops_before_getchatmember():
    result, caller = run_with([ok("getMe", {"id": 123456789, "is_bot": True}), fail("getChat")])

    assert result["result_classification"] == gate.BLOCKED_GETCHAT_FAILED
    assert [call[0] for call in caller.calls] == ["getMe", "getChat"]
    assert result["request_budget_used"] == 2


def test_getchat_non_channel_stops_before_getchatmember():
    result, caller = run_with([
        ok("getMe", {"id": 123456789, "is_bot": True}),
        ok("getChat", {"id": 123456789, "type": "group"}),
    ])

    assert result["result_classification"] == gate.BLOCKED_NOT_CHANNEL
    assert [call[0] for call in caller.calls] == ["getMe", "getChat"]
    assert result["request_budget_used"] == 2


def test_getchatmember_failure_blocks():
    result, caller = run_with([
        ok("getMe", {"id": 123456789, "is_bot": True}),
        ok("getChat", {"id": -1001234567890, "type": "channel"}),
        fail("getChatMember"),
    ])

    assert result["result_classification"] == gate.BLOCKED_GETCHATMEMBER_FAILED
    assert [call[0] for call in caller.calls] == ["getMe", "getChat", "getChatMember"]
    assert result["request_budget_used"] == 3


def test_member_non_admin_blocks():
    result, _caller = run_with(success_responses({"status": "member"}))

    assert result["result_classification"] == gate.BLOCKED_BOT_NOT_ADMIN
    assert result["request_budget_used"] == 3


def test_admin_without_can_post_messages_blocks():
    result, _caller = run_with(success_responses({"status": "administrator", "can_post_messages": False}))

    assert result["result_classification"] == gate.BLOCKED_BOT_CANNOT_POST_MESSAGES
    assert result["request_budget_used"] == 3


def test_admin_with_can_post_messages_passes_readonly_proof_candidate():
    result, caller = run_with(success_responses())

    assert [call[0] for call in caller.calls] == ["getMe", "getChat", "getChatMember"]
    assert result["result_classification"] == gate.PASS_READONLY_PROOF
    assert result["request_budget_used"] == 3
    assert result["live_write_allowed_now"] is False
    assert result["send_permission_unlocked_now"] is False
    gate.assert_no_telegram_secret_output(result)


def test_result_classification_matches_request_state_and_no_zero_request_pass(tmp_path):
    result = gate.run_telegram_readonly_channel_binding_permission_proof(
        operator_go=True,
        execution_requested=True,
        write=True,
        repo_root=tmp_path,
        env_provider=lambda: env(),
    )
    evidence = __import__("json").loads((tmp_path / gate.PACKET_REL_DIR / "evidence_packet.json").read_text(encoding="utf-8"))

    assert result["request_budget_used"] == 0
    assert result["result_classification"] == gate.BLOCKED_MISSING_CREDENTIAL
    assert evidence["status"] == gate.BLOCKED_MISSING_CREDENTIAL
    assert evidence["request_budget_used"] == 0


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
