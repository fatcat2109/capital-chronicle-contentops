import pytest
import json
import os
from live_contentops.scd_provider_gateway_batch_dry_run import (
    validate_provider_gateway_batch_dry_run_input,
    validate_provider_gateway_aggregate_spend_ceiling,
    validate_provider_gateway_batch_audit_manifest,
    build_aggregate_spend_ceiling
)

def _load(f):
    with open(os.path.join("fixtures", "scd_provider_gateway_batch_dry_run", f)) as file:
        return json.load(file)

def test_pass_single_item():
    res = validate_provider_gateway_batch_dry_run_input(_load("pass_single_item.json"))
    assert res["validation_state"] == "PASS"

def test_pass_multi_item():
    d = _load("pass_multi_item.json")
    res = validate_provider_gateway_batch_dry_run_input(d)
    assert res["validation_state"] == "PASS"
    agg = build_aggregate_spend_ceiling(d["batch_items"], d["declared_spend_ceiling"])
    assert validate_provider_gateway_aggregate_spend_ceiling(agg)["validation_state"] == "PASS"
    assert agg["aggregate_estimated_cost"] == 3.0

def test_pass_cache_hit_current():
    res = validate_provider_gateway_batch_dry_run_input(_load("pass_cache_hit_current.json"))
    assert res["validation_state"] == "PASS"

def test_blocked_aggregate_cost_above():
    d = _load("blocked_aggregate_cost_above.json")
    agg = build_aggregate_spend_ceiling(d["batch_items"], d["declared_spend_ceiling"])
    assert validate_provider_gateway_aggregate_spend_ceiling(agg)["validation_state"] == "BLOCKED"

def test_blocked_item_non_pass():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_item_non_pass.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_executable_true():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_executable_true.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_api_key_present():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_api_key_present.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_negative_cost():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_negative_cost.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_retry_loop():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_retry_loop.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_platform_variants():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_platform_variants.json"))
    assert res["validation_state"] == "BLOCKED"

def test_blocked_financial_signal():
    res = validate_provider_gateway_batch_dry_run_input(_load("blocked_financial_signal.json"))
    assert res["validation_state"] == "BLOCKED"

def test_review_stale_cache():
    res = validate_provider_gateway_batch_dry_run_input(_load("review_stale_cache.json"))
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_unknown_empty_batch():
    res = validate_provider_gateway_batch_dry_run_input(_load("unknown_empty_batch.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_pass_audit_manifest():
    res = validate_provider_gateway_batch_audit_manifest(_load("pass_audit_manifest.json"))
    assert res["validation_state"] == "PASS"

def test_mutations():
    # test blocked cost mismatch (manually passing incorrect aggregate cost)
    res = validate_provider_gateway_aggregate_spend_ceiling({
        "schema_version": "1.0", "batch_id": "b",
        "declared_spend_ceiling": 5.0, "aggregate_estimated_cost": 6.0, "validation_state": "PASS"
    })
    assert res["validation_state"] == "BLOCKED"
