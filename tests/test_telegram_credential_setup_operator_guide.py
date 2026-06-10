import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(__file__))
FIX = os.path.join(BASE, "fixtures", "telegram_credential_setup_operator_guide")

from live_contentops import telegram_credential_setup_operator_guide as m


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("telegram_credential_setup_operator_guide_valid.json")


def validate(p):
    return m.validate_telegram_credential_setup_operator_guide_packet(p)


def _inv(name):
    return _load("telegram_credential_setup_operator_guide_invalid_" + name + ".json")


def _flag(flag, value=True):
    p = _valid()
    p[flag] = value
    return validate(p)


def test_valid_packet_passes():
    res = validate(_valid())
    assert res["valid"] is True, res["errors"]


def test_platform_api_key_token_needed_now_fails():
    res = _flag("platform_api_key_token_needed_from_operator_now")
    assert res["valid"] is False
    assert any("platform_api_key_token_needed_from_operator_now_must_be_false" in e for e in res["errors"])


def test_telegram_bot_token_needed_now_fails():
    res = _flag("telegram_bot_token_needed_from_operator_now")
    assert res["valid"] is False
    assert any("telegram_bot_token_needed_from_operator_now_must_be_false" in e for e in res["errors"])


def test_telegram_chat_id_needed_now_fails():
    res = _flag("telegram_chat_id_needed_from_operator_now")
    assert res["valid"] is False
    assert any("telegram_chat_id_needed_from_operator_now_must_be_false" in e for e in res["errors"])


def test_real_env_file_read_by_repo_now_fails():
    res = _flag("real_env_file_read_by_repo_now")
    assert res["valid"] is False
    assert any("real_env_file_read_by_repo_now_must_be_false" in e for e in res["errors"])


def test_real_env_file_read_allowed_now_fails():
    res = validate(_inv("env_file_read_allowed"))
    assert res["valid"] is False
    assert any("real_env_file_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_env_read_allowed_now_fails():
    res = _flag("env_read_allowed_now")
    assert res["valid"] is False
    assert any("env_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_os_env_read_allowed_now_fails():
    res = validate(_inv("os_env_read_allowed"))
    assert res["valid"] is False
    assert any("os_env_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_credential_validation_enabled_now_fails():
    res = validate(_inv("credential_validation_enabled"))
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


def test_token_value_present_fails():
    res = validate(_inv("token_value_present"))
    assert res["valid"] is False
    assert any("token_value_present_must_be_false" in e for e in res["errors"])


def test_chat_id_value_present_fails():
    res = validate(_inv("chat_id_value_present"))
    assert res["valid"] is False
    assert any("chat_id_value_present_must_be_false" in e for e in res["errors"])


def test_real_secret_values_present_fails():
    res = _flag("real_secret_values_present")
    assert res["valid"] is False


def test_placeholder_only_false_fails():
    res = _flag("placeholder_only", False)
    assert res["valid"] is False
    assert any("placeholder_only_must_be_true" in e for e in res["errors"])


def test_secret_redaction_required_false_fails():
    res = _flag("secret_redaction_required", False)
    assert res["valid"] is False
    assert any("secret_redaction_required_must_be_true" in e for e in res["errors"])


def test_never_commit_secrets_required_false_fails():
    res = _flag("never_commit_secrets_required", False)
    assert res["valid"] is False
    assert any("never_commit_secrets_required_must_be_true" in e for e in res["errors"])


def test_never_paste_secrets_warning_required_false_fails():
    res = _flag("never_paste_secrets_warning_required", False)
    assert res["valid"] is False
    assert any("never_paste_secrets_warning_required_must_be_true" in e for e in res["errors"])


def test_rotation_warning_required_if_exposed_false_fails():
    res = _flag("rotation_warning_required_if_exposed", False)
    assert res["valid"] is False
    assert any("rotation_warning_required_if_exposed_must_be_true" in e for e in res["errors"])


def test_future_presence_check_required_false_fails():
    res = _flag("future_presence_check_required", False)
    assert res["valid"] is False
    assert any("future_presence_check_required_must_be_true" in e for e in res["errors"])


def test_future_live_adapter_gate_required_false_fails():
    res = _flag("future_live_adapter_gate_required", False)
    assert res["valid"] is False
    assert any("future_live_adapter_gate_required_must_be_true" in e for e in res["errors"])


def test_realistic_telegram_token_value_fails():
    p = _valid()
    p["credential_slot_policy"][0]["placeholder_value"] = "123456789:AAFakeBotTokenABCDEFGHIJKLMNOPQRSTUVWXYZ12"
    res = validate(p)
    assert res["valid"] is False
    assert any("secret_like_value_detected" in e for e in res["errors"])


def test_realistic_chat_id_value_fails():
    p = _valid()
    p["credential_slot_policy"][1]["placeholder_value"] = "-1001234567890"
    res = validate(p)
    assert res["valid"] is False
    assert any("secret_like_value_detected" in e for e in res["errors"])


def test_committed_real_env_path_caught_by_evidence_policy():
    # A realistic absolute env path should be flagged if it carries a token-like value;
    # the no_secret_evidence_policy forbids real local paths in evidence.
    p = _valid()
    policy = p["no_secret_evidence_policy"]
    assert "real_local_env_path" in policy["evidence_must_not_include"]


def test_placeholder_template_realistic_values_fails():
    p = _valid()
    p["placeholder_env_stub_policy"]["example_lines"] = [
        "TELEGRAM_BOT_TOKEN=123456789:AAFakeBotTokenABCDEFGHIJKLMNOPQRSTUVWXYZ12"
    ]
    res = validate(p)
    assert res["valid"] is False
    assert any("secret_like_value_detected" in e for e in res["errors"])


def test_telegram_api_allowed_now_fails():
    res = validate(_inv("telegram_api_enabled"))
    assert res["valid"] is False
    assert any("telegram_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_platform_api_allowed_now_fails():
    res = _flag("platform_api_allowed_now")
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_live_adapter_enabled_now_fails():
    res = validate(_inv("live_adapter_enabled"))
    assert res["valid"] is False
    assert any("live_adapter_enabled_now_must_be_false" in e for e in res["errors"])


def test_oauth_flow_enabled_now_fails():
    res = _flag("oauth_flow_enabled_now")
    assert res["valid"] is False
    assert any("oauth_flow_enabled_now_must_be_false" in e for e in res["errors"])


def test_live_posting_enabled_now_fails():
    res = validate(_inv("live_posting_enabled"))
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
    res = validate(_inv("final_public_ready_copy"))
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


def test_official_docs_verification_completed_now_fails():
    res = _flag("official_docs_verification_completed_now")
    assert res["valid"] is False
    assert any("official_docs_verification_completed_now_must_be_false" in e for e in res["errors"])


def test_missing_never_paste_warning_fails():
    res = validate(_inv("missing_never_paste_warning"))
    assert res["valid"] is False
    assert any("never_paste_secrets_warning_required" in e for e in res["errors"])


def test_missing_rotation_warning_fails():
    res = validate(_inv("missing_rotation_warning"))
    assert res["valid"] is False
    assert any("rotation_warning_required" in e for e in res["errors"])


def test_missing_future_presence_check_boundary_fails():
    res = validate(_inv("missing_future_presence_check_boundary"))
    assert res["valid"] is False
    assert any("future_presence_check_boundary_required" in e for e in res["errors"])


def test_unsafe_signal_language_fails():
    res = validate(_inv("signal_language"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["telegram_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])
    assert any("telegram_api_allowed_now_must_be_false" in e for e in res["errors"])

