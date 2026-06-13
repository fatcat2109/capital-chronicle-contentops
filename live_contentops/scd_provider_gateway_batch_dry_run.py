"""Local-only provider-gateway dry-run batch plan and aggregate spend ceiling contract (SCD, 0174BC)."""
from live_contentops.scd_domain_model import PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN, _schema_ok, _result
from live_contentops.scd_canonical_draft_lifecycle import _common_safety_blocks

def validate_provider_gateway_batch_item_plan(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_batch_item_plan.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
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
    if cost is None or cost < 0:
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
    if ceiling is None or ceiling < 0:
        blocked.append("declared_spend_ceiling must be present and non-negative")
    
    items = packet.get("batch_items", [])
    if not items:
        unknown.append("empty batch")
        
    for item in items:
        res = validate_provider_gateway_batch_item_plan(item)
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
            
    return _result(blocked, review, unknown)

def validate_provider_gateway_aggregate_spend_ceiling(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_aggregate_spend_ceiling.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    agg = packet.get("aggregate_estimated_cost")
    ceil = packet.get("declared_spend_ceiling")
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
            
    return _result(blocked, review, unknown)

def validate_provider_gateway_batch_audit_manifest(packet):
    ok, msg = _schema_ok(packet, "scd_provider_gateway_batch_audit_manifest.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    return _result(blocked, review, unknown)

def build_batch_item_plan(item_input):
    return {
        "schema_version": "1.0",
        "item_id": item_input.get("item_id", "unknown"),
        "validation_state": "PASS",
        "dry_run_only": True,
        "executable": False,
        "provider_api_allowed": False,
        "network_allowed": False,
        "credentials_required": False,
        "env_read_performed": False,
        "api_key_present": False,
        "estimated_cost": item_input.get("estimated_cost", 0.0),
        "platform_variants_requested": False
    }

def build_aggregate_spend_ceiling(item_plans, declared_ceiling):
    agg = sum(i.get("estimated_cost", 0) for i in item_plans)
    val = PASS if agg <= declared_ceiling else BLOCKED
    return {
        "schema_version": "1.0",
        "batch_id": "batch",
        "declared_spend_ceiling": declared_ceiling,
        "aggregate_estimated_cost": agg,
        "validation_state": val
    }

def build_batch_dry_run_report(batch_input, item_plans, ceiling_packet):
    return {
        "schema_version": "1.0",
        "batch_id": batch_input.get("batch_id", "batch"),
        "validation_state": ceiling_packet.get("validation_state", UNKNOWN),
        "reasons": ceiling_packet.get("reasons", [])
    }

PROVIDER_GATEWAY_BATCH_DRY_RUN_VALIDATORS = {
    "batch_dry_run_input": validate_provider_gateway_batch_dry_run_input,
    "batch_item_plan": validate_provider_gateway_batch_item_plan,
    "aggregate_spend_ceiling": validate_provider_gateway_aggregate_spend_ceiling,
    "batch_dry_run_report": validate_provider_gateway_batch_dry_run_report,
    "batch_audit_manifest": validate_provider_gateway_batch_audit_manifest
}
