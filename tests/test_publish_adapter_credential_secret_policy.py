import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(__file__))
FIX = os.path.join(BASE, "fixtures", "publish_adapter_credential_secret_policy")

from live_contentops import publish_adapter_credential_secret_policy as m


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("publish_adapter_credential_secret_policy_valid.json")


def validate(p):
    return m.validate_publish_adapter_credential_secret_policy_packet(p)


def _inv(name):
    return _load("publish_adapter_credential_secret_policy_invalid_" + name + ".json")


def _flag(flag, value=True):
    p = _valid()
    p[flag] = value
    return validate(p)


def test_valid_policy_passes():
    res = validate(_valid())
    assert res["valid"] is True, res["errors"]


def test_credentials_requested_now_fails():
    res = _flag("credentials_requested_now")
    assert res["valid"] is False
    assert any("credentials_requested_now_must_be_false" in e for e in res["errors"])


def test_platform_api_key_token_needed_now_fails():
    res = _flag("platform_api_key_token_needed_from_operator_now")
    assert res["valid"] is False
    assert any("platform_api_key_token_needed_from_operator_now_must_be_false" in e for e in res["errors"])


def test_real_secret_values_allowed_in_repo_fails():
    res = _flag("real_secret_values_allowed_in_repo")
    assert res["valid"] is False
    assert any("real_secret_values_allowed_in_repo_must_be_false" in e for e in res["errors"])


def test_real_secret_values_present_fails():
    res = _flag("real_secret_values_present")
    assert res["valid"] is False
    assert any("real_secret_values_present_must_be_false" in e for e in res["errors"])


