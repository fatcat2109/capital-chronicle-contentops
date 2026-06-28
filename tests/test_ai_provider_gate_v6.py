from live_contentops import ai_provider_gate_v6 as provider_gate

def test_default_execution_mode_is_dry_run_stub():
    assert provider_gate.get_provider_mode() == "dry_run_stub"

def test_does_not_call_live_provider_in_dry_run():
    res = provider_gate.call_llm_deferred("idea_classifier", "test idea")
    assert res["result_status"] == "review_only_stub"
    assert "stub_response" in res

def test_inspect_credentials_presence_only():
    creds = provider_gate.inspect_provider_credentials()
    assert isinstance(creds, dict)
    for key, value in creds.items():
        assert isinstance(value, bool)
        # Verify no values are exposed
        assert str(value) in ["True", "False"]

def test_zero_network_or_env_printing_dependencies():
    # Make sure we don't import requests or print raw env
    attrs = dir(provider_gate)
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "urlopen" not in attrs
