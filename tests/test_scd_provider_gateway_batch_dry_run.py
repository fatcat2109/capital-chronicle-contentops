import pytest
import json
import os
from live_contentops.scd_provider_gateway_batch_dry_run import (
    validate_provider_gateway_batch_dry_run_input,
    validate_provider_gateway_aggregate_spend_ceiling,
    validate_provider_gateway_batch_audit_manifest,
    validate_provider_gateway_batch_dry_run_report,
    build_aggregate_spend_ceiling
)

def _load(f):
    with open(os.path.join("fixtures", "scd_provider_gateway_batch_dry_run", f)) as file:
        return json.load(file)

def test_pass_multi_item():
    res = validate_provider_gateway_batch_dry_run_input(_load("pass_multi_item.json"))
    assert res["validation_state"] == "PASS"

def test_blocked_aggregate_cost_mismatch():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_aggregate_cost_mismatch.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_declared_ceiling_missing():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_declared_ceiling_missing.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_declared_ceiling_negative():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_declared_ceiling_negative.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_aggregate_cost_missing_in_ceiling():
    res = validate_provider_gateway_aggregate_spend_ceiling(_load("blocked_aggregate_cost_missing_in_ceiling.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_aggregate_cost_negative_in_ceiling():
    res = validate_provider_gateway_aggregate_spend_ceiling(_load("blocked_aggregate_cost_negative_in_ceiling.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_report_pass_while_item_blocked():
    res = validate_provider_gateway_batch_dry_run_report(_load("blocked_report_pass_while_item_blocked.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_report_pass_while_ceiling_blocked():
    res = validate_provider_gateway_batch_dry_run_report(_load("blocked_report_pass_while_ceiling_blocked.json"))
    assert res["validation_state"] == "BLOCKED"

def test_unknown_missing_item_refs():
    res = validate_provider_gateway_batch_dry_run_input(_load("unknown_missing_item_refs.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_unknown_empty_batch():
    res = validate_provider_gateway_batch_dry_run_input(_load("unknown_empty_batch.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_review_stale_cache():
    res = validate_provider_gateway_batch_dry_run_input(_load("review_stale_cache.json"))
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_pass_audit_manifest():
    res = validate_provider_gateway_batch_audit_manifest(_load("pass_audit_manifest.json"))
    assert res["validation_state"] == "PASS"

def test_unknown_audit_manifest_empty_refs():
    res = validate_provider_gateway_batch_audit_manifest(_load("unknown_audit_manifest_empty_refs.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_blocked_audit_manifest_empty_refs_claimed_pass():
    res = validate_provider_gateway_batch_audit_manifest(_load("blocked_audit_manifest_empty_refs_claimed_pass.json"))
    assert res["validation_state"] == "BLOCKED"
