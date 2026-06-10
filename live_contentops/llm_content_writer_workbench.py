import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("llm_content_writer_workbench_packet.schema.json")

ALLOWED_CONTENT_TYPES = [
    "build_in_public",
    "macro_education",
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
    "product_update",
    "market_note_review_only",
    "grounded_news_context_review_only",
    "official_data_explainer_review_only",
    "policy_process_commentary_review_only",
]

CLAIM_CLASSIFICATIONS = [
    "first_party_product_process",
    "evergreen_macro_education",
    "cited_factual_claim",
    "current_factual_claim_requires_source",
    "market_sensitive_claim_review_only",
    "unsupported_numeric_claim_blocked",
    "signal_or_trade_claim_blocked",
    "artifact_backed_claim_blocked_until_real_artifact",
]

# Per-template flags that must never be enabled.
TEMPLATE_FORBIDDEN_TRUE = {
    "provider_call_allowed_by_repo": "provider_call_allowed_by_repo_must_be_false",
    "repo_executes_prompt": "repo_executes_prompt_must_be_false",
    "public_ready_allowed_now": "public_ready_allowed_now_must_be_false",
}

# Per-template flags that must always be true.
TEMPLATE_REQUIRED_TRUE = {
    "template_only": "template_only_must_be_true",
    "external_llm_use_only": "external_llm_use_only_must_be_true",
    "manual_review_required": "manual_review_required_must_be_true",
    "not_public_postable": "not_public_postable_must_be_true",
}



def validate_llm_content_writer_workbench_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)

    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("runtime_authority"):
        errors.append("runtime_authority_must_be_false")

    # Prompt pack templates: template-only / external-use-only enforcement.
    templates = packet.get("prompt_pack_templates", [])
    for t in templates:
        tid = t.get("template_id", "unknown")
        for flag, label in TEMPLATE_FORBIDDEN_TRUE.items():
            if t.get(flag) is True:
                errors.append(f"{label}:{tid}")
        for flag, label in TEMPLATE_REQUIRED_TRUE.items():
            if t.get(flag) is not True:
                errors.append(f"{label}:{tid}")

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

    # Source requirement policy enforcement.
    src = packet.get("source_requirement_policy", {})
    if src.get("source_references_required") is not True:
        errors.append("source_references_required_must_be_true")
    if src.get("current_factual_claim_requires_source") is not True:
        errors.append("current_factual_claim_requires_source_must_be_true")

    # Allowed content type sanity.
    for ct in packet.get("allowed_content_types", []):
        if ct not in ALLOWED_CONTENT_TYPES:
            errors.append(f"unknown_content_type:{ct}")

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
    claim = packet.get("claim_classification_policy", {})
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
        "prompt_template_count": 6,
        "angle_count": 6,
        "allowed_content_type_count": len(ALLOWED_CONTENT_TYPES),
        "provider_call_enabled_count": 0,
        "repo_prompt_execution_enabled_count": 0,
        "public_ready_allowed_count": 0,
        "publish_ready_count": 0,
        "auto_approval_enabled_count": 0,
        "platform_export_final_enabled_count": 0,
        "newsletter_send_enabled_count": 0,
        "cms_integration_enabled_count": 0,
        "manual_review_required_all": True,
        "not_public_postable_all": True,
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
        "autonomous_reply_dm_enabled": False,
    }

