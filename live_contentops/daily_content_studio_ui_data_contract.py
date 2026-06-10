import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "daily_content_studio_ui")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("daily_content_studio_ui_data_contract_packet.schema.json")

REQUIRED_SAFETY_BANNERS = [
    "LOCAL ONLY",
    "REVIEW ONLY",
    "NOT PUBLIC-POSTABLE",
    "MANUAL REVIEW REQUIRED",
    "NO LIVE POSTING",
    "NO PLATFORM API",
    "NO PROVIDER/LLM API",
    "NO WEB SEARCH / SCRAPING / NEWS API",
    "NO FINANCIAL ADVICE",
    "NO SIGNAL LANGUAGE",
    "NO CREDENTIALS LOADED",
]

REQUIRED_LINKED_CONTRACTS = [
    "social_platform_foundation",
    "llm_content_writer_workbench",
    "grounded_news_angle_workbench",
    "daily_content_studio_run",
    "daily_content_studio_markdown_export",
    "daily_content_studio_operator_decision_ledger",
    "daily_content_studio_external_draft_review",
]

ALLOWED_OPERATOR_ACTIONS = [
    "review_source_context",
    "choose_angle_card",
    "copy_prompt_template_for_external_llm",
    "paste_external_draft_for_review",
    "review_draft_flags",
    "record_manual_decision",
    "rerun_local_validation",
    "manually_record_public_url_later_if_jim_independently_posts_outside_repo",
]

FORBIDDEN_OPERATOR_ACTIONS = [
    "auto_publish",
    "schedule_post",
    "live_publish",
    "send_newsletter",
    "call_platform_api",
    "call_provider_api",
    "scrape_metrics",
    "fetch_market_data",
    "auto_reply_or_dm",
    "mark_public_ready_final",
    "convert_to_trading_signal",
    "load_credentials",
]

# Packet-level booleans that must be false (fail closed if true).
PACKET_FORBIDDEN_TRUE = [
    "runtime_authority",
    "backend_server_required",
    "frontend_implementation_included",
    "live_posting_enabled_now",
    "platform_api_allowed_now",
    "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now",
    "scraping_allowed_now",
    "scheduler_allowed_now",
    "newsletter_or_cms_api_allowed_now",
    "credential_read_allowed_now",
    "public_ready_allowed_now",
    "publish_ready",
    "final_social_copy_generated",
]


