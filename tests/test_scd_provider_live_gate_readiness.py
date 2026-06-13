import pytest
import json
import os
from live_contentops.scd_provider_live_gate_readiness import (
    validate_provider_live_gate_readiness_input,
    validate_provider_live_gate_operator_approval,
    validate_provider_live_gate_readiness_report,
    validate_provider_live_gate_audit_manifest,
    build_provider_live_gate_readiness_report
)

def _load(f):
    with open(os.path.join("fixtures", "scd_provider_live_gate_readiness", f)) as file:
        return json.load(file)

def test_pass_readiness_input():
    res = validate_provider_live_gate_readiness_input(_load("pass_readiness_input.json"))
    assert res["validation_state"] == "PASS"

def test_pass_operator_approval():
    res = validate_provider_live_gate_operator_approval(_load("pass_operator_approval.json"))
    assert res["validation_state"] == "PASS"

def test_pass_readiness_report():
    res = validate_provider_live_gate_readiness_report(_load("pass_readiness_report.json"))
    assert res["validation_state"] == "PASS"

def test_pass_audit_manifest():
    res = validate_provider_live_gate_audit_manifest(_load("pass_audit_manifest.json"))
    assert res["validation_state"] == "PASS"

def test_review_missing_operator_approval():
    res = validate_provider_live_gate_operator_approval(_load("review_missing_operator_approval.json"))
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_review_stale_approval():
    res = validate_provider_live_gate_operator_approval(_load("review_stale_approval.json"))
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_unknown_missing_lineage_refs():
    res = validate_provider_live_gate_audit_manifest(_load("unknown_missing_lineage_refs.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_blocked_approval_says_execute():
    res = validate_provider_live_gate_operator_approval(_load("blocked_approval_says_execute.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_provider_api_allowed():
    res = validate_provider_live_gate_readiness_input(_load("blocked_provider_api_allowed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_network_allowed():
    res = validate_provider_live_gate_readiness_input(_load("blocked_network_allowed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_env_read_allowed():
    res = validate_provider_live_gate_readiness_input(_load("blocked_env_read_allowed.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_credential_lookup():
    res = validate_provider_live_gate_readiness_input(_load("blocked_credential_lookup.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_api_key_present():
    res = validate_provider_live_gate_readiness_input(_load("blocked_api_key_present.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_executable_true():
    res = validate_provider_live_gate_readiness_input(_load("blocked_executable_true.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_provider_ready():
    res = validate_provider_live_gate_readiness_input(_load("blocked_provider_ready.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_live_ready():
    res = validate_provider_live_gate_readiness_input(_load("blocked_live_ready.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_public_ready():
    res = validate_provider_live_gate_readiness_input(_load("blocked_public_ready.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_batch_dry_run_non_pass():
    res = validate_provider_live_gate_readiness_input(_load("blocked_batch_dry_run_non_pass.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_spend_ceiling_non_pass():
    res = validate_provider_live_gate_readiness_input(_load("blocked_spend_ceiling_non_pass.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_retry_loop():
    res = validate_provider_live_gate_readiness_input(_load("blocked_retry_loop.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_financial_signal():
    res = validate_provider_live_gate_readiness_input(_load("blocked_financial_signal.json"))
    assert res["validation_state"] == "BLOCKED"

def test_build_report_determinism():
    rep = build_provider_live_gate_readiness_report(
        _load("pass_readiness_input.json"),
        _load("pass_operator_approval.json"),
        _load("pass_audit_manifest.json")
    )
    assert rep["validation_state"] == "PASS"
    
    rep2 = build_provider_live_gate_readiness_report(
        _load("pass_readiness_input.json"),
        _load("blocked_approval_says_execute.json"),
        _load("pass_audit_manifest.json")
    )
    assert rep2["validation_state"] == "BLOCKED"
