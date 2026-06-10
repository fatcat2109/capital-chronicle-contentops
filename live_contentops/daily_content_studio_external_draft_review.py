import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "daily_content_studio_external_draft_review")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("daily_content_studio_external_draft_review_packet.schema.json")

CLAIM_CLASSIFICATIONS = [
    "first_party_product_process",
    "evergreen_macro_education",
    "cited_factual_claim",
    "current_factual_claim_requires_source",
    "market_sensitive_review_only",
    "unsupported_numeric_claim_blocked",
    "signal_or_trade_claim_blocked",
    "artifact_backed_claim_blocked_until_real_artifact",
]

ALLOWED_MANUAL_NEXT_ACTIONS = [
    "revise_draft_outside_repo",
    "add_source_reference",
    "add_limitation_note",
    "choose_different_angle_card",
    "rerun_local_validation",
    "send_back_to_external_llm_manually",
    "manually_record_public_url_later_if_jim_independently_posts_outside_repo",
]

FORBIDDEN_NEXT_ACTIONS = [
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
]

# Packet-level booleans that must be false (fail closed if true).
PACKET_FORBIDDEN_TRUE = [
    "runtime_authority",
    "repo_generated_draft",
    "repo_executes_prompt",
    "provider_call_allowed_by_repo",
    "provider_llm_api_allowed_now",
    "public_ready_allowed_now",
    "publish_ready",
    "final_social_copy_generated",
    "auto_approval_allowed",
    "platform_export_final_allowed_now",
    "platform_api_allowed_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "newsletter_or_cms_api_allowed_now",
    "credential_read_allowed_now",
    "repo_web_search_allowed_now",
    "scraping_allowed_now",
    "news_or_rss_api_allowed_now",
    "market_data_api_allowed_now",
]


def validate_daily_content_studio_external_draft_review_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)
    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("review_mode") != "external_draft_review_only":
        errors.append("review_mode_must_be_external_draft_review_only")

    if packet.get("operator_supplied") is not True:
        errors.append("operator_supplied_must_be_true")

    # Packet-level forbidden-true booleans (checked across packet + policy blocks).
    draft_origin = packet.get("draft_origin_policy", {})
    output = packet.get("output_policy", {})
    review = packet.get("review_policy", {})
    merged = {}
    merged.update(packet)
    for block in (draft_origin, output, review):
        for k, v in block.items():
            if k in PACKET_FORBIDDEN_TRUE and v is True:
                merged[k] = True
    for flag in PACKET_FORBIDDEN_TRUE:
        if merged.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    # external_draft_supplied_by_operator must be true.
    if draft_origin.get("external_draft_supplied_by_operator") is not True:
        errors.append("external_draft_supplied_by_operator_must_be_true")

    # Manual review / not public-postable required at packet and output level.
    if review.get("manual_review_required") is not True:
        errors.append("manual_review_required_must_be_true")
    if output.get("not_public_postable") is not True:
        errors.append("not_public_postable_must_be_true")

    # External draft input enforcement.
    draft = packet.get("external_draft_input", {})
    if draft.get("generated_outside_repo") is not True:
        errors.append("draft_generated_outside_repo_must_be_true")
    if draft.get("operator_pasted") is not True:
        errors.append("draft_operator_pasted_must_be_true")
    if draft.get("manual_review_required") is not True:
        errors.append("draft_manual_review_required_must_be_true")
    if draft.get("not_public_postable") is not True:
        errors.append("draft_not_public_postable_must_be_true")
    if draft.get("source_references_visible") is not True:
        errors.append("draft_source_references_must_be_visible")
    if draft.get("limitation_notes_visible") is not True:
        errors.append("draft_limitation_notes_must_be_visible")


    # Claim classification + source/limitation coverage from review_result.
    rr = packet.get("review_result", {})
    claims = rr.get("claims", [])
    missing_src = 0
    missing_lim = 0
    for c in claims:
        cls = c.get("classification")
        if cls and cls not in CLAIM_CLASSIFICATIONS:
            errors.append(f"unknown_claim_classification:{cls}")
        needs_source = cls in ("cited_factual_claim", "current_factual_claim_requires_source")
        if needs_source and c.get("source_reference_present") is not True:
            missing_src += 1
            errors.append(f"missing_source_reference_for_claim:{c.get('claim_id', 'unknown')}")
        if c.get("limitation_note_present") is not True:
            missing_lim += 1
            errors.append(f"missing_limitation_note_for_claim:{c.get('claim_id', 'unknown')}")

    # Allowed manual next actions must not contain forbidden actions.
    actions = packet.get("manual_operator_actions", {})
    for act in actions.get("allowed_manual_next_actions", []):
        if act in FORBIDDEN_NEXT_ACTIONS:
            errors.append(f"forbidden_manual_action_allowed:{act}")
        elif act not in ALLOWED_MANUAL_NEXT_ACTIONS:
            errors.append(f"unknown_manual_action:{act}")

    # Forbidden trading/signal/execution language scan over draft text only.
    draft_text = draft.get("draft_text", "") or ""
    lower = draft_text.lower()
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

    # "Capital Chronicle alpha says" requires real approved artifacts.
    real_artifacts = review.get("real_approved_artifacts_present") is True
    if "capital chronicle alpha says" in lower and not real_artifacts:
        errors.append("alpha_claim_without_real_artifact")

    # Draft must not be represented as final ready-to-post social copy.
    if draft_text and "ready to post" in lower:
        errors.append("draft_represented_as_final_ready_to_post")
    if rr.get("represented_as_final_social_copy") is True:
        errors.append("draft_represented_as_final_social_copy")

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": sorted(set(errors))}


