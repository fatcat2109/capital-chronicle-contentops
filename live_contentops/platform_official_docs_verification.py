import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

DOCS_SCHEMA = _load_schema("platform_official_docs_verification_packet.schema.json")

def validate_platform_official_docs_verification_packet(packet):
    errors = []
    try:
        jsonschema.validate(instance=packet, schema=DOCS_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if not packet.get("operator_supplied"): errors.append("operator_supplied_must_be_true")
    
    missing_docs = False
    
    for rec in packet.get("platform_records", []):
        if rec.get("runtime_authority"): errors.append("runtime_authority_must_be_false")
        if rec.get("live_api_status") != "disabled": errors.append("live_api_status_must_be_disabled")
        if rec.get("credential_read_allowed_now"): errors.append("credential_read_allowed_now_must_be_false")
        if rec.get("platform_api_call_allowed_now"): errors.append("platform_api_call_allowed_now_must_be_false")
        if rec.get("scheduler_allowed_now"): errors.append("scheduler_allowed_now_must_be_false")
        if rec.get("scraping_allowed_now"): errors.append("scraping_allowed_now_must_be_false")
        if rec.get("automatic_metrics_ingestion_allowed_now"): errors.append("automatic_metrics_ingestion_allowed_now_must_be_false")
        if rec.get("posting_allowed_now"): errors.append("posting_allowed_now_must_be_false")
        
        sources = rec.get("official_docs_sources", [])
        if rec.get("official_docs_verified"):
            if len(sources) == 0:
                errors.append(f"verified_without_source:{rec.get('platform_id')}")
            for s in sources:
                if s.get("source_type") == "unknown":
                    errors.append(f"verified_with_unofficial_source:{rec.get('platform_id')}")
                    
        if len(sources) == 0:
            missing_docs = True

        for s in sources:
            if not s.get("accessed_date"): errors.append(f"source_missing_accessed_date:{s.get('source_id')}")
            if not s.get("credibility_note"): errors.append(f"source_missing_credibility_note:{s.get('source_id')}")
            if not s.get("limitation_note"): errors.append(f"source_missing_limitation_note:{s.get('source_id')}")

    if missing_docs and "all_verified" in packet.get("verification_summary", "").lower():
        errors.append("summary_claims_all_verified_but_docs_missing")
        
    packet_str = json.dumps(packet)
    unsafe_tokens = ["fake_token", "Bearer ", "api_key=", "FAKE_SECRET", "FAKE_KEY", "client_secret="]
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
        "platform_record_count": 0,
        "verified_platform_count": 0,
        "partially_verified_platform_count": 0,
        "unknown_platform_count": 0,
        "blocked_platform_count": 0,
        "runtime_authority_count": 0,
        "unsafe_flag_count": 0,
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
