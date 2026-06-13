import pytest
import json
import os
from live_contentops.scd_provider_api_gate_contract import (
    validate_provider_credential_envelope,
    validate_explicit_api_gate_policy,
    validate_provider_api_request_budget,
    validate_provider_api_gate_readiness_report,
    validate_provider_api_gate_audit_manifest,
    build_provider_api_gate_readiness_report
)

def _load(f):
    with open(os.path.join("fixtures", "scd_provider_api_gate_contract", f)) as file:
        return json.load(file)

def test_pass_credential_envelope():
    res = validate_provider_credential_envelope(_load("pass_credential_envelope.json"))
    assert res["validation_state"] == "PASS"

def test_pass_api_gate_policy():
    res = validate_explicit_api_gate_policy(_load("pass_api_gate_policy.json"))
    assert res["validation_state"] == "PASS"

def test_pass_request_budget():
    res = validate_provider_api_request_budget(_load("pass_request_budget.json"))
    assert res["validation_state"] == "PASS"

def test_pass_audit_manifest():
    res = validate_provider_api_gate_audit_manifest(_load("pass_audit_manifest.json"))
    assert res["validation_state"] == "PASS"

def test_pass_readiness_report():
    res = validate_provider_api_gate_readiness_report(_load("pass_readiness_report.json"))
    assert res["validation_state"] == "PASS"

def test_unknown_missing_credential_slot_refs():
    res = validate_provider_credential_envelope(_load("unknown_missing_credential_slot_refs.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_unknown_missing_audit_lineage_refs():
    res = validate_provider_api_gate_audit_manifest(_load("unknown_missing_audit_lineage_refs.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_review_stale_operator_api_approval():
    res = validate_provider_api_gate_readiness_report(_load("review_stale_operator_api_approval.json"))
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_blocked_raw_api_key_in_envelope():
    res = validate_provider_credential_envelope(_load("blocked_raw_api_key_in_envelope.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_bearer_token_in_envelope():
    res = validate_provider_credential_envelope(_load("blocked_bearer_token_in_envelope.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_credential_value_present():
    res = validate_provider_credential_envelope(_load("blocked_credential_value_present.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_env_read_allowed():
    res = validate_provider_api_gate_readiness_report(_load("blocked_env_read_allowed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_env_read_performed():
    res = validate_provider_credential_envelope(_load("blocked_env_read_performed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_credential_lookup_performed():
    res = validate_provider_credential_envelope(_load("blocked_credential_lookup_performed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_provider_client_constructed():
    res = validate_explicit_api_gate_policy(_load("blocked_provider_client_constructed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_network_allowed():
    res = validate_explicit_api_gate_policy(_load("blocked_network_allowed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_executable():
    res = validate_explicit_api_gate_policy(_load("blocked_executable.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_real_url():
    res = validate_explicit_api_gate_policy(_load("blocked_real_url.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_request_budget_missing():
    res = validate_provider_api_request_budget(_load("blocked_request_budget_missing.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_request_budget_negative():
    res = validate_provider_api_request_budget(_load("blocked_request_budget_negative.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_provider_not_allowlisted():
    res = validate_explicit_api_gate_policy(_load("blocked_provider_not_allowlisted.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_operator_wording():
    res = validate_provider_api_gate_readiness_report(_load("blocked_operator_wording.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_public_ready_true():
    res = validate_provider_api_gate_readiness_report(_load("blocked_public_ready_true.json"))
    assert res["validation_state"] == "BLOCKED"

def test_build_provider_api_gate_readiness_report():
    rep = build_provider_api_gate_readiness_report(
        _load("pass_credential_envelope.json"),
        _load("pass_api_gate_policy.json"),
        _load("pass_request_budget.json"),
        _load("pass_audit_manifest.json")
    )
    assert rep["validation_state"] == "PASS"
    
    rep2 = build_provider_api_gate_readiness_report(
        _load("pass_credential_envelope.json"),
        _load("pass_api_gate_policy.json"),
        _load("blocked_request_budget_negative.json"),
        _load("pass_audit_manifest.json")
    )
    assert rep2["validation_state"] == "BLOCKED"
