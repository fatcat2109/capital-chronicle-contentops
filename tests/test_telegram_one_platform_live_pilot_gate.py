import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(__file__))
FIX = os.path.join(BASE, "fixtures", "telegram_live_pilot_gate")

from live_contentops import telegram_one_platform_live_pilot_gate as m


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("telegram_live_pilot_gate_valid.json")


def validate(p):
    return m.validate_telegram_live_pilot_gate_packet(p)


def _inv(name):
    return _load("telegram_live_pilot_gate_invalid_" + name + ".json")


def _flag(flag, value=True):
    p = _valid()
    p[flag] = value
    return validate(p)


def test_valid_packet_passes():
    res = validate(_valid())
    assert res["valid"] is True, res["errors"]


def test_candidate_platform_not_telegram_fails():
    p = _valid()
    p["candidate_platform_id"] = "linkedin"
    res = validate(p)
    assert res["valid"] is False
    assert any("candidate_platform_id_must_be_telegram" in e for e in res["errors"])


def test_readiness_gate_only_false_fails():
    res = _flag("readiness_gate_only", False)
    assert res["valid"] is False
    assert any("readiness_gate_only_must_be_true" in e for e in res["errors"])


def test_platform_api_key_token_needed_now_fails():
    res = _flag("platform_api_key_token_needed_from_operator_now")
    assert res["valid"] is False
    assert any("platform_api_key_token_needed_from_operator_now_must_be_false" in e for e in res["errors"])


def test_telegram_bot_token_needed_now_fails():
    res = validate(_inv("token_requested_now"))
    assert res["valid"] is False
    assert any("telegram_bot_token_needed_from_operator_now_must_be_false" in e for e in res["errors"])


def test_telegram_chat_id_needed_now_fails():
    res = validate(_inv("chat_id_requested_now"))
    assert res["valid"] is False
    assert any("telegram_chat_id_needed_from_operator_now_must_be_false" in e for e in res["errors"])


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
    res = validate(_inv("credential_validation_enabled_now"))
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


def test_realistic_telegram_token_value_fails():
    res = validate(_inv("real_token_value"))
    assert res["valid"] is False


def test_future_credential_slot_action_required_now_fails():
    p = _valid()
    p["future_telegram_credential_requirements"][0]["operator_action_required_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("future_credential_slot_action_required_now" in e for e in res["errors"])


def test_future_operator_prerequisite_action_required_now_fails():
    p = _valid()
    p["future_operator_prerequisite_checklist"][0]["operator_action_required_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("future_operator_prerequisite_action_required_now" in e for e in res["errors"])


def test_missing_operator_warning_fails():
    res = validate(_inv("missing_operator_warning"))
    assert res["valid"] is False
    assert any("operator_warning_no_token_needed_now_required" in e for e in res["errors"])


def test_official_docs_verification_completed_now_fails():
    res = validate(_inv("official_docs_verification_claimed_done"))
    assert res["valid"] is False
    assert any("official_docs_verification_completed_now_must_be_false" in e for e in res["errors"])


def test_official_docs_verification_required_later_false_fails():
    res = _flag("official_docs_verification_required_later", False)
    assert res["valid"] is False
    assert any("official_docs_verification_required_later_must_be_true" in e for e in res["errors"])


def test_missing_0148_dependency_fails():
    p = _valid()
    del p["dependency_gate_status"]["publish_automation_readiness_0148"]
    res = validate(p)
    assert res["valid"] is False
    assert any("dependency_gate_missing:publish_automation_readiness_0148" in e for e in res["errors"])


def test_missing_0149_dependency_fails():
    p = _valid()
    p["dependency_gate_status"]["dry_run_publish_batch_manifest_0149"] = "unsatisfied"
    res = validate(p)
    assert res["valid"] is False
    assert any("dependency_gate_unsatisfied:dry_run_publish_batch_manifest_0149" in e for e in res["errors"])


def test_missing_0150_dependency_fails():
    res = validate(_inv("missing_credential_policy_dependency"))
    assert res["valid"] is False
    assert any("dependency_gate_missing:credential_secret_policy_0150" in e for e in res["errors"])


def test_missing_0151_dependency_fails():
    res = validate(_inv("missing_audit_guard_dependency"))
    assert res["valid"] is False
    assert any("dependency_gate_missing:redacted_publish_audit_log_0151" in e for e in res["errors"])


def test_missing_kill_switch_requirement_fails():
    res = validate(_inv("missing_kill_switch_gate"))
    assert res["valid"] is False
    assert any("kill_switch_required_must_be_true" in e for e in res["errors"])


def test_redacted_audit_log_required_false_fails():
    res = _flag("redacted_audit_log_required", False)
    assert res["valid"] is False
    assert any("redacted_audit_log_required_must_be_true" in e for e in res["errors"])


def test_no_secret_scan_required_false_fails():
    res = _flag("no_secret_scan_required", False)
    assert res["valid"] is False
    assert any("no_secret_scan_required_must_be_true" in e for e in res["errors"])


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
    res = validate(_inv("scheduler_enabled"))
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


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["telegram_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_gate_decision_is_ready_to_prepare_future_credential_setup():
    p = _valid()
    assert p["gate_decision"] == "ready_to_prepare_future_credential_setup_task"
    assert validate(p)["valid"] is True



def test_summary_counters_zero_or_false():
    s = m.summary()
    zero_counts = [
        "platform_api_key_token_needed_now_count",
        "telegram_bot_token_needed_now_count",
        "telegram_chat_id_needed_now_count",
        "credentials_requested_now_count",
        "env_read_allowed_now_count",
        "os_env_read_allowed_now_count",
        "credential_validation_enabled_now_count",
        "credential_storage_enabled_now_count",
        "credential_logging_allowed_count",
        "credential_commit_allowed_count",
        "credential_printing_allowed_count",
        "secret_like_value_detected_count",
        "real_secret_values_present_count",
        "telegram_api_enabled_count",
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
        "official_docs_verification_completed_now_count",
        "operator_action_required_now_count",
    ]
    for k in zero_counts:
        assert s[k] == 0, k
    assert s["candidate_platform_id"] == "telegram"
    assert s["gate_decision"] == "ready_to_prepare_future_credential_setup_task"
    assert s["dependency_gate_satisfied_count"] == 4
    for k in [
        "manual_review_required_all",
        "not_public_postable_all",
        "official_docs_verification_required_later_all",
        "kill_switch_required_all",
        "redacted_audit_log_required_all",
        "no_secret_scan_required_all",
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


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli", "pre-alpha-telegram-live-pilot-gate-summary"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["validation_valid"] is True
    assert out["telegram_bot_token_needed_now_count"] == 0
    assert out["live_posting_enabled_count"] == 0
    assert out["gate_decision"] == "ready_to_prepare_future_credential_setup_task"


def test_existing_cli_summaries_still_run():
    cmds = [
        "pre-alpha-redacted-publish-audit-log-summary",
        "pre-alpha-publish-adapter-credential-secret-policy-summary",
        "pre-alpha-social-platform-foundation-summary",
    ]
    for c in cmds:
        r = subprocess.run(
            [sys.executable, "-m", "live_contentops.cli", c],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"{c} failed: {r.stderr}"
