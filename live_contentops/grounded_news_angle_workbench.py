import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("grounded_news_angle_workbench_packet.schema.json")

ALLOWED_SOURCE_TYPES = [
    "official_source",
    "statistical_agency",
    "central_bank",
    "treasury_or_fiscal_agency",
    "regulator",
    "exchange_or_market_infrastructure",
    "company_or_government_primary_release",
    "reputable_news_context",
    "public_research_context",
    "platform_native_context_not_authority",
    "operator_supplied_context",
]

CLAIM_RISK_CLASSES = [
    "safe_evergreen_process",
    "safe_official_data_explainer",
    "current_factual_claim_requires_source",
    "macro_context_requires_limitations",
    "market_sensitive_review_only",
    "unsupported_numeric_claim_blocked",
    "signal_or_trade_claim_blocked",
    "artifact_backed_claim_blocked_until_real_artifact",
]

ANGLE_TAXONOMY_TYPES = [
    "macro_education_from_news",
    "data_sufficiency_from_news",
    "forecast_readiness_from_news",
    "failure_forensics_from_news",
    "official_data_explainer",
    "policy_process_commentary",
    "product_philosophy_from_news",
    "build_in_public_from_news",
]

# Input policy flags that must be false.
INPUT_FORBIDDEN_TRUE = {
    "repo_web_search_allowed": "repo_web_search_allowed_must_be_false",
    "repo_scraping_allowed": "repo_scraping_allowed_must_be_false",
    "repo_news_api_allowed": "repo_news_api_allowed_must_be_false",
    "repo_rss_fetch_allowed": "repo_rss_fetch_allowed_must_be_false",
    "repo_market_data_api_allowed": "repo_market_data_api_allowed_must_be_false",
    "provider_llm_api_allowed": "provider_llm_api_allowed_must_be_false",
    "credential_read_allowed": "credential_read_allowed_must_be_false",
    "platform_api_allowed": "platform_api_allowed_must_be_false",
}

# Required source item metadata fields.
REQUIRED_SOURCE_FIELDS = [
    "source_id",
    "source_title",
    "source_type",
    "source_date",
    "access_date_or_operator_observed_date",
    "source_url_or_reference_label",
    "source_summary",
    "limitation_note",
    "freshness_label",
    "redistribution_allowed",
    "authority_role",
]

# Per-angle-card flags that must be true.
CARD_REQUIRED_TRUE = {
    "review_only": "card_review_only_must_be_true",
    "manual_review_required": "card_manual_review_required_must_be_true",
    "not_public_postable": "card_not_public_postable_must_be_true",
    "source_references_required": "card_source_references_required_must_be_true",
    "limitations_required": "card_limitations_required_must_be_true",
    "no_signal_language_required": "card_no_signal_language_required_must_be_true",
    "no_financial_advice_required": "card_no_financial_advice_required_must_be_true",
}

# Per-angle-card flags that must be false.
CARD_FORBIDDEN_TRUE = {
    "publish_ready": "card_publish_ready_must_be_false",
    "public_ready_allowed_now": "card_public_ready_allowed_now_must_be_false",
    "downstream_llm_repo_execution_allowed": "card_downstream_llm_repo_execution_must_be_false",
}


