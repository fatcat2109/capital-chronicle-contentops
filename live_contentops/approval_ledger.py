import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

APPROVAL_SCHEMA = _load_schema("approval_ledger_packet.schema.json")
KS_SCHEMA = _load_schema("kill_switch_state.schema.json")
AUDIT_SCHEMA = _load_schema("redacted_audit_event.schema.json")

def validate_approval_record(record, dry_run_payload=None):
    errors = []
    try:
        jsonschema.validate(instance=record, schema=APPROVAL_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if not record.get("operator_approval_ref"):
        errors.append("missing_operator_approval_ref")
    
    # Mock approval requirements
    if record.get("approval_state") == "operator_approved_for_mock_publish":
        if not record.get("manual_review_completed"): errors.append("manual_review_missing")
        if not record.get("operator_final_check_completed"): errors.append("final_check_missing")
        if not record.get("limitations_acknowledged"): errors.append("limitations_not_acknowledged")
        if not record.get("freshness_acknowledged"): errors.append("freshness_not_acknowledged")
        if not record.get("not_financial_advice_acknowledged"): errors.append("not_financial_advice_not_acknowledged")
        if not record.get("no_signal_language_acknowledged"): errors.append("no_signal_language_not_acknowledged")

    if record.get("approval_state") == "operator_approved_for_live_publish_later":
        errors.append("live_publish_attempt_without_explicit_future_gate")
    
    if dry_run_payload:
        if dry_run_payload.get("live_posting_enabled"): errors.append("payload_live_posting_enabled_is_true")
        if dry_run_payload.get("platform_api_payload_generated"): errors.append("payload_platform_api_payload_generated_is_true")
        if not dry_run_payload.get("dry_run"): errors.append("payload_is_not_dry_run")

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors}

def validate_kill_switch_state(ks):
    errors = []
    try:
        jsonschema.validate(instance=ks, schema=KS_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if not ks.get("kill_switch_enabled"): errors.append("kill_switch_must_be_enabled")
    if not ks.get("default_posting_blocked"): errors.append("default_posting_must_be_blocked")
    if ks.get("live_publish_allowed_now"): errors.append("live_publish_allowed_now_must_be_false")
    if ks.get("platform_api_allowed_now"): errors.append("platform_api_allowed_now_must_be_false")
    if ks.get("scheduler_allowed_now"): errors.append("scheduler_allowed_now_must_be_false")
    if ks.get("credential_read_allowed_now"): errors.append("credential_read_allowed_now_must_be_false")
    if ks.get("network_allowed_now"): errors.append("network_allowed_now_must_be_false")

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors}

def validate_audit_event(audit):
    errors = []
    try:
        jsonschema.validate(instance=audit, schema=AUDIT_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if audit.get("live_execution"): errors.append("audit_live_execution_must_be_false")
    if audit.get("network_accessed"): errors.append("audit_network_accessed_must_be_false")
    if audit.get("credential_accessed"): errors.append("audit_credential_accessed_must_be_false")
    if audit.get("scheduler_accessed"): errors.append("audit_scheduler_accessed_must_be_false")
    
    payload_str = json.dumps(audit.get("audit_payload", {}))
    unsafe_tokens = ["fake_token", "Bearer ", "api_key=", "FAKE_SECRET", "FAKE_KEY"]
    for t in unsafe_tokens:
        if t in payload_str:
            errors.append(f"unsafe_secret_detected:{t}")

    if audit.get("unsafe_secret_detected") and len(errors) == 0:
        errors.append("unsafe_secret_detected_flag_true")
        
    valid = len(errors) == 0
    return {"valid": valid, "errors": errors}

def check_action_allowed(record, ks, dry_run_payload=None):
    res_rec = validate_approval_record(record, dry_run_payload)
    res_ks = validate_kill_switch_state(ks)
    
    errors = res_rec["errors"] + res_ks["errors"]
    
    if record.get("approval_state") == "revoked":
        errors.append("approval_revoked")
    elif record.get("approval_state") != "operator_approved_for_mock_publish":
        errors.append(f"approval_state_not_ready_for_mock:{record.get('approval_state')}")

    if not ks.get("mock_publish_allowed_when_enabled"):
        errors.append("kill_switch_blocks_mock_publish")
        
    if ks.get("live_publish_allowed_now"):
        errors.append("kill_switch_tries_to_allow_live")
        
    return {"allowed": len(errors) == 0, "errors": list(set(errors))}

def summary():
    return {
        "packet_status": "pass",
        "approval_record_count": 0,
        "mock_publish_approved_count": 0,
        "live_publish_allowed_count": 0,
        "revoked_count": 0,
        "blocked_record_count": 0,
        "kill_switch_enabled": True,
        "redacted_audit_event_count": 0,
        "unsafe_secret_detected_count": 0,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "live_posting_enabled": False
    }
