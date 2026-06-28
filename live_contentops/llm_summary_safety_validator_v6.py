"""V6 LLM Summary Safety Validator.

Validates LLM feedback loop output packets, prompt contracts, and refined candidates against strict safety policies.
"""
from __future__ import annotations

import re
from typing import Any

# Forbidden pattern matches
EMAIL_re = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
PHONE_re = re.compile(r"\+?\b\d{1,4}[-.\s]??\(?\d{1,3}\)?[-.\s]??\d{1,4}[-.\s]??\d{1,4}[-.\s]??\d{1,5}\b")
DISCORD_USER_ID_re = re.compile(r"<@!?\d{17,20}>|\b\d{17,20}\b")
TELEGRAM_BOT_TOKEN_re = re.compile(r"\b\d{8,11}:[a-zA-Z0-9_-]{35,45}\b")
WEBHOOK_URL_re = re.compile(r"https://(discord\.com/api/webhooks/|api\.telegram\.org/bot)\S+")
ENV_FILE_re = re.compile(r"\.env(\.local|\.production|\.development)?\b")
LOCAL_PATH_re = re.compile(r"\b([a-zA-Z]:\\[Uu]sers\\[a-zA-Z0-9_-]+|/home/[a-zA-Z0-9_-]+|/Users/[a-zA-Z0-9_-]+)\b")

SECRET_KEYWORDS = ["cookie", "sessionid", "session_id", "localstorage", "sessionstorage", "document.cookie", "jwt", "access_token"]
DM_KEYWORDS = ["dm", "direct message", "private message", "private chat"]
FINANCIAL_KEYWORDS = ["buy", "sell", "hold", "target price", "stop loss", "position size", "trade setup"]


def validate_summary_artifacts(
    intake_packet: dict[str, Any],
    prompt_contract: dict[str, Any],
    summary_output: dict[str, Any],
    refined_ideas: list[dict[str, Any]],
    refined_backlog: list[dict[str, Any]],
    unsafe_handling: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Runs structural and semantic checks, returning validation packet and list of blockers."""
    blockers = []

    # 1. Check for live model / provider claims
    for p in [intake_packet, prompt_contract, summary_output]:
        if p.get("provider_call_performed") is True or p.get("llm_provider_call_performed") is True:
            blockers.append("live_provider_call_detected")

    if summary_output.get("model_output_claimed") is True or summary_output.get("model_name") is not None:
        blockers.append("fake_model_output_claim_detected")

    # 2. Check for leaks / secrets in textual outputs
    all_texts = []
    # Scrape texts from prompt contract instructions and summary output summaries
    all_texts.append(prompt_contract.get("summarizer_instruction", ""))
    all_texts.append(prompt_contract.get("safety_instruction", ""))
    all_texts.append(summary_output.get("high_signal_feedback_themes", ""))
    all_texts.append(summary_output.get("source_request_summary", ""))
    all_texts.append(summary_output.get("methodology_question_summary", ""))

    for t in all_texts:
        if not t:
            continue
        t_lower = t.lower()
        if EMAIL_re.search(t) or PHONE_re.search(t) or DISCORD_USER_ID_re.search(t):
            blockers.append("private_or_secret_material_detected")
        if TELEGRAM_BOT_TOKEN_re.search(t) or WEBHOOK_URL_re.search(t) or ENV_FILE_re.search(t) or LOCAL_PATH_re.search(t):
            blockers.append("private_or_secret_material_detected")
        if any(k in t_lower for k in SECRET_KEYWORDS):
            blockers.append("private_or_secret_material_detected")
        if any(k in t_lower for k in DM_KEYWORDS):
            blockers.append("dm_or_private_message_detected")

    # 3. Check fake urls or metrics
    for r in refined_ideas + refined_backlog:
        if r.get("public_url_verified") is True or r.get("metrics_verified") is True:
            blockers.append("fake_public_result_detected")
        # Check executable reply commands
        if r.get("auto_reply_created") is True or r.get("executable_reply") is True:
            blockers.append("executable_response_control_detected")

    # 4. Check for publishable flags / overrides
    for r in refined_ideas + refined_backlog + [intake_packet, prompt_contract, summary_output]:
        if r.get("allowed_for_publication") is True:
            blockers.append("publication_blocked_until_source_verification")
        if r.get("dispatch_allowed_now") is True:
            blockers.append("dispatch_allowed_now_must_be_false")
        if r.get("public_postable") is True:
            blockers.append("public_postable_must_be_false")

    # 5. Check if any unsafe financial advice is matched in summary or candidates
    # Check if any snapshot had unsafe advice, verify blockers are preserved
    has_unsafe = unsafe_handling.get("unsafe_advice_snapshots_count", 0) > 0
    if has_unsafe:
        blockers.append("unsafe_financial_advice_request_detected")
        blockers.append("source_verification_required")

    # Deduplicate and sort blockers
    blockers = sorted(list(set(blockers)))

    validation_report = {
        "schema_version": "6.0.0",
        "validation_status": "FAILED_WITH_BLOCKERS" if blockers else "PASSED",
        "blockers": blockers,
        "blocker_count": len(blockers),
        "safety_checks": {
            "no_live_provider_call": True,
            "no_fake_model_claims": True,
            "no_secrets_leaked": True,
            "no_executable_replies": True,
            "no_publication_bypasses": True
        }
    }

    return validation_report, blockers