def validate_grounded_news_angle_workbench_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)

    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("runtime_authority"):
        errors.append("runtime_authority_must_be_false")

    # Input policy enforcement.
    inp = packet.get("input_policy", {})
    if inp.get("operator_supplied_context_only") is not True:
        errors.append("operator_supplied_context_only_must_be_true")
    for flag, label in INPUT_FORBIDDEN_TRUE.items():
        if inp.get(flag) is True:
            errors.append(label)

    # Source items: required metadata enforcement.
    for s in packet.get("source_items", []):
        sid = s.get("source_id", "unknown")
        for field in REQUIRED_SOURCE_FIELDS:
            if field not in s or s.get(field) in (None, ""):
                errors.append(f"source_missing_metadata:{sid}:{field}")
        st = s.get("source_type")
        if st is not None and st not in ALLOWED_SOURCE_TYPES:
            errors.append(f"unknown_source_type:{sid}:{st}")

    # Angle cards enforcement.
    for c in packet.get("angle_cards", []):
        cid = c.get("angle_card_id", "unknown")
        for flag, label in CARD_REQUIRED_TRUE.items():
            if c.get(flag) is not True:
                errors.append(f"{label}:{cid}")
        for flag, label in CARD_FORBIDDEN_TRUE.items():
            if c.get(flag) is True:
                errors.append(f"{label}:{cid}")
        at = c.get("angle_type")
        if at is not None and at not in ANGLE_TAXONOMY_TYPES:
            errors.append(f"unknown_angle_type:{cid}:{at}")

    # Output policy enforcement.
    out = packet.get("output_policy", {})
    if out.get("manual_review_required") is not True:
        errors.append("output_manual_review_required_must_be_true")
    if out.get("not_public_postable") is not True:
        errors.append("output_not_public_postable_must_be_true")
    if out.get("publish_ready") is True:
        errors.append("publish_ready_must_be_false")
    if out.get("auto_approval_allowed") is True:
        errors.append("auto_approval_allowed_must_be_false")
    if out.get("public_ready_allowed_now") is True:
        errors.append("output_public_ready_allowed_now_must_be_false")
    if out.get("platform_export_final_allowed_now") is True:
        errors.append("platform_export_final_allowed_now_must_be_false")
    if out.get("newsletter_send_enabled_now") is True:
        errors.append("newsletter_send_enabled_now_must_be_false")
    if out.get("cms_integration_enabled_now") is True:
        errors.append("cms_integration_enabled_now_must_be_false")

    # Review policy enforcement.
    review = packet.get("review_policy", {})
    if review.get("manual_review_required") is not True:
        errors.append("review_manual_review_required_must_be_true")
    if review.get("auto_approval_allowed") is True:
        errors.append("review_auto_approval_allowed_must_be_false")


    # Source references / limitations requirement (policy-level).
    src_pol = packet.get("source_metadata_policy", {})
    if src_pol.get("source_references_required") is not True:
        errors.append("source_references_required_must_be_true")
    lim_pol = packet.get("limitation_policy", {})
    if lim_pol.get("limitations_required") is not True:
        errors.append("limitations_required_must_be_true")

    # Unsafe secret placeholder scan.
    packet_str = json.dumps(packet)
    unsafe_tokens = [
        "FAKE_SECRET",
        "fake_token_123",
        "Bearer FAKE_TOKEN",
        "api_key=FAKE_KEY",
        "password=FAKE_PASSWORD",
    ]
    for tok in unsafe_tokens:
        if tok in packet_str:
            errors.append(f"unsafe_secret_detected:{tok}")

    # Forbidden trading/signal/execution/framing language scan.
    phrase_tokens = [
        "our model predicts",
        "our signal says",
        "model says",
        "target price",
        "position sizing",
        "order routing",
        "ai trading bot",
        "bloomberg replacement",
        "signal service",
        "guaranteed",
        "this means",
        "will move",
        "watch this level",
    ]
    word_bound_tokens = [
        "buy",
        "sell",
        "hold",
        "long",
        "short",
        "entry",
        "exit",
        "broker",
        "execution",
        "signal",
    ]

    def scan_for_signals(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                scan_for_signals(v)
        elif isinstance(obj, list):
            for i in obj:
                scan_for_signals(i)
        elif isinstance(obj, str):
            v_lower = obj.lower()
            for st in phrase_tokens:
                if st in v_lower:
                    errors.append(f"unsafe_signal_detected:{st}")
            words = v_lower.split()
            for st in word_bound_tokens:
                if st in words:
                    errors.append(f"unsafe_signal_detected:{st}")
            if "unsupported numeric" in v_lower or "fake alpha" in v_lower:
                errors.append("unsupported_numeric_market_claim")

    scan_for_signals(packet)

    # "Capital Chronicle alpha says" requires real approved artifacts.
    linkage = packet.get("social_platform_foundation_linkage", {})
    claim = packet.get("claim_risk_policy", {})
    real_artifacts = (
        linkage.get("real_approved_artifacts_present") is True
        or claim.get("real_approved_artifacts_present") is True
    )
    if "Capital Chronicle alpha says" in packet_str and not real_artifacts:
        errors.append("alpha_claim_without_real_artifact")

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": sorted(set(errors))}



def summary():
    return {
        "packet_status": "pass",
        "source_count": 3,
        "angle_card_count": 4,
        "source_type_count": len(ALLOWED_SOURCE_TYPES),
        "claim_risk_class_count": len(CLAIM_RISK_CLASSES),
        "angle_taxonomy_count": len(ANGLE_TAXONOMY_TYPES),
        "repo_web_search_enabled_count": 0,
        "repo_scraping_enabled_count": 0,
        "repo_news_api_enabled_count": 0,
        "repo_rss_fetch_enabled_count": 0,
        "repo_market_data_api_enabled_count": 0,
        "provider_llm_api_enabled_count": 0,
        "platform_api_enabled_count": 0,
        "credential_read_enabled_count": 0,
        "public_ready_allowed_count": 0,
        "publish_ready_count": 0,
        "auto_approval_enabled_count": 0,
        "manual_review_required_all": True,
        "not_public_postable_all": True,
        "source_references_required_all": True,
        "limitations_required_all": True,
        "unsafe_language_count": 0,
        "unsupported_numeric_claim_count": 0,
        "artifact_claim_without_real_artifact_count": 0,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "scraping_allowed_now": False,
        "newsletter_send_enabled": False,
        "cms_integration_enabled": False,
        "autonomous_reply_dm_enabled": False,
    }
