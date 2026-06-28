"""V6 Real Source Pack Manual Import Validator.

Checks blank and future operator-filled import structures offline for compliance.
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

SECRET_KEYWORDS = ["cookie", "sessionid", "session_id", "localstorage", "sessionstorage", "document.cookie", "jwt", "access_token"]
DM_KEYWORDS = ["dm", "direct message", "private message", "private chat"]
FINANCIAL_ADVICE_KEYWORDS = ["buy", "sell", "hold", "target price", "stop loss", "position size", "trade setup", "alpha call", "guaranteed return"]


def is_placeholder(val: Any) -> bool:
    if val is None or val is False or val == "":
        return True
    if isinstance(val, bool):
        return True
    if isinstance(val, str):
        val_lower = val.lower()
        placeholders = [
            "missing", "unverified", "none: verification pending",
            "placeholder:", "manual_ingestion_pending",
            "manual_operator_research_pending", "null"
        ]
        if any(p in val_lower for p in placeholders):
            return True
    return False


def validate_real_source_pack_manual_import(
    import_fixture: dict[str, Any],
    hash_review: dict[str, Any],
    policy: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Runs offline compliance audits over manual import fixtures."""
    blockers = []
    failed = False

    # 1. Default required blockers
    blockers.extend([
        "operator_source_pack_missing",
        "source_verification_required",
        "redacted_source_pack_required",
        "evidence_hash_presence_missing",
        "source_requirement_coverage_missing",
        "claim_binding_missing",
        "operator_signature_missing",
        "real_draft_generation_blocked",
        "publication_blocked_until_real_source_verification",
        "dispatch_blocked",
        "human_review_required"
    ])

    # 2. Block if runtime_truth is True
    if import_fixture.get("runtime_truth") is True or hash_review.get("runtime_truth") is True:
        blockers.append("runtime_truth_claimed")
        failed = True

    # 3. Block active publish/dispatch flags
    forbidden_flags = [
        "allowed_for_publication",
        "public_postable",
        "dispatch_allowed_now",
        "live_write_allowed_now",
        "canonical_draft_generation_allowed",
        "allowed_for_article_use"
    ]
    for flag in forbidden_flags:
        if import_fixture.get(flag) is True or hash_review.get(flag) is True:
            blockers.append("forbidden_active_dispatch_flags")
            failed = True

    # 4. Check if raw hash/URL/excerpts are persisted flags are True
    raw_persist_flags = [
        "raw_values_persisted",
        "raw_hash_values_persisted",
        "raw_source_urls_persisted",
        "raw_source_excerpts_persisted"
    ]
    for flag in raw_persist_flags:
        if import_fixture.get(flag) is True or hash_review.get(flag) is True:
            blockers.append("raw_source_data_persisted")
            failed = True

    # 5. Scan all strings in nested dict structures
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
        is_excerpt_key = any(x in key_name.lower() for x in ["excerpt", "excerpt_content"])
        if is_excerpt_key and not is_placeholder(t):
            blockers.append("source_excerpt_leak_in_runtime_artifact")
            failed = True

        # D. Operator signature check
        is_op_key = key_name.lower() in ["operator_id", "operator_verified_by", "approved_by", "operator_signature", "operator"]
        if is_op_key and not is_placeholder(t):
            blockers.append("operator_signature_leaked")
            failed = True
        if "operator_jim_sig" in t_lower or "operator_test_sig" in t_lower or "test_only_operator_not_real_verification" in t_lower:
            blockers.append("operator_signature_leaked")
            failed = True

        # E. Metric checks
        if any(m in t_lower for m in ["impressions", "clicks", "views", "ctr", "engagement", "followers"]):
            blockers.append("metric_leak_detected")
            failed = True

        # F. Private details check
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
        if any(k in t_lower for k in FINANCIAL_ADVICE_KEYWORDS):
            blockers.append("financial_advice_or_signal_language_detected")
            failed = True

    check_value(import_fixture)
    check_value(hash_review)
    check_value(policy)

    # Sort and deduplicate
    blockers = sorted(list(set(blockers)))

    validation_status = "FAILED_WITH_BLOCKERS" if failed else "PASSED_WITH_REVIEW_ONLY_BLOCKERS"

    report = {
        "schema_version": "6.0.0",
        "validation_status": validation_status,
        "runtime_truth": False,
        "real_source_pack_manual_import_validated": True,
        "blockers": blockers,
        "blocker_count": len(blockers)
    }

    return report, blockers
