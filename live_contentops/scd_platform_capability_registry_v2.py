"""Grounded platform capability registry v2 validators.

Local-only, deterministic, fail-closed. This module models official-doc-backed
platform capability metadata, future credential slots, dry-run payload policy,
and compatibility reports for existing compiler/readiness/audit contracts.

It does not call platform APIs, read credentials, build clients, schedule work,
dispatch content, scrape, or enable public/live readiness.
"""
import re
from datetime import date

from live_contentops.scd_domain_model import (
    PASS,
    BLOCKED,
    REVIEW_REQUIRED,
    UNKNOWN,
    _schema_ok,
)


APPROVED_PLATFORM_IDS_V2 = (
    "telegram",
    "x_twitter",
    "linkedin",
    "facebook_page",
    "instagram",
    "threads",
    "tiktok",
    "substack_newsletter",
    "generic_manual",
)

OFFICIAL_DOC_DOMAIN_ALLOWLIST = (
    "core.telegram.org",
    "docs.x.com",
    "developer.x.com",
    "learn.microsoft.com",
    "developers.facebook.com",
    "developers.tiktok.com",
    "substack.com",
    "support.substack.com",
)

PLATFORM_LIVE_RISK_LEVELS = {
    "telegram": "medium_first_future_candidate",
    "x_twitter": "high_policy_cost_access_sensitive",
    "linkedin": "high_restricted_permissions",
    "facebook_page": "high_meta_app_review_identity",
    "instagram": "high_meta_app_review_media_constraints",
    "threads": "high_access_and_permissions",
    "tiktok": "very_high_audit_and_creator_control",
    "substack_newsletter": "high_write_api_unknown_manual_only",
    "generic_manual": "low_manual_only",
}

CURRENT_REPO_ALLOWED_STATES = (
    "dry_run_only",
    "manual_export_only",
    "future_live_gate_required",
    "unsupported_until_docs_verified",
    "blocked_unknown_docs",
)

FORBIDDEN_RUNTIME_ACTION_WORDS = (
    "http" + "://",
    "https" + "://",
    "api.telegram" + ".org",
    "api.x" + ".com",
    "graph.facebook" + ".com",
    "open.tiktokapis" + ".com",
    "authorization",
    "bearer",
    "token" + "=",
    "api" + "_" + "key",
    "access" + "_" + "token",
    "client" + "_" + "secret",
    "refresh" + "_" + "token",
    "webhook",
    "send" + "message",
    "set" + "webhook",
    "get" + "updates",
    "dispatch",
    "publish now",
    "go live",
    "live call",
    "scheduler",
    "scrape",
    "autonomous reply",
)

FORBIDDEN_SECRET_PATTERNS = (
    r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b",
    r"\bsk-[A-Za-z0-9]{8,}\b",
    r"\bghp_[A-Za-z0-9]{20,}\b",
    r"\bxoxb-[A-Za-z0-9-]{10,}\b",
    r"\bAKIA[0-9A-Z]{12,}\b",
    r"\bya29\.[A-Za-z0-9_-]{20,}\b",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bbearer\s+[A-Za-z0-9_\-.=]{20,}\b",
    r"\bapi[_-]?key\b",
    r"\baccess[_-]?token\b",
    r"\bclient[_-]?secret\b",
    r"\brefresh[_-]?token\b",
)

REQUIRED_DISABLED_FLAGS = (
    "live_api_enabled_now",
    "platform_api_allowed_now",
    "credential_read_allowed_now",
    "credentials_requested_now",
    "posting_enabled_now",
    "scheduler_enabled_now",
    "autonomous_replies_enabled_now",
    "dms_enabled_now",
    "scraping_enabled_now",
    "public_ready",
    "live_ready",
    "dispatch_ready",
)

SIGNAL_LANGUAGE_PATTERNS = (
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\blong\b",
    r"\bshort\b",
    r"target price",
    r"price target",
    r"position sizing",
    r"trading signal",
    r"watch this level",
    r"our model predicts",
    r"our signal says",
    r"guaranteed prediction",
    r"capital chronicle alpha says",
)

REQUIRED_READINESS_FALSE_FLAGS = (
    "credentials_requested_now",
    "credential_read_allowed_now",
    "platform_api_allowed_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now",
    "scraping_allowed_now",
    "publish_all_button_enabled_now",
    "one_button_publish_all_enabled_now",
    "final_social_copy_generated",
)

