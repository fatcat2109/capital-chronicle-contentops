"""V6 Real Source Pack Operator Approval Gate Validator.

Ensures offline operator approval controls are intact and clean.
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
        placeholders = [
            "missing", "unverified", "none: verification pending",
            "placeholder:", "manual_ingestion_pending",
            "manual_operator_research_pending", "null",
            "source_pack_draft_generation_review_only"
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


def validate_operator_approval_gate(
    gate_packet: dict[str, Any],
    template: dict[str, Any],
    matrix: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    """Validates the unapproved operator approval gate packets offline."""
    blockers = []
    failed = False

    # 1. Default checkers when unapproved
    blockers.extend([
        "operator_approval_missing",
        "approval_signature_missing",
        "source_pack_hash_approval_missing",
        "draft_generation_blocked",
        "publication_blocked_until_operator_approval",
        "dispatch_blocked",
        "human_review_required"
    ])

    # 2. Block if runtime_truth is True
    if gate_packet.get("runtime_truth") is True or template.get("runtime_truth") is True:
        blockers.append("runtime_truth_claimed")
        failed = True

    # 3. Block active approval / signature / hash creations
    if gate_packet.get("operator_approval_created") is True:
        blockers.append("operator_approval_creation_detected")
        failed = True
    if gate_packet.get("operator_signature_present") is True:
        blockers.append("operator_signature_leaked")
        failed = True
    if gate_packet.get("source_pack_hash_present") is True:
        blockers.append("hash_leak_in_runtime_artifact")
        failed = True
    if template.get("approval_created") is True:
        blockers.append("operator_approval_creation_detected")
        failed = True

    # 4. Check non-null approved IDs
    if len(gate_packet.get("approved_source_requirement_ids", [])) > 0 or len(gate_packet.get("approved_claim_ids", [])) > 0:
        blockers.append("active_approval_claims_detected")
        failed = True
    if len(template.get("approved_source_requirement_ids", [])) > 0 or len(template.get("approved_claim_ids", [])) > 0:
        blockers.append("active_approval_claims_detected")
        failed = True

    # 5. Block active dispatch / generation flags
    forbidden_flags = [
        "valid_for_draft_generation",
        "valid_for_article_use",
        "valid_for_publication",
        "valid_for_dispatch",
        "public_postable",
        "dispatch_allowed_now",
        "live_write_allowed_now"
    ]
    for flag in forbidden_flags:
        if gate_packet.get(flag) is True or template.get(flag) is True:
            blockers.append("forbidden_active_dispatch_flags")
            failed = True

    # Check matrix rows
    for row in matrix:
        if row.get("operator_approval_present") is True:
            blockers.append("active_approval_claims_detected")
            failed = True

    # 6. Scan nested texts recursively
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
            parts = t.split("excerpt:")
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

        # E. Operator signature check
        is_op_key = key_name.lower() in ["operator_id", "operator_verified_by", "operator_signature", "approved_by", "operator"] or (key_name.lower().startswith("operator_id") and not key_name.lower().endswith("_redacted"))
        if is_op_key and not is_placeholder(t):
            blockers.append("operator_signature_leaked")
            failed = True
        if "operator_jim_sig" in t_lower or "operator_test_sig" in t_lower or "test_only_operator_not_real_verification" in t_lower:
            blockers.append("operator_signature_leaked")
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
        if any(k in t_lower for k in FINANCIAL_ADVICE_KEYWORDS):
            blockers.append("financial_advice_or_signal_language_detected")
            failed = True

    check_value(gate_packet)
    check_value(template)
    check_value(matrix)

    blockers = sorted(list(set(blockers)))
    status = "FAILED_WITH_BLOCKERS" if failed else "PASSED_WITH_REVIEW_ONLY_BLOCKERS"

    report = {
        "schema_version": "6.0.0",
        "validation_status": status,
        "runtime_truth": False,
        "operator_approval_gate_validated": True,
        "blockers": blockers,
        "blocker_count": len(blockers)
    }

    return report, blockers