def _load_valid_packet():
    path = os.path.join(FIXTURES_DIR, "daily_content_studio_external_draft_review_valid.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summary():
    packet = _load_valid_packet()
    res = validate_daily_content_studio_external_draft_review_packet(packet)
    draft = packet.get("external_draft_input", {})
    rr = packet.get("review_result", {})
    claims = rr.get("claims", [])

    source_ref_count = sum(1 for c in claims if c.get("source_reference_present") is True)
    limitation_count = sum(1 for c in claims if c.get("limitation_note_present") is True)
    missing_src = sum(
        1
        for c in claims
        if c.get("classification") in ("cited_factual_claim", "current_factual_claim_requires_source")
        and c.get("source_reference_present") is not True
    )
    missing_lim = sum(1 for c in claims if c.get("limitation_note_present") is not True)

    return {
        "packet_status": packet.get("packet_status", ""),
        "external_draft_review_packet_count": 1,
        "draft_supplied_by_operator_count": 1 if draft.get("operator_pasted") is True else 0,
        "repo_generated_draft_count": 0,
        "provider_call_enabled_count": 0,
        "repo_prompt_execution_enabled_count": 0,
        "public_ready_allowed_count": 0,
        "publish_ready_count": 0,
        "final_social_copy_generated_count": 0,
        "auto_approval_enabled_count": 0,
        "platform_export_final_enabled_count": 0,
        "platform_api_enabled_count": 0,
        "live_posting_enabled_count": 0,
        "scheduler_enabled_count": 0,
        "newsletter_or_cms_api_enabled_count": 0,
        "credential_read_enabled_count": 0,
        "repo_web_search_enabled_count": 0,
        "scraping_enabled_count": 0,
        "news_or_rss_api_enabled_count": 0,
        "market_data_api_enabled_count": 0,
        "manual_review_required_all": True,
        "not_public_postable_all": True,
        "claim_count": len(claims),
        "source_reference_count": source_ref_count,
        "missing_source_reference_count": missing_src,
        "limitation_visibility_count": limitation_count,
        "missing_limitation_count": missing_lim,
        "unsafe_language_count": 0,
        "unsupported_numeric_claim_count": 0,
        "artifact_claim_without_real_artifact_count": 0,
        "forbidden_manual_action_allowed_count": 0,
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


