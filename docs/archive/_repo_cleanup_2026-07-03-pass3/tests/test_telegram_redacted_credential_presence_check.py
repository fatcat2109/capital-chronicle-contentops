import json
import live_contentops.telegram_redacted_credential_presence_check as chk

# Clearly-fake synthetic values. NOT real credentials. Used only to exercise
# classification/presence logic; they must never leak into emitted output.
FAKE_TOKEN = "111111:FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE_xx"
FAKE_CHAT_ID = "-1009999999999"
FAKE_HANDLE = "@fake_test_channel"


def _both_present_env():
    return f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n"


def test_missing_env_source_blocked_no_values():
    s = chk.summary(env_text=None, source_label=None)
    assert s["packet_status"] == "blocked"
    assert s["env_source_missing_or_unavailable"] is True
    assert s["telegram_bot_token_present"] is None
    assert s["telegram_target_chat_id_present"] is None
    assert s["telegram_bot_token_shape_class"] == "not_checked_blocked"
    assert s["telegram_target_chat_id_shape_class"] == "not_checked_blocked"
    assert "approved_local_env_source_unavailable" in s["blocked_reasons"]


def test_both_present_returns_true_and_redacted_classes():
    s = chk.summary(env_text=_both_present_env(), source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED")
    assert s["packet_status"] == "pass"
    assert s["validation_valid"] is True
    assert s["telegram_bot_token_present"] is True
    assert s["telegram_target_chat_id_present"] is True
    assert s["telegram_bot_token_shape_class"] == "present_redacted_telegram_bot_token_like"
    assert s["telegram_target_chat_id_shape_class"] == "present_redacted_integer_like"


def test_missing_token_only():
    env = f"TELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n"
    s = chk.summary(env_text=env)
    assert s["telegram_bot_token_present"] is False
    assert s["telegram_target_chat_id_present"] is True
    assert s["telegram_bot_token_shape_class"] == "absent"


def test_missing_chat_id_only():
    env = f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\n"
    s = chk.summary(env_text=env)
    assert s["telegram_bot_token_present"] is True
    assert s["telegram_target_chat_id_present"] is False
    assert s["telegram_target_chat_id_shape_class"] == "absent"


def test_empty_whitespace_not_present():
    env = "TELEGRAM_BOT_TOKEN=   \nTELEGRAM_TARGET_CHAT_ID=\n"
    s = chk.summary(env_text=env)
    assert s["telegram_bot_token_present"] is False
    assert s["telegram_target_chat_id_present"] is False
    assert s["telegram_bot_token_shape_class"] == "present_redacted_empty_or_whitespace"
    assert s["telegram_target_chat_id_shape_class"] == "present_redacted_empty_or_whitespace"


def test_channel_handle_chat_id():
    env = f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_HANDLE}\n"
    s = chk.summary(env_text=env)
    assert s["telegram_target_chat_id_shape_class"] == "present_redacted_channel_handle_like"


def test_no_raw_values_in_packet_or_summary():
    env = _both_present_env()
    packet = chk.build_presence_check(env_text=env, source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED")
    s = chk.summary(env_text=env)
    blob = json.dumps(packet) + json.dumps(s)
    assert FAKE_TOKEN not in blob
    assert FAKE_CHAT_ID not in blob
    assert FAKE_HANDLE not in blob


def test_no_prefix_suffix_length_or_digest_emitted():
    env = _both_present_env()
    s = chk.summary(env_text=env)
    blob = json.dumps(s)
    assert "111111" not in blob
    assert "FAKEFAKE" not in blob
    assert s["exact_length_reported"] is False
    assert s["hash_or_digest_reported"] is False
    assert s["token_snippet_reported"] is False
    assert s["chat_id_snippet_reported"] is False


def test_telegram_api_flags_false():
    s = chk.summary(env_text=_both_present_env())
    assert s["telegram_api_allowed_now"] is False
    assert s["telegram_api_called"] is False
    assert s["credential_validation_enabled_now"] is False


def test_live_flags_false():
    s = chk.summary(env_text=_both_present_env())
    assert s["live_adapter_enabled_now"] is False
    assert s["live_posting_enabled_now"] is False
    assert s["scheduler_allowed_now"] is False
    assert s["platform_api_allowed_now"] is False
    assert s["final_social_copy_generated"] is False



def test_secret_scanner_rejects_leaked_value():
    packet = chk._base_packet()
    packet["blocked_reasons"] = ["123456:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789xx"]
    res = chk.validate_telegram_redacted_credential_presence_check_packet(packet)
    assert res["valid"] is False
    assert any("secret_like_value_detected" in e for e in res["errors"])


def test_ignores_unrelated_env_keys():
    env = (
        "OPENAI_API_KEY=should_be_ignored\n"
        "SOME_OTHER=zzz\n"
        f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\n"
        f"TELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n"
    )
    packet = chk.build_presence_check(env_text=env, source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED")
    blob = json.dumps(packet)
    assert "OPENAI_API_KEY" not in blob
    assert "SOME_OTHER" not in blob
    assert "should_be_ignored" not in blob


def test_parse_warnings_do_not_expose_line_contents():
    env = "this_is_an_invalid_line_without_equals\nTELEGRAM_BOT_TOKEN=" + FAKE_TOKEN + "\n"
    packet = chk.build_presence_check(env_text=env, source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED")
    blob = json.dumps(packet)
    assert "this_is_an_invalid_line_without_equals" not in blob
    assert packet.get("env_parse_warnings_present") is True


def test_packet_status_pass_with_errors_flagged():
    p = chk._base_packet()
    p["telegram_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = chk.validate_telegram_redacted_credential_presence_check_packet(p)
    assert res["valid"] is False
    assert any("telegram_api_allowed_now_must_be_false" in e for e in res["errors"])
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_required_true_enforced():
    p = chk._base_packet()
    p["manual_review_required"] = False
    res = chk.validate_telegram_redacted_credential_presence_check_packet(p)
    assert res["valid"] is False
    assert any("manual_review_required_must_be_true" in e for e in res["errors"])

