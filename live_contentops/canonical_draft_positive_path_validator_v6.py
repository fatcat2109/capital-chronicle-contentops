"""V6 Canonical Draft Positive-Path Validator.

Performs safety compliance scans to verify test-only isolation and block runtime deployment.
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
URL_re = re.compile(r"https?://\S+")

SECRET_KEYWORDS = ["cookie", "sessionid", "session_id", "localstorage", "sessionstorage", "document.cookie", "jwt", "access_token"]
DM_KEYWORDS = ["dm", "direct message", "private message", "private chat"]
FINANCIAL_ADVICE_KEYWORDS = ["buy", "sell", "hold", "target price", "stop loss", "position size", "trade setup", "alpha call", "guaranteed return"]


def validate_positive_path_draft_generation(
    positive_path_packet: dict[str, Any],
    fixture_summary: dict[str, Any],
    binding_proof: list[dict[str, Any]],
    draft_packet: dict[str, Any],
    draft_markdown: str
) -> tuple[dict[str, Any], list[str]]:
    """Runs compliance checks, appending default blockers."""
    blockers = []
    failed = False

    # 1. Enforce default publication blockers
    blockers.append("runtime_source_pack_not_verified")
    blockers.append("publication_blocked_until_real_source_verification")
    blockers.append("public_postable_blocked")
    blockers.append("dispatch_blocked")
    blockers.append("human_review_required")

    # 2. Block if runtime_truth is claimed or active
    if positive_path_packet.get("runtime_truth") is True:
        blockers.append("runtime_truth_claimed")
        failed = True

    if draft_packet.get("runtime_truth") is True:
        blockers.append("runtime_truth_claimed")
        failed = True

    # 3. Block if publication/dispatch flags are true
    forbidden_flags = ["allowed_for_publication", "public_postable", "dispatch_allowed_now", "live_write_allowed_now"]
    for flag in forbidden_flags:
        if positive_path_packet.get(flag) is True or draft_packet.get(flag) is True:
            blockers.append("forbidden_active_dispatch_flags")
            failed = True

    # 4. Check for presence of real operator signatures or source info
    # Scan all texts in the draft preview
    texts_to_scan = [draft_markdown]

    # Add fixture summary values
    for v in fixture_summary.values():
        if isinstance(v, str):
            texts_to_scan.append(v)
            
    # Add binding proof entries
    for b in binding_proof:
        for v in b.values():
            if isinstance(v, str):
                texts_to_scan.append(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        texts_to_scan.append(item)

    for t in texts_to_scan:
        t_lower = t.lower()
        if EMAIL_re.search(t) or PHONE_re.search(t) or DISCORD_USER_ID_re.search(t):
            blockers.append("private_or_secret_material_detected")
            failed = True
        if TELEGRAM_BOT_TOKEN_re.search(t) or WEBHOOK_URL_re.search(t) or ENV_FILE_re.search(t) or LOCAL_PATH_re.search(t):
            blockers.append("private_or_secret_material_detected")
            failed = True
        if "operator_jim_sig" in t_lower:
            blockers.append("real_operator_signature_leaked")
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
        # Check for URLs or hashes
        if URL_re.search(t):
            blockers.append("url_leak_in_runtime_artifact")
            failed = True
        if HASH_re.search(t):
            blockers.append("hash_leak_in_runtime_artifact")
            failed = True

    # Deduplicate and sort blockers
    blockers = sorted(list(set(blockers)))

    validation_status = "FAILED_WITH_BLOCKERS" if failed else "PASSED_WITH_REVIEW_ONLY_BLOCKERS"

    report = {
        "schema_version": "6.0.0",
        "validation_status": validation_status,
        "runtime_truth": False,
        "test_only_fixture_validated": True,
        "blockers": blockers,
        "blocker_count": len(blockers)
    }

    return report, blockers
