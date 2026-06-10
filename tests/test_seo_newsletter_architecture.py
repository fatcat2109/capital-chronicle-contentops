import os
import json
from live_contentops.seo_newsletter_architecture import validate_seo_newsletter_architecture_packet, validate_newsletter_issue_blueprint_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "seo_newsletter_architecture")

def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_architecture():
    res = validate_seo_newsletter_architecture_packet(_load("valid_content_architecture_spec.json"))
    assert res["valid"] is True

def test_valid_blueprint():
    res = validate_newsletter_issue_blueprint_packet(_load("valid_newsletter_issue_blueprint.json"))
    assert res["valid"] is True

def test_invalid_public_ready_true():
    res = validate_seo_newsletter_architecture_packet(_load("invalid_public_ready_true.json"))
    assert res["valid"] is False
    assert any("seo_public_ready_allowed_now_must_be_false" in e for e in res["errors"])

def test_invalid_live_newsletter_send_enabled():
    res = validate_seo_newsletter_architecture_packet(_load("invalid_live_newsletter_send_enabled.json"))
    assert res["valid"] is False
    assert any("newsletter_send_enabled_now_must_be_false" in e for e in res["errors"])

def test_invalid_seo_claim_without_source():
    res = validate_seo_newsletter_architecture_packet(_load("invalid_seo_claim_without_source.json"))
    assert res["valid"] is False
    assert any("seo_claim_without_source_detected" in e for e in res["errors"])

def test_invalid_trading_signal_keyword_strategy():
    res = validate_seo_newsletter_architecture_packet(_load("invalid_trading_signal_keyword_strategy.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])

def test_invalid_missing_safety_disclaimer():
    res = validate_seo_newsletter_architecture_packet(_load("invalid_missing_safety_disclaimer.json"))
    assert res["valid"] is False
    assert any("missing_safety_disclaimer" in e for e in res["errors"])

def test_invalid_external_platform_integration_enabled():
    res = validate_seo_newsletter_architecture_packet(_load("invalid_external_platform_integration_enabled.json"))
    assert res["valid"] is False
    assert any("external_integration_enabled" in e for e in res["errors"])