SCHEMA_BY_KIND = {
    "official_doc_source": "scd_platform_official_doc_source.schema.json",
    "official_docs_verification_pack": "scd_platform_official_docs_verification_pack.schema.json",
    "capability_profile_v2": "scd_platform_capability_profile_v2.schema.json",
    "credential_slot_policy": "scd_platform_credential_slot_policy.schema.json",
    "live_gate_checklist": "scd_platform_live_gate_checklist.schema.json",
    "dry_run_payload_policy_matrix": "scd_platform_dry_run_payload_policy_matrix.schema.json",
    "registry_compiler_alignment_report": "scd_platform_registry_compiler_alignment_report.schema.json",
    "publish_readiness_alignment_report": "scd_platform_publish_readiness_alignment_report.schema.json",
    "redacted_audit_alignment_report": "scd_platform_redacted_audit_alignment_report.schema.json",
}


def _value(mapping, key, default=None):
    if isinstance(mapping, dict) and key in mapping:
        return mapping[key]
    return default


def _state(blocked, review=None, unknown=None):
    review = review or []
    unknown = unknown or []
    if blocked:
        return {"validation_state": BLOCKED, "reasons": sorted(set(blocked))}
    if unknown:
        return {"validation_state": UNKNOWN, "reasons": sorted(set(unknown))}
    if review:
        return {"validation_state": REVIEW_REQUIRED, "reasons": sorted(set(review))}
    return {"validation_state": PASS, "reasons": ["ok"]}


def _schema_state(packet, kind):
    schema_name = SCHEMA_BY_KIND[kind]
    ok, message = _schema_ok(packet, schema_name)
    if ok:
        return []
    return [f"schema:{message}"]


def _domain_from_url(url):
    if not isinstance(url, str) or not url:
        return ""
    lowered = url.strip().lower()
    marker = "://"
    if marker in lowered:
        lowered = lowered.split(marker, 1)[1]
    domain = lowered.split("/", 1)[0]
    domain = domain.split("?", 1)[0]
    domain = domain.split("#", 1)[0]
    return domain


def _is_official_doc_url(url):
    domain = _domain_from_url(url)
    return domain in OFFICIAL_DOC_DOMAIN_ALLOWLIST


def _collect_string_values(node, skip_keys=()):
    values = []
    skip = set(skip_keys)

    def walk(current, parent_key=""):
        if isinstance(current, dict):
            for key, val in current.items():
                if key in skip:
                    continue
                walk(val, key)
        elif isinstance(current, list):
            for item in current:
                walk(item, parent_key)
        elif isinstance(current, str):
            values.append((parent_key, current))

    walk(node)
    return values


def _unsafe_runtime_hits(packet, skip_keys=()):
    hits = []
    values = _collect_string_values(packet, skip_keys)
    for key, raw in values:
        lower = raw.lower()
        for word in FORBIDDEN_RUNTIME_ACTION_WORDS:
            if word in lower:
                hits.append(f"forbidden_runtime_value:{key}:{word}")
        for pat in SIGNAL_LANGUAGE_PATTERNS:
            if re.search(pat, lower):
                hits.append(f"forbidden_signal_value:{key}:{pat}")
    return hits


def _secret_hits(packet):
    hits = []
    values = _collect_string_values(packet)
    for key, raw in values:
        for pat in FORBIDDEN_SECRET_PATTERNS:
            if re.search(pat, raw, flags=re.IGNORECASE):
                hits.append(f"secret_like_value:{key}:{pat}")
    return hits


def _declared_state(packet):
    return _value(packet, "validation_state")


def _apply_declared_state(packet, computed):
    declared = _declared_state(packet)
    if declared == PASS and computed["validation_state"] != PASS:
        reasons = list(computed["reasons"])
        reasons.append("declared_pass_contradicts_computed_state")
        return {"validation_state": BLOCKED, "reasons": sorted(set(reasons))}
    return computed


def _stale_retrieval(retrieved_date):
    if not isinstance(retrieved_date, str) or not retrieved_date:
        return False
    try:
        retrieved = date.fromisoformat(retrieved_date)
    except ValueError:
        return False
    return (date(2026, 6, 14) - retrieved).days > 365


def _sources_for_platform(sources, platform_id):
    selected = []
    for source in sources:
        if _value(source, "platform_id") == platform_id:
            selected.append(source)
    return selected


