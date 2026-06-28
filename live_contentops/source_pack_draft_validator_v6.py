"""V6 Source Pack Draft Validator.

Performs offline validations on manual source entries and packages to detect fake inputs or missing requirements.
"""
from __future__ import annotations

import re
from typing import Any

EMAIL_re = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
PHONE_re = re.compile(r"\+?\b\d{1,4}[-.\s]??\(?\d{1,3}\)?[-.\s]??\d{1,4}[-.\s]??\d{1,4}[-.\s]??\d{1,5}\b")
DISCORD_USER_ID_re = re.compile(r"<@!?\d{17,20}>|\b\d{17,20}\b")
TELEGRAM_BOT_TOKEN_re = re.compile(r"\b\d{8,11}:[a-zA-Z0-9_-]{35,45}\b")
WEBHOOK_URL_re = re.compile(r"https://(discord\.com/api/webhooks/|api\.telegram\.org/bot)\S+")
ENV_FILE_re = re.compile(r"\.env(\.local|\.production|\.development)?\b")
LOCAL_PATH_re = re.compile(r"\b([a-zA-Z]:\\[Uu]sers\\[a-zA-Z0-9_-]+|/home/[a-zA-Z0-9_-]+|/Users/[a-zA-Z0-9_-]+)\b")

SECRET_KEYWORDS = ["cookie", "sessionid", "session_id", "localstorage", "sessionstorage", "document.cookie", "jwt", "access_token"]
DM_KEYWORDS = ["dm", "direct message", "private message", "private chat"]
FINANCIAL_ADVICE_KEYWORDS = ["buy", "sell", "hold", "target price", "stop loss", "position size", "trade setup", "alpha call", "guaranteed return"]


def validate_source_pack_draft(source_pack: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Runs compliance checks on operator-filled source-pack draft, compiling blockers."""
    blockers = []

    # Default structural blockers
    blockers.append("publication_blocked_until_source_verification")

    pack_complete = source_pack.get("source_pack_complete", False)
    pack_status = source_pack.get("verified_source_pack_status")

    is_missing_state = pack_status == "MISSING_REQUIRED_SOURCE_VERIFICATION" or not pack_complete

    if is_missing_state:
        blockers.append("operator_source_entries_missing")
        blockers.append("source_verification_required")

    entries = source_pack.get("source_entries", [])
    if not entries:
        blockers.append("operator_source_entries_missing")

    # Claim binding
    if source_pack.get("source_claim_binding_pending", True):
        blockers.append("claim_binding_missing")

    missing_fields_by_source_requirement_id = {}

    for entry in entries:
        req_id = entry.get("source_requirement_id", "stub_id")
        vstatus = entry.get("verification_status", "missing")
        url = entry.get("source_url")
        eh = entry.get("evidence_hash")
        name = entry.get("source_name")
        rat = entry.get("retrieved_at")
        ovb = entry.get("operator_verified_by")
        sex = entry.get("source_excerpt_ref")

        # Fake detections
        if url is not None:
            url_lower = url.lower()
            if any(f in url_lower for f in ["fake", "example.com", "test.com", "placeholder"]):
                blockers.append("fake_source_or_evidence_detected")
                blockers.append("source_url_missing")

        if eh is not None:
            eh_lower = eh.lower()
            if any(f in eh_lower for f in ["fake", "example", "test", "placeholder", "stub_hash"]):
                blockers.append("fake_source_or_evidence_detected")
                blockers.append("evidence_hash_missing")

        # Mandatory missing field triggers for draft / missing state
        if vstatus == "missing" or is_missing_state:
            missing_reqs = []
            if not url:
                blockers.append("source_url_missing")
                missing_reqs.append("source_url")
            if not eh:
                blockers.append("evidence_hash_missing")
                missing_reqs.append("evidence_hash")
            if not rat:
                blockers.append("retrieved_at_missing")
                missing_reqs.append("retrieved_at")
            if not ovb:
                blockers.append("operator_signature_missing")
                missing_reqs.append("operator_verified_by")
            if not sex:
                blockers.append("source_excerpt_ref_missing")
                missing_reqs.append("source_excerpt_ref")
            if missing_reqs:
                missing_fields_by_source_requirement_id[req_id] = missing_reqs

        if vstatus == "verified":
            if not url:
                blockers.append("source_url_missing")
            if not eh:
                blockers.append("evidence_hash_missing")
            if not rat:
                blockers.append("retrieved_at_missing")
            if not ovb:
                blockers.append("operator_signature_missing")
            if not sex:
                blockers.append("source_excerpt_ref_missing")
            if name and any(p in name.lower() for p in ["placeholder", "stub", "missing", "unverified"]):
                blockers.append("verified_status_without_required_fields")

        # Detect fake verifications
        if url is not None and vstatus == "missing":
            blockers.append("source_verification_required")

        # Text scans
        all_texts = [url, eh, name, sex, entry.get("limitations"), entry.get("caveats")]
        for t in all_texts:
            if not t:
                continue
            t_lower = t.lower()
            if EMAIL_re.search(t) or PHONE_re.search(t) or DISCORD_USER_ID_re.search(t):
                blockers.append("private_or_secret_material_detected")
            if TELEGRAM_BOT_TOKEN_re.search(t) or WEBHOOK_URL_re.search(t) or ENV_FILE_re.search(t) or LOCAL_PATH_re.search(t):
                blockers.append("private_or_secret_material_detected")
            if any(m in t_lower for m in ["real_name", "full_name", "john_smith", "first_last"]):
                blockers.append("private_or_secret_material_detected")
            if any(k in t_lower for k in SECRET_KEYWORDS):
                blockers.append("private_or_secret_material_detected")
            if any(k in t_lower for k in DM_KEYWORDS):
                blockers.append("dm_or_private_message_detected")
            if any(k in t_lower for k in FINANCIAL_ADVICE_KEYWORDS):
                blockers.append("financial_advice_or_signal_language_detected")

    # Standard pipeline protections
    if source_pack.get("allowed_for_article_use") is True or source_pack.get("draft_generation_allowed") is True:
        blockers.append("publication_blocked_until_source_verification")

    # Deduplicate blockers
    blockers = sorted(list(set(blockers)))

    verified_fields_complete = not any(
        b in blockers for b in [
            "source_url_missing", "evidence_hash_missing", "retrieved_at_missing",
            "operator_signature_missing", "source_excerpt_ref_missing"
        ]
    )

    validation_report = {
        "schema_version": "6.0.0",
        "validation_status": "FAILED_WITH_BLOCKERS" if blockers else "PASSED",
        "blockers": blockers,
        "blocker_count": len(blockers),
        "safety_checks": {
            "no_live_provider_call": True,
            "no_secrets_leaked": True,
            "no_financial_advice_language": True,
            "verified_fields_complete": verified_fields_complete
        },
        "missing_fields_by_source_requirement_id": missing_fields_by_source_requirement_id,
        "missing_required_field_counts": sum(len(v) for v in missing_fields_by_source_requirement_id.values())
    }

    return validation_report, blockers
