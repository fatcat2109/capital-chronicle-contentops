import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

MOCK_PUBLISH_SCHEMA = _load_schema("mock_publish_result_packet.schema.json")
MANUAL_METRICS_SCHEMA = _load_schema("manual_metrics_readiness_packet.schema.json")

def validate_mock_publish_result(mock_res, approval_rec=None, ks=None, audit=None, dry_run_payload=None):
    errors = []
    try:
        jsonschema.validate(instance=mock_res, schema=MOCK_PUBLISH_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if not mock_res.get("mock_only"): errors.append("mock_only_must_be_true")
    if not mock_res.get("dry_run"): errors.append("dry_run_must_be_true")
    if mock_res.get("live_execution"): errors.append("live_execution_must_be_false")
    if mock_res.get("platform_api_call_used"): errors.append("platform_api_call_used_must_be_false")
    if mock_res.get("platform_api_payload_generated"): errors.append("platform_api_payload_generated_must_be_false")
    if mock_res.get("network_accessed"): errors.append("network_accessed_must_be_false")
    if mock_res.get("credential_accessed"): errors.append("credential_accessed_must_be_false")
    if mock_res.get("scheduler_accessed"): errors.append("scheduler_accessed_must_be_false")

    if approval_rec:
        state = approval_rec.get("approval_state")
        if state not in ["operator_approved_for_mock_publish"]:
            errors.append(f"invalid_approval_state_for_mock_publish:{state}")
    else:
        errors.append("missing_approval_record")

    if ks:
        if not ks.get("mock_publish_allowed_when_enabled"):
            errors.append("kill_switch_blocks_mock_publish")
            
    if dry_run_payload:
        if not dry_run_payload.get("dry_run"):
            errors.append("dry_run_payload_is_not_dry_run")

    if audit:
        if audit.get("unsafe_secret_detected"): errors.append("audit_contains_unsafe_secret")
        if audit.get("live_execution"): errors.append("audit_live_execution_is_true")
        if audit.get("network_accessed"): errors.append("audit_network_accessed_is_true")
        if audit.get("credential_accessed"): errors.append("audit_credential_accessed_is_true")
        if audit.get("scheduler_accessed"): errors.append("audit_scheduler_accessed_is_true")

    if mock_res.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors}

def validate_manual_metrics_readiness(mm):
    errors = []
    try:
        jsonschema.validate(instance=mm, schema=MANUAL_METRICS_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if not mm.get("manual_metrics_entry_required"): errors.append("manual_metrics_entry_required_must_be_true")
    if mm.get("automatic_metrics_ingestion"): errors.append("automatic_metrics_ingestion_must_be_false")
    if mm.get("scraping_allowed"): errors.append("scraping_allowed_must_be_false")
    if mm.get("platform_metrics_api_allowed"): errors.append("platform_metrics_api_allowed_must_be_false")
    if not mm.get("operator_entered_only"): errors.append("operator_entered_only_must_be_true")
    
    null_policy = mm.get("metric_null_policy", "")
    if "zero" in null_policy.lower() or "coerce" in null_policy.lower():
        errors.append("metric_null_policy_coerces_to_zero")
        
    if mm.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors}

def summary():
    return {
        "packet_status": "pass",
        "mock_publish_result_count": 0,
        "mock_publish_allowed_count": 0,
        "manual_metrics_readiness_count": 0,
        "blocked_record_count": 0,
        "automatic_metrics_ingestion_count": 0,
        "live_execution_count": 0,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "live_posting_enabled": False
    }
