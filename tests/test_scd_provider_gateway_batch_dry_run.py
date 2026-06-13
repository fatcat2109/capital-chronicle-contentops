import pytest
import json
import os
from live_contentops.scd_provider_gateway_batch_dry_run import (
    validate_provider_gateway_batch_dry_run_input,
    validate_provider_gateway_aggregate_spend_ceiling,
    validate_provider_gateway_batch_audit_manifest,
    validate_provider_gateway_batch_dry_run_report,
    build_aggregate_spend_ceiling,
    build_batch_item_plan,
    build_batch_dry_run_report
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

def test_report_unknown_with_unknown_substate():
    res = validate_provider_gateway_batch_dry_run_report(_load("report_unknown_with_unknown_substate.json"))
    assert res["validation_state"] == "UNKNOWN"

def test_report_review_with_review_substate():
    res = validate_provider_gateway_batch_dry_run_report(_load("report_review_with_review_substate.json"))
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_report_pass_while_unknown():
    res = validate_provider_gateway_batch_dry_run_report(_load("report_pass_while_unknown.json"))
    assert res["validation_state"] == "BLOCKED"

def test_report_pass_while_review():
    res = validate_provider_gateway_batch_dry_run_report(_load("report_pass_while_review.json"))
    assert res["validation_state"] == "BLOCKED"


# --- BUILDER TESTS ---

def test_build_item_plan_pass():
    plan = build_batch_item_plan({"item_id": "i1", "estimated_cost": 0.5})
    assert plan["validation_state"] == "PASS"
    assert plan["item_id"] == "i1"
    assert plan["estimated_cost"] == 0.5

def test_build_item_plan_missing_cost_not_pass():
    plan = build_batch_item_plan({"item_id": "i1"})
    assert plan["validation_state"] != "PASS"

def test_build_item_plan_missing_item_id_not_pass():
    plan = build_batch_item_plan({"estimated_cost": 0.5})
    assert plan["validation_state"] != "PASS"

def test_build_item_plan_negative_cost():
    plan = build_batch_item_plan({"item_id": "i1", "estimated_cost": -1.0})
    assert plan["validation_state"] == "BLOCKED"

def test_build_item_plan_zero_cost_no_cache():
    plan = build_batch_item_plan({"item_id": "i1", "estimated_cost": 0.0})
    assert plan["validation_state"] == "BLOCKED"

def test_build_item_plan_zero_cost_with_valid_cache():
    plan = build_batch_item_plan({
        "item_id": "i1", 
        "estimated_cost": 0.0, 
        "cache_hit_state": "PASS", 
        "prompt_version": "current"
    })
    assert plan["validation_state"] == "PASS"

def test_build_item_plan_zero_cost_with_stale_cache():
    plan = build_batch_item_plan({
        "item_id": "i1", 
        "estimated_cost": 0.0, 
        "cache_hit_state": "PASS", 
        "prompt_version": "stale"
    })
    assert plan["validation_state"] == "REVIEW_REQUIRED"

def test_build_item_plan_ignores_unsafe_flags():
    plan = build_batch_item_plan({
        "item_id": "i1", 
        "estimated_cost": 0.5,
        "executable": True,
        "network_allowed": True
    })
    assert plan["executable"] is False
    assert plan["network_allowed"] is False
    assert plan["validation_state"] == "PASS"

def test_build_item_plan_platform_variants_requested():
    plan = build_batch_item_plan({
        "item_id": "i1", 
        "estimated_cost": 0.5,
        "platform_variants_requested": True
    })
    assert plan["platform_variants_requested"] is False
    assert plan["validation_state"] != "BLOCKED"

# --- REPORT BUILDER TESTS ---

def _valid_batch_input():
    return _load("pass_multi_item.json")

def _valid_item_plans():
    return _valid_batch_input()["batch_items"]

def _valid_ceiling():
    return {
        "schema_version": "1.0",
        "batch_id": "b1",
        "declared_spend_ceiling": 10.0,
        "aggregate_estimated_cost": 0.0,
        "item_estimated_costs": [0.0, 0.0],
        "validation_state": "PASS"
    }

def _valid_manifest():
    return _load("pass_audit_manifest.json")

def test_build_report_all_pass():
    rep = build_batch_dry_run_report(_valid_batch_input(), _valid_item_plans(), _valid_ceiling(), _valid_manifest())
    assert rep["validation_state"] == "PASS"

def test_build_report_missing_manifest():
    rep = build_batch_dry_run_report(_valid_batch_input(), _valid_item_plans(), _valid_ceiling())
    assert rep["validation_state"] == "UNKNOWN"

def test_build_report_blocked_manifest():
    m = _valid_manifest()
    m["per_item_dry_run_input_refs"] = [] 
    m["validation_state"] = "PASS" 
    rep = build_batch_dry_run_report(_valid_batch_input(), _valid_item_plans(), _valid_ceiling(), m)
    assert rep["validation_state"] == "BLOCKED"

def test_build_report_unknown_manifest():
    m = _valid_manifest()
    m["per_item_dry_run_input_refs"] = [] 
    m["validation_state"] = "UNKNOWN"
    rep = build_batch_dry_run_report(_valid_batch_input(), _valid_item_plans(), _valid_ceiling(), m)
    assert rep["validation_state"] == "UNKNOWN"

def test_build_report_blocked_batch_input():
    b = _valid_batch_input()
    b["declared_spend_ceiling"] = -1.0 
    rep = build_batch_dry_run_report(b, _valid_item_plans(), _valid_ceiling(), _valid_manifest())
    assert rep["validation_state"] == "BLOCKED"

def test_build_report_unknown_batch_input():
    b = _valid_batch_input()
    b["batch_items"] = [] 
    if "aggregate_estimated_cost" in b:
        b["aggregate_estimated_cost"] = 0.0
    rep = build_batch_dry_run_report(b, [], _valid_ceiling(), _valid_manifest())
    assert rep["validation_state"] == "UNKNOWN"

def test_build_report_blocked_item_plan():
    items = _valid_item_plans()
    items[0]["estimated_cost"] = -1.0
    rep = build_batch_dry_run_report(_valid_batch_input(), items, _valid_ceiling(), _valid_manifest())
    assert rep["validation_state"] == "BLOCKED"

def test_build_report_review_item_plan():
    items = _valid_item_plans()
    items[0]["estimated_cost"] = 0.0
    items[0]["cache_hit_state"] = "PASS"
    items[0]["prompt_version"] = "stale"
    
    b = _valid_batch_input()
    b["batch_items"] = items
    if "aggregate_estimated_cost" in b:
        b["aggregate_estimated_cost"] = sum(i.get("estimated_cost", 0.0) for i in items)
        
    rep = build_batch_dry_run_report(b, items, _valid_ceiling(), _valid_manifest())
    assert rep["validation_state"] == "REVIEW_REQUIRED"

def test_build_report_blocked_ceiling():
    c = _valid_ceiling()
    c["declared_spend_ceiling"] = -1.0
    rep = build_batch_dry_run_report(_valid_batch_input(), _valid_item_plans(), c, _valid_manifest())
    assert rep["validation_state"] == "BLOCKED"

def test_build_report_audit_manifest_state_not_from_ceiling():
    c = _valid_ceiling()
    c["validation_state"] = "REVIEW_REQUIRED"
    rep = build_batch_dry_run_report(_valid_batch_input(), _valid_item_plans(), c, _valid_manifest())
    assert rep["audit_manifest_state"] == "PASS"

def test_build_report_forged_pass_corrected():
    c = _valid_ceiling()
    c["declared_spend_ceiling"] = -1.0
    c["validation_state"] = "PASS" 
    rep = build_batch_dry_run_report(_valid_batch_input(), _valid_item_plans(), c, _valid_manifest())
    assert rep["validation_state"] == "BLOCKED"

