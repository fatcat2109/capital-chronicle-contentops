import os
import json
from live_contentops.daily_content_studio_operator_decision_ledger import (
    validate_daily_content_studio_operator_decision_ledger_packet as validate,
    summary,
)

FIX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "fixtures",
    "daily_content_studio_decision_ledger",
)


def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("daily_content_studio_decision_ledger_valid.json")


def test_valid_packet_passes():
    res = validate(_valid())
    assert res["valid"] is True
    assert res["errors"] == []


def test_invalid_forbidden_state_live_publish():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_live_publish_approval.json"))
    assert res["valid"] is False
    assert any("forbidden_decision_state:approved_for_live_publish" in e for e in res["errors"])


def test_invalid_forbidden_state_auto_publish():
    p = _valid()
    p["decision_records"][0]["decision_state"] = "approved_for_auto_publish"
    res = validate(p)
    assert res["valid"] is False
    assert any("forbidden_decision_state:approved_for_auto_publish" in e for e in res["errors"])


def test_invalid_live_publish_approval_allowed_now():
    p = _valid()
    p["decision_policy"]["live_publish_approval_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("live_publish_approval_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_live_publish_approval_granted():
    p = _valid()
    p["decision_records"][0]["live_publish_approval_granted"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("record_live_publish_approval_must_be_false" in e for e in res["errors"])


def test_invalid_platform_api_allowed_now():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_platform_api.json"))
    assert res["valid"] is False
    assert any("platform_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_platform_api_approval_granted():
    p = _valid()
    p["decision_records"][0]["platform_api_approval_granted"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("record_platform_api_approval_must_be_false" in e for e in res["errors"])


def test_invalid_provider_llm_api_allowed_now():
    p = _valid()
    p["decision_policy"]["provider_llm_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("provider_llm_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_provider_call_approval_granted():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_provider_call.json"))
    assert res["valid"] is False
    assert any("record_provider_call_approval_must_be_false" in e for e in res["errors"])


def test_invalid_scheduler_allowed_now():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_scheduler.json"))
    assert res["valid"] is False
    assert any("scheduler_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_scheduler_approval_granted():
    p = _valid()
    p["decision_records"][0]["scheduler_approval_granted"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("record_scheduler_approval_must_be_false" in e for e in res["errors"])


def test_invalid_newsletter_or_cms_api_allowed_now():
    p = _valid()
    p["decision_policy"]["newsletter_or_cms_api_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("newsletter_or_cms_api_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_newsletter_or_cms_send_approval_granted():
    p = _valid()
    p["decision_records"][0]["newsletter_or_cms_send_approval_granted"] = True
    res = validate(p)
    assert res["valid"] is False


def test_invalid_credential_read_allowed_now():
    p = _valid()
    p["decision_policy"]["credential_read_allowed_now"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("credential_read_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_auto_approval_allowed():
    p = _valid()
    p["decision_policy"]["auto_approval_allowed"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("auto_approval_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_public_ready_allowed_now():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_public_ready.json"))
    assert res["valid"] is False
    assert any("public_ready_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_publish_ready():
    p = _valid()
    p["decision_policy"]["publish_ready"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("publish_ready_must_be_false" in e for e in res["errors"])


def test_invalid_final_social_copy_generated():
    p = _valid()
    p["decision_policy"]["final_social_copy_generated"] = True
    res = validate(p)
    assert res["valid"] is False
    assert any("final_social_copy_generated_must_be_false" in e for e in res["errors"])


def test_invalid_manual_review_required_false():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_missing_manual_review.json"))
    assert res["valid"] is False
    assert any("record_manual_review_required_must_be_true" in e for e in res["errors"])


def test_invalid_not_public_postable_false():
    p = _valid()
    p["decision_records"][0]["not_public_postable"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("record_not_public_postable_must_be_true" in e for e in res["errors"])


def test_invalid_missing_source_lineage():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_missing_source_lineage.json"))
    assert res["valid"] is False
    assert any("source_lineage_required_must_be_true" in e for e in res["errors"])


def test_invalid_missing_limitations():
    p = _valid()
    p["source_lineage_policy"]["limitations_required"] = False
    res = validate(p)
    assert res["valid"] is False
    assert any("limitations_required_must_be_true" in e for e in res["errors"])


def test_invalid_forbidden_manual_action_allowed():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_forbidden_manual_action.json"))
    assert res["valid"] is False
    assert any("forbidden_manual_action_allowed:auto_publish" in e for e in res["errors"])


def test_invalid_signal_language():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_signal_language.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_invalid_alpha_claim_without_artifact():
    res = validate(_load("daily_content_studio_decision_ledger_invalid_artifact_claim.json"))
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_invalid_unsupported_numeric_claim():
    p = _valid()
    p["decision_records"][0]["operator_notes"] = "this note has fake alpha numbers"
    res = validate(p)
    assert res["valid"] is False
    assert any("unsupported_numeric_market_claim" in e for e in res["errors"])


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["decision_policy"]["platform_api_allowed_now"] = True
    p["packet_status"] = "pass"
    res = validate(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])


def test_summary_counters_zero_or_false():
    s = summary()
    zero_counts = [
        "forbidden_decision_state_count",
        "publish_ready_count",
        "public_ready_allowed_count",
        "live_publish_approval_count",
        "platform_api_approval_count",
        "provider_call_approval_count",
        "scheduler_approval_count",
        "newsletter_or_cms_send_approval_count",
        "auto_approval_enabled_count",
        "final_social_copy_generated_count",
        "forbidden_manual_action_allowed_count",
        "unsafe_language_count",
        "unsupported_numeric_claim_count",
        "artifact_claim_without_real_artifact_count",
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