def test_env_read_allowed_now_fails():
    res = _flag("env_read_allowed_now")
    assert res["valid"] is False
    assert any("env_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_os_env_read_allowed_now_fails():
    res = _flag("os_env_read_allowed_now")
    assert res["valid"] is False
    assert any("os_env_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_credential_validation_enabled_now_fails():
    res = _flag("credential_validation_enabled_now")
    assert res["valid"] is False
    assert any("credential_validation_enabled_now_must_be_false" in e for e in res["errors"])


def test_credential_storage_enabled_now_fails():
    res = _flag("credential_storage_enabled_now")
    assert res["valid"] is False
    assert any("credential_storage_enabled_now_must_be_false" in e for e in res["errors"])


def test_credential_logging_allowed_fails():
    res = _flag("credential_logging_allowed")
    assert res["valid"] is False
    assert any("credential_logging_allowed_must_be_false" in e for e in res["errors"])


def test_credential_commit_allowed_fails():
    res = _flag("credential_commit_allowed")
    assert res["valid"] is False
    assert any("credential_commit_allowed_must_be_false" in e for e in res["errors"])


def test_credential_printing_allowed_fails():
    res = _flag("credential_printing_allowed")
    assert res["valid"] is False
    assert any("credential_printing_allowed_must_be_false" in e for e in res["errors"])


def test_secret_redaction_required_false_fails():
    res = _flag("secret_redaction_required", False)
    assert res["valid"] is False
    assert any("secret_redaction_required_must_be_true" in e for e in res["errors"])


def test_never_commit_secrets_required_false_fails():
    res = _flag("never_commit_secrets_required", False)
    assert res["valid"] is False


def test_platform_api_allowed_now_fails():
    res = _flag("platform_api_allowed_now")
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_live_adapter_enabled_now_fails():
    res = validate(_inv("live_adapter_enabled"))
    assert res["valid"] is False
    assert any("live_adapter_enabled_now_must_be_false" in e for e in res["errors"])


def test_oauth_flow_enabled_now_fails():
    res = validate(_inv("oauth_flow_enabled"))
    assert res["valid"] is False
    assert any("oauth_flow_enabled_now_must_be_false" in e for e in res["errors"])


def test_live_posting_enabled_now_fails():
    res = _flag("live_posting_enabled_now")
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_scheduler_allowed_now_fails():
    res = _flag("scheduler_allowed_now")
    assert res["valid"] is False
    assert any("scheduler_allowed_now_must_be_false" in e for e in res["errors"])


def test_provider_llm_api_allowed_now_fails():
    res = _flag("provider_llm_api_allowed_now")
    assert res["valid"] is False
    assert any("provider_llm_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_repo_web_search_allowed_now_fails():
    res = _flag("repo_web_search_allowed_now")
    assert res["valid"] is False
    assert any("repo_web_search_allowed_now_must_be_false" in e for e in res["errors"])


def test_scraping_allowed_now_fails():
    res = _flag("scraping_allowed_now")
    assert res["valid"] is False
    assert any("scraping_allowed_now_must_be_false" in e for e in res["errors"])


def test_newsletter_or_cms_api_allowed_now_fails():
    res = _flag("newsletter_or_cms_api_allowed_now")
    assert res["valid"] is False
    assert any("newsletter_or_cms_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_backend_server_required_fails():
    res = _flag("backend_server_required")
    assert res["valid"] is False
    assert any("backend_server_required_must_be_false" in e for e in res["errors"])


def test_publish_all_button_enabled_now_fails():
    res = _flag("publish_all_button_enabled_now")
    assert res["valid"] is False
    assert any("publish_all_button_enabled_now_must_be_false" in e for e in res["errors"])


def test_one_button_publish_all_enabled_now_fails():
    res = validate(_inv("publish_all_enabled"))
    assert res["valid"] is False
    assert any("one_button_publish_all_enabled_now_must_be_false" in e for e in res["errors"])


def test_publish_approval_system_created_fails():
    res = _flag("publish_approval_system_created")
    assert res["valid"] is False
    assert any("publish_approval_system_created_must_be_false" in e for e in res["errors"])


def test_public_ready_approval_allowed_now_fails():
    res = _flag("public_ready_approval_allowed_now")
    assert res["valid"] is False
    assert any("public_ready_approval_allowed_now_must_be_false" in e for e in res["errors"])


def test_final_social_copy_generated_fails():
    res = _flag("final_social_copy_generated")
    assert res["valid"] is False
    assert any("final_social_copy_generated_must_be_false" in e for e in res["errors"])


def test_manual_review_required_false_fails():
    res = _flag("manual_review_required", False)
    assert res["valid"] is False
    assert any("manual_review_required_must_be_true" in e for e in res["errors"])


def test_not_public_postable_false_fails():
    res = _flag("not_public_postable", False)
    assert res["valid"] is False
    assert any("not_public_postable_must_be_true" in e for e in res["errors"])



def test_unsupported_platform_credential_target_fails():
    p = _valid()
    p["platform_credential_requirements"][0]["platform_id"] = "facebook_unknown"
    res = validate(p)
    assert res["valid"] is False
    assert any("unsupported_platform_credential_target" in e for e in res["errors"])


def test_realistic_token_like_secret_value_fails():
    res = validate(_inv("real_secret_value"))
    assert res["valid"] is False
    assert any("secret_like_value_detected" in e for e in res["errors"])


def test_missing_future_operator_setup_gate_fails():
    res = validate(_inv("missing_future_setup_gate"))
    assert res["valid"] is False
    assert any("future_operator_setup_gate_required" in e for e in res["errors"])


def test_missing_operator_warning_fails():
    res = validate(_inv("missing_operator_warning"))
    assert res["valid"] is False
    assert any("operator_warning_no_keys_needed_now_required" in e for e in res["errors"])


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["platform_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_summary_counters_zero_or_false():
    s = m.summary()
    zero_counts = [
        "credentials_requested_now_count",
        "platform_api_key_token_needed_now_count",
        "real_secret_values_present_count",
        "env_read_allowed_now_count",
        "os_env_read_allowed_now_count",
        "credential_validation_enabled_now_count",
        "credential_storage_enabled_now_count",
        "credential_logging_allowed_count",
        "credential_commit_allowed_count",
        "credential_printing_allowed_count",
        "platform_api_enabled_count",
        "live_adapter_enabled_count",
        "oauth_flow_enabled_count",
        "live_posting_enabled_count",
        "scheduler_enabled_count",
        "provider_llm_api_enabled_count",
        "repo_web_search_enabled_count",
        "scraping_enabled_count",
        "newsletter_or_cms_api_enabled_count",
        "backend_server_required_count",
        "publish_all_button_enabled_count",
        "one_button_publish_all_enabled_count",
        "publish_approval_system_created_count",
        "public_ready_approval_allowed_count",
        "final_social_copy_generated_count",
        "secret_like_value_detected_count",
        "unsupported_platform_credential_target_count",
    ]
    for k in zero_counts:
        assert s[k] == 0, k
    assert s["platform_api_key_token_needed_later_count"] == 1
    for k in [
        "secret_redaction_required_all",
        "never_commit_secrets_required_all",
        "manual_review_required_all",
        "not_public_postable_all",
        "validation_valid",
    ]:
        assert s[k] is True, k
    for k in [
        "provider_call_used_by_repo",
        "search_call_used_by_repo",
        "network_call_used_by_repo",
        "news_api_used_by_repo",
        "market_data_api_used_by_repo",
        "platform_action_used_by_repo",
        "credential_or_env_read_used",
        "scheduler_accessed",
        "scraping_allowed_now",
        "newsletter_send_enabled",
        "cms_integration_enabled",
        "autonomous_reply_dm_enabled",
    ]:
        assert s[k] is False, k
    json.dumps(s)