def _rollup(states):
    if BLOCKED in states:
        return BLOCKED
    if UNKNOWN in states:
        return UNKNOWN
    if REVIEW_REQUIRED in states:
        return REVIEW_REQUIRED
    return PASS


def validate_platform_official_doc_source(packet):
    blocked = _schema_state(packet, "official_doc_source")
    review = []
    unknown = []

    platform_id = _value(packet, "platform_id")
    if platform_id not in APPROVED_PLATFORM_IDS_V2:
        blocked.append(f"platform_not_approved:{platform_id}")

    source_status = _value(packet, "source_status", "official")
    manual_not_applicable = platform_id == "generic_manual" and source_status == "not_applicable_manual"

    url = _value(packet, "official_doc_url")
    if not url and not manual_not_applicable:
        unknown.append("official_doc_url_missing")
    elif url and not manual_not_applicable and not _is_official_doc_url(url):
        blocked.append("official_doc_domain_not_allowlisted")

    if not _value(packet, "doc_title"):
        unknown.append("doc_title_missing")
    if not _value(packet, "retrieved_date"):
        unknown.append("retrieved_date_missing")
    elif _stale_retrieval(_value(packet, "retrieved_date")):
        review.append("retrieved_date_stale")

    if _value(packet, "advisory_only") is not True:
        blocked.append("official_doc_source_must_be_advisory_only")
    if _value(packet, "runtime_authority") is True:
        blocked.append("runtime_authority_must_be_false")

    if manual_not_applicable:
        pass
    elif source_status == "missing":
        unknown.append("official_docs_missing")
    elif source_status in ("unofficial", "unknown_source"):
        blocked.append("source_status_not_official")
    elif source_status in ("deprecated", "sunset"):
        review.append(f"source_status_requires_review:{source_status}")

    blocked.extend(_unsafe_runtime_hits(packet, skip_keys=("official_doc_url",)))
    blocked.extend(_secret_hits(packet))

    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_official_docs_verification_pack(packet):
    blocked = _schema_state(packet, "official_docs_verification_pack")
    review = []
    unknown = []

    if _value(packet, "advisory_only") is not True:
        blocked.append("verification_pack_must_be_advisory_only")
    if _value(packet, "runtime_authority") is True:
        blocked.append("runtime_authority_must_be_false")

    sources = _value(packet, "official_doc_sources", []) or []
    if not sources:
        unknown.append("no_official_doc_sources")

    source_states = []
    for source in sources:
        res = validate_platform_official_doc_source(source)
        source_states.append(res["validation_state"])
        if res["validation_state"] == BLOCKED:
            blocked.append(f"source_blocked:{_value(source, 'official_doc_source_id', 'unknown')}")
        elif res["validation_state"] == UNKNOWN:
            unknown.append(f"source_unknown:{_value(source, 'official_doc_source_id', 'unknown')}")
        elif res["validation_state"] == REVIEW_REQUIRED:
            review.append(f"source_review_required:{_value(source, 'official_doc_source_id', 'unknown')}")

    for platform_id in APPROVED_PLATFORM_IDS_V2:
        if not _sources_for_platform(sources, platform_id):
            unknown.append(f"missing_official_doc_source_for:{platform_id}")

    blocked.extend(_unsafe_runtime_hits(packet, skip_keys=("official_doc_url",)))
    blocked.extend(_secret_hits(packet))

    computed = _state(blocked, review, unknown)
    return _apply_declared_state(packet, computed)


def _disabled_flag_errors(packet):
    errors = []
    for flag in REQUIRED_DISABLED_FLAGS:
        if _value(packet, flag) is True:
            errors.append(f"{flag}_must_be_false")
    return errors


