import os
import json
from live_contentops.daily_content_studio_ui_data_contract import (
    validate_daily_content_studio_ui_data_contract_packet as validate,
    summary,
)

FIX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "fixtures",
    "daily_content_studio_ui",
)


def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("daily_content_studio_ui_data_contract_valid.json")


P = "daily_content_studio_ui_data_contract_invalid_"


def test_valid_packet_passes():
    res = validate(_valid())
    assert res["valid"] is True
    assert res["errors"] == []


def test_local_fixture_only_false_fails():
    p = _valid()
    p["local_fixture_only"] = False
    p["output_policy"]["local_fixture_only"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("local_fixture_only_must_be_true" in e for e in res["errors"])


def test_backend_server_required_fails():
    p = _valid()
    p["backend_server_required"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("backend_server_required_must_be_false" in e for e in res["errors"])


def test_frontend_implementation_included_fails():
    p = _valid()
    p["frontend_implementation_included"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("frontend_implementation_included_must_be_false" in e for e in res["errors"])


def test_live_posting_enabled_now_fails():
    res = validate(_load(P + "live_action.json"))
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_platform_api_allowed_now_fails():
    res = validate(_load(P + "platform_api.json"))
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_provider_llm_api_allowed_now_fails():
    res = validate(_load(P + "provider_call.json"))
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
    assert any("scraping_allowed_now_must_be_false" in e for e in res["errors"])


def test_scheduler_allowed_now_fails():
    p = _valid()
    p["scheduler_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("scheduler_allowed_now_must_be_false" in e for e in res["errors"])


def test_newsletter_or_cms_api_allowed_now_fails():
    p = _valid()
    p["newsletter_or_cms_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("newsletter_or_cms_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_credential_read_allowed_now_fails():
    p = _valid()
    p["credential_read_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("credential_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_public_ready_allowed_now_fails():
    res = validate(_load(P + "public_ready.json"))
    assert res["valid"] is False
    assert any("public_ready_allowed_now_must_be_false" in e for e in res["errors"])


def test_publish_ready_fails():
    p = _valid()
    p["publish_ready"] = True
    res = validate(p)
    assert res["valid"] is False


def test_final_social_copy_generated_fails():
    p = _valid()
    p["final_social_copy_generated"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("final_social_copy_generated_must_be_false" in e for e in res["errors"])


def test_manual_review_required_false_fails():
    res = validate(_load(P + "missing_manual_review.json"))
    assert res["valid"] is False
    assert any("section_manual_review_required_must_be_true" in e for e in res["errors"])


def test_not_public_postable_false_fails():
    p = _valid()
    p["screen_sections"][1]["not_public_postable"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("section_not_public_postable_must_be_true" in e for e in res["errors"])


def test_limitations_visible_false_fails():
    res = validate(_load(P + "hidden_limitations.json"))
    assert res["valid"] is False
    assert any("section_limitations_not_visible" in e for e in res["errors"])


def test_source_references_visible_false_fails():
    p = _valid()
    p["screen_sections"][2]["source_references_visible"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("section_source_references_not_visible" in e for e in res["errors"])


def test_missing_safety_banner_fails():
    res = validate(_load(P + "missing_safety_banner.json"))
    assert res["valid"] is False
    assert any("missing_safety_banner:NOT PUBLIC-POSTABLE" in e for e in res["errors"])


def test_forbidden_operator_action_allowed_fails():
    p = _valid()
    p["allowed_operator_actions"].append("auto_publish")
    res = validate(p)
    assert res["valid"] is False
    assert any("forbidden_operator_action_allowed:auto_publish" in e for e in res["errors"])


def test_signal_language_fails():
    res = validate(_load(P + "signal_language.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_alpha_claim_without_artifact_fails():
    p = _valid()
    p["view_model"]["summary"] = "Capital Chronicle alpha says this is confirmed"
    res = validate(p)
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_hidden_blockers_fails():
    p = _valid()
    p["screen_sections"][9]["blocked_actions_visible"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("section_blocked_actions_not_visible" in e for e in res["errors"])


def test_final_ready_to_post_representation_fails():
    res = validate(_load(P + "final_social_copy.json"))
    assert res["valid"] is False
    assert any("view_model_represents_final_social_copy" in e for e in res["errors"])


def test_missing_linked_contract_fails():
    p = _valid()
    del p["source_contracts"]["social_platform_foundation"]
    res = validate(p)
    assert res["valid"] is False
    assert any("missing_linked_contract:social_platform_foundation" in e for e in res["errors"])


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["platform_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_summary_counters_zero_or_false():
    s = summary()
    zero_counts = [
        "live_posting_enabled_count",
        "platform_api_enabled_count",
        "provider_llm_api_enabled_count",
        "repo_web_search_enabled_count",
        "scraping_enabled_count",
        "scheduler_enabled_count",
        "newsletter_or_cms_api_enabled_count",
        "credential_read_enabled_count",
        "public_ready_allowed_count",
        "publish_ready_count",
        "final_social_copy_generated_count",
        "forbidden_operator_action_enabled_count",
        "unsafe_language_count",
    ]
    for k in zero_counts:
        assert s[k] == 0
    assert s["local_fixture_only"] is True
    assert s["backend_server_required"] is False
    assert s["frontend_implementation_included"] is False
    assert s["manual_review_required_all"] is True
    assert s["not_public_postable_all"] is True
    assert s["limitations_visible_all"] is True
    assert s["source_references_visible_all"] is True
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
