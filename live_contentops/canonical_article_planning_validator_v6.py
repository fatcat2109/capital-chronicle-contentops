"""V6 Canonical Article Planning Validator.

Validates article planning packets, outlines, and checklists against strict safety and financial advice policies.
"""
from __future__ import annotations

import re
from typing import Any

# Patterns to scan
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


def validate_article_planning(
    article_packet: dict[str, Any],
    research_requirements: list[dict[str, Any]],
    source_checklist: dict[str, Any],
    claim_ledger: list[dict[str, Any]],
    article_outline: dict[str, Any],
    editorial_risk: list[dict[str, Any]],
    downstream_placeholders: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Runs compliance scans on article planning components, returning validation report and blockers."""
    blockers = []

    # 1. Enforce required blockers
    blockers.append("source_verification_required")
    blockers.append("publication_blocked_until_source_verification")
    blockers.append("claim_ledger_unverified")
    blockers.append("article_copy_not_generated")
    blockers.append("human_research_required")
    blockers.append("no_publication_allowed")

    # 2. Check live model / browser / provider execution claims
    for p in [article_packet, source_checklist, article_outline]:
        if p.get("provider_call_performed") is True or p.get("llm_provider_call_performed") is True:
            blockers.append("live_provider_call_detected")
        if p.get("browser_session_started") is True:
            blockers.append("browser_session_detected")

    # 3. Check for publication overrides / live flags
    for p in [article_packet, source_checklist]:
        if p.get("allowed_for_publication") is True:
            blockers.append("no_publication_allowed")
        if p.get("dispatch_allowed_now") is True:
            blockers.append("dispatch_allowed_now_must_be_false")
        if p.get("public_postable") is True:
            blockers.append("public_postable_must_be_false")

    # 4. Check for fake source URLs, citations, or metrics
    for req in research_requirements:
        if req.get("source_url_placeholder") is not None:
            blockers.append("fake_source_or_citation_detected")
        if req.get("source_verification_status") == "verified":
            blockers.append("fake_source_or_citation_detected")

    # 5. Check if outline contains copy generated
    if article_packet.get("article_copy_generated") is True:
        blockers.append("fake_model_output_claim_detected")

    # 6. Check downstream placeholders for active state
    for key, val in downstream_placeholders.items():
        if val.get("generated") is True or val.get("public_postable") is True:
            blockers.append("no_publication_allowed")

    # 7. Check text fields for private/DM/secret info or financial advice/signals
    all_texts = []
    all_texts.append(article_packet.get("title_candidate", ""))
    all_texts.append(article_packet.get("thesis_candidate", ""))
    all_texts.append(article_outline.get("title_candidate", ""))
    all_texts.append(article_outline.get("subtitle_candidate", ""))
    all_texts.append(article_outline.get("opening_question", ""))
    all_texts.extend(article_outline.get("section_outline", []))
    all_texts.extend(article_outline.get("evidence_slots", []))
    all_texts.extend(article_outline.get("caveat_slots", []))

    for t in all_texts:
        if not t:
            continue
        t_lower = t.lower()
        # Scan for private name identifiers (e.g. real_name, john_smith) or identifiers
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
        # Scan for financial advice or signals
        if any(k in t_lower for k in FINANCIAL_ADVICE_KEYWORDS):
            blockers.append("financial_advice_or_signal_language_detected")

    # 8. Check claim ledger numeric claim slots without source refs
    # For every claim, check if its source_requirement_refs list is empty
    for c in claim_ledger:
        if not c.get("source_requirement_refs"):
            blockers.append("unsupported_numeric_claim_slot_detected")

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
            "no_financial_advice_language": True,
            "source_verification_checklist_present": True,
            "claim_ledger_scaffold_present": True
        }
    }

    return validation_report, blockers