def validate_platform_capability_profile_v2(packet):
    blocked = _schema_state(packet, "capability_profile_v2")
    review = []
    unknown = []

    platform_id = _value(packet, "platform_id")
    if platform_id not in APPROVED_PLATFORM_IDS_V2:
        blocked.append(f"platform_not_approved:{platform_id}")

    source_ids = _value(packet, "official_doc_source_ids", []) or []
    if not source_ids:
        unknown.append("official_doc_source_ids_missing")

    allowed_state = _value(packet, "current_repo_allowed_state")
    if allowed_state not in CURRENT_REPO_ALLOWED_STATES:
        blocked.append(f"invalid_current_repo_allowed_state:{allowed_state}")
    if allowed_state == "blocked_unknown_docs":
        unknown.append("current_repo_state_blocked_unknown_docs")
    if allowed_state == "unsupported_until_docs_verified":
        unknown.append("unsupported_until_docs_verified")

    blocked.extend(_disabled_flag_errors(packet))
    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))

    if _value(packet, "app_review_or_verification_required") is True:
        review.append("app_review_or_verification_required_later")
    if _value(packet, "restricted_access_or_cost_sensitive") is True:
        review.append("restricted_access_or_cost_sensitive")
    if _value(packet, "future_live_gate_required") is True:
        review.append("future_live_gate_required_later")

    if platform_id == "telegram":
        if _value(packet, "first_future_supervised_live_candidate") is not True:
            blocked.append("telegram_must_be_first_future_supervised_live_candidate")
        if allowed_state not in ("dry_run_only", "future_live_gate_required"):
            blocked.append("telegram_current_state_must_be_dry_run_or_future_gate")
        if _value(packet, "actual_channel_id_present") is True:
            blocked.append("telegram_actual_channel_id_must_not_be_present")
    elif platform_id == "x_twitter":
        disclosures = _value(packet, "disclosure_and_policy_fields", []) or []
        if "made_with_ai" not in disclosures:
            review.append("x_made_with_ai_disclosure_field_not_recorded")
    elif platform_id == "linkedin":
        modes = _value(packet, "posting_identity_modes", []) or []
        if "member" not in modes or "organization" not in modes:
            blocked.append("linkedin_must_distinguish_member_and_organization_posting")
    elif platform_id == "tiktok":
        if _value(packet, "future_priority") != "last_priority_high_friction":
            blocked.append("tiktok_must_be_last_priority_high_friction")
    elif platform_id == "substack_newsletter":
        if _value(packet, "api_write_publish_supported") is True:
            blocked.append("substack_write_publish_api_must_not_be_claimed")
        if allowed_state not in ("manual_export_only", "blocked_unknown_docs"):
            blocked.append("substack_must_be_manual_export_or_unknown_docs")
    elif platform_id == "generic_manual":
        if _value(packet, "platform_api_allowed_now") is True:
            blocked.append("generic_manual_must_have_no_api")
        if _value(packet, "credential_required_later") is True:
            blocked.append("generic_manual_must_have_no_credential")

    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_credential_slot_policy(packet):
    blocked = _schema_state(packet, "credential_slot_policy")
    review = []
    unknown = []

    if _value(packet, "credential_value_present") is True:
        blocked.append("credential_value_present_must_be_false")
    if _value(packet, "credential_validation_enabled_now") is True:
        blocked.append("credential_validation_enabled_now_must_be_false")
    if _value(packet, "env_read_allowed_now") is True:
        blocked.append("env_read_allowed_now_must_be_false")
    if _value(packet, "os_env_read_allowed_now") is True:
        blocked.append("os_env_read_allowed_now_must_be_false")
    if _value(packet, "secret_redaction_required") is not True:
        blocked.append("secret_redaction_required_must_be_true")
    if _value(packet, "no_secret_scan_required") is not True:
        blocked.append("no_secret_scan_required_must_be_true")

    slots = _value(packet, "platform_credential_slots", []) or []
    if not slots:
        unknown.append("no_credential_slots_declared")
    for slot in slots:
        platform_id = _value(slot, "platform_id")
        if platform_id not in APPROVED_PLATFORM_IDS_V2:
            blocked.append(f"credential_slot_platform_not_approved:{platform_id}")
        if _value(slot, "slot_values_present") is True:
            blocked.append(f"slot_values_present_must_be_false:{platform_id}")
        if _value(slot, "credential_requested_now") is True:
            blocked.append(f"credential_requested_now_must_be_false:{platform_id}")
        if _value(slot, "credential_read_allowed_now") is True:
            blocked.append(f"credential_read_allowed_now_must_be_false:{platform_id}")
        if not (_value(slot, "slot_names", []) or []):
            unknown.append(f"slot_names_missing:{platform_id}")

    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))
    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_live_gate_checklist(packet):
    blocked = _schema_state(packet, "live_gate_checklist")
    review = []
    unknown = []

    platform_id = _value(packet, "platform_id")
    if platform_id not in APPROVED_PLATFORM_IDS_V2:
        blocked.append(f"platform_not_approved:{platform_id}")

    if _value(packet, "live_ready") is True:
        blocked.append("live_ready_must_be_false_now")
    for flag in (
        "operator_go_required_later",
        "per_post_approval_required_later",
        "kill_switch_check_required_later",
        "redacted_audit_required_later",
    ):
        if _value(packet, flag) is not True:
            blocked.append(f"{flag}_must_be_true")
    for flag in (
        "autonomous_replies_enabled_now",
        "dms_enabled_now",
        "scheduler_enabled_now",
        "scraping_enabled_now",
        "posting_enabled_now",
        "dispatch_ready",
    ):
        if _value(packet, flag) is True:
            blocked.append(f"{flag}_must_be_false")

    if platform_id == "telegram" and _value(packet, "first_future_candidate") is not True:
        review.append("telegram_first_future_candidate_not_marked")
    if platform_id == "tiktok" and _value(packet, "high_friction_future_late") is not True:
        blocked.append("tiktok_high_friction_future_late_must_be_true")

    if not (_value(packet, "official_doc_source_ids", []) or []):
        unknown.append("official_doc_source_ids_missing")

    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))
    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_dry_run_payload_policy_matrix(packet):
    blocked = _schema_state(packet, "dry_run_payload_policy_matrix")
    review = []
    unknown = []

    rows = _value(packet, "platform_policies", []) or []
    if not rows:
        unknown.append("platform_policies_missing")

    for row in rows:
        platform_id = _value(row, "platform_id")
        if platform_id not in APPROVED_PLATFORM_IDS_V2:
            blocked.append(f"platform_not_approved:{platform_id}")
        endpoint_names = _value(row, "endpoint_family_names_symbolic", []) or []
        if not endpoint_names:
            unknown.append(f"endpoint_family_names_symbolic_missing:{platform_id}")
        for endpoint_name in endpoint_names:
            lowered = endpoint_name.lower()
            if "://" in lowered or ".com" in lowered or ".org" in lowered or "/" in lowered:
                blocked.append(f"endpoint_family_must_be_symbolic:{platform_id}")
        shapes = _value(row, "allowed_payload_shapes", []) or []
        for shape in shapes:
            if shape not in ("dry_run", "mock", "manual_export"):
                blocked.append(f"invalid_allowed_payload_shape:{platform_id}:{shape}")
        for flag in (
            "authorization_header_allowed",
            "webhook_url_allowed",
            "live_control_allowed",
            "public_ready_allowed",
            "posting_control_allowed",
        ):
            if _value(row, flag) is True:
                blocked.append(f"{flag}_must_be_false:{platform_id}")

    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))
    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_registry_compiler_alignment_report(packet):
    blocked = _schema_state(packet, "registry_compiler_alignment_report")
    review = []
    unknown = []

    registry_ids = set(_value(packet, "registry_platform_ids", []) or [])
    compiler_ids = set(_value(packet, "existing_compiler_platform_ids", []) or [])
    registry_only = set(_value(packet, "registry_only_platform_ids", []) or [])

    if not registry_ids:
        unknown.append("registry_platform_ids_missing")
    if not compiler_ids:
        unknown.append("existing_compiler_platform_ids_missing")
    computed_registry_only = registry_ids - compiler_ids
    if computed_registry_only != registry_only:
        blocked.append("registry_only_platform_ids_do_not_match_computed_set")
    if registry_only:
        review.append("compiler_expansion_required_later")

    contradictions = _value(packet, "contradictions", []) or []
    if contradictions:
        blocked.append("compiler_alignment_contradictions_present")
    if _value(packet, "credential_allowed_now") is True:
        blocked.append("credential_allowed_now_must_be_false")
    if _value(packet, "live_allowed_now") is True:
        blocked.append("live_allowed_now_must_be_false")
    if _value(packet, "public_ready_allowed_now") is True:
        blocked.append("public_ready_allowed_now_must_be_false")

    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))
    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_publish_readiness_alignment_report(packet):
    blocked = _schema_state(packet, "publish_readiness_alignment_report")
    review = []
    unknown = []

    flags = _value(packet, "forbidden_now_flags_confirmed_false", []) or []
    seen = set()
    for item in flags:
        flag = _value(item, "flag")
        seen.add(flag)
        if _value(item, "confirmed_false") is not True:
            blocked.append(f"readiness_flag_not_confirmed_false:{flag}")
    for required in REQUIRED_READINESS_FALSE_FLAGS:
        if required not in seen:
            unknown.append(f"readiness_required_flag_missing:{required}")

    if _value(packet, "contradiction_count", 0) != 0:
        blocked.append("publish_readiness_contradiction_count_must_be_zero")
    if _value(packet, "publish_readiness_still_dry_run_only") is not True:
        blocked.append("publish_readiness_still_dry_run_only_must_be_true")

    blocked.extend(_unsafe_runtime_hits(packet, skip_keys=("flag",)))
    blocked.extend(_secret_hits(packet))
    return _apply_declared_state(packet, _state(blocked, review, unknown))


