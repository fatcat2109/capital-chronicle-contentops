"""V6 Platform Variant Approval Validator.

Ensures empty platform variant approval contract states are secure, redacted, and unapproved.
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
    if val is None or val is False or val == "" or val == []:
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
            "approval_packet_contract_blocked_waiting_for_rendered_platform_variants",
            "future_platform_variant_approval_input_contract_only",
            "blocked_template_only_not_approval",
            "blocked_no_approval_packet_created",
            "blocked_missing_rendered_payload_and_destination",
            "approval_packet_contract_blocked_pending_rendered_payloads",
            "no_approval_id_created",
            "no_approval_hash_created",
            "no_payload_hash_created",
            "no_outbox_entry_created",
            "operator_signature_absent"
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


def is_non_empty_forbidden_value(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, (list, tuple, set)):
        return len(val) > 0 and any(not is_placeholder(x) for x in val)
    if isinstance(val, dict):
        return len(val) > 0
    return not is_placeholder(val)


def validate_platform_variant_approval_packet_contract(
    platform_variant_approval_contract_packet: dict[str, Any],
    platform_variant_approval_input_contract: dict[str, Any],
    platform_variant_blocked_approval_template: dict[str, Any],
    platform_variant_blocked_approval_output: dict[str, Any],
    platform_variant_approval_gate_matrix: list[dict[str, Any]],
    platform_variant_approval_checklist: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Validates the offline dry-run platform variant approval contract state."""
    blockers = []
    failed = False

    # 1. Default required blockers
    blockers.extend([
        "rendered_platform_variants_missing",
        "exact_payload_preview_missing",
        "destination_binding_missing",
        "account_binding_missing",
        "approval_packet_creation_blocked",
        "jim_review_required",
        "publication_blocked",
        "dispatch_blocked",
        "human_review_required"
    ])

    # 2. Check packet availability claims and flags
    packet_flags_to_fail = [
        "rendered_platform_variants_available",
        "exact_payload_preview_available",
        "destination_binding_completed",
        "account_binding_completed",
        "jim_review_completed",
        "operator_approval_present",
        "exact_payload_approval_completed",
        "approval_packet_creation_allowed",
        "approval_packet_created",
        "approval_id_created",
        "approval_hash_created",
        "payload_hash_created",
        "approval_signature_present",
        "approval_valid_for_dispatch",
        "platform_payload_hash_created",
        "outbox_entry_created"
    ]
    for flag in packet_flags_to_fail:
        if platform_variant_approval_contract_packet.get(flag) is True:
            blockers.append("approval_packet_creation_blocked")
            failed = True

    # 3. Check template fields
    template_fields = [
        "approval_id", "approval_hash", "payload_hash", "operator_id_redacted",
        "operator_signature_redacted", "approved_at_redacted", "destination_binding_ref",
        "account_binding_ref", "platform_payload_manifest_ref", "approval_statement"
    ]
    for field in template_fields:
        val = platform_variant_blocked_approval_template.get(field)
        if val is not None and val != "":
            blockers.append("non_null_approval_template_fields_detected")
            failed = True

    template_flags = [
        "approval_valid_for_dispatch", "approval_packet_created",
        "exact_payload_approval_completed", "outbox_entry_created",
        "dispatch_allowed_now", "public_postable", "live_write_allowed_now"
    ]
    for flag in template_flags:
        if platform_variant_blocked_approval_template.get(flag) is True:
            blockers.append("forbidden_active_dispatch_flags")
            failed = True

    # 4. Check output fields and lists
    output_flags_to_fail = [
        "approval_packet_created", "approval_id_created", "approval_hash_created",
        "payload_hash_created", "operator_signature_present", "approval_valid_for_dispatch",
        "exact_payload_approval_completed", "destination_binding_completed", "account_binding_completed"
    ]
    for flag in output_flags_to_fail:
        if platform_variant_blocked_approval_output.get(flag) is True:
            blockers.append("approval_packet_creation_blocked")
            failed = True

    output_lists = [
        "platform_payloads", "platform_payload_hashes", "approval_records",
        "approval_ledger_entries", "destination_bindings", "account_bindings",
        "public_urls", "outbox_entries", "citations", "evidence_refs",
        "source_names", "platform_metrics"
    ]
    for field in output_lists:
        if len(platform_variant_blocked_approval_output.get(field, [])) > 0:
            blockers.append("non_empty_output_lists_detected")
            failed = True

    # 5. Check output counts
    count_keys = ["approval_record_count", "payload_hash_count", "outbox_entry_count", "destination_binding_count", "public_url_count"]
    for key in count_keys:
        if platform_variant_blocked_approval_output.get(key, 0) > 0:
            blockers.append("non_zero_word_or_variant_count_detected")
            failed = True

    # 6. Block active publication, dispatch, outbox, etc.
    forbidden_flags = [
        "allowed_for_publication",
        "public_postable",
        "dispatch_allowed_now",
        "live_write_allowed_now"
    ]
    for flag in forbidden_flags:
        if platform_variant_approval_contract_packet.get(flag) is True:
            blockers.append("forbidden_active_dispatch_flags")
            failed = True

    # 7. Check browser/provider/network claims
    behavior_flags = [
        "provider_call_performed",
        "browser_session_started",
        "env_read_performed",
        "credentials_hydrated",
        "platform_api_request_performed",
        "webhook_request_performed"
    ]
    for flag in behavior_flags:
        if platform_variant_approval_contract_packet.get(flag) is True:
            blockers.append("forbidden_behavior_claims")
            failed = True

    # 8. Check readiness matrix rows
    readiness_keys_to_block = [
        "rendered_platform_variant_available",
        "exact_payload_preview_available",
        "destination_binding_completed",
        "account_binding_completed",
        "payload_hash_created",
        "approval_packet_created",
        "approval_hash_created",
        "operator_signature_present",
        "exact_payload_approval_completed",
        "approval_valid_for_dispatch",
        "outbox_entry_created",
        "dispatch_allowed_now",
        "live_write_allowed_now",
        "public_url_created",
        "valid_for_publication"
    ]
    required_row_blockers = {
        "rendered_platform_variants_missing",
        "exact_payload_preview_missing",
        "destination_binding_missing",
        "account_binding_missing",
        "approval_packet_creation_blocked",
        "dispatch_blocked"
    }
    for row in platform_variant_approval_gate_matrix:
        # A. Check active flags
        for rk in readiness_keys_to_block:
            if row.get(rk) is True:
                blockers.append("readiness_matrix_active_lane_detected")
                failed = True
        
        # B. Check blocks_publication is True
        if row.get("blocks_publication") is not True:
            blockers.append("readiness_matrix_publication_unblocked_detected")
            failed = True

        # C. Check variant_generation_status is correct
        if row.get("approval_gate_status") != "blocked_missing_rendered_payload_and_destination":
            blockers.append("readiness_matrix_active_lane_detected")
            failed = True

        # D. Check blockers list contains all expected values
        row_blockers = row.get("blockers")
        if not isinstance(row_blockers, list) or not required_row_blockers.issubset(set(row_blockers)):
            blockers.append("readiness_matrix_active_lane_detected")
            failed = True

    # 9. Check input contract details
    if platform_variant_approval_input_contract.get("contract_status") != "FUTURE_PLATFORM_VARIANT_APPROVAL_INPUT_CONTRACT_ONLY":
        blockers.append("platform_input_contract_incomplete")
        failed = True

    required_inputs = platform_variant_approval_input_contract.get("required_inputs")
    expected_names = {
        "rendered_platform_variants_ref",
        "exact_payload_preview_ref",
        "platform_payload_manifest_ref",
        "destination_binding_ref",
        "account_binding_ref",
        "payload_hash_policy_ref",
        "approval_policy_ref",
        "jim_review_ref"
    }

    if not isinstance(required_inputs, list) or len(required_inputs) == 0:
        blockers.append("platform_input_contract_incomplete")
        failed = True
    else:
        found_names = set()
        for inp in required_inputs:
            if not isinstance(inp, dict):
                blockers.append("platform_input_contract_incomplete")
                failed = True
                continue
            name = inp.get("input_name")
            if name is None or name not in expected_names:
                blockers.append("platform_input_contract_incomplete")
                failed = True
                continue
            found_names.add(name)

            if inp.get("required") is not True:
                blockers.append("platform_input_contract_incomplete")
                failed = True

            if inp.get("current_status") != "missing":
                blockers.append("platform_input_contract_incomplete")
                failed = True

            if inp.get("value_ref") is not None:
                blockers.append("platform_input_value_ref_present")
                failed = True

            if inp.get("raw_value_persisted") is not False:
                blockers.append("platform_input_raw_value_persisted")
                failed = True

            if inp.get("blocks_approval_packet_creation") is not True:
                blockers.append("platform_input_not_blocking_generation")
                failed = True

        if found_names != expected_names:
            blockers.append("platform_input_contract_incomplete")
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
                k_lower = k.lower()
                if k_lower in ["citations", "evidence_refs", "source_citations", "source_urls"]:
                    if is_non_empty_forbidden_value(v):
                        blockers.append("citation_or_source_reference_leak_detected")
                        blockers.append("non_empty_forbidden_output_lists_detected")
                        failed = True
                elif k_lower in ["source_names", "source_publishers", "publishers", "source_titles", "source_labels", "source_display_names"]:
                    if is_non_empty_forbidden_value(v):
                        blockers.append("source_name_leak_detected")
                        blockers.append("non_empty_forbidden_output_lists_detected")
                        failed = True
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

    check_value(platform_variant_approval_contract_packet)
    check_value(platform_variant_approval_input_contract)
    check_value(platform_variant_blocked_approval_template)
    check_value(platform_variant_blocked_approval_output)
    check_value(platform_variant_approval_gate_matrix)
    check_value(platform_variant_approval_checklist)
    for text in texts_to_scan:
        check_text(text)

    blockers = sorted(list(set(blockers)))
    status = "FAILED_WITH_BLOCKERS" if failed else "PASSED_WITH_REVIEW_ONLY_BLOCKERS"

    report = {
        "schema_version": "6.0.0",
        "validation_status": status,
        "runtime_truth": False,
        "platform_variant_approval_validated": True,
        "blockers": blockers,
        "blocker_count": len(blockers)
    }

    return report, blockers
