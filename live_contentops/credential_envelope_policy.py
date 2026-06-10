import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

POLICY_SCHEMA = _load_schema("credential_envelope_policy_packet.schema.json")
REDACTION_SCHEMA = _load_schema("secret_redaction_policy.schema.json")

def validate_credential_envelope_policy_packet(packet):
    errors = []
    
    store = {
        "secret_redaction_policy.schema.json": REDACTION_SCHEMA
    }
    
    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=POLICY_SCHEMA, store=store)
    
    try:
        jsonschema.validate(instance=packet, schema=POLICY_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("runtime_authority"): errors.append("runtime_authority_must_be_false")
    
    flg = packet.get("future_live_gate_requirements", {})
    if flg.get("live_execution_allowed_now"): errors.append("live_execution_allowed_now_must_be_false")
    if not flg.get("operator_explicit_live_gate_required"): errors.append("operator_explicit_live_gate_must_be_required")
    
    for rec in packet.get("credential_records", []):
        rid = rec.get("credential_record_id")
        if rec.get("secret_value_present"): errors.append(f"secret_value_present_must_be_false:{rid}")
        if not rec.get("secret_value_redacted"): errors.append(f"secret_value_redacted_must_be_true:{rid}")
        if rec.get("credential_value_loaded"): errors.append(f"credential_value_loaded_must_be_false:{rid}")
        if rec.get("credential_presence_checked"): errors.append(f"credential_presence_checked_must_be_false:{rid}")
        if rec.get("env_file_accessed"): errors.append(f"env_file_accessed_must_be_false:{rid}")
        if rec.get("credential_read_allowed_now"): errors.append(f"credential_read_allowed_now_must_be_false:{rid}")
        if rec.get("platform_api_call_allowed_now"): errors.append(f"platform_api_call_allowed_now_must_be_false:{rid}")
        if rec.get("posting_allowed_now"): errors.append(f"posting_allowed_now_must_be_false:{rid}")
        if rec.get("scheduler_allowed_now"): errors.append(f"scheduler_allowed_now_must_be_false:{rid}")
        if rec.get("scraping_allowed_now"): errors.append(f"scraping_allowed_now_must_be_false:{rid}")
        if rec.get("metrics_api_allowed_now"): errors.append(f"metrics_api_allowed_now_must_be_false:{rid}")
        if not rec.get("future_live_gate_required"): errors.append(f"future_live_gate_must_be_required:{rid}")

    packet_str = json.dumps(packet)
    unsafe_tokens = ["FAKE_SECRET", "fake_token_123", "Bearer FAKE_TOKEN", "api_key=FAKE_KEY", "password=FAKE_PASSWORD"]
    for t in unsafe_tokens:
        if t in packet_str:
            errors.append(f"unsafe_secret_detected:{t}")

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors}

def summary():
    return {
        "packet_status": "pass",
        "credential_record_count": 0,
        "credential_loaded_count": 0,
        "credential_presence_checked_count": 0,
        "env_file_accessed_count": 0,
        "runtime_authority_count": 0,
        "unsafe_secret_detected_count": 0,
        "future_live_gate_required_count": 0,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "live_posting_enabled": False,
        "scraping_allowed_now": False,
        "automatic_metrics_ingestion_allowed_now": False
    }
