import json
import pytest
from pathlib import Path
from live_contentops.adapters import linkedin

def load_fixture(name):
    p = Path(__file__).parent / "fixtures" / "linkedin_adapter" / name
    return json.loads(p.read_text(encoding="utf-8"))

def test_dry_run_success():
    req = load_fixture("valid_linkedin_dry_run_request.json")
    res = linkedin.run_linkedin_dry_run(req)
    assert "[SIMULATED LINKEDIN PREVIEW]" in res["simulated_post_preview"]
    assert "SCOPE VERIFICATION REQUIRED" in res["simulated_post_preview"]
    assert "safe_for_publish" in res and res["safe_for_publish"] is False
    assert res["linkedin_api_used"] is False

def test_dry_run_article():
    req = load_fixture("valid_linkedin_article_request.json")
    res = linkedin.run_linkedin_dry_run(req)
    assert "simulated_article_preview" in res
    assert "Simulated Article Title" in res["simulated_article_preview"]["title"]

def test_dry_run_blocked():
    req = load_fixture("blocked_source_required_request.json")
    res = linkedin.run_linkedin_dry_run(req)
    assert "[BLOCKED]" in res["simulated_post_preview"]

def test_invalid_api_used():
    req = load_fixture("invalid_linkedin_api_used_true.json")
    with pytest.raises(ValueError, match="linkedin_api_used cannot be true"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_platform_used():
    req = load_fixture("invalid_platform_api_used_true.json")
    with pytest.raises(ValueError, match="platform_api_used cannot be true"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_safe_for_publish():
    req = load_fixture("invalid_safe_for_publish_true.json")
    with pytest.raises(ValueError, match="safe_for_publish cannot be true"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_bearer_token():
    req = load_fixture("invalid_bearer_token_field.json")
    with pytest.raises(ValueError, match="Bearer/OAuth/ClientSecret-like field detected"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_client_secret():
    req = load_fixture("invalid_client_secret_field.json")
    with pytest.raises(ValueError, match="Bearer/OAuth/ClientSecret-like field detected"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_real_linkedin_url():
    req = load_fixture("invalid_real_linkedin_url_field.json")
    with pytest.raises(ValueError, match="Real-looking LinkedIn URL or ID detected"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_real_org_id():
    req = load_fixture("invalid_real_org_id_field.json")
    with pytest.raises(ValueError, match="Real-looking LinkedIn URL or ID detected"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_live_send():
    req = load_fixture("invalid_live_post_request.json")
    with pytest.raises(ValueError, match="dry_run_only must be true"):
        linkedin.run_linkedin_dry_run(req)

def test_invalid_scope_verification_false():
    req = load_fixture("invalid_scope_verification_false.json")
    with pytest.raises(ValueError, match="scope_verification_required must be true"):
        linkedin.run_linkedin_dry_run(req)

def test_staging_contract_builds():
    contract = linkedin.build_linkedin_staging_contract()
    assert contract["platform"] == "linkedin"
    assert contract["is_ready_for_credentials"] is False
    assert len(contract["prerequisites_required"]) > 10

def test_scope_checklist_builds():
    checklist = linkedin.build_linkedin_scope_verification_checklist()
    assert checklist["platform"] == "linkedin"
    assert checklist["scope_names_verified_real"] is False
    assert len(checklist["verification_items"]) >= 4