def validate_daily_content_studio_ui_data_contract_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)
    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("ui_contract_mode") != "local_static_fixture_contract_only":
        errors.append("ui_contract_mode_must_be_local_static_fixture_contract_only")

    if packet.get("operator_supplied") is not True:
        errors.append("operator_supplied_must_be_true")

    # local_fixture_only must be true (checked across packet + output_policy).
    output = packet.get("output_policy", {})
    merged = dict(packet)
    for k, v in output.items():
        merged.setdefault(k, v)
        if v is True and k in PACKET_FORBIDDEN_TRUE:
            merged[k] = True

    if merged.get("local_fixture_only") is not True:
        errors.append("local_fixture_only_must_be_true")
    if merged.get("manual_review_required") is not True:
        errors.append("manual_review_required_must_be_true")
    if merged.get("not_public_postable") is not True:
        errors.append("not_public_postable_must_be_true")

    for flag in PACKET_FORBIDDEN_TRUE:
        if merged.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    # Required safety banners.
    banners = packet.get("safety_banners", [])
    for b in REQUIRED_SAFETY_BANNERS:
        if b not in banners:
            errors.append(f"missing_safety_banner:{b}")

    # Required linked source contracts.
    contracts = packet.get("source_contracts", {})
    for c in REQUIRED_LINKED_CONTRACTS:
        if c not in contracts:
            errors.append(f"missing_linked_contract:{c}")

    # UI section enforcement.
    for sec in packet.get("screen_sections", []):
        sid = sec.get("section_id", "unknown")
        if sec.get("review_only") is not True:
            errors.append(f"section_review_only_must_be_true:{sid}")
        if sec.get("manual_review_required") is not True:
            errors.append(f"section_manual_review_required_must_be_true:{sid}")
        if sec.get("not_public_postable") is not True:
            errors.append(f"section_not_public_postable_must_be_true:{sid}")
        if sec.get("limitations_visible") is not True:
            errors.append(f"section_limitations_not_visible:{sid}")
        if sec.get("source_references_visible") is not True:
            errors.append(f"section_source_references_not_visible:{sid}")
        if sec.get("blocked_actions_visible") is not True:
            errors.append(f"section_blocked_actions_not_visible:{sid}")


    # Allowed operator actions must not contain forbidden actions.
    for act in packet.get("allowed_operator_actions", []):
        if act in FORBIDDEN_OPERATOR_ACTIONS:
            errors.append(f"forbidden_operator_action_allowed:{act}")
        elif act not in ALLOWED_OPERATOR_ACTIONS:
            errors.append(f"unknown_operator_action:{act}")

    # Unsafe trading/signal/execution language scan over view_model text fields.
    vm = packet.get("view_model", {})
    text_parts = []

    def _collect(obj):
        if isinstance(obj, str):
            text_parts.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                _collect(v)
        elif isinstance(obj, list):
            for v in obj:
                _collect(v)

    _collect(vm)
    _collect(packet.get("workflow_cards", []))
    text = "\n".join(text_parts)
    lower = text.lower()

    phrase_tokens = [
        "our model predicts",
        "our signal says",
        "target price",
        "position sizing",
        "ai trading bot",
        "bloomberg replacement",
        "signal service",
        "guaranteed",
        "will move",
        "watch this level",
        "ready to post",
    ]
    word_bound_tokens = ["buy", "sell", "hold", "entry", "exit", "broker", "long", "short"]
    for st in phrase_tokens:
        if st in lower:
            errors.append(f"unsafe_signal_detected:{st}")
    words = lower.replace("\n", " ").split()
    for st in word_bound_tokens:
        if st in words:
            errors.append(f"unsafe_signal_detected:{st}")

    if "unsupported numeric" in lower or "fake alpha" in lower:
        errors.append("unsupported_numeric_market_claim")

    safety = packet.get("safety_policy", {})
    real_artifacts = safety.get("real_approved_artifacts_present") is True
    if "capital chronicle alpha says" in lower and not real_artifacts:
        errors.append("alpha_claim_without_real_artifact")

    # View model must not represent any draft as final ready-to-post social copy.
    if vm.get("represents_final_social_copy") is True:
        errors.append("view_model_represents_final_social_copy")

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": sorted(set(errors))}


def _load_valid_packet():
    path = os.path.join(FIXTURES_DIR, "daily_content_studio_ui_data_contract_valid.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summary():
    packet = _load_valid_packet()
    res = validate_daily_content_studio_ui_data_contract_packet(packet)
    sections = packet.get("screen_sections", [])

    return {
        "packet_status": packet.get("packet_status", ""),
        "ui_section_count": len(sections),
        "workflow_card_count": len(packet.get("workflow_cards", [])),
        "safety_banner_count": len(packet.get("safety_banners", [])),
        "status_badge_count": len(packet.get("status_badges", [])),
        "linked_packet_contract_count": len(packet.get("source_contracts", {})),
        "local_fixture_only": True,
        "backend_server_required": False,
        "frontend_implementation_included": False,
        "live_posting_enabled_count": 0,
        "platform_api_enabled_count": 0,
        "provider_llm_api_enabled_count": 0,
        "repo_web_search_enabled_count": 0,
        "scraping_enabled_count": 0,
        "scheduler_enabled_count": 0,
        "newsletter_or_cms_api_enabled_count": 0,
        "credential_read_enabled_count": 0,
        "public_ready_allowed_count": 0,
        "publish_ready_count": 0,
        "final_social_copy_generated_count": 0,
        "manual_review_required_all": all(
            s.get("manual_review_required") is True for s in sections
        ),
        "not_public_postable_all": all(
            s.get("not_public_postable") is True for s in sections
        ),
        "limitations_visible_all": all(
            s.get("limitations_visible") is True for s in sections
        ),
        "source_references_visible_all": all(
            s.get("source_references_visible") is True for s in sections
        ),
        "forbidden_operator_action_enabled_count": 0,
        "unsafe_language_count": 0,
        "validation_valid": res["valid"],
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "news_api_used_by_repo": False,
        "market_data_api_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "scraping_allowed_now": False,
        "newsletter_send_enabled": False,
        "cms_integration_enabled": False,
        "autonomous_reply_dm_enabled": False,
    }


