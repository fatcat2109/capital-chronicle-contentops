import json
import pytest
from pathlib import Path
from live_contentops.adapters import x_adapter

def load_fixture(name):
    p = Path(__file__).parent / "fixtures" / "x_adapter" / name
    return json.loads(p.read_text(encoding="utf-8"))

def test_dry_run_success():
    req = load_fixture("valid_x_dry_run_request.json")
    res = x_adapter.run_x_dry_run(req)
    assert "[SIMULATED POST PREVIEW]" in res["simulated_post_preview"]
    assert "safe_for_publish" in res and res["safe_for_publish"] is False
    assert res["x_api_used"] is False

def test_dry_run_thread():
    req = load_fixture("valid_x_thread_request.json")
    res = x_adapter.run_x_dry_run(req)
    assert "simulated_thread_preview" in res
    assert res["thread_part_count"] > 1

def test_dry_run_blocked():
    req = load_fixture("blocked_source_required_request.json")
    res = x_adapter.run_x_dry_run(req)
    assert "[BLOCKED]" in res["simulated_post_preview"]

def test_invalid_api_used():
    req = load_fixture("invalid_x_api_used_true.json")
    with pytest.raises(ValueError, match="x_api_used cannot be true"):
        x_adapter.run_x_dry_run(req)

def test_invalid_platform_used():
    req = load_fixture("invalid_platform_api_used_true.json")
    with pytest.raises(ValueError, match="platform_api_used cannot be true"):
        x_adapter.run_x_dry_run(req)

def test_invalid_safe_for_publish():
    req = load_fixture("invalid_safe_for_publish_true.json")
    with pytest.raises(ValueError, match="safe_for_publish cannot be true"):
        x_adapter.run_x_dry_run(req)

def test_invalid_bearer_token():
    req = load_fixture("invalid_bearer_token_field.json")
    with pytest.raises(ValueError, match="Bearer/OAuth-token-like field detected"):
        x_adapter.run_x_dry_run(req)

def test_invalid_real_handle():
    req = load_fixture("invalid_real_handle_field.json")
    with pytest.raises(ValueError, match="Real-looking handle or ID detected"):
        x_adapter.run_x_dry_run(req)

def test_invalid_real_tweet_id():
    req = load_fixture("invalid_real_tweet_id_field.json")
    with pytest.raises(ValueError, match="Real-looking handle or ID detected"):
        x_adapter.run_x_dry_run(req)

def test_invalid_live_send():
    req = load_fixture("invalid_live_post_request.json")
    with pytest.raises(ValueError, match="dry_run_only must be true"):
        x_adapter.run_x_dry_run(req)

def test_staging_contract_builds():
    contract = x_adapter.build_x_staging_contract()
    assert contract["platform"] == "x"
    assert contract["is_ready_for_credentials"] is False
    assert len(contract["prerequisites_required"]) > 10
