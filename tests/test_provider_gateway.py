import json
import pytest
from pathlib import Path
from live_contentops import provider_gateway, policy_rules

def load_fixture(name):
    p = Path(__file__).parent / "fixtures" / "provider_gateway" / name
    return json.loads(p.read_text(encoding="utf-8"))

def test_provider_status_disabled():
    assert provider_gateway.PROVIDER_STATUS[provider_gateway.OPENAI_FUTURE_ONLY]["disabled"] is True
    assert provider_gateway.PROVIDER_STATUS[provider_gateway.ANTHROPIC_FUTURE_ONLY]["disabled"] is True
    assert provider_gateway.PROVIDER_STATUS[provider_gateway.DRY_RUN_SIMULATOR]["disabled"] is False

def test_dry_run_success():
    req = load_fixture("valid_dry_run_request.json")
    res = provider_gateway.run_provider_dry_run(req)
    assert "[SIMULATED OUTPUT]" in res["simulated_output_text"]
    assert "safe candidate outline" in res["simulated_output_text"]
    assert res["safe_for_publish"] is False
    assert res["provider_call_used"] is False

def test_dry_run_blocked():
    req = load_fixture("blocked_source_required_request.json")
    res = provider_gateway.run_provider_dry_run(req)
    assert "[BLOCKED]" in res["simulated_output_text"]
    assert "blocked due to policy/source state" in res["simulated_output_text"]
    assert len(res["candidate_outputs"]) == 0

def test_invalid_provider():
    req = load_fixture("invalid_live_provider_request.json")
    with pytest.raises(ValueError, match="Only DRY_RUN_SIMULATOR is currently permitted"):
        provider_gateway.run_provider_dry_run(req)

def test_invalid_provider_call():
    req = load_fixture("invalid_provider_call_used_true.json")
    with pytest.raises(ValueError, match="provider_call_used cannot be true"):
        provider_gateway.run_provider_dry_run(req)

def test_invalid_network():
    req = load_fixture("invalid_network_used_true.json")
    with pytest.raises(ValueError, match="network_used cannot be true"):
        provider_gateway.run_provider_dry_run(req)

def test_invalid_safe_for_publish():
    req = load_fixture("invalid_safe_for_publish_true.json")
    with pytest.raises(ValueError, match="safe_for_publish cannot be true"):
        provider_gateway.run_provider_dry_run(req)

def test_invalid_secret_field():
    req = load_fixture("invalid_secret_field.json")
    with pytest.raises(ValueError, match="Secret-like field detected"):
        provider_gateway.run_provider_dry_run(req)