def validate_platform_redacted_audit_alignment_report(packet):
    blocked = _schema_state(packet, "redacted_audit_alignment_report")
    review = []
    unknown = []

    for flag in (
        "platform_response_logging_future_only",
        "platform_response_redaction_required_later",
        "credential_values_forbidden",
        "credential_logging_forbidden",
        "credential_printing_forbidden",
        "credential_commit_forbidden",
    ):
        if _value(packet, flag) is not True:
            blocked.append(f"{flag}_must_be_true")

    if _value(packet, "credential_value_present") is True:
        blocked.append("credential_value_present_must_be_false")
    if _value(packet, "live_event_present") is True:
        blocked.append("live_event_present_must_be_false")
    if _value(packet, "platform_api_called") is True:
        blocked.append("platform_api_called_must_be_false")
    if _value(packet, "contradiction_count", 0) != 0:
        blocked.append("redacted_audit_contradiction_count_must_be_zero")

    blocked.extend(_unsafe_runtime_hits(packet))
    blocked.extend(_secret_hits(packet))
    return _apply_declared_state(packet, _state(blocked, review, unknown))


def _source_ids(official_doc_sources, platform_id):
    ids = []
    for source in official_doc_sources:
        if _value(source, "platform_id") == platform_id:
            source_id = _value(source, "official_doc_source_id")
            if source_id:
                ids.append(source_id)
    return ids


