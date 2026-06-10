import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("daily_content_studio_operator_decision_ledger_packet.schema.json")

ALLOWED_DECISION_STATES = [
    "pending_review",
    "approved_for_manual_external_llm_prompting",
    "approved_for_manual_rewrite_outside_repo",
    "needs_revision",
    "needs_source_or_limitation_fix",
    "held_for_operator_review",
    "rejected_by_operator",
    "blocked_by_safety_policy",
    "archived_no_public_action",
]

FORBIDDEN_DECISION_STATES = [
    "approved_for_live_publish",
    "approved_for_auto_publish",
    "approved_for_platform_api",
    "approved_for_scheduler",
    "approved_for_provider_call",
    "approved_for_newsletter_send",
    "approved_public_ready_final",
    "approved_as_trading_signal",
]

DECISION_REASON_TAXONOMY = [
    "source_context_sufficient_for_review",
    "source_context_missing",
    "limitation_note_missing",
    "claim_risk_too_high",
    "signal_language_detected",
    "unsupported_numeric_claim",
    "artifact_claim_without_real_artifact",
    "platform_fit_needs_revision",
    "prompt_template_needs_revision",
    "safe_for_manual_external_drafting_only",
    "safe_for_manual_rewrite_only",
    "no_public_action",
]

ALLOWED_MANUAL_NEXT_ACTIONS = [
    "review_source_context",
    "choose_or_reject_angle_card",
    "copy_prompt_template_for_external_llm",
    "manually_rewrite_draft_outside_repo",
    "revise_source_or_limitation_notes",
    "rerun_local_validation",
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

# Packet-level decision_policy flags that must be false.
POLICY_FORBIDDEN_TRUE = {
    "live_publish_approval_allowed_now": "live_publish_approval_allowed_now_must_be_false",
    "platform_api_allowed_now": "platform_api_allowed_now_must_be_false",
    "provider_llm_api_allowed_now": "provider_llm_api_allowed_now_must_be_false",
    "repo_web_search_allowed_now": "repo_web_search_allowed_now_must_be_false",
    "scraping_allowed_now": "scraping_allowed_now_must_be_false",
    "scheduler_allowed_now": "scheduler_allowed_now_must_be_false",
    "newsletter_or_cms_api_allowed_now": "newsletter_or_cms_api_allowed_now_must_be_false",
    "credential_read_allowed_now": "credential_read_allowed_now_must_be_false",
    "auto_approval_allowed": "auto_approval_allowed_must_be_false",
    "public_ready_allowed_now": "public_ready_allowed_now_must_be_false",
    "publish_ready": "publish_ready_must_be_false",
    "final_social_copy_generated": "final_social_copy_generated_must_be_false",
}

# Per-decision-record approval flags that must be false.
RECORD_FORBIDDEN_APPROVALS = {
    "publish_ready": "record_publish_ready_must_be_false",
    "public_ready_allowed_now": "record_public_ready_allowed_now_must_be_false",
    "live_publish_approval_granted": "record_live_publish_approval_must_be_false",
    "platform_api_approval_granted": "record_platform_api_approval_must_be_false",
    "provider_call_approval_granted": "record_provider_call_approval_must_be_false",
    "scheduler_approval_granted": "record_scheduler_approval_must_be_false",
    "newsletter_or_cms_send_approval_granted": "record_newsletter_cms_approval_must_be_false",
}


def validate_daily_content_studio_operator_decision_ledger_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)
    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("runtime_authority"):
        errors.append("runtime_authority_must_be_false")

    if packet.get("ledger_mode") != "local_review_decision_only":
        errors.append("ledger_mode_must_be_local_review_decision_only")

    # Packet-level decision policy enforcement.
    dp = packet.get("decision_policy", {})
    if dp.get("manual_review_required") is not True:
        errors.append("decision_policy_manual_review_required_must_be_true")
    if dp.get("not_public_postable") is not True:
        errors.append("decision_policy_not_public_postable_must_be_true")
    for flag, label in POLICY_FORBIDDEN_TRUE.items():
        if dp.get(flag) is True:
            errors.append(label)

    # Source lineage / limitations policy.
    lineage = packet.get("source_lineage_policy", {})
    if lineage.get("source_lineage_required") is not True:
        errors.append("source_lineage_required_must_be_true")
    if lineage.get("limitations_required") is not True:
        errors.append("limitations_required_must_be_true")

    # Allowed decision states must not contain forbidden states.
    for st in packet.get("allowed_decision_states", []):
        if st in FORBIDDEN_DECISION_STATES:
            errors.append(f"forbidden_decision_state_in_allowed_list:{st}")

    # Decision records enforcement.
    for rec in packet.get("decision_records", []):
        rid = rec.get("decision_id", "unknown")
        state = rec.get("decision_state")
        if state in FORBIDDEN_DECISION_STATES:
            errors.append(f"forbidden_decision_state:{state}:{rid}")
        elif state not in ALLOWED_DECISION_STATES:
            errors.append(f"unknown_decision_state:{state}:{rid}")

        if rec.get("manual_review_required") is not True:
            errors.append(f"record_manual_review_required_must_be_true:{rid}")
        if rec.get("not_public_postable") is not True:
            errors.append(f"record_not_public_postable_must_be_true:{rid}")

        for flag, label in RECORD_FORBIDDEN_APPROVALS.items():
            if rec.get(flag) is True:
                errors.append(f"{label}:{rid}")

        if rec.get("source_lineage_confirmed") is not True:
            errors.append(f"record_source_lineage_not_confirmed:{rid}")
        if rec.get("limitations_confirmed") is not True:
            errors.append(f"record_limitations_not_confirmed:{rid}")

        for reason in rec.get("decision_reasons", []):
            if reason not in DECISION_REASON_TAXONOMY:
                errors.append(f"unknown_decision_reason:{reason}:{rid}")

        for act in rec.get("allowed_manual_next_actions", []):
            if act in FORBIDDEN_NEXT_ACTIONS:
                errors.append(f"forbidden_manual_action_allowed:{act}:{rid}")
            elif act not in ALLOWED_MANUAL_NEXT_ACTIONS:
                errors.append(f"unknown_manual_action:{act}:{rid}")


    # Forbidden trading/signal/execution/model-prediction language scan.
    # Scan only operator-authored free-text, not structural policy/taxonomy keys.
    free_text_parts = []
    for rec in packet.get("decision_records", []):
        note = rec.get("operator_notes")
        if isinstance(note, str):
            free_text_parts.append(note)
    audit_note = packet.get("audit_summary", {}).get("operator_notes")
    if isinstance(audit_note, str):
        free_text_parts.append(audit_note)
    free_text = "\n".join(free_text_parts)
    lower = free_text.lower()

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
        "entry",
        "exit",
        "broker",
    ]
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
    review = packet.get("review_policy", {})
    real_artifacts = review.get("real_approved_artifacts_present") is True
    if "Capital Chronicle alpha says" in json.dumps(packet) and not real_artifacts:
        errors.append("alpha_claim_without_real_artifact")

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": sorted(set(errors))}


