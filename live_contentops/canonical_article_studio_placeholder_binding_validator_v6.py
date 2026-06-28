"""V6 Canonical Article Studio Placeholder Binding Validator.

Ensures empty placeholder binding states are secure, redacted, and unapproved.
"""
from __future__ import annotations

import re
from typing import Any

EMAIL_re = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_re = re.compile(r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
DISCORD_USER_ID_re = re.compile(r"\b\d{17,19}\b")
TELEGRAM_BOT_TOKEN_re = re.compile(r"\b\d{9,10}:[a-zA-Z0-9_-]{35}\b")
WEBHOOK_URL_re = re.compile(r"https://(discord\.com/api/webhooks/|hooks\.slack\.com/services/|api\.telegram\.org/bot)\S+")
ENV_FILE_re = re.compile(r"\.env(\.local|\.production|\.development)?\b")
LOCAL_PATH_re = re.compile(r"\b([a-zA-Z]:\\[Uu]sers\\[a-zA-Z0-9_-]+|/home/[a-zA-Z0-9_-]+|/Users/[a-zA-Z0-9_-]+)\b")
HASH_re = re.compile(r"\b[a-fA-F0-9]{64}\b")
HASH_SHA256_re = re.compile(r"\bsha256[:_][a-fA-F0-9]+\b", re.IGNORECASE)
URL_re = re.compile(r"https?://\S+")
DATE_re = re.compile(r"\b\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?\b")

SECRET_KEYWORDS = ["cookie", "sessionid", "session_id", "localstorage", "sessionstorage", "document.cookie", "jwt", "access_token"]
DM_KEYWORDS = ["dm", "direct message", "private message", "private chat"]
FINANCIAL_ADVICE_KEYWORDS = ["buy", "sell", "hold", "target price", "stop loss", "position size", "trade setup", "alpha call", "guaranteed return"]
METRICS = ["impressions", "clicks", "views", "ctr", "engagement", "followers"]

CITATION_MARKERS = [
    re.compile(r"\[\d+\]"),
    re.compile(r"\bSource:\s*\S+"),
    re.compile(r"\bcitation:\s*\S+"),
    re.compile(r"\breference_url:\s*\S+"),
    re.compile(r"\bsource_url:\s*\S+"),
    re.compile(r"\(Source:\s*\S+\)")
]


def is_placeholder(val: Any) -> bool:
    if val is None or val is False or val == "":
        return True
    if isinstance(val, bool):
        return True
    if isinstance(val, str):
        val_lower = val.lower()
        if "redacted" in val_lower or "placeholder" in val_lower or "unverified" in val_lower or "missing" in val_lower:
            return True
        placeholders = [
            "none: verification pending",
            "manual_ingestion_pending",
            "manual_operator_research_pending", "null",
            "placeholder_bound_review_only",
            "placeholder_only_not_content",
            "empty_draft_shell_blocked",
            "placeholder_bound_empty_draft_shell_blocked"
        ]
        if any(p in val_lower for p in placeholders):
            return True
    return False


def has_actual_citation(text: str) -> bool:
    for pattern in CITATION_MARKERS:
        for match in pattern.finditer(text):
            matched_str = match.group(0).lower()
            if any(p in matched_str for p in ["redacted", "required", "missing", "unverified", "pending", "placeholder", "null"]):
                continue
            return True
    return False


def validate_canonical_article_studio_placeholder_binding(
    binding_packet: dict[str, Any],
    slot_binding_map: list[dict[str, Any]],
    binding_review: dict[str, Any],
    placeholder_bound_shell_instance: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Validates unapproved placeholder binding state and reports blockers."""
    blockers = []
    failed = False

    # 1. Default required blockers when unapproved
    blockers.extend([
        "real_source_pack_not_approved",
        "runtime_operator_approval_missing",
        "placeholder_values_not_materialized",
        "article_copy_generation_blocked",
        "editor_review_required",
        "jim_review_required",
        "publication_blocked",
        "dispatch_blocked",
        "human_review_required"
    ])

    # 2. Block active copy or draft creation claims
    copy_keys = [
        "article_copy_generated", "title_generated", "dek_generated",
        "body_generated", "citations_generated", "seo_metadata_generated",
        "slot_values_materialized"
    ]
    for key in copy_keys:
        if binding_packet.get(key) is True or placeholder_bound_shell_instance.get(key) is True:
            blockers.append("article_copy_generation_blocked")
            failed = True

    # 3. Fail if approved_placeholder_binding_for_runtime=True
    if binding_packet.get("approved_placeholder_binding_for_runtime") is True:
        blockers.append("placeholder_binding_approved_for_runtime")
        failed = True

    # 4. Fail if any placeholder value or slot value is non-null
    for binding in slot_binding_map:
        if binding.get("placeholder_value") is not None:
            blockers.append("non_null_placeholder_value_detected")
            failed = True
        if binding.get("generated") is True or binding.get("materialized") is True:
            blockers.append("non_null_placeholder_value_detected")
            failed = True
        if binding.get("valid_for_runtime_draft") is True or binding.get("valid_for_publication") is True:
            blockers.append("non_null_placeholder_value_detected")
            failed = True

    if "slots" in placeholder_bound_shell_instance:
        for slot in placeholder_bound_shell_instance["slots"]:
            if slot.get("current_value") is not None:
                blockers.append("non_empty_slot_value_detected")
                failed = True
            if slot.get("generated") is True:
                blockers.append("non_empty_slot_value_detected")
                failed = True

    # 5. Fail if word counts or citation/excerpt counts are non-zero
    count_keys = ["body_word_count", "source_citation_count", "evidence_excerpt_count"]
    for key in count_keys:
        if placeholder_bound_shell_instance.get(key, 0) > 0:
            blockers.append("non_zero_word_or_citation_count_detected")
            failed = True

    # 6. Block active review flags in review
    if binding_review.get("runtime_generation_allowed") is True:
        blockers.append("article_copy_generation_blocked")
        failed = True
    if binding_review.get("publication_allowed") is True:
        blockers.append("publication_blocked")
        failed = True
    if binding_review.get("dispatch_allowed") is True:
        blockers.append("dispatch_blocked")
        failed = True

    # 7. Block dispatch / publication flags
    forbidden_flags = [
        "canonical_draft_generation_allowed",
        "allowed_for_publication",
        "public_postable",
        "dispatch_allowed_now",
        "live_write_allowed_now",
        "outbox_entry_created"
    ]
    for flag in forbidden_flags:
        if binding_packet.get(flag) is True or placeholder_bound_shell_instance.get(flag) is True:
            blockers.append("forbidden_active_dispatch_flags")
            failed = True

    # 8. Check real browser/provider behavior claims
    behavior_flags = [
        "provider_call_performed",
        "browser_session_started",
        "env_read_performed",
        "credentials_hydrated"
    ]
    for flag in behavior_flags:
        if binding_packet.get(flag) is True:
            blockers.append("forbidden_behavior_claims")
            failed = True

    # 9. Check approval claims
    if binding_packet.get("source_pack_approved") is True or binding_packet.get("jim_review_completed") is True:
        blockers.append("real_source_pack_approved_claimed")
        failed = True

    # 10. Scan text fields recursively for leaks
    texts_to_scan: list[str] = []

    def check_value(val: Any, key_name: str = ""):
        nonlocal failed
        if isinstance(val, str):
            texts_to_scan.append(val)
            check_text(val, key_name)
        elif isinstance(val, dict):
            for k, v in val.items():
                check_value(v, k)
        elif isinstance(val, list):
            for item in val:
                check_value(item, key_name)

    def check_text(t: str, key_name: str = ""):
        nonlocal failed
        t_lower = t.lower()

        # A. URL check
        if URL_re.search(t):
            blockers.append("url_leak_in_runtime_artifact")
            failed = True

        # B. Hash check
        if HASH_re.search(t) or HASH_SHA256_re.search(t):
            blockers.append("hash_leak_in_runtime_artifact")
            failed = True

        # C. Excerpt check
        is_excerpt_key = "excerpt" in key_name.lower() and not key_name.lower().endswith("_redacted")
        if is_excerpt_key and not is_placeholder(t):
            blockers.append("source_excerpt_leak_in_runtime_artifact")
            failed = True
        if "excerpt:" in t_lower:
            parts = t_lower.split("excerpt:")
            if len(parts) > 1 and not is_placeholder(parts[1].strip()):
                blockers.append("source_excerpt_leak_in_runtime_artifact")
                failed = True

        # D. Citation check
        is_citation_key = key_name.lower() in ["source_url", "reference_url", "citation"]
        if is_citation_key and not is_placeholder(t):
            blockers.append("citation_or_source_reference_leak_detected")
            failed = True
        if has_actual_citation(t):
            blockers.append("citation_or_source_reference_leak_detected")
            failed = True

        # E. Operator signature / Approval ID / Approval Hash checks
        is_op_key = key_name.lower() in [
            "operator_id", "operator_verified_by", "operator_signature",
            "approved_by", "operator", "approval_id", "approval_hash"
        ] or (key_name.lower().startswith("operator_id") and not key_name.lower().endswith("_redacted"))
        if is_op_key and not is_placeholder(t):
            blockers.append("operator_signature_leaked")
            failed = True
        if "operator_jim_sig" in t_lower or "operator_test_sig" in t_lower or "test_only_operator_not_real_verification" in t_lower:
            blockers.append("operator_signature_leaked")
            failed = True
        if "approval_123" in t_lower or "approval_id" in t_lower and not is_placeholder(t):
            blockers.append("approval_id_present")
            failed = True

        # F. Timestamp check
        is_date_key = key_name.lower() in ["approved_at", "retrieved_at", "created_at"] or (key_name.lower().endswith("_at") and not key_name.lower().endswith("_redacted"))
        if is_date_key and not is_placeholder(t):
            blockers.append("fake_approval_timestamp_detected")
            failed = True
        if DATE_re.search(t):
            blockers.append("fake_approval_timestamp_detected")
            failed = True

        # G. Public ready checks
        if re.search(r"\b(public_ready|publication_ready|ready_to_publish)\b", t_lower):
            blockers.append("public_ready_claim_detected")
            failed = True

        # H. Metric checks
        if any(m in t_lower for m in METRICS):
            blockers.append("metric_leak_detected")
            failed = True

        # I. Private details check
        if EMAIL_re.search(t) or PHONE_re.search(t) or DISCORD_USER_ID_re.search(t):
            blockers.append("private_or_secret_material_detected")
            failed = True
        if TELEGRAM_BOT_TOKEN_re.search(t) or WEBHOOK_URL_re.search(t) or ENV_FILE_re.search(t) or LOCAL_PATH_re.search(t):
            blockers.append("private_or_secret_material_detected")
            failed = True
        if any(k in t_lower for k in SECRET_KEYWORDS):
            blockers.append("private_or_secret_material_detected")
            failed = True
        if any(k in t_lower for k in DM_KEYWORDS):
            blockers.append("dm_or_private_message_detected")
            failed = True
        for k in FINANCIAL_ADVICE_KEYWORDS:
            if re.search(rf"\b{re.escape(k)}\b", t_lower):
                blockers.append("financial_advice_or_signal_language_detected")
                failed = True
                break

        # J. Source Name / Publisher check
        raw_source_names = [
            "Federal Reserve", "US Treasury", "Treasury", "Bloomberg",
            "Reuters", "FRED", "BLS", "BEA", "Census", "EIA"
        ]

        is_source_identity_key = key_name.lower() in [
            "source_name", "source_publisher", "publisher",
            "source_title", "source_label", "source_display_name"
        ]
        if is_source_identity_key and not is_placeholder(t):
            blockers.append("source_name_leak_detected")
            failed = True

        for name in raw_source_names:
            pattern = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
            if pattern.search(t):
                # Safe context check
                if key_name.lower() in ["source_requirement_refs", "evidence_ref"]:
                    continue
                blockers.append("source_name_leak_detected")
                failed = True

        # Check explicit text patterns
        patterns = [
            re.compile(r"\bsource\s+name\s*:\s*(?!\b(?:redacted|placeholder|null|missing|pending)\b)(\S+)", re.IGNORECASE),
            re.compile(r"\bsource\s+publisher\s*:\s*(?!\b(?:redacted|placeholder|null|missing|pending)\b)(\S+)", re.IGNORECASE),
            re.compile(r"\bpublisher\s*:\s*(?!\b(?:redacted|placeholder|null|missing|pending)\b)(\S+)", re.IGNORECASE)
        ]
        for pat in patterns:
            if pat.search(t):
                blockers.append("source_name_leak_detected")
                failed = True

    check_value(binding_packet)
    check_value(slot_binding_map)
    check_value(binding_review)
    check_value(placeholder_bound_shell_instance)
    for text in texts_to_scan:
        check_text(text)

    blockers = sorted(list(set(blockers)))
    status = "FAILED_WITH_BLOCKERS" if failed else "PASSED_WITH_REVIEW_ONLY_BLOCKERS"

    report = {
        "schema_version": "6.0.0",
        "validation_status": status,
        "runtime_truth": False,
        "placeholder_binding_validated": True,
        "blockers": blockers,
        "blocker_count": len(blockers)
    }

    return report, blockers