def build_platform_capability_profile_v2(platform_id, official_doc_sources, capability_notes):
    source_ids = _source_ids(official_doc_sources, platform_id)
    base = {
        "schema_version": "2.0",
        "profile_id": f"capability-profile-v2-{platform_id}",
        "platform_id": platform_id,
        "display_name": _value(capability_notes, "display_name", platform_id),
        "official_doc_source_ids": source_ids,
        "endpoint_family_names_symbolic": list(_value(capability_notes, "endpoint_family_names_symbolic", [])),
        "publish_capability_summary": _value(capability_notes, "publish_capability_summary", ""),
        "current_repo_allowed_state": _value(
            capability_notes,
            "current_repo_allowed_state",
            "blocked_unknown_docs" if not source_ids else "future_live_gate_required",
        ),
        "live_risk_level": _value(
            capability_notes,
            "live_risk_level",
            _value(PLATFORM_LIVE_RISK_LEVELS, platform_id, "high_unknown"),
        ),
        "credential_slot_names_future_only": list(_value(capability_notes, "credential_slot_names_future_only", [])),
        "credential_required_later": _value(capability_notes, "credential_required_later", platform_id != "generic_manual"),
        "app_review_or_verification_required": _value(capability_notes, "app_review_or_verification_required", False),
        "restricted_access_or_cost_sensitive": _value(capability_notes, "restricted_access_or_cost_sensitive", False),
        "future_live_gate_required": _value(capability_notes, "future_live_gate_required", platform_id != "generic_manual"),
        "first_future_supervised_live_candidate": platform_id == "telegram",
        "actual_channel_id_present": False,
        "posting_identity_modes": list(_value(capability_notes, "posting_identity_modes", [])),
        "disclosure_and_policy_fields": list(_value(capability_notes, "disclosure_and_policy_fields", [])),
        "future_priority": _value(capability_notes, "future_priority", "normal_future_gate"),
        "api_write_publish_supported": _value(capability_notes, "api_write_publish_supported", platform_id not in ("substack_newsletter", "generic_manual")),
        "live_api_enabled_now": False,
        "platform_api_allowed_now": False,
        "credential_read_allowed_now": False,
        "credentials_requested_now": False,
        "posting_enabled_now": False,
        "scheduler_enabled_now": False,
        "autonomous_replies_enabled_now": False,
        "dms_enabled_now": False,
        "scraping_enabled_now": False,
        "public_ready": False,
        "live_ready": False,
        "dispatch_ready": False,
        "validation_state": _value(capability_notes, "validation_state", REVIEW_REQUIRED if platform_id != "generic_manual" else PASS),
        "blocked_reasons": [],
        "review_required_reasons": list(_value(capability_notes, "review_required_reasons", [])),
        "unsupported_or_unknown_fields": list(_value(capability_notes, "unsupported_or_unknown_fields", [])),
    }
    if not source_ids:
        base["validation_state"] = UNKNOWN
    return base


