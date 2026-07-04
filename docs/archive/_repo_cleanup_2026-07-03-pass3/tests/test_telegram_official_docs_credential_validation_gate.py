import json
import pytest

from live_contentops import telegram_official_docs_credential_validation_gate as g

# Clearly-fake synthetic values used ONLY in tests. Not real credentials.
FAKE_TOKEN = "111111:FAKEFAKEfakefakeFAKEfakefakeFAKEfake12"
FAKE_CHAT_ID = "-1009999999999"
FAKE_HANDLE = "@fake_test_channel"

GOOD_DOCS = {
    "source_domain": "core.telegram.org",
    "verified": True,
    "fetch_count": 1,
    "notes": g.DEFAULT_OFFICIAL_DOCS_NOTES,
}


def _both_env():
    return f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\nTELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n"


def _token_only_env():
    return f"TELEGRAM_BOT_TOKEN={FAKE_TOKEN}\n"


def _chat_only_env():
    return f"TELEGRAM_TARGET_CHAT_ID={FAKE_CHAT_ID}\n"


def _fake_getme_ok(method, token):
    assert method == "getMe"
    return {"ok": True, "result": {"id": 123, "is_bot": True, "first_name": "FakeBot",
                                    "username": "fake_bot"}, "error_code": None, "description": None}


def _fake_getme_error(method, token):
    assert method == "getMe"
    return {"ok": False, "result": None, "error_code": 401, "description": "Unauthorized"}


class _BudgetCaller:
    """Counts calls so tests can assert the request budget is enforced."""

    def __init__(self):
        self.calls = 0

    def __call__(self, method, token):
        self.calls += 1


def test_valid_getme_success_both_present_passes():
    s = g.summary(env_text=_both_env(), api_caller=_fake_getme_ok,
                  source_label="OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND", fetched_docs=GOOD_DOCS)
    assert s["packet_status"] == "pass"
    assert s["validation_valid"] is True
    assert s["getme_validation_succeeded"] is True
    assert s["getme_bot_identity_confirmed"] is True
    assert s["telegram_api_request_count"] == 1
    assert s["channel_write_permission_validated"] is False
    assert s["channel_posting_validated"] is False
    assert s["next_gate_required_before_posting"] is True


