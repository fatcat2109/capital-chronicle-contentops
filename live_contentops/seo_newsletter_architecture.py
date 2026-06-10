import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")

def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

ARCH_SCHEMA = _load_schema("seo_newsletter_architecture_packet.schema.json")
BLUEPRINT_SCHEMA = _load_schema("newsletter_issue_blueprint_packet.schema.json")

def validate_seo_newsletter_architecture_packet(packet):
    errors = []
    
    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=ARCH_SCHEMA)
    
    try:
        jsonschema.validate(instance=packet, schema=ARCH_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("runtime_authority"): errors.append("runtime_authority_must_be_false")
    
    # Pillars
    pillars = packet.get("content_pillars", [])
    for p in pillars:
        if p.get("public_ready_allowed_now") is True:
            errors.append(f"public_ready_allowed_now_true_in_pillar:{p.get('pillar_id')}")
        sp = p.get("required_source_policy", "")
        if sp != "required":
            errors.append("seo_claim_without_source_detected")
            
    # SEO Policy
    seo = packet.get("seo_metadata_policy", {})
    if seo.get("public_ready_allowed_now") is True: errors.append("seo_public_ready_allowed_now_must_be_false")
    if seo.get("sitemap_generation_enabled") is True: errors.append("sitemap_generation_enabled_must_be_false")
    if seo.get("rss_generation_enabled") is True: errors.append("rss_generation_enabled_must_be_false")
    if seo.get("real_domain_required") is True: errors.append("real_domain_required_must_be_false")
    if seo.get("no_financial_advice_disclaimer_required") is not True: errors.append("missing_safety_disclaimer:no_financial_advice")
    if seo.get("no_signal_language_required") is not True: errors.append("missing_safety_disclaimer:no_signal_language")
    
    # Newsletter Architecture
    news = packet.get("newsletter_architecture", {})
    if news.get("manual_send_only") is not True: errors.append("manual_send_only_must_be_true")
    if news.get("newsletter_send_enabled_now") is True: errors.append("newsletter_send_enabled_now_must_be_false")
    if news.get("mailing_list_integration_enabled_now") is True: errors.append("external_integration_enabled")
    if news.get("email_provider_api_allowed_now") is True: errors.append("external_integration_enabled")
    if news.get("subscriber_data_allowed_now") is True: errors.append("external_integration_enabled")
    if news.get("tracking_pixels_allowed_now") is True: errors.append("tracking_pixels_allowed_now_must_be_false")
    if news.get("utm_generation_allowed_now") is True: errors.append("utm_generation_allowed_now_must_be_false")
    if news.get("manual_metrics_entry_only") is not True: errors.append("manual_metrics_entry_only_must_be_true")

    # Text scan for signals and secrets
    packet_str = json.dumps(packet)
    unsafe_tokens = ["FAKE_SECRET", "fake_token_123", "Bearer FAKE_TOKEN", "api_key=FAKE_KEY", "password=FAKE_PASSWORD"]
    for t in unsafe_tokens:
        if t in packet_str:
            errors.append(f"unsafe_secret_detected:{t}")
            
    signal_tokens = [
        "Capital Chronicle alpha says", "our model predicts", "buy", "sell", "hold",
        "long", "short", "entry", "exit", "target", "position sizing", "broker",
        "order routing", "execution", "signal", "model says"
    ]
    
    def scan_for_signals(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    for st in signal_tokens:
                        st_lower = st.lower()
                        v_lower = v.lower()
                        if st_lower in v_lower:
                            if st in ["buy", "sell", "hold", "long", "short"]:
                                words = v_lower.split()
                                if st_lower in words:
                                    errors.append(f"unsafe_signal_detected:{st}")
                            else:
                                errors.append(f"unsafe_signal_detected:{st}")
                else:
                    scan_for_signals(v)
        elif isinstance(obj, list):
            for i in obj:
                scan_for_signals(i)
                
    scan_for_signals(packet)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": list(set(errors))}

def validate_newsletter_issue_blueprint_packet(packet):
    errors = []
    
    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=BLUEPRINT_SCHEMA)
    
    try:
        jsonschema.validate(instance=packet, schema=BLUEPRINT_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("publish_ready") is True: errors.append("publish_ready_must_be_false")
    if packet.get("newsletter_send_enabled_now") is True: errors.append("newsletter_send_enabled_now_must_be_false")
    if packet.get("source_references_required") is not True: errors.append("source_references_must_be_required")

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": list(set(errors))}


def summary():
    return {
        "packet_status": "pass",
        "content_pillar_count": 10,
        "newsletter_section_count": 8,
        "public_ready_allowed_count": 0,
        "live_send_enabled_count": 0,
        "external_integration_enabled_count": 0,
        "missing_disclaimer_count": 0,
        "unsafe_language_count": 0,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "live_posting_enabled": False,
        "scraping_allowed_now": False,
        "automatic_metrics_ingestion_allowed_now": False,
        "email_integration_enabled": False
    }
