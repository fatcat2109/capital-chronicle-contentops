import json
import pytest
from pathlib import Path
from live_contentops.adapters import instagram

def load_fixture(name):
    p = Path(__file__).parent / "fixtures" / "instagram_asset_export" / name
    return json.loads(p.read_text(encoding="utf-8"))

def test_dry_run_success():
    req = load_fixture("valid_instagram_asset_package_request.json")
    res = instagram.run_instagram_asset_export_dry_run(req)
    assert "[SIMULATED ASSET PACKAGE]" in res["caption_preview"]
    assert "META CAPABILITY REVIEW REQUIRED" in res["caption_preview"]
    assert "safe_for_publish" in res and res["safe_for_publish"] is False
    assert res["instagram_api_used"] is False

def test_dry_run_carousel():
    req = load_fixture("valid_carousel_request.json")
    res = instagram.run_instagram_asset_export_dry_run(req)
    assert "carousel_plan" in res

def test_dry_run_story():
    req = load_fixture("valid_story_request.json")
    res = instagram.run_instagram_asset_export_dry_run(req)
    assert "story_plan" in res

def test_dry_run_reel():
    req = load_fixture("valid_reel_request.json")
    res = instagram.run_instagram_asset_export_dry_run(req)
    assert "reel_plan" in res

def test_dry_run_blocked():
    req = load_fixture("blocked_source_required_request.json")
    res = instagram.run_instagram_asset_export_dry_run(req)
    assert "[BLOCKED]" in res["caption_preview"]

def test_invalid_api_used():
    req = load_fixture("invalid_instagram_api_used_true.json")
    with pytest.raises(ValueError, match="instagram_api_used cannot be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_meta_api_used():
    req = load_fixture("invalid_meta_api_used_true.json")
    with pytest.raises(ValueError, match="meta_api_used cannot be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_graph_api_used():
    req = load_fixture("invalid_graph_api_used_true.json")
    with pytest.raises(ValueError, match="graph_api_used cannot be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_platform_used():
    req = load_fixture("invalid_platform_api_used_true.json")
    with pytest.raises(ValueError, match="platform_api_used cannot be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_upload_enabled():
    req = load_fixture("invalid_upload_enabled_true.json")
    with pytest.raises(ValueError, match="upload_enabled cannot be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_safe_for_publish():
    req = load_fixture("invalid_safe_for_publish_true.json")
    with pytest.raises(ValueError, match="safe_for_publish cannot be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_bearer_token():
    req = load_fixture("invalid_bearer_token_field.json")
    with pytest.raises(ValueError, match="Bearer/OAuth/ClientSecret/AppSecret-like field detected"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_app_secret():
    req = load_fixture("invalid_app_secret_field.json")
    with pytest.raises(ValueError, match="Bearer/OAuth/ClientSecret/AppSecret-like field detected"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_real_instagram_url():
    req = load_fixture("invalid_real_instagram_url_field.json")
    with pytest.raises(ValueError, match="Real-looking Instagram/Meta URL, handle, or ID detected"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_real_account_id():
    req = load_fixture("invalid_real_account_id_field.json")
    with pytest.raises(ValueError, match="Real-looking Instagram/Meta URL, handle, or ID detected"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_live_upload():
    req = load_fixture("invalid_live_upload_request.json")
    with pytest.raises(ValueError, match="dry_run_only must be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_invalid_meta_capability_review_false():
    req = load_fixture("invalid_meta_capability_review_false.json")
    with pytest.raises(ValueError, match="meta_capability_review_required must be true"):
        instagram.run_instagram_asset_export_dry_run(req)

def test_staging_contract_builds():
    contract = instagram.build_instagram_staging_contract()
    assert contract["platform"] == "instagram"
    assert contract["is_ready_for_credentials"] is False
    assert len(contract["prerequisites_required"]) > 10

def test_capability_checklist_builds():
    checklist = instagram.build_meta_capability_review_checklist()
    assert checklist["platform"] == "instagram"
    assert checklist["permission_names_verified_real"] is False
    assert len(checklist["verification_items"]) >= 4