def build_platform_live_gate_checklist(platform_id, official_doc_sources, future_scope):
    return {
        "schema_version": "2.0",
        "checklist_id": f"live-gate-checklist-{platform_id}",
        "platform_id": platform_id,
        "official_doc_source_ids": _source_ids(official_doc_sources, platform_id),
        "future_scope": future_scope,
        "live_ready": False,
        "operator_go_required_later": True,
        "per_post_approval_required_later": True,
        "kill_switch_check_required_later": True,
        "redacted_audit_required_later": True,
        "autonomous_replies_enabled_now": False,
        "dms_enabled_now": False,
        "scheduler_enabled_now": False,
        "scraping_enabled_now": False,
        "posting_enabled_now": False,
        "dispatch_ready": False,
        "first_future_candidate": platform_id == "telegram",
        "high_friction_future_late": platform_id == "tiktok",
        "validation_state": PASS,
        "blocked_reasons": [],
    }


def build_platform_dry_run_payload_policy_matrix(platform_profiles):
    rows = []
    for profile in platform_profiles:
        platform_id = _value(profile, "platform_id")
        state = _value(profile, "current_repo_allowed_state")
        shape = "manual_export" if state == "manual_export_only" else "dry_run"
        rows.append({
            "platform_id": platform_id,
            "endpoint_family_names_symbolic": list(_value(profile, "endpoint_family_names_symbolic", [])),
            "allowed_payload_shapes": [shape],
            "authorization_header_allowed": False,
            "webhook_url_allowed": False,
            "live_control_allowed": False,
            "public_ready_allowed": False,
            "posting_control_allowed": False,
            "future_gate_notes": list(_value(profile, "unsupported_or_unknown_fields", [])),
        })
    return {
        "schema_version": "2.0",
        "matrix_id": "dry-run-payload-policy-matrix-v2",
        "platform_policies": rows,
        "validation_state": PASS,
        "blocked_reasons": [],
    }


def build_registry_compiler_alignment_report(platform_profiles, existing_compiler_platforms):
    registry_ids = sorted(_value(profile, "platform_id") for profile in platform_profiles)
    compiler_ids = sorted(existing_compiler_platforms)
    registry_only = sorted(set(registry_ids) - set(compiler_ids))
    live_allowed = any(_value(profile, "live_api_enabled_now") is True for profile in platform_profiles)
    credential_allowed = any(_value(profile, "credential_read_allowed_now") is True for profile in platform_profiles)
    public_allowed = any(_value(profile, "public_ready") is True for profile in platform_profiles)
    contradictions = []
    if live_allowed:
        contradictions.append("registry_live_allowed_now")
    if credential_allowed:
        contradictions.append("registry_credential_allowed_now")
    if public_allowed:
        contradictions.append("registry_public_ready_allowed_now")
    state = BLOCKED if contradictions else REVIEW_REQUIRED if registry_only else PASS
    return {
        "schema_version": "2.0",
        "report_id": "registry-compiler-alignment-v2",
        "registry_platform_ids": registry_ids,
        "existing_compiler_platform_ids": compiler_ids,
        "registry_only_platform_ids": registry_only,
        "compiler_expansion_required_later": bool(registry_only),
        "credential_allowed_now": credential_allowed,
        "live_allowed_now": live_allowed,
        "public_ready_allowed_now": public_allowed,
        "contradictions": contradictions,
        "validation_state": state,
        "blocked_reasons": contradictions,
    }


def build_publish_readiness_alignment_report(platform_profiles, readiness_summary):
    flags = []
    contradictions = []
    for flag in REQUIRED_READINESS_FALSE_FLAGS:
        value = _value(readiness_summary, flag, False)
        confirmed_false = value is False or value == 0
        flags.append({"flag": flag, "confirmed_false": confirmed_false})
        if not confirmed_false:
            contradictions.append(flag)
    return {
        "schema_version": "2.0",
        "report_id": "publish-readiness-alignment-v2",
        "profile_count": len(platform_profiles),
        "publish_readiness_still_dry_run_only": _value(readiness_summary, "dry_run_only", True) is True,
        "forbidden_now_flags_confirmed_false": flags,
        "contradiction_count": len(contradictions),
        "contradictions": contradictions,
        "validation_state": BLOCKED if contradictions else PASS,
        "blocked_reasons": contradictions,
    }


