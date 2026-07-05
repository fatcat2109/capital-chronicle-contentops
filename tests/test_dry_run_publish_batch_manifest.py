import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(__file__))
FIX = os.path.join(BASE, "fixtures", "dry_run_publish_batch_manifest")

from live_contentops import dry_run_publish_batch_manifest as m


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("dry_run_publish_batch_manifest_valid.json")


def validate(p):
    return m.validate_dry_run_publish_batch_manifest_packet(p)


def _inv(name):
    return _load("dry_run_publish_batch_manifest_invalid_" + name + ".json")


def test_valid_manifest_passes():
    res = validate(_valid())
    assert res["valid"] is True, res["errors"]


def test_dry_run_only_false_fails():
    p = _valid()
    p["dry_run_only"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("dry_run_only_must_be_true" in e for e in res["errors"])


def test_credentials_requested_now_fails():
    res = validate(_inv("credentials_requested"))
    assert res["valid"] is False
    assert any("credentials_requested_now_must_be_false" in e for e in res["errors"])


def test_credential_read_allowed_now_fails():
    res = validate(_inv("credential_read"))
    assert res["valid"] is False
    assert any("credential_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_credential_operator_action_now_fails():
    p = _valid()
    p["credential_operator_action_required_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("credential_operator_action_required_now_must_be_false" in e for e in res["errors"])


def test_platform_api_allowed_now_fails():
    res = validate(_inv("platform_api_enabled"))
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_live_posting_enabled_now_fails():
    res = validate(_inv("live_posting_enabled"))
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_scheduler_allowed_now_fails():
    res = validate(_inv("scheduler_enabled"))
    assert res["valid"] is False
    assert any("scheduler_allowed_now_must_be_false" in e for e in res["errors"])


def test_provider_llm_api_allowed_now_fails():
    p = _valid()
    p["provider_llm_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("provider_llm_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_repo_web_search_allowed_now_fails():
    p = _valid()
    p["repo_web_search_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("repo_web_search_allowed_now_must_be_false" in e for e in res["errors"])


def test_scraping_allowed_now_fails():
    p = _valid()
    p["scraping_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False


def test_newsletter_or_cms_api_allowed_now_fails():
    p = _valid()
    p["newsletter_or_cms_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("newsletter_or_cms_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_backend_server_required_fails():
    res = validate(_inv("backend_server_required"))
    assert res["valid"] is False
    assert any("backend_server_required_must_be_false" in e for e in res["errors"])


def test_publish_all_button_enabled_now_fails():
    p = _valid()
    p["publish_all_button_enabled_now"] = True
    res = validate(p)
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
    res = validate(_inv("public_ready_approval"))
    assert res["valid"] is False
    assert any("public_ready_approval_allowed_now_must_be_false" in e for e in res["errors"])


def test_final_social_copy_generated_fails():
    res = validate(_inv("final_social_copy"))
    assert res["valid"] is False
    assert any("final_social_copy_generated_must_be_false" in e for e in res["errors"])


def test_final_payload_true_fails():
    p = _valid()
    p["per_platform_payload_previews"][0]["final_payload"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("preview_final_payload_must_be_false" in e for e in res["errors"])


def test_manual_review_required_false_fails():
    p = _valid()
    p["manual_review_required"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("manual_review_required_must_be_true" in e for e in res["errors"])


def test_not_public_postable_false_fails():
    p = _valid()
    p["not_public_postable"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("not_public_postable_must_be_true" in e for e in res["errors"])


def test_missing_kill_switch_fails():
    res = validate(_inv("missing_kill_switch"))
    assert res["valid"] is False
    assert any("kill_switch_required_must_be_true" in e for e in res["errors"])


def test_missing_redacted_audit_log_fails():
    res = validate(_inv("missing_redacted_audit_log"))
    assert res["valid"] is False
    assert any("redacted_audit_log_required_must_be_true" in e for e in res["errors"])


def test_missing_idempotency_policy_fails():
    res = validate(_inv("missing_idempotency_policy"))
    assert res["valid"] is False
    assert any("idempotency_policy_required_must_be_true" in e for e in res["errors"])


def test_missing_partial_failure_policy_fails():
    res = validate(_inv("missing_partial_failure_policy"))
    assert res["valid"] is False
    assert any("partial_failure_policy_required_must_be_true" in e for e in res["errors"])


def test_missing_manual_approval_gate_fails():
    res = validate(_inv("missing_manual_approval_gate"))
    assert res["valid"] is False
    assert any("manual_approval_gate_required_must_be_true" in e for e in res["errors"])



def test_unsupported_platform_target_fails():
    res = validate(_inv("unknown_platform_target"))
    assert res["valid"] is False
    assert any("unsupported_platform_target" in e for e in res["errors"])


def test_implemented_live_platform_adapter_fails():
    p = _valid()
    p["per_platform_payload_previews"][0]["platform_adapter_status"] = "implemented"
    res = validate(p)
    assert res["valid"] is False
    assert any("preview_adapter_status_must_not_be_live" in e for e in res["errors"])


def test_source_refs_visible_false_fails():
    p = _valid()
    p["per_platform_payload_previews"][0]["source_refs_visible"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("preview_source_refs_not_visible" in e for e in res["errors"])


def test_limitations_visible_false_fails():
    p = _valid()
    p["per_platform_payload_previews"][0]["limitations_visible"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("preview_limitations_not_visible" in e for e in res["errors"])


def test_final_ready_to_post_preview_representation_fails():
    p = _valid()
    p["per_platform_payload_previews"][0]["payload_text_preview_status"] = "ready to post final copy"
    res = validate(p)
    assert res["valid"] is False
    assert any("unsafe_signal_detected:ready to post" in e for e in res["errors"])


def test_unsafe_signal_language_fails():
    res = validate(_inv("signal_language"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_unsupported_numeric_claim_fails():
    res = validate(_inv("unsupported_numeric_claim"))
    assert res["valid"] is False
    assert any("unsupported_numeric_market_claim" in e for e in res["errors"])


def test_alpha_claim_without_real_artifact_fails():
    res = validate(_inv("artifact_claim"))
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


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
        "credential_read_enabled_count",
        "credential_operator_action_required_now_count",
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
        "publish_approval_system_created_count",
        "public_ready_approval_allowed_count",
        "final_social_copy_generated_count",
        "final_payload_count",
        "unsupported_platform_target_count",
        "unsafe_language_count",
        "unsupported_numeric_claim_count",
        "artifact_claim_without_real_artifact_count",
    ]
    for k in zero_counts:
        assert s[k] == 0, k
    for k in [
        "dry_run_only",
        "manual_review_required_all",
        "not_public_postable_all",
        "kill_switch_required_all",
        "redacted_audit_log_required_all",
        "idempotency_policy_required_all",
        "partial_failure_policy_required_all",
        "manual_approval_gate_required_all",
        "source_refs_visible_all",
        "limitations_visible_all",
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