def _load_valid_packet():
    fixtures_dir = os.path.join(BASE_DIR, "fixtures", "daily_content_studio_decision_ledger")
    path = os.path.join(fixtures_dir, "daily_content_studio_decision_ledger_valid.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summary():
    packet = _load_valid_packet()
    res = validate_daily_content_studio_operator_decision_ledger_packet(packet)
    records = packet.get("decision_records", [])
    lineage = packet.get("source_lineage_policy", {})

    def _count(flag):
        return sum(1 for r in records if r.get(flag) is True)

    forbidden_states = sum(
        1 for r in records if r.get("decision_state") in FORBIDDEN_DECISION_STATES
    )
    forbidden_actions = sum(
        1
        for r in records
        for a in r.get("allowed_manual_next_actions", [])
        if a in FORBIDDEN_NEXT_ACTIONS
    )
    dp = packet.get("decision_policy", {})
    lineage_required = lineage.get("source_lineage_required") is True
    limitations_required = lineage.get("limitations_required") is True

    return {
        "packet_status": packet.get("packet_status", ""),
        "decision_record_count": len(records),
        "allowed_decision_state_count": len(packet.get("allowed_decision_states", [])),
        "forbidden_decision_state_count": forbidden_states,
        "manual_review_required_all": all(
            r.get("manual_review_required") is True for r in records
        ),
        "not_public_postable_all": all(
            r.get("not_public_postable") is True for r in records
        ),
        "publish_ready_count": _count("publish_ready"),
        "public_ready_allowed_count": _count("public_ready_allowed_now"),
        "live_publish_approval_count": _count("live_publish_approval_granted"),
        "platform_api_approval_count": _count("platform_api_approval_granted"),
        "provider_call_approval_count": _count("provider_call_approval_granted"),
        "scheduler_approval_count": _count("scheduler_approval_granted"),
        "newsletter_or_cms_send_approval_count": _count("newsletter_or_cms_send_approval_granted"),
        "auto_approval_enabled_count": 1 if dp.get("auto_approval_allowed") is True else 0,
        "final_social_copy_generated_count": 1 if dp.get("final_social_copy_generated") is True else 0,
        "source_lineage_required_count": len(records) if lineage_required else 0,
        "source_lineage_confirmed_count": _count("source_lineage_confirmed"),
        "limitations_required_count": len(records) if limitations_required else 0,
        "limitations_confirmed_count": _count("limitations_confirmed"),
        "forbidden_manual_action_allowed_count": forbidden_actions,
        "unsafe_language_count": 0,
        "unsupported_numeric_claim_count": 0,
        "artifact_claim_without_real_artifact_count": 0,
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


