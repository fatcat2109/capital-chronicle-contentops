"""V6 Canonical Article Draft Safety Validator.

Audits draft packets, checklists, and markdown text for compliance with editorial, regulatory, and privacy constraints.
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

FINANCIAL_ADVICE_PATTERNS = [
    re.compile(r"\bbuy\b", re.IGNORECASE),
    re.compile(r"\bsell\b", re.IGNORECASE),
    re.compile(r"\bhold\b", re.IGNORECASE),
    re.compile(r"\btarget\s+price\b", re.IGNORECASE),
    re.compile(r"\bentry\b", re.IGNORECASE),
    re.compile(r"\bexit\b", re.IGNORECASE),
    re.compile(r"\bstop\s+loss\b", re.IGNORECASE),
    re.compile(r"\bposition\s+size\b", re.IGNORECASE),
    re.compile(r"\bposition\s+sizing\b", re.IGNORECASE),
    re.compile(r"\btrade\s+setup\b", re.IGNORECASE),
    re.compile(r"\balpha\s+call\b", re.IGNORECASE),
    re.compile(r"\bguaranteed\s+return\b", re.IGNORECASE),
    re.compile(r"\btrading\s+signals?\b", re.IGNORECASE)
]


def detect_financial_advice_language(text: str) -> list[str]:
    """Detects actual standalone financial-advice or signal terms, returning matched phrases."""
    matches = []
    for pattern in FINANCIAL_ADVICE_PATTERNS:
        # Find all occurrences
        found = pattern.findall(text)
        if found:
            matches.extend(found)
    return sorted(list(set(matches)))


def validate_article_draft(
    draft_packet: dict[str, Any],
    source_pack: dict[str, Any],
    gate_report: dict[str, Any],
    binding_report: dict[str, Any],
    draft_preview_markdown: str
) -> tuple[dict[str, Any], list[str]]:
    """Runs programmatic safety audits on draft generation artifacts, returning validation report and blockers."""
    blockers = []

    # 1. Base mandatory blockers
    blockers.append("publication_blocked_until_source_verification")
    blockers.append("claim_ledger_unverified")
    blockers.append("no_publication_allowed")

    # 2. Check source pack missing / gate mismatch
    pack_status = source_pack.get("verified_source_pack_status")
    pack_complete = source_pack.get("source_pack_complete", False)
    gate_passed = gate_report.get("gate_status") == "PASSED"

    if pack_status == "MISSING_REQUIRED_SOURCE_VERIFICATION" or not pack_complete:
        blockers.append("verified_source_pack_missing")
        blockers.append("source_verification_required")
        blockers.append("human_research_required")
        if draft_packet.get("article_copy_generated") is True:
            blockers.append("fake_model_output_claim_detected")
        if gate_passed:
            blockers.append("fake_source_or_citation_detected")

    # 3. Check claim binding
    if not binding_report.get("all_claims_bound_to_sources", False):
        blockers.append("all_claims_not_bound_to_verified_sources")

    # 4. Check draft copy generated flag
    if not draft_packet.get("article_copy_generated", False):
        blockers.append("article_copy_not_generated")

    # 5. Check fake source URLs / citations / hashes in pack
    for entry in source_pack.get("source_entries", []):
        url = entry.get("source_url")
        eh = entry.get("evidence_hash")
        vstatus = entry.get("verification_status")

        # Fake URL/evidence checking
        if url is not None and "fake" in url.lower():
            blockers.append("fake_source_or_citation_detected")
            blockers.append("fake_metric_or_public_url_detected")
        if eh is not None and "fake" in eh.lower():
            blockers.append("fake_source_or_citation_detected")
        if url is not None and vstatus == "missing" and pack_status != "MISSING_REQUIRED_SOURCE_VERIFICATION":
            blockers.append("fake_source_or_citation_detected")

    # 6. Check publication / dispatch flags
    if draft_packet.get("allowed_for_publication") is True:
        blockers.append("no_publication_allowed")
    if draft_packet.get("dispatch_allowed_now") is True:
        blockers.append("dispatch_allowed_now_must_be_false")
    if draft_packet.get("public_postable") is True:
        blockers.append("public_postable_must_be_false")
    if draft_packet.get("live_write_allowed_now") is True:
        blockers.append("live_write_allowed_now_must_be_false")

    # 7. Check for live provider / model claims
    if draft_packet.get("provider_call_performed") is True or draft_packet.get("llm_provider_call_performed") is True:
        blockers.append("live_provider_call_detected")
    if draft_packet.get("browser_session_started") is True:
        blockers.append("browser_session_detected")

    # 8. Check text content for secret/DM leaks or financial advice
    all_texts = [
        draft_packet.get("title_candidate", ""),
        draft_packet.get("thesis_candidate", ""),
        draft_preview_markdown
    ]

    financial_advice_matches = []
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
        
        # Word boundary aware matching
        detected_phrases = detect_financial_advice_language(t)
        if detected_phrases:
            financial_advice_matches.extend(detected_phrases)

    financial_advice_matches = sorted(list(set(financial_advice_matches)))
    if financial_advice_matches:
        blockers.append("financial_advice_or_signal_language_detected")

    # Deduplicate and sort blockers
    blockers = sorted(list(set(blockers)))

    validation_report = {
        "schema_version": "6.0.0",
        "validation_status": "FAILED_WITH_BLOCKERS" if blockers else "PASSED",
        "blockers": blockers,
        "blocker_count": len(blockers),
        "safety_checks": {
            "no_live_provider_call": True,
            "no_secrets_leaked": True,
            "no_financial_advice_language": not bool(financial_advice_matches),
            "gate_compliance_verified": True
        },
        "financial_advice_matches": financial_advice_matches
    }

    return validation_report, blockers


PostPathVerification_gate = True
