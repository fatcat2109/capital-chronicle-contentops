import os
import json
from live_contentops.daily_content_studio_markdown_export import (
    render_daily_content_studio_markdown_review,
    validate_daily_content_studio_markdown_review,
    summary,
    _load_valid_packet,
)


def _render():
    return render_daily_content_studio_markdown_review(_load_valid_packet())


def test_valid_packet_renders_markdown():
    md = _render()
    assert isinstance(md, str)
    assert len(md) > 0
    assert "Capital Chronicle ContentOps — Daily Content Studio Review Packet" in md


def test_rendered_markdown_includes_all_safety_banners():
    md = _render()
    for b in [
        "LOCAL ONLY",
        "REVIEW ONLY",
        "NOT PUBLIC-POSTABLE",
        "NO FINANCIAL ADVICE",
        "NO SIGNAL LANGUAGE",
        "NO LIVE POSTING",
        "NO PLATFORM API",
        "NO PROVIDER/LLM API",
        "NO WEB SEARCH / SCRAPING / NEWS API",
        "MANUAL REVIEW REQUIRED",
    ]:
        assert b in md


def test_rendered_markdown_includes_source_context_section():
    md = _render()
    assert "## Source Context Summary" in md
    assert "source_references_required: True" in md
    assert "limitations_required: True" in md


def test_rendered_markdown_includes_selected_angle_cards():
    md = _render()
    assert "## Selected Angle Cards (Review Only)" in md
    assert "card-1" in md


def test_rendered_markdown_includes_prompt_template_handoff_no_repo_exec():
    md = _render()
    assert "## External LLM Prompt-Template Handoff" in md
    assert "repo_executes_prompt: False" in md
    assert "The repo does not execute prompts" in md


def test_rendered_markdown_includes_platform_fit_no_live_api():
    md = _render()
    assert "## Platform-Fit Notes" in md
    assert "live_posting_enabled_now: False" in md
    assert "platform_api_allowed_now: False" in md


def test_rendered_markdown_includes_manual_operator_checklist():
    md = _render()
    assert "## Manual Operator Checklist" in md
    assert "### Allowed manual-only actions" in md
    assert "### Forbidden actions" in md


def test_rendered_markdown_includes_final_not_public_postable_status():
    md = _render()
    assert "## Final Status" in md
    assert "not_public_postable: True" in md
    assert "publish_ready: False" in md


def test_validation_passes_for_valid_render():
    res = validate_daily_content_studio_markdown_review(_render())
    assert res["export_status"] == "pass"
    assert res["errors"] == []


def test_validation_fails_if_not_public_postable_banner_removed():
    md = _render().replace("- NOT PUBLIC-POSTABLE\n", "")
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"


def test_validation_fails_if_manual_review_required_banner_removed():
    md = _render().replace("- MANUAL REVIEW REQUIRED\n", "")
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("missing_banner:MANUAL REVIEW REQUIRED" in e for e in res["errors"])


def test_validation_fails_if_publish_ready_true():
    md = _render() + "\npublish_ready=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:publish_ready=true" in e for e in res["errors"])


def test_validation_fails_if_public_ready_allowed_now_true():
    md = _render() + "\npublic_ready_allowed_now=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:public_ready_allowed_now=true" in e for e in res["errors"])


def test_validation_fails_if_live_posting_enabled():
    md = _render() + "\nlive_posting_enabled_now=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:live_posting_enabled_now=true" in e for e in res["errors"])


def test_validation_fails_if_platform_api_enabled():
    md = _render() + "\nplatform_api_allowed_now=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:platform_api_allowed_now=true" in e for e in res["errors"])


def test_validation_fails_if_provider_api_enabled():
    md = _render() + "\nprovider_call_allowed_by_repo=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:provider_call_allowed_by_repo=true" in e for e in res["errors"])


def test_validation_fails_if_web_search_enabled():
    md = _render() + "\nrepo_web_search_allowed=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:repo_web_search_allowed=true" in e for e in res["errors"])


def test_validation_fails_if_scraping_enabled():
    md = _render() + "\nrepo_scraping_allowed=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:repo_scraping_allowed=true" in e for e in res["errors"])


def test_validation_fails_if_news_api_enabled():
    md = _render() + "\nrepo_news_api_allowed=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:repo_news_api_allowed=true" in e for e in res["errors"])


def test_validation_fails_if_market_data_api_enabled():
    md = _render() + "\nrepo_market_data_api_allowed=true\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_flag_enabled:repo_market_data_api_allowed=true" in e for e in res["errors"])


def test_validation_fails_if_forbidden_manual_action_allowed():
    md = _render().replace(
        "### Allowed manual-only actions\n",
        "### Allowed manual-only actions\n- auto publish\n",
    )
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("forbidden_manual_action_allowed:auto publish" in e for e in res["errors"])


def test_validation_fails_on_unsafe_signal_language():
    md = _render() + "\nour model predicts the asset will move higher; buy now\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_validation_fails_on_alpha_claim_without_artifact():
    md = _render() + "\nCapital Chronicle alpha says this is confirmed\n"
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_validation_fails_if_source_or_limitation_sections_missing():
    md = _render().replace("source_references_required: True", "source_references_required: False")
    md = md.replace("limitations_required: True", "limitations_required: False")
    res = validate_daily_content_studio_markdown_review(md)
    assert res["export_status"] == "blocked"
    assert any("missing_source_reference_section" in e for e in res["errors"])
    assert any("missing_limitation_section" in e for e in res["errors"])


def test_summary_counters_zero_or_false():
    s = summary()
    zero_counts = [
        "forbidden_manual_action_allowed_count",
        "unsafe_language_count",
        "missing_source_reference_section_count",
        "missing_limitation_section_count",
    ]
    for k in zero_counts:
        assert s[k] == 0
    assert s["markdown_export_enabled"] is True
    assert s["review_only"] is True
    assert s["not_public_postable"] is True
    assert s["manual_review_required"] is True
    assert s["publish_ready"] is False
    assert s["public_ready_allowed_now"] is False
    assert s["final_social_copy_generated"] is False
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