def test_missing_token_blocks_getme():
    s = g.summary(env_text=_chat_only_env(), api_caller=_fake_getme_ok,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert s["packet_status"] == "blocked"
    assert s["telegram_api_called"] is False
    assert any("telegram_bot_token_absent" in r for r in s["blocked_reasons"])


def test_missing_chat_id_blocks_future_live_even_if_token_validates():
    s = g.summary(env_text=_token_only_env(), api_caller=_fake_getme_ok,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert s["getme_validation_succeeded"] is True
    assert s["packet_status"] == "blocked"
    assert any("target_chat_id_absent" in r for r in s["blocked_reasons"])


def test_fake_getme_error_is_redacted():
    s = g.summary(env_text=_both_env(), api_caller=_fake_getme_error,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert s["packet_status"] == "blocked"
    assert s["getme_validation_succeeded"] is False
    assert s["api_error_redacted"] is True
    blob = json.dumps(s)
    assert "Unauthorized" not in blob
    assert FAKE_TOKEN not in blob



def test_request_budget_only_one_getme_call():
    caller = _BudgetCaller()
    s = g.summary(env_text=_both_env(), api_caller=caller,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert caller.calls == 1
    assert s["telegram_api_request_count"] == 1
    assert s["telegram_api_request_count"] <= s["telegram_api_request_budget"]


def test_only_getme_method_is_used():
    seen = {}

    def caller(method, token):
        seen["method"] = method
        return _fake_getme_ok(method, token)

    g.summary(env_text=_both_env(), api_caller=caller,
              source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert seen["method"] == "getMe"


def test_sendmessage_and_getupdates_flags_blocked():
    s = g.summary(env_text=_both_env(), api_caller=_fake_getme_ok,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert s["sendmessage_called"] is False
    assert s["getupdates_called"] is False


def test_no_token_or_url_or_snippet_emitted():
    s = g.summary(env_text=_both_env(), api_caller=_fake_getme_ok,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    blob = json.dumps(s)
    assert FAKE_TOKEN not in blob
    assert FAKE_CHAT_ID not in blob
    assert "api.telegram.org/bot" not in blob
    assert s["request_url_printed"] is False
    assert s["raw_response_printed"] is False
    assert s["token_snippet_reported"] is False
    assert s["chat_id_snippet_reported"] is False
    assert s["exact_length_reported"] is False
    assert s["hash_or_digest_reported"] is False
    assert s["bot_id_reported"] is False
    assert s["bot_username_reported"] is False


def test_live_flags_remain_false():
    s = g.summary(env_text=_both_env(), api_caller=_fake_getme_ok,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert s["live_adapter_enabled_now"] is False
    assert s["live_posting_enabled_now"] is False
    assert s["scheduler_allowed_now"] is False
    assert s["final_social_copy_generated"] is False
    assert s["publish_all_button_enabled_now"] is False
    assert s["one_button_publish_all_enabled_now"] is False



def test_official_docs_domain_allowlist_blocks_non_core():
    bad_docs = {"source_domain": "evil.example.com", "verified": True, "fetch_count": 1}
    verified, domain, count, notes = g.verify_official_docs(fetched_docs=bad_docs)
    assert verified is False
    assert domain == "none"
    assert any("not_allowlisted" in n for n in notes)


def test_official_docs_fetch_budget_enforced():
    over = {"source_domain": "core.telegram.org", "verified": True, "fetch_count": 4}
    verified, domain, count, notes = g.verify_official_docs(fetched_docs=over)
    assert verified is False
    assert any("budget_exceeded" in n for n in notes)


def test_official_docs_verified_path():
    verified, domain, count, notes = g.verify_official_docs(fetched_docs=GOOD_DOCS)
    assert verified is True
    assert domain == "core.telegram.org"
    assert count <= g.OFFICIAL_DOCS_FETCH_BUDGET


def test_packet_status_pass_with_errors_flagged():
    p = g._base_packet()
    p["live_posting_enabled_now"] = True
    p["packet_status"] = "pass"
    res = g.validate_telegram_official_docs_credential_validation_gate_packet(p)
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_required_true_enforced():
    p = g._base_packet()
    p["not_public_postable"] = False
    res = g.validate_telegram_official_docs_credential_validation_gate_packet(p)
    assert res["valid"] is False
    assert any("not_public_postable_must_be_true" in e for e in res["errors"])


def test_request_budget_exceeded_fails_validation():
    p = g._base_packet()
    p["telegram_api_request_count"] = 2
    res = g.validate_telegram_official_docs_credential_validation_gate_packet(p)
    assert res["valid"] is False
    assert any("telegram_api_request_budget_exceeded" in e for e in res["errors"])


def test_secret_scanner_catches_leaked_token():
    p = g._base_packet()
    p["blocked_reasons"] = ["123456:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789xx"]
    res = g.validate_telegram_official_docs_credential_validation_gate_packet(p)
    assert res["valid"] is False
    assert any("secret_like_value_detected" in e for e in res["errors"])


def test_channel_write_permission_remains_unvalidated():
    s = g.summary(env_text=_both_env(), api_caller=_fake_getme_ok,
                  source_label="APPROVED_LOCAL_ENV_SOURCE_REDACTED", fetched_docs=GOOD_DOCS)
    assert s["channel_write_permission_validated"] is False
    assert s["channel_posting_validated"] is False


def test_unavailable_env_fails_closed():
    s = g.summary()
    assert s["packet_status"] == "blocked"
    assert s["telegram_api_called"] is False
    assert s["validation_valid"] is True
