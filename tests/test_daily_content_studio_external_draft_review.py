import os
import json
from live_contentops.daily_content_studio_external_draft_review import (
    validate_daily_content_studio_external_draft_review_packet as validate,
    summary,
)

FIX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "fixtures",
    "daily_content_studio_external_draft_review",
)


def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("daily_content_studio_external_draft_review_valid.json")


P = "daily_content_studio_external_draft_review_invalid_"


def test_valid_packet_passes():
    res = validate(_valid())
    assert res["valid"] is True
    assert res["errors"] == []


def test_repo_generated_draft_fails():
    p = _valid()
    p["draft_origin_policy"]["repo_generated_draft"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("repo_generated_draft_must_be_false" in e for e in res["errors"])


def test_repo_executes_prompt_fails():
    res = validate(_load(P + "repo_executes_prompt.json"))
    assert res["valid"] is False
    assert any("repo_executes_prompt_must_be_false" in e for e in res["errors"])


def test_provider_call_allowed_by_repo_fails():
    res = validate(_load(P + "provider_call.json"))
    assert res["valid"] is False
    assert any("provider_call_allowed_by_repo_must_be_false" in e for e in res["errors"])


def test_provider_llm_api_allowed_now_fails():
    p = _valid()
    p["draft_origin_policy"]["provider_llm_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("provider_llm_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_public_ready_allowed_now_fails():
    res = validate(_load(P + "public_ready.json"))
    assert res["valid"] is False
    assert any("public_ready_allowed_now_must_be_false" in e for e in res["errors"])


def test_publish_ready_fails():
    p = _valid()
    p["output_policy"]["publish_ready"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("publish_ready_must_be_false" in e for e in res["errors"])


def test_final_social_copy_generated_fails():
    p = _valid()
    p["output_policy"]["final_social_copy_generated"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("final_social_copy_generated_must_be_false" in e for e in res["errors"])


def test_auto_approval_allowed_fails():
    res = validate(_load(P + "auto_approval.json"))
    assert res["valid"] is False
    assert any("auto_approval_allowed_must_be_false" in e for e in res["errors"])


def test_platform_export_final_allowed_now_fails():
    res = validate(_load(P + "platform_export.json"))
    assert res["valid"] is False
    assert any("platform_export_final_allowed_now_must_be_false" in e for e in res["errors"])


def test_platform_api_allowed_now_fails():
    p = _valid()
    p["output_policy"]["platform_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_live_posting_enabled_now_fails():
    p = _valid()
    p["output_policy"]["live_posting_enabled_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_scheduler_allowed_now_fails():
    p = _valid()
    p["output_policy"]["scheduler_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("scheduler_allowed_now_must_be_false" in e for e in res["errors"])


def test_newsletter_or_cms_api_allowed_now_fails():
    p = _valid()
    p["output_policy"]["newsletter_or_cms_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("newsletter_or_cms_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_credential_read_allowed_now_fails():
    p = _valid()
    p["output_policy"]["credential_read_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False


def test_repo_web_search_allowed_now_fails():
    p = _valid()
    p["output_policy"]["repo_web_search_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("repo_web_search_allowed_now_must_be_false" in e for e in res["errors"])


def test_scraping_allowed_now_fails():
    p = _valid()
    p["output_policy"]["scraping_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("scraping_allowed_now_must_be_false" in e for e in res["errors"])


def test_news_or_rss_api_allowed_now_fails():
    p = _valid()
    p["output_policy"]["news_or_rss_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("news_or_rss_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_market_data_api_allowed_now_fails():
    p = _valid()
    p["output_policy"]["market_data_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("market_data_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_manual_review_required_false_fails():
    res = validate(_load(P + "missing_manual_review.json"))
    assert res["valid"] is False
    assert any("draft_manual_review_required_must_be_true" in e for e in res["errors"])


def test_not_public_postable_false_fails():
    p = _valid()
    p["output_policy"]["not_public_postable"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("not_public_postable_must_be_true" in e for e in res["errors"])


def test_missing_source_reference_fails():
    res = validate(_load(P + "missing_source_reference.json"))
    assert res["valid"] is False
    assert any("missing_source_reference_for_claim" in e for e in res["errors"])


def test_missing_limitation_fails():
    res = validate(_load(P + "missing_limitation.json"))
    assert res["valid"] is False
    assert any("missing_limitation_note_for_claim" in e for e in res["errors"])


def test_forbidden_manual_action_allowed_fails():
    p = _valid()
    p["manual_operator_actions"]["allowed_manual_next_actions"].append("auto_publish")
    res = validate(p)
    assert res["valid"] is False
    assert any("forbidden_manual_action_allowed:auto_publish" in e for e in res["errors"])


def test_signal_language_fails():
    res = validate(_load(P + "signal_language.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_alpha_claim_without_artifact_fails():
    res = validate(_load(P + "artifact_claim.json"))
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_unsupported_numeric_claim_fails():
    res = validate(_load(P + "unsupported_numeric_claim.json"))
    assert res["valid"] is False
    assert any("unsupported_numeric_market_claim" in e for e in res["errors"])


def test_final_social_copy_representation_fails():
    res = validate(_load(P + "final_social_copy.json"))
    assert res["valid"] is False
    assert any("draft_represented_as_final_social_copy" in e for e in res["errors"])


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["output_policy"]["platform_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_summary_counters_zero_or_false():
    s = summary()
    zero_counts = [
        "repo_generated_draft_count",
        "provider_call_enabled_count",
        "repo_prompt_execution_enabled_count",
        "public_ready_allowed_count",
        "publish_ready_count",
        "final_social_copy_generated_count",
        "auto_approval_enabled_count",
        "platform_export_final_enabled_count",
        "platform_api_enabled_count",
        "live_posting_enabled_count",
        "scheduler_enabled_count",
        "newsletter_or_cms_api_enabled_count",
        "credential_read_enabled_count",
        "repo_web_search_enabled_count",
        "scraping_enabled_count",
        "news_or_rss_api_enabled_count",
        "market_data_api_enabled_count",
        "missing_source_reference_count",
        "missing_limitation_count",
        "unsafe_language_count",
        "unsupported_numeric_claim_count",
        "artifact_claim_without_real_artifact_count",
        "forbidden_manual_action_allowed_count",
    ]
    for k in zero_counts:
        assert s[k] == 0
    assert s["manual_review_required_all"] is True
    assert s["not_public_postable_all"] is True
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
        assert s[k] is False
    json.dumps(s)
