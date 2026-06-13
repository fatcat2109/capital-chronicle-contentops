"""Local-only provider-gateway dry-run batch plan and aggregate spend ceiling contract (SCD, 0174BC)."""
from live_contentops.scd_domain_model import PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN, _schema_ok, _result
from live_contentops.scd_canonical_draft_lifecycle import _common_safety_blocks

def _rollup(states):
    if BLOCKED in states: return BLOCKED
    if UNKNOWN in states: return UNKNOWN
    if REVIEW_REQUIRED in states: return REVIEW_REQUIRED
    return PASS

def validate_provider_gateway_batch_item_plan(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_batch_item_plan.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    if "item_id" not in packet: blocked.append("item_id missing")
    
    if packet.get("platform_variants_requested"):
        blocked.append("platform variants forbidden in this batch task")

    if not packet.get("dry_run_only"): blocked.append("dry_run_only must be true")
    if packet.get("executable"): blocked.append("executable must be false")
    if packet.get("provider_api_allowed"): blocked.append("provider_api_allowed must be false")
    if packet.get("network_allowed"): blocked.append("network_allowed must be false")
    if packet.get("credentials_required"): blocked.append("credentials_required must be false")
    if packet.get("env_read_performed"): blocked.append("env_read_performed must be false")
    if packet.get("api_key_present"): blocked.append("api_key_present must be false")

    cost = packet.get("estimated_cost")
    if cost is None or not isinstance(cost, (int, float)) or cost < 0:
        blocked.append("estimated_cost must be present and non-negative")
    else:
        if cost == 0:
            if packet.get("cache_hit_state") == PASS and packet.get("prompt_version") == "current":
                pass
            elif packet.get("cache_hit_state") == PASS and packet.get("prompt_version") == "stale":
                review.append("stale cache hit")
            else:
                blocked.append("zero estimated provider cost requires valid cache hit")
                
    return _result(blocked, review, unknown)

def validate_provider_gateway_batch_dry_run_input(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_batch_dry_run_input.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    ceiling = packet.get("declared_spend_ceiling")
    if ceiling is None or not isinstance(ceiling, (int, float)) or ceiling < 0:
        blocked.append("declared_spend_ceiling must be present and non-negative")
        
    for ref_field in ["per_item_dry_run_input_refs", "per_item_call_plan_refs", "per_item_spend_ledger_refs", "lifecycle_report_refs"]:
        if ref_field in packet and not packet[ref_field]:
            unknown.append(f"{ref_field} empty")
            
    items = packet.get("batch_items", [])
    if not items:
        unknown.append("empty batch")
        
    item_states = []
    computed_sum = 0.0
    for item in items:
        res = validate_provider_gateway_batch_item_plan(item)
        item_states.append(res["validation_state"])
        if res["validation_state"] == BLOCKED:
            blocked.extend([r for r in res["reasons"] if r != "ok"])
            blocked.append(f"item {item.get('item_id')} BLOCKED")
        elif res["validation_state"] == UNKNOWN:
            unknown.extend([r for r in res["reasons"] if r != "ok"])
            unknown.append(f"item {item.get('item_id')} UNKNOWN")
        elif res["validation_state"] == REVIEW_REQUIRED:
            review.extend([r for r in res["reasons"] if r != "ok"])
            review.append(f"item {item.get('item_id')} REVIEW_REQUIRED")
        if item.get("validation_state") != PASS:
            blocked.append(f"item {item.get('item_id')} validation_state must be PASS")
            
        c = item.get("estimated_cost")
        if c is not None and isinstance(c, (int, float)):
            computed_sum += c
            
    agg_cost = packet.get("aggregate_estimated_cost")
    if agg_cost is not None:
        # Avoid float precision issues
        if abs(agg_cost - computed_sum) > 0.0001:
            blocked.append("aggregate_estimated_cost does not match sum of items")
            
    if ceiling is not None and computed_sum > ceiling:
        blocked.append("aggregate_estimated_cost > declared_spend_ceiling")

    # If any item is blocked, batch is blocked
    rolled = _rollup(item_states)
    if rolled == BLOCKED:
        blocked.append("rolled up BLOCKED")
    elif rolled == UNKNOWN:
        unknown.append("rolled up UNKNOWN")
    elif rolled == REVIEW_REQUIRED:
        review.append("rolled up REVIEW_REQUIRED")

    return _result(blocked, review, unknown)

def validate_provider_gateway_aggregate_spend_ceiling(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_aggregate_spend_ceiling.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    ceil = packet.get("declared_spend_ceiling")
    if ceil is None or not isinstance(ceil, (int, float)) or ceil < 0:
        blocked.append("declared_spend_ceiling must be present and non-negative")

    agg = packet.get("aggregate_estimated_cost")
    if agg is None or not isinstance(agg, (int, float)) or agg < 0:
        blocked.append("aggregate_estimated_cost must be present and non-negative")
        
    costs = packet.get("item_estimated_costs")
    if costs is not None:
        if abs(sum(costs) - agg) > 0.0001:
            blocked.append("sum of item_estimated_costs != aggregate_estimated_cost")
            
    if agg is not None and ceil is not None and agg > ceil:
        blocked.append("aggregate_estimated_cost > declared_spend_ceiling")
        
    return _result(blocked, review, unknown)

def validate_provider_gateway_batch_dry_run_report(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_batch_dry_run_report.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    for f in ("provider_ready", "live_ready", "public_ready"):
        if packet.get(f):
            blocked.append(f"{f} must be false or absent")
            
    states = [
        packet.get("batch_input_state", UNKNOWN),
        packet.get("aggregate_spend_ceiling_state", UNKNOWN),
        packet.get("audit_manifest_state", UNKNOWN)
    ]
    rolled = _rollup(states)
    
    claim = packet.get("validation_state")
    if claim != rolled:
        blocked.append(f"claimed validation_state {claim} != rolled up state {rolled}")

    if claim == PASS and rolled != PASS:
        blocked.append("PASS only allowed if batch input, ceiling, and manifest are PASS")
        
    if rolled == UNKNOWN:
        unknown.append("rolled up state is UNKNOWN")
    elif rolled == REVIEW_REQUIRED:
        review.append("rolled up state is REVIEW_REQUIRED")
    elif rolled == BLOCKED:
        blocked.append("rolled up state is BLOCKED")

    return _result(blocked, review, unknown)

def validate_provider_gateway_batch_audit_manifest(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_batch_audit_manifest.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    if not packet.get("batch_id"):
        blocked.append("batch_id missing")
        
    for ref_field in ["per_item_dry_run_input_refs", "per_item_call_plan_refs", "per_item_spend_ledger_refs", "lifecycle_report_refs"]:
        if not packet.get(ref_field):
            unknown.append(f"{ref_field} empty or missing")
            
    if unknown and packet.get("validation_state") == PASS:
        blocked.append("cannot be PASS if refs are missing")

    return _result(blocked, review, unknown)

def build_batch_item_plan(item_input):
    cost = item_input.get("estimated_cost")
    
    plan = {
        "schema_version": "1.0",
        "dry_run_only": True,
        "executable": False,
        "provider_api_allowed": False,
        "network_allowed": False,
        "credentials_required": False,
        "env_read_performed": False,
        "api_key_present": False,
        "platform_variants_requested": False,
        "validation_state": "UNKNOWN"
    }
    
    if "item_id" in item_input: plan["item_id"] = item_input["item_id"]
    if cost is not None: plan["estimated_cost"] = cost
    if "cache_hit_state" in item_input: plan["cache_hit_state"] = item_input["cache_hit_state"]
    if "prompt_version" in item_input: plan["prompt_version"] = item_input["prompt_version"]
    
    res = validate_provider_gateway_batch_item_plan(plan)
    plan["validation_state"] = res["validation_state"]
    
    reasons = [r for r in res["reasons"] if r != "ok"]
    if not reasons: reasons = ["ok"]
    plan["reasons"] = reasons
    return plan

def build_aggregate_spend_ceiling(item_plans, declared_ceiling):
    agg = sum(i.get("estimated_cost", 0) for i in item_plans)
    val = PASS if agg <= declared_ceiling else BLOCKED
    return {
        "schema_version": "1.0",
        "batch_id": "batch",
        "declared_spend_ceiling": declared_ceiling,
        "aggregate_estimated_cost": agg,
        "item_estimated_costs": [i.get("estimated_cost", 0) for i in item_plans],
        "validation_state": val
    }

def build_batch_dry_run_report(batch_input, item_plans, ceiling_packet, audit_manifest_packet=None):
    res_input = validate_provider_gateway_batch_dry_run_input(batch_input)
    res_ceiling = validate_provider_gateway_aggregate_spend_ceiling(ceiling_packet)
    
    blocked, review, unknown = [], [], []
    
    item_states = []
    for item in item_plans:
        res = validate_provider_gateway_batch_item_plan(item)
        item_states.append(res["validation_state"])
    rolled_items = _rollup(item_states) if item_states else UNKNOWN
    
    manifest_state = UNKNOWN
    res_manifest = None
    if audit_manifest_packet is None:
        unknown.append("audit_manifest_packet missing")
    else:
        res_manifest = validate_provider_gateway_batch_audit_manifest(audit_manifest_packet)
        manifest_state = res_manifest["validation_state"]
        
    states = [res_input["validation_state"], rolled_items, res_ceiling["validation_state"], manifest_state]
    rolled = _rollup(states)
    
    reasons = res_input["reasons"] + res_ceiling["reasons"]
    if res_manifest:
        reasons += res_manifest["reasons"]
    reasons += blocked + review + unknown
    reasons = [r for r in list(dict.fromkeys(reasons)) if r != "ok"]
    if not reasons: reasons = ["ok"]
    
    return {
        "schema_version": "1.0",
        "batch_id": batch_input.get("batch_id", "unknown"),
        "validation_state": rolled,
        "batch_input_state": res_input["validation_state"],
        "aggregate_spend_ceiling_state": res_ceiling["validation_state"],
        "audit_manifest_state": manifest_state,
        "provider_ready": False,
        "live_ready": False,
        "public_ready": False,
        "reasons": reasons
    }

PROVIDER_GATEWAY_BATCH_DRY_RUN_VALIDATORS = {
    "batch_dry_run_input": validate_provider_gateway_batch_dry_run_input,
    "batch_item_plan": validate_provider_gateway_batch_item_plan,
    "aggregate_spend_ceiling": validate_provider_gateway_aggregate_spend_ceiling,
    "batch_dry_run_report": validate_provider_gateway_batch_dry_run_report,
    "batch_audit_manifest": validate_provider_gateway_batch_audit_manifest
}
