import os
import json
from live_contentops.credential_envelope_policy import validate_credential_envelope_policy_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "credential_envelope_policy")

def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_no_credentials_loaded_policy():
    res = validate_credential_envelope_policy_packet(_load("valid_no_credentials_loaded_policy.json"))
    assert res["valid"] is True

def test_valid_future_live_gate_placeholder_policy():
    res = validate_credential_envelope_policy_packet(_load("valid_future_live_gate_placeholder_policy.json"))
    assert res["valid"] is True

def test_invalid_credential_read_allowed_now():
    res = validate_credential_envelope_policy_packet(_load("invalid_credential_read_allowed_now.json"))
    assert res["valid"] is False
    assert any("credential_read_allowed_now_must_be_false" in e for e in res["errors"])

def test_invalid_env_file_access_allowed():
    res = validate_credential_envelope_policy_packet(_load("invalid_env_file_access_allowed.json"))
    assert res["valid"] is False
    assert any("env_file_accessed_must_be_false" in e for e in res["errors"])

def test_invalid_unredacted_secret_value():
    res = validate_credential_envelope_policy_packet(_load("invalid_unredacted_secret_value.json"))
    assert res["valid"] is False
    assert any("unsafe_secret_detected" in e for e in res["errors"])

def test_invalid_platform_api_enabled_now():
    res = validate_credential_envelope_policy_packet(_load("invalid_platform_api_enabled_now.json"))
    assert res["valid"] is False
    assert any("platform_api_call_allowed_now_must_be_false" in e for e in res["errors"])

def test_invalid_runtime_authority_true():
    res = validate_credential_envelope_policy_packet(_load("invalid_runtime_authority_true.json"))
    assert res["valid"] is False
    assert "runtime_authority_must_be_false" in res["errors"]

def test_packet_status_pass_but_errors_exist():
    p = _load("valid_no_credentials_loaded_policy.json")
    p["credential_records"][0]["credential_read_allowed_now"] = True
    res = validate_credential_envelope_policy_packet(p)
    assert res["valid"] is False
    assert "packet_status_pass_but_errors_exist" in res["errors"]
    assert any("credential_read_allowed_now_must_be_false" in e for e in res["errors"])
