import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(__file__))
FIX = os.path.join(BASE, "fixtures", "redacted_publish_audit_log")

from live_contentops import redacted_publish_audit_log as m


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("redacted_publish_audit_log_valid.json")


def validate(p):
    return m.validate_redacted_publish_audit_log_packet(p)


def _inv(name):
    return _load("redacted_publish_audit_log_invalid_" + name + ".json")


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


def test_credentials_requested_now_fails():
    res = _flag("credentials_requested_now")
    assert res["valid"] is False
    assert any("credentials_requested_now_must_be_false" in e for e in res["errors"])


def test_env_read_allowed_now_fails():
    res = validate(_inv("env_read_allowed_now"))
    assert res["valid"] is False
    assert any("env_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_os_env_read_allowed_now_fails():
    res = validate(_inv("os_env_read_allowed_now"))
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


def test_unredacted_secret_allowed_in_audit_fails():
    res = _flag("unredacted_secret_allowed_in_audit")
    assert res["valid"] is False
    assert any("unredacted_secret_allowed_in_audit_must_be_false" in e for e in res["errors"])


def test_unredacted_secret_allowed_in_evidence_fails():
    res = _flag("unredacted_secret_allowed_in_evidence")
    assert res["valid"] is False
    assert any("unredacted_secret_allowed_in_evidence_must_be_false" in e for e in res["errors"])


def test_secret_redaction_required_false_fails():
    res = _flag("secret_redaction_required", False)
    assert res["valid"] is False
    assert any("secret_redaction_required_must_be_true" in e for e in res["errors"])


def test_never_commit_secrets_required_false_fails():
    res = _flag("never_commit_secrets_required", False)
    assert res["valid"] is False
    assert any("never_commit_secrets_required_must_be_true" in e for e in res["errors"])


def test_no_secret_scan_required_false_fails():
    res = _flag("no_secret_scan_required", False)
    assert res["valid"] is False
    assert any("no_secret_scan_required_must_be_true" in e for e in res["errors"])


def test_kill_switch_audit_required_false_fails():
    res = _flag("kill_switch_audit_required", False)
    assert res["valid"] is False


def test_forbidden_audit_event_type_fails():
    res = validate(_inv("forbidden_audit_event"))
    assert res["valid"] is False
    assert any("forbidden_audit_event_type" in e for e in res["errors"])


def test_event_secret_values_present_fails():
    p = _valid()
    p["audit_events"][0]["secret_values_present"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("event_secret_values_present" in e for e in res["errors"])


def test_event_credential_values_present_fails():
    res = validate(_inv("unredacted_credential_event"))
    assert res["valid"] is False
    assert any("event_credential_values_present" in e for e in res["errors"])


def test_event_unredacted_platform_response_fails():
    res = validate(_inv("platform_response_secret"))
    assert res["valid"] is False
    assert any("event_unredacted_platform_response" in e for e in res["errors"])


def test_evidence_policy_allow_env_contents_fails():
    p = _valid()
    p["evidence_packet_policy"]["allow_env_contents"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("evidence_policy_allow_env_contents_must_be_false" in e for e in res["errors"])


def test_evidence_policy_allow_os_env_values_fails():
    p = _valid()
    p["evidence_packet_policy"]["allow_os_env_values"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("evidence_policy_allow_os_env_values_must_be_false" in e for e in res["errors"])


def test_evidence_policy_allow_token_snippets_fails():
    p = _valid()
    p["evidence_packet_policy"]["allow_token_snippets"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("evidence_policy_allow_token_snippets_must_be_false" in e for e in res["errors"])


def test_evidence_policy_allow_screenshots_with_secrets_fails():
    p = _valid()
    p["evidence_packet_policy"]["allow_screenshots_with_secrets"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("evidence_policy_allow_screenshots_with_secrets_must_be_false" in e for e in res["errors"])


def test_evidence_policy_allow_logs_with_secrets_fails():
    p = _valid()
    p["evidence_packet_policy"]["allow_logs_with_secrets"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("evidence_policy_allow_logs_with_secrets_must_be_false" in e for e in res["errors"])


def test_realistic_token_like_secret_value_fails():
    res = validate(_inv("secret_value_in_evidence"))
    assert res["valid"] is False
    assert any("secret_like_value_detected" in e for e in res["errors"])



def test_platform_api_allowed_now_fails():
    res = validate(_inv("platform_api_enabled"))
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_live_adapter_enabled_now_fails():
    res = _flag("live_adapter_enabled_now")
    assert res["valid"] is False
    assert any("live_adapter_enabled_now_must_be_false" in e for e in res["errors"])


def test_oauth_flow_enabled_now_fails():
    res = validate(_inv("oauth_flow_enabled"))
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
    res = validate(_inv("publish_approval_system"))
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


def test_unsafe_signal_language_fails():
    res = validate(_inv("signal_language"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_missing_kill_switch_audit_fails():
    res = validate(_inv("missing_kill_switch_audit"))
    assert res["valid"] is False
    assert any("kill_switch_audit_required_must_be_true" in e for e in res["errors"])


def test_missing_redaction_policy_fails():
    res = validate(_inv("missing_redaction_policy"))
    assert res["valid"] is False
    assert any("secret_redaction" in e for e in res["errors"])


def test_missing_no_secret_scan_result_fails():
    res = validate(_inv("missing_no_secret_scan_result"))
    assert res["valid"] is False
    assert any("no_secret_scan" in e for e in res["errors"])


def test_detector_regex_literal_allowed_as_false_positive():
    p = _valid()
    # detector-source field carrying regex literal should NOT trip secret detection
    p["no_secret_scan_result_model"]["false_positive_notes"] = "pattern -----BEGIN RSA PRIVATE KEY----- is detector source"
    res = validate(p)
    assert res["valid"] is True, res["errors"]


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["platform_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])
