import os
import json
import copy
from live_contentops.social_platform_foundation import (
    validate_social_platform_foundation_packet,
    summary,
)

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "social_platform_foundation")


def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("social_platform_foundation_valid.json")


def test_valid_packet_passes():
    res = validate_social_platform_foundation_packet(_valid())
    assert res["valid"] is True
    assert res["errors"] == []


def test_invalid_live_posting_enabled():
    p = _valid()
    p["platform_fit_matrix"][0]["live_posting_enabled_now"] = True
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_invalid_platform_api_allowed():
    p = _valid()
    p["platform_fit_matrix"][0]["platform_api_allowed_now"] = True
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_credential_read_allowed():
    p = _valid()
    p["platform_fit_matrix"][0]["credential_read_allowed_now"] = True
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("credential_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_scheduler_allowed():
    p = _valid()
    p["platform_fit_matrix"][0]["scheduler_allowed_now"] = True
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("scheduler_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_scraping_allowed():
    p = _valid()
    p["platform_fit_matrix"][0]["scraping_allowed_now"] = True
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("scraping_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_autonomous_reply_or_dm_allowed():
    p = _valid()
    p["platform_fit_matrix"][0]["autonomous_reply_or_dm_allowed_now"] = True
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("autonomous_reply_or_dm_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_public_ready_allowed():
    res = validate_social_platform_foundation_packet(_load("social_platform_foundation_invalid_public_ready.json"))
    assert res["valid"] is False
    assert any("public_ready_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_manual_review_required_false():
    res = validate_social_platform_foundation_packet(_load("social_platform_foundation_invalid_missing_manual_review.json"))
    assert res["valid"] is False
    assert any("manual_review_required_must_be_true" in e for e in res["errors"])


def test_invalid_not_public_postable_false():
    p = _valid()
    p["platform_fit_matrix"][0]["not_public_postable"] = False
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("not_public_postable_must_be_true" in e for e in res["errors"])


def test_invalid_signal_language():
    res = validate_social_platform_foundation_packet(_load("social_platform_foundation_invalid_signal_language.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_invalid_live_action_fixture():
    res = validate_social_platform_foundation_packet(_load("social_platform_foundation_invalid_live_action.json"))
    assert res["valid"] is False
    assert any("live_posting_enabled_now_must_be_false" in e for e in res["errors"])


def test_alpha_says_without_artifact_fails():
    p = _valid()
    p["content_lane_policy"]["example_caption"] = "Capital Chronicle alpha says this is the call"
    p["seo_newsletter_policy_linkage"]["real_approved_artifacts_present"] = False
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["platform_fit_matrix"][0]["live_posting_enabled_now"] = True
    p["packet_status"] = "pass"
    res = validate_social_platform_foundation_packet(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_summary_all_live_external_counters_zero_or_false():
    s = summary()
    assert s["live_posting_enabled_count"] == 0
    assert s["platform_api_enabled_count"] == 0
    assert s["credential_read_enabled_count"] == 0
    assert s["scheduler_enabled_count"] == 0
    assert s["scraping_enabled_count"] == 0
    assert s["autonomous_reply_dm_enabled_count"] == 0
    assert s["public_ready_allowed_count"] == 0
    assert s["unsafe_language_count"] == 0
    assert s["manual_review_required_all"] is True
    assert s["not_public_postable_all"] is True
    assert s["provider_call_used_by_repo"] is False
    assert s["search_call_used_by_repo"] is False
    assert s["network_call_used_by_repo"] is False
    assert s["platform_action_used_by_repo"] is False
    assert s["credential_or_env_read_used"] is False
    assert s["newsletter_send_enabled"] is False
    assert s["cms_integration_enabled"] is False
    assert s["platform_count"] == 8
    # JSON-serializable
    json.dumps(s)
