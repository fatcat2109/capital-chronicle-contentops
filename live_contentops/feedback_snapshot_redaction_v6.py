"""V6 Feedback Snapshot Redaction.

Provides rules and functions to redact sensitive/personal data and detect blockers.
"""
from __future__ import annotations

import re
from typing import Any

# Regex patterns for redaction and detection
EMAIL_re = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
# Phone regex: restrict to standard phone lengths to avoid greedy matching of long IDs
PHONE_re = re.compile(r"\+?\b\d{1,4}[-.\s]??\(?\d{1,3}\)?[-.\s]??\d{1,4}[-.\s]??\d{1,4}[-.\s]??\d{1,5}\b")
DISCORD_USER_ID_re = re.compile(r"<@!?\d{17,20}>|\b\d{17,20}\b")
TELEGRAM_BOT_TOKEN_re = re.compile(r"\b\d{8,11}:[a-zA-Z0-9_-]{35,45}\b")
WEBHOOK_URL_re = re.compile(r"https://(discord\.com/api/webhooks/|api\.telegram\.org/bot)\S+")
ENV_FILE_re = re.compile(r"\.env(\.local|\.production|\.development)?\b")
LOCAL_PATH_re = re.compile(r"\b([a-zA-Z]:\\[Uu]sers\\[a-zA-Z0-9_-]+|/home/[a-zA-Z0-9_-]+|/Users/[a-zA-Z0-9_-]+)\b")
API_KEY_re = re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|sk-proj-[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9._-]+)\b", re.IGNORECASE)

# Keywords to trigger specific blockers
SECRET_KEYWORDS = [
    "cookie", "sessionid", "session_id", "localstorage", "sessionstorage", 
    "document.cookie", "jwt", "access_token", "secret_key", "webhook", 
    "bot_token", "account selector"
]
DM_KEYWORDS = [
    "dm", "direct message", "private message", "inbox", "pm", "private chat", "dms"
]
ADDRESS_KEYWORDS = [
    "street", "st.", "avenue", "ave.", "road", "rd.", "drive", "dr.", 
    "boulevard", "blvd.", "zip code", "zipcode", "postal code"
]


def redact_text(text: str) -> tuple[str, list[str]]:
    """Scans and redacts a string of text, returning the redacted version and blockers found."""
    if not text:
        return "", []

    blockers = []
    redacted = text

    # Redact Webhook URLs (run first)
    if WEBHOOK_URL_re.search(redacted):
        redacted = WEBHOOK_URL_re.sub("[WEBHOOK_REDACTED]", redacted)
        blockers.append("secret_or_destination_material_detected")

    # Redact Bot Tokens (run first)
    if TELEGRAM_BOT_TOKEN_re.search(redacted):
        redacted = TELEGRAM_BOT_TOKEN_re.sub("[BOT_TOKEN_REDACTED]", redacted)
        blockers.append("secret_or_destination_material_detected")

    # Redact Discord User IDs (run before phone/email)
    if DISCORD_USER_ID_re.search(redacted):
        redacted = DISCORD_USER_ID_re.sub("[DISCORD_ID_REDACTED]", redacted)
        blockers.append("private_identifier_detected")
        blockers.append("secret_or_destination_material_detected")

    # Redact Emails
    if EMAIL_re.search(redacted):
        redacted = EMAIL_re.sub("[EMAIL_REDACTED]", redacted)
        blockers.append("private_identifier_detected")
        blockers.append("unredacted_personal_data_detected")

    # Redact Phone Numbers
    if PHONE_re.search(redacted):
        redacted = PHONE_re.sub("[PHONE_REDACTED]", redacted)
        blockers.append("private_identifier_detected")
        blockers.append("unredacted_personal_data_detected")

    # Redact Env Files
    if ENV_FILE_re.search(redacted):
        redacted = ENV_FILE_re.sub("[ENV_REDACTED]", redacted)
        blockers.append("secret_or_destination_material_detected")

    # Redact Local Paths
    if LOCAL_PATH_re.search(redacted):
        redacted = LOCAL_PATH_re.sub("[LOCAL_PATH_REDACTED]", redacted)
        blockers.append("secret_or_destination_material_detected")

    # Redact API Keys
    if API_KEY_re.search(redacted):
        redacted = API_KEY_re.sub("[API_KEY_REDACTED]", redacted)
        blockers.append("secret_or_destination_material_detected")

    # Lowercase text for keyword checks
    lower_text = text.lower()

    # Address keywords
    if any(k in lower_text for k in ADDRESS_KEYWORDS):
        blockers.append("private_identifier_detected")
        blockers.append("unredacted_personal_data_detected")

    # Secret/cookie/token keywords
    if any(k in lower_text for k in SECRET_KEYWORDS):
        blockers.append("secret_or_destination_material_detected")

    # DM keywords
    if any(k in lower_text for k in DM_KEYWORDS):
        blockers.append("dm_or_private_message_detected")

    return redacted, sorted(list(set(blockers)))


def redact_snapshot(snapshot: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Redacts private info from a feedback snapshot dict, returns the redacted dict and all blockers."""
    # Work on a copy of the snapshot
    redacted_snap = dict(snapshot)

    blockers = list(redacted_snap.get("blocked_reasons", []))

    # Redact raw feedback text
    raw_text = redacted_snap.get("raw_feedback_text_redacted", "")
    redacted_text, text_blockers = redact_text(raw_text)
    redacted_snap["raw_feedback_text_redacted"] = redacted_text
    blockers.extend(text_blockers)

    # Redact author handle
    author_handle = redacted_snap.get("author_handle_redacted", "")
    redacted_handle, handle_blockers = redact_text(author_handle)
    redacted_snap["author_handle_redacted"] = redacted_handle
    blockers.extend(handle_blockers)

    # If snapshot flags personal data but redaction was not marked as performed or contains unredacted flags
    if redacted_snap.get("contains_personal_data") is True:
        if redacted_snap.get("redaction_required") is True:
            # Check if any blockers got added, if not, verify we still trigger safety checks
            if not text_blockers and not handle_blockers:
                blockers.append("unredacted_personal_data_detected")

    # Safety bounds checks on the fields
    if redacted_snap.get("allowed_for_publication") is True:
        blockers.append("publication_blocked_until_source_verification")
        redacted_snap["allowed_for_publication"] = False

    # Force review status
    redacted_snap["human_review_required"] = True

    # Check for fake metrics or urls
    metrics = redacted_snap.get("metrics_optional")
    if metrics:
        # Check if the metrics contain fake-looking values or claim verification without evidence
        if redacted_snap.get("metrics_verified") is True:
            blockers.append("claims_metrics_verified_without_evidence")
            redacted_snap["metrics_verified"] = False

    if redacted_snap.get("public_url_verified") is True:
        blockers.append("creates_fake_public_url")
        redacted_snap["public_url_verified"] = False

    # Deduplicate and sort blockers
    blockers = sorted(list(set(blockers)))
    redacted_snap["blocked_reasons"] = blockers

    # Update allowed for summary state based on blockers
    if any(b in blockers for b in ["secret_or_destination_material_detected", "dm_or_private_message_detected"]):
        redacted_snap["allowed_for_llm_summary"] = False

    return redacted_snap, blockers
