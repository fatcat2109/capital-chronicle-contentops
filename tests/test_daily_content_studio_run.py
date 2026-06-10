import os
import json
from live_contentops.daily_content_studio_run import (
    validate_daily_content_studio_run_packet,
    summary,
)

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "daily_content_studio_run")


def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("daily_content_studio_run_valid.json")


def test_valid_packet_passes():
    res = validate_daily_content_studio_run_packet(_valid())
    assert res["valid"] is True
    assert res["errors"] == []


def test_invalid_repo_web_search():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_web_search.json"))
    assert res["valid"] is False
    assert any("repo_web_search_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_repo_scraping():
    p = _valid()
    p["input_policy"]["repo_scraping_allowed"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("repo_scraping_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_repo_news_api():
    p = _valid()
    p["input_policy"]["repo_news_api_allowed"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("repo_news_api_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_repo_rss_fetch():
    p = _valid()
    p["input_policy"]["repo_rss_fetch_allowed"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("repo_rss_fetch_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_repo_market_data_api():
    p = _valid()
    p["input_policy"]["repo_market_data_api_allowed"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("repo_market_data_api_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_provider_llm_api():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_provider_call.json"))
    assert res["valid"] is False
    assert any("provider_llm_api_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_platform_api():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_platform_api.json"))
    assert res["valid"] is False
    assert any("platform_api_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_credential_read():
    p = _valid()
    p["input_policy"]["credential_read_allowed"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("credential_read_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_scheduler():
    p = _valid()
    p["input_policy"]["scheduler_allowed"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("scheduler_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_newsletter_or_cms_api():
    p = _valid()
    p["input_policy"]["newsletter_or_cms_api_allowed"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("newsletter_or_cms_api_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_repo_executes_prompt():
    p = _valid()
    p["llm_writer_handoff"]["repo_executes_prompt"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("llm_repo_executes_prompt_must_be_false" in e for e in res["errors"])


def test_invalid_provider_call_allowed_by_repo():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_provider_call.json"))
    assert res["valid"] is False
    assert any("llm_provider_call_allowed_by_repo_must_be_false" in e for e in res["errors"])


def test_invalid_public_ready():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_public_ready.json"))
    assert res["valid"] is False


def test_invalid_publish_ready():
    p = _valid()
    p["output_policy"]["publish_ready"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("publish_ready_must_be_false" in e for e in res["errors"])


def test_invalid_auto_approval():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_auto_approval.json"))
    assert res["valid"] is False
    assert any("auto_approval_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_platform_export_final():
    p = _valid()
    p["output_policy"]["platform_export_final_allowed_now"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("output_platform_export_final_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_manual_review_required_false():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_missing_manual_review.json"))
    assert res["valid"] is False
    assert any("output_manual_review_required_must_be_true" in e for e in res["errors"])


def test_invalid_not_public_postable_false():
    p = _valid()
    p["output_policy"]["not_public_postable"] = False
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("output_not_public_postable_must_be_true" in e for e in res["errors"])


def test_invalid_source_references_required_false():
    p = _valid()
    p["freshness_and_limitations_policy"]["source_references_required"] = False
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("source_references_required_must_be_true" in e for e in res["errors"])


def test_invalid_limitations_required_false():
    p = _valid()
    p["freshness_and_limitations_policy"]["limitations_required"] = False
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("limitations_required_must_be_true" in e for e in res["errors"])


def test_invalid_missing_source_lineage():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_missing_source_lineage.json"))
    assert res["valid"] is False
    assert any("source_lineage_missing" in e for e in res["errors"])


def test_invalid_signal_language():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_signal_language.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_invalid_alpha_claim_without_artifact():
    res = validate_daily_content_studio_run_packet(_load("daily_content_studio_run_invalid_artifact_claim.json"))
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_invalid_unsupported_numeric_claim():
    p = _valid()
    p["selected_angle_cards"][0]["note"] = "this fake alpha note reports unsupported numeric figures"
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("unsupported_numeric_market_claim" in e for e in res["errors"])


def test_invalid_forbidden_manual_action():
    p = _valid()
    p["manual_operator_actions"].append("auto_publish")
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("forbidden_manual_action:auto_publish" in e for e in res["errors"])


def test_invalid_handoff_live_execution_enabled():
    p = _valid()
    p["platform_foundation_handoff"]["live_posting_enabled_now"] = True
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("platform_live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_summary_all_live_external_counters_zero_or_false():
    s = summary()
    zero_counts = [
        "repo_web_search_enabled_count",
        "repo_scraping_enabled_count",
        "repo_news_api_enabled_count",
        "repo_rss_fetch_enabled_count",
        "repo_market_data_api_enabled_count",
        "provider_llm_api_enabled_count",
        "platform_api_enabled_count",
        "credential_read_enabled_count",
        "scheduler_enabled_count",
        "newsletter_or_cms_api_enabled_count",
        "public_ready_allowed_count",
        "publish_ready_count",
        "auto_approval_enabled_count",
        "platform_export_final_enabled_count",
        "unsafe_language_count",
        "unsupported_numeric_claim_count",
        "artifact_claim_without_real_artifact_count",
    ]
    for k in zero_counts:
        assert s[k] == 0
    bool_true = [
        "manual_review_required_all",
        "not_public_postable_all",
        "source_references_required_all",
        "limitations_required_all",
    ]
    for k in bool_true:
        assert s[k] is True
    bool_false = [
        "provider_call_used_by_repo",
        "search_call_used_by_repo",
        "network_call_used_by_repo",
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


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["input_policy"]["repo_web_search_allowed"] = True
    p["packet_status"] = "pass"
    res = validate_daily_content_studio_run_packet(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])
