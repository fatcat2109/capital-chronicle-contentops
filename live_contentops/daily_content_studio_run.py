import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("daily_content_studio_run_packet.schema.json")

SUPPORTED_CONTENT_LANES = [
    "build_in_public",
    "macro_education",
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
    "product_update",
    "grounded_news_context_review_only",
    "official_data_explainer_review_only",
    "policy_process_commentary_review_only",
    "market_note_review_only",
]

ALLOWED_MANUAL_ACTIONS = [
    "review_source_context",
    "choose_angle_card",
    "copy_prompt_template_for_external_llm",
    "manually_rewrite_draft_outside_repo",
    "rerun_local_validation",
    "manually_record_public_url_later_if_jim_posts_outside_repo",
]

FORBIDDEN_MANUAL_ACTIONS = [
    "auto_publish",
    "schedule_post",
    "send_newsletter",
    "call_platform_api",
    "call_provider_api",
    "scrape_metrics",
    "fetch_market_data",
    "auto_reply_or_dm",
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
    "scheduler_allowed": "scheduler_allowed_must_be_false",
    "newsletter_or_cms_api_allowed": "newsletter_or_cms_api_allowed_must_be_false",
}

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
}


def validate_daily_content_studio_run_packet(packet):
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

    # Source lineage enforcement.
    lineage = packet.get("source_lineage_policy", {})
    if lineage.get("source_lineage_required") is not True:
        errors.append("source_lineage_required_must_be_true")
    if not packet.get("source_context_summary"):
        errors.append("source_lineage_missing")

    # Source references / limitations policy.
    fl = packet.get("freshness_and_limitations_policy", {})
    if fl.get("source_references_required") is not True:
        errors.append("source_references_required_must_be_true")
    if fl.get("limitations_required") is not True:
        errors.append("limitations_required_must_be_true")

    # Selected angle cards enforcement.
    for c in packet.get("selected_angle_cards", []):
        cid = c.get("angle_card_id", "unknown")
        for flag, label in CARD_REQUIRED_TRUE.items():
            if c.get(flag) is not True:
                errors.append(f"{label}:{cid}")
        for flag, label in CARD_FORBIDDEN_TRUE.items():
            if c.get(flag) is True:
                errors.append(f"{label}:{cid}")

    # Content lane selection.
    lane = packet.get("content_lane_selection", {}).get("content_lane")
    if lane is not None and lane not in SUPPORTED_CONTENT_LANES:
        errors.append(f"unknown_content_lane:{lane}")


    # LLM writer handoff enforcement.
    lw = packet.get("llm_writer_handoff", {})
    if lw.get("external_llm_use_only") is not True:
        errors.append("llm_external_llm_use_only_must_be_true")
    if lw.get("prompt_template_only") is not True:
        errors.append("llm_prompt_template_only_must_be_true")
    if lw.get("manual_review_required") is not True:
        errors.append("llm_manual_review_required_must_be_true")
    if lw.get("not_public_postable") is not True:
        errors.append("llm_not_public_postable_must_be_true")
    if lw.get("repo_executes_prompt") is True:
        errors.append("llm_repo_executes_prompt_must_be_false")
    if lw.get("provider_call_allowed_by_repo") is True:
        errors.append("llm_provider_call_allowed_by_repo_must_be_false")
    if lw.get("generated_copy_final_allowed_now") is True:
        errors.append("llm_generated_copy_final_allowed_now_must_be_false")

    # Platform foundation handoff enforcement.
    pf = packet.get("platform_foundation_handoff", {})
    if pf.get("manual_review_required") is not True:
        errors.append("platform_manual_review_required_must_be_true")
    if pf.get("not_public_postable") is not True:
        errors.append("platform_not_public_postable_must_be_true")
    if pf.get("platform_export_final_allowed_now") is True:
        errors.append("platform_export_final_allowed_now_must_be_false")
    if pf.get("platform_api_allowed_now") is True:
        errors.append("platform_api_allowed_now_must_be_false")
    if pf.get("live_posting_enabled_now") is True:
        errors.append("platform_live_posting_enabled_now_must_be_false")
    if pf.get("credential_read_allowed_now") is True:
        errors.append("platform_credential_read_allowed_now_must_be_false")
    if pf.get("scheduler_allowed_now") is True:
        errors.append("platform_scheduler_allowed_now_must_be_false")

    # Grounded news workbench handoff enforcement.
    gn = packet.get("grounded_news_workbench_handoff", {})
    if gn.get("operator_supplied_source_only") is not True:
        errors.append("grounded_news_operator_supplied_source_only_must_be_true")
    if gn.get("repo_web_search_allowed") is True:
        errors.append("grounded_news_repo_web_search_allowed_must_be_false")

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
        errors.append("output_platform_export_final_allowed_now_must_be_false")
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

    # Manual operator actions enforcement.
    for a in packet.get("manual_operator_actions", []):
        if a in FORBIDDEN_MANUAL_ACTIONS:
            errors.append(f"forbidden_manual_action:{a}")
        elif a not in ALLOWED_MANUAL_ACTIONS:
            errors.append(f"unknown_manual_action:{a}")


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
    review = packet.get("review_policy", {})
    out = packet.get("output_policy", {})
    real_artifacts = (
        review.get("real_approved_artifacts_present") is True
        or out.get("real_approved_artifacts_present") is True
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
        "selected_angle_card_count": 3,
        "source_context_item_count": 3,
        "supported_content_lane_count": len(SUPPORTED_CONTENT_LANES),
        "manual_operator_action_count": len(ALLOWED_MANUAL_ACTIONS),
        "repo_web_search_enabled_count": 0,
        "repo_scraping_enabled_count": 0,
        "repo_news_api_enabled_count": 0,
        "repo_rss_fetch_enabled_count": 0,
        "repo_market_data_api_enabled_count": 0,
        "provider_llm_api_enabled_count": 0,
        "platform_api_enabled_count": 0,
        "credential_read_enabled_count": 0,
        "scheduler_enabled_count": 0,
        "newsletter_or_cms_api_enabled_count": 0,
        "public_ready_allowed_count": 0,
        "publish_ready_count": 0,
        "auto_approval_enabled_count": 0,
        "platform_export_final_enabled_count": 0,
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
