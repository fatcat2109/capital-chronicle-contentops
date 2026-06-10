import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(__file__))
FIX = os.path.join(BASE, "fixtures", "publish_automation_readiness")

from live_contentops import publish_automation_readiness as m


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid_readiness():
    return _load("publish_automation_readiness_valid.json")


def _valid_registry():
    return _load("platform_capability_registry_valid.json")


def validate(p):
    return m.validate_publish_automation_readiness_packet(p)


def test_valid_readiness_packet_passes():
    res = validate(_valid_readiness())
    assert res["valid"] is True, res["errors"]


def test_valid_platform_capability_registry_passes():
    res = m.validate_platform_capability_registry_packet(_valid_registry())
    assert res["valid"] is True, res["errors"]


def test_credentials_requested_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_credentials_requested.json"))
    assert res["valid"] is False
    assert any("credentials_requested_now_must_be_false" in e for e in res["errors"])


def test_credential_read_allowed_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_credential_read.json"))
    assert res["valid"] is False
    assert any("credential_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_credential_operator_action_now_fails():
    p = _valid_readiness()
    p["operator_action_required_now_for_credentials"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("operator_action_required_now_for_credentials_must_be_false" in e for e in res["errors"])


def test_platform_api_allowed_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_platform_api_enabled.json"))
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_live_api_enabled_now_in_registry_fails():
    reg = _valid_registry()
    reg["platforms"][0]["live_api_enabled_now"] = True
    res = m.validate_platform_capability_registry_packet(reg)
    assert res["valid"] is False
    assert any("platform_live_api_enabled_now_must_be_false" in e for e in res["errors"])


def test_live_posting_enabled_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_live_posting_enabled.json"))
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_scheduler_allowed_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_scheduler_enabled.json"))
    assert res["valid"] is False
    assert any("scheduler_allowed_now_must_be_false" in e for e in res["errors"])


def test_provider_llm_api_allowed_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_provider_call.json"))
    assert res["valid"] is False


def test_repo_web_search_allowed_now_fails():
    p = _valid_readiness()
    p["repo_web_search_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("repo_web_search_allowed_now_must_be_false" in e for e in res["errors"])


def test_scraping_allowed_now_fails():
    p = _valid_readiness()
    p["scraping_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("scraping_allowed_now_must_be_false" in e for e in res["errors"])


def test_newsletter_or_cms_api_allowed_now_fails():
    p = _valid_readiness()
    p["newsletter_or_cms_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("newsletter_or_cms_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_backend_server_required_fails():
    res = validate(_load("publish_automation_readiness_invalid_backend_server_required.json"))
    assert res["valid"] is False
    assert any("backend_server_required_must_be_false" in e for e in res["errors"])


def test_publish_all_button_enabled_now_fails():
    p = _valid_readiness()
    p["publish_all_button_enabled_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("publish_all_button_enabled_now_must_be_false" in e for e in res["errors"])


def test_one_button_publish_all_enabled_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_publish_all_enabled.json"))
    assert res["valid"] is False
    assert any("one_button_publish_all_enabled_now_must_be_false" in e for e in res["errors"])


def test_publish_approval_system_created_fails():
    p = _valid_readiness()
    p["publish_approval_system_created"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("publish_approval_system_created_must_be_false" in e for e in res["errors"])


def test_public_ready_approval_allowed_now_fails():
    res = validate(_load("publish_automation_readiness_invalid_public_ready_approval.json"))
    assert res["valid"] is False
    assert any("public_ready_approval_allowed_now_must_be_false" in e for e in res["errors"])


def test_final_social_copy_generated_fails():
    p = _valid_readiness()
    p["final_social_copy_generated"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("final_social_copy_generated_must_be_false" in e for e in res["errors"])


def test_manual_review_required_false_fails():
    p = _valid_readiness()
    p["manual_review_required"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("manual_review_required_must_be_true" in e for e in res["errors"])


def test_not_public_postable_false_fails():
    p = _valid_readiness()
    p["not_public_postable"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("not_public_postable_must_be_true" in e for e in res["errors"])



def test_missing_kill_switch_requirement_fails():
    res = validate(_load("publish_automation_readiness_invalid_missing_kill_switch.json"))
    assert res["valid"] is False
    assert any("kill_switch_required_must_be_true" in e for e in res["errors"])


def test_missing_redacted_audit_log_requirement_fails():
    p = _valid_readiness()
    p["redacted_audit_log_required"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("redacted_audit_log_required_must_be_true" in e for e in res["errors"])


def test_missing_manual_approval_gate_fails():
    res = validate(_load("publish_automation_readiness_invalid_missing_manual_approval_gate.json"))
    assert res["valid"] is False
    assert any("manual_approval_gate_model_required" in e for e in res["errors"])


def test_implemented_live_platform_adapter_fails():
    reg = _valid_registry()
    reg["platforms"][0]["adapter_status"] = "implemented"
    res = m.validate_platform_capability_registry_packet(reg)
    assert res["valid"] is False
    assert any("platform_adapter_status_must_not_be_live" in e for e in res["errors"])


def test_platform_credentials_available_fails():
    reg = _valid_registry()
    reg["platforms"][0]["credentials_available"] = True
    res = m.validate_platform_capability_registry_packet(reg)
    assert res["valid"] is False
    assert any("platform_credentials_available_must_be_false" in e for e in res["errors"])


def test_exact_api_claim_without_future_docs_verification_fails():
    reg = _valid_registry()
    reg["platforms"][0]["requires_future_official_docs_verification"] = False
    res = m.validate_platform_capability_registry_packet(reg)
    assert res["valid"] is False
    assert any("platform_requires_future_official_docs_verification_must_be_true" in e for e in res["errors"])


def test_unsafe_signal_language_fails():
    res = validate(_load("publish_automation_readiness_invalid_signal_language.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_alpha_claim_without_real_artifact_fails():
    p = _valid_readiness()
    p["blocked_reasons"].append("Capital Chronicle alpha says this is confirmed")
    res = validate(p)
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_packet_status_pass_with_errors_flagged():
    p = _valid_readiness()
    p["platform_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_summary_counters_zero_or_false():
    s = m.summary()
    zero_counts = [
        "credentials_requested_now_count",
        "credential_read_enabled_count",
        "platform_api_enabled_count",
        "live_posting_enabled_count",
        "scheduler_enabled_count",
        "provider_llm_api_enabled_count",
        "repo_web_search_enabled_count",
        "scraping_enabled_count",
        "newsletter_or_cms_api_enabled_count",
        "backend_server_required_count",
        "publish_all_button_enabled_count",
        "one_button_publish_all_enabled_count",
        "public_ready_approval_allowed_count",
        "publish_approval_system_created_count",
        "final_social_copy_generated_count",
        "credential_operator_action_required_now_count",
        "unsafe_language_count",
    ]
    for k in zero_counts:
        assert s[k] == 0, k
    assert s["manual_review_required_all"] is True
    assert s["not_public_postable_all"] is True
    assert s["kill_switch_required_all"] is True
    assert s["redacted_audit_log_required_all"] is True
    assert s["validation_valid"] is True
    assert s["registry_validation_valid"] is True
    bool_false = [
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
    ]
    for k in bool_false:
        assert s[k] is False, k
    json.dumps(s)


def test_cli_summary_runs():
    r = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli", "pre-alpha-publish-automation-readiness-summary"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["validation_valid"] is True
    assert out["one_button_publish_all_enabled_count"] == 0


def test_existing_cli_summaries_still_run():
    cmds = [
        "pre-alpha-daily-content-studio-static-frontend-summary",
        "pre-alpha-daily-content-studio-ui-data-contract-summary",
        "pre-alpha-social-platform-foundation-summary",
    ]
    for c in cmds:
        r = subprocess.run(
            [sys.executable, "-m", "live_contentops.cli", c],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"{c} failed: {r.stderr}"