def build_redacted_audit_alignment_report(platform_profiles, audit_policy_summary):
    contradiction_flags = []
    for flag in ("credential_value_present", "live_event_present", "platform_api_called"):
        if _value(audit_policy_summary, flag, False) is True:
            contradiction_flags.append(flag)
    return {
        "schema_version": "2.0",
        "report_id": "redacted-audit-alignment-v2",
        "profile_count": len(platform_profiles),
        "platform_response_logging_future_only": _value(audit_policy_summary, "platform_response_logging_future_only", True) is True,
        "platform_response_redaction_required_later": _value(audit_policy_summary, "platform_response_redaction_required_later", True) is True,
        "credential_values_forbidden": _value(audit_policy_summary, "credential_values_forbidden", True) is True,
        "credential_logging_forbidden": _value(audit_policy_summary, "credential_logging_forbidden", True) is True,
        "credential_printing_forbidden": _value(audit_policy_summary, "credential_printing_forbidden", True) is True,
        "credential_commit_forbidden": _value(audit_policy_summary, "credential_commit_forbidden", True) is True,
        "credential_value_present": _value(audit_policy_summary, "credential_value_present", False) is True,
        "live_event_present": _value(audit_policy_summary, "live_event_present", False) is True,
        "platform_api_called": _value(audit_policy_summary, "platform_api_called", False) is True,
        "contradiction_count": len(contradiction_flags),
        "contradictions": contradiction_flags,
        "validation_state": BLOCKED if contradiction_flags else PASS,
        "blocked_reasons": contradiction_flags,
    }


def build_platform_registry_v2_summary(
    pack,
    profiles,
    credential_policy,
    live_gate_checklists,
    policy_matrix,
    alignment_reports,
):
    results = []
    results.append(validate_platform_official_docs_verification_pack(pack))
    for profile in profiles:
        results.append(validate_platform_capability_profile_v2(profile))
    results.append(validate_platform_credential_slot_policy(credential_policy))
    for checklist in live_gate_checklists:
        results.append(validate_platform_live_gate_checklist(checklist))
    results.append(validate_platform_dry_run_payload_policy_matrix(policy_matrix))
    for report in alignment_reports:
        if "registry_only_platform_ids" in report:
            results.append(validate_platform_registry_compiler_alignment_report(report))
        elif "forbidden_now_flags_confirmed_false" in report:
            results.append(validate_platform_publish_readiness_alignment_report(report))
        elif "platform_response_logging_future_only" in report:
            results.append(validate_platform_redacted_audit_alignment_report(report))
        else:
            results.append({"validation_state": UNKNOWN, "reasons": ["unknown_alignment_report_type"]})
    states = [result["validation_state"] for result in results]
    reasons = []
    for result in results:
        if result["validation_state"] != PASS:
            reasons.extend(result["reasons"])
    return {
        "validation_state": _rollup(states),
        "platform_count": len(profiles),
        "profile_platform_ids": sorted(_value(profile, "platform_id") for profile in profiles),
        "component_states": states,
        "reasons": sorted(set(reasons)) or ["ok"],
    }


PLATFORM_CAPABILITY_REGISTRY_V2_VALIDATORS = {
    "platform_official_doc_source": validate_platform_official_doc_source,
    "platform_official_docs_verification_pack": validate_platform_official_docs_verification_pack,
    "platform_capability_profile_v2": validate_platform_capability_profile_v2,
    "platform_credential_slot_policy": validate_platform_credential_slot_policy,
    "platform_live_gate_checklist": validate_platform_live_gate_checklist,
    "platform_dry_run_payload_policy_matrix": validate_platform_dry_run_payload_policy_matrix,
    "platform_registry_compiler_alignment_report": validate_platform_registry_compiler_alignment_report,
    "platform_publish_readiness_alignment_report": validate_platform_publish_readiness_alignment_report,
    "platform_redacted_audit_alignment_report": validate_platform_redacted_audit_alignment_report,
}
