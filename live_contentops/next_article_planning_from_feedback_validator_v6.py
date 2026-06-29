"""V6 Next Article Planning From Feedback Validator.

Ensures empty next article planning from feedback contract states are secure, redacted, and blocked.
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
        if "redacted" in val_lower or "placeholder" in val_lower or "unverified" in val_lower or "missing" in val_lower or "pending" in val_lower:
            return True
        exact_placeholders = {
            "none", "null", "blocked",
            "none: verification pending",
            "manual_ingestion_pending",
            "manual_operator_research_pending",
            "next_article_planning_blocked_waiting_for_feedback_summary_backlog",
            "future_next_article_planning_from_feedback_input_contract_only",
            "blocked_template_only_not_next_article_planning",
            "blocked_no_next_article_planning_created",
            "blocked_missing_feedback_summary_and_planning_policy",
            "next_article_planning_blocked_pending_feedback_summary_and_planning_policy",
            "next_article_planning_from_feedback_input_contract.json",
            "feedback_summary_backlog_ref",
            "feedback_summary_ref",
            "backlog_items_ref",
            "next_article_signals_ref",
            "redacted_feedback_records_ref",
            "public_url_proof_ref",
            "platform_publication_id_ref",
            "planning_policy_ref",
            "source_research_policy_ref",
            "audit_redaction_policy_ref",
            "operator_planning_authorization_ref",
            "jim_planning_review_ref",
            "feedback_summary_backlog_required",
            "feedback_summary_required",
            "backlog_items_required",
            "next_article_signals_required",
            "redacted_feedback_records_required",
            "public_url_proof_required",
            "platform_publication_id_required",
            "planning_policy_required",
            "source_research_policy_required",
            "operator_planning_authorization_required",
            "jim_planning_review_required",
            "next_article_planning_blocked",
            "source_pack_request_blocked",
            "no_article_ideas_created",
            "no_research_questions_created",
            "no_source_pack_requests_created",
            "no_canonical_draft_requests_created",
            "no_feedback_summaries_created",
            "no_backlog_items_created",
            "no_next_article_signals_created",
            "no_redacted_feedback_records_created",
            "no_public_url_created",
            "no_publication_ready_claim",
            "no_financial_advice_language",
            "jim_final_review_required",
            "no_audit_record_mutated"
        }
        if val_lower in exact_placeholders:
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


def validate_next_article_planning_from_feedback_contract(
    next_article_planning_packet: dict[str, Any],
    next_article_planning_input_contract: dict[str, Any],
    next_article_planning_blocked_template: dict[str, Any],
    next_article_planning_blocked_output: dict[str, Any],
    next_article_planning_gate_matrix: list[dict[str, Any]],
    next_article_planning_checklist: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Validates the offline dry-run next article planning contract state."""
    blockers = []
    failed = False

    # 1. Default required blockers
    blockers.extend([
        "feedback_summary_backlog_missing",
        "feedback_summary_missing",
        "backlog_items_missing",
        "next_article_signals_missing",
        "planning_policy_missing",
        "source_research_policy_missing",
        "next_article_planning_blocked",
        "source_pack_request_blocked",
        "jim_planning_review_required",
        "audit_mutation_blocked",
        "human_review_required"
    ])

    # 2. Check packet availability claims and flags
    packet_flags_to_fail = [
        "feedback_summary_available",
        "backlog_items_available",
        "next_article_signals_available",
        "redacted_feedback_records_available",
        "public_url_proof_available",
        "platform_publication_id_available",
        "planning_policy_available",
        "source_research_policy_available",
        "jim_planning_review_completed",
        "operator_planning_authorization_present",
        "article_planning_allowed",
        "article_planning_performed",
        "article_idea_created",
        "research_question_created",
        "source_pack_request_created",
        "canonical_draft_requested",
        "scraping_performed",
        "live_write_attempted",
        "retry_attempted",
        "public_url_created",
        "public_postable"
    ]
    for flag in packet_flags_to_fail:
        if next_article_planning_packet.get(flag) is True:
            blockers.append("next_article_planning_blocked")
            failed = True

    # 3. Check template fields
    template_fields = [
        "article_planning_id", "article_idea_id", "research_question_id", "source_pack_request_id", "canonical_draft_request_id",
        "feedback_summary_backlog_ref", "feedback_summary_ref", "backlog_items_ref", "next_article_signals_ref",
        "redacted_feedback_records_ref", "public_url_proof_ref", "platform_publication_id_ref",
        "planning_policy_ref", "source_research_policy_ref", "audit_redaction_policy_ref",
        "operator_id_redacted", "operator_signature_redacted", "created_at_redacted",
        "article_idea_statement", "research_question_statement", "source_pack_request_statement", "canonical_draft_request_statement"
    ]
    for field in template_fields:
        val = next_article_planning_blocked_template.get(field)
        if val is not None and val != "":
            blockers.append("non_null_feedback_template_fields_detected")
            failed = True

    template_flags = [
        "article_planning_performed", "article_idea_created", "research_question_created",
        "source_pack_request_created", "canonical_draft_requested", "audit_record_mutated"
    ]
    for flag in template_flags:
        if next_article_planning_blocked_template.get(flag) is True:
            blockers.append("forbidden_active_feedback_flags")
            failed = True

    # 4. Check output fields and lists
    output_flags_to_fail = [
        "article_planning_performed", "article_idea_created", "research_question_created",
        "source_pack_request_created", "canonical_draft_requested", "audit_record_mutated", "public_url_created"
    ]
    for flag in output_flags_to_fail:
        if next_article_planning_blocked_output.get(flag) is True:
            blockers.append("next_article_planning_blocked")
            failed = True

    output_lists = [
        "article_ideas", "research_questions", "source_pack_requests", "canonical_draft_requests",
        "feedback_summaries", "backlog_items", "next_article_signals", "redacted_feedback_records",
        "public_urls", "public_url_proofs", "platform_publication_ids",
        "citations", "evidence_refs", "source_names", "request_payloads", "response_payloads"
    ]
    for field in output_lists:
        if len(next_article_planning_blocked_output.get(field, [])) > 0:
            blockers.append("non_empty_output_lists_detected")
            failed = True

    # 5. Check output counts
    count_keys = [
        "article_idea_count", "research_question_count", "source_pack_request_count", "canonical_draft_request_count",
        "feedback_summary_count", "backlog_item_count", "next_article_signal_count", "redacted_record_count"
    ]
    for key in count_keys:
        if next_article_planning_blocked_output.get(key, 0) > 0:
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
        if next_article_planning_packet.get(flag) is True:
            blockers.append("forbidden_active_feedback_flags")
            failed = True

    # 7. Check browser/provider/network/scraping claims
    behavior_flags = [
        "model_provider_call_performed",
        "provider_call_performed",
        "browser_session_started",
        "env_read_performed",
        "credentials_hydrated",
        "platform_api_request_performed",
        "webhook_request_performed",
        "scraping_performed"
    ]
    for flag in behavior_flags:
        if next_article_planning_packet.get(flag) is True:
            blockers.append("forbidden_behavior_claims")
            failed = True

    # 8. Check readiness matrix rows
    readiness_keys_to_block = [
        "feedback_summary_available",
        "backlog_items_available",
        "next_article_signals_available",
        "redacted_feedback_records_available",
        "public_url_proof_available",
        "platform_publication_id_available",
        "planning_policy_available",
        "source_research_policy_available",
        "operator_planning_authorization_present",
        "jim_planning_review_completed",
        "article_planning_allowed",
        "article_planning_performed",
        "article_idea_created",
        "research_question_created",
        "source_pack_request_created",
        "canonical_draft_requested",
        "model_provider_call_performed",
        "provider_call_performed",
        "browser_session_started",
        "env_read_performed",
        "credentials_hydrated",
        "platform_api_request_performed",
        "webhook_request_performed",
        "scraping_performed",
        "audit_record_mutated",
        "live_write_attempted",
        "retry_attempted",
        "public_url_created"
    ]
    required_row_blockers = {
        "feedback_summary_backlog_missing",
        "feedback_summary_missing",
        "backlog_items_missing",
        "next_article_signals_missing",
        "planning_policy_missing",
        "source_research_policy_missing",
        "next_article_planning_blocked",
        "source_pack_request_blocked",
        "jim_planning_review_required",
        "audit_mutation_blocked"
    }
    for row in next_article_planning_gate_matrix:
        # A. Check active flags
        for rk in readiness_keys_to_block:
            if row.get(rk) is True:
                blockers.append("readiness_matrix_active_lane_detected")
                failed = True
        
        # B. Check blocks_publication is True
        if row.get("blocks_publication") is not True:
            blockers.append("readiness_matrix_publication_unblocked_detected")
            failed = True

        # C. Check status is correct
        if row.get("planning_gate_status") != "blocked_missing_feedback_summary_and_planning_policy":
            blockers.append("readiness_matrix_active_lane_detected")
            failed = True

        # D. Check blockers list contains all expected values
        row_blockers = row.get("blockers")
        if not isinstance(row_blockers, list) or not required_row_blockers.issubset(set(row_blockers)):
            blockers.append("readiness_matrix_active_lane_detected")
            failed = True

    # 9. Check input contract details
    if next_article_planning_input_contract.get("contract_status") != "FUTURE_NEXT_ARTICLE_PLANNING_FROM_FEEDBACK_INPUT_CONTRACT_ONLY":
        blockers.append("platform_input_contract_incomplete")
        failed = True

    required_inputs = next_article_planning_input_contract.get("required_inputs")
    expected_names = {
        "feedback_summary_backlog_ref",
        "feedback_summary_ref",
        "backlog_items_ref",
        "next_article_signals_ref",
        "redacted_feedback_records_ref",
        "public_url_proof_ref",
        "platform_publication_id_ref",
        "planning_policy_ref",
        "source_research_policy_ref",
        "audit_redaction_policy_ref",
        "operator_planning_authorization_ref",
        "jim_planning_review_ref"
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

            if inp.get("blocks_next_article_planning") is not True:
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

        # E. Operator signature / Approval ID / Approval Hash / Feedback statement / IDs checks
        is_op_key = key_name.lower() in [
            "operator_id", "operator_verified_by", "operator_signature",
            "approved_by", "operator", "approval_id", "approval_hash", "feedback_summary_statement",
            "backlog_item_statement", "article_idea_statement", "research_question_statement",
            "source_pack_request_statement", "canonical_draft_request_statement",
            "outbox_entry_id", "approval_queue_entry_id", "dispatch_attempt_id",
            "destination_binding_ref", "account_binding_ref", "destination_binding", "account_binding",
            "payload_hash", "platform_endpoint_ref", "credential_scope_ref",
            "request_payload_ref", "response_ref", "credential_scope_proof_ref",
            "public_url_proof_ref", "platform_publication_id_ref", "audit_redaction_policy_ref",
            "platform_publication_id", "audit_record_id", "feedback_summary_id", "backlog_item_id", "next_article_signal_id",
            "community_feedback_capture_ref", "redacted_feedback_records_ref", "feedback_capture_policy_ref",
            "feedback_summarization_policy_ref", "backlog_routing_policy_ref", "operator_summary_authorization_ref",
            "jim_feedback_review_ref", "article_planning_id", "article_idea_id", "research_question_id",
            "source_pack_request_id", "canonical_draft_request_id", "feedback_summary_backlog_ref",
            "feedback_summary_ref", "backlog_items_ref", "next_article_signals_ref", "planning_policy_ref",
            "source_research_policy_ref", "operator_planning_authorization_ref", "jim_planning_review_ref"
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

        is_url_or_account_key = key_name.lower() in [
            "public_url", "public_urls", "webhook_url", "webhook_urls", "webhook_request_url", "platform_account_id"
        ]
        if is_url_or_account_key and not is_placeholder(t):
            blockers.append("private_or_secret_material_detected")
            failed = True

        # F. Timestamp check
        is_date_key = key_name.lower() in ["approved_at", "retrieved_at", "created_at", "reviewed_at", "created_at_redacted"] or (key_name.lower().endswith("_at") and not key_name.lower().endswith("_redacted"))
        if is_date_key and not is_placeholder(t):
            blockers.append("fake_approval_timestamp_detected")
            failed = True
        if DATE_re.search(t):
            blockers.append("fake_approval_timestamp_detected")
            failed = True

        # G. Public ready/publication ready/dispatch ready checks
        if re.search(r"\b(public_ready|publication_ready|ready_to_publish|dispatch_ready)\b", t_lower):
            blockers.append("public_ready_claim_detected")
            failed = True

        # H. Metric / Comment / Reaction / User handle checks
        if any(m in t_lower for m in METRICS):
            blockers.append("metric_leak_detected")
            failed = True
        if ("comment" in key_name.lower() and not is_placeholder(t)) or ("comment:" in t_lower and not is_placeholder(t.split("comment:")[1].strip())):
            blockers.append("comment_text_leak_detected")
            failed = True
        if ("reaction" in key_name.lower() and not is_placeholder(t)) or ("reaction:" in t_lower and not is_placeholder(t.split("reaction:")[1].strip())):
            blockers.append("reaction_text_leak_detected")
            failed = True
        if ("summary" in key_name.lower() and not is_placeholder(t)) or ("summary:" in t_lower and not is_placeholder(t.split("summary:")[1].strip())):
            blockers.append("summary_text_leak_detected")
            failed = True
        if ("backlog" in key_name.lower() and not is_placeholder(t)) or ("backlog:" in t_lower and not is_placeholder(t.split("backlog:")[1].strip())):
            blockers.append("backlog_text_leak_detected")
            failed = True
        if ("idea" in key_name.lower() and not is_placeholder(t)) or ("idea:" in t_lower and not is_placeholder(t.split("idea:")[1].strip())):
            blockers.append("article_idea_text_leak_detected")
            failed = True
        if ("question" in key_name.lower() and not is_placeholder(t)) or ("question:" in t_lower and not is_placeholder(t.split("question:")[1].strip())):
            blockers.append("research_question_text_leak_detected")
            failed = True
        if ("source_pack_request" in key_name.lower() and not is_placeholder(t)) or ("source_pack_request:" in t_lower and not is_placeholder(t.split("source_pack_request:")[1].strip())):
            blockers.append("source_pack_request_text_leak_detected")
            failed = True
        if ("canonical_draft_request" in key_name.lower() and not is_placeholder(t)) or ("canonical_draft_request:" in t_lower and not is_placeholder(t.split("canonical_draft_request:")[1].strip())):
            blockers.append("canonical_draft_request_text_leak_detected")
            failed = True
        if ("handle" in key_name.lower() or "user_handle" in key_name.lower() or t.startswith("@")) and not is_placeholder(t):
            blockers.append("user_handle_leak_detected")
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

    check_value(next_article_planning_packet)
    check_value(next_article_planning_input_contract)
    check_value(next_article_planning_blocked_template)
    check_value(next_article_planning_blocked_output)
    check_value(next_article_planning_gate_matrix)
    check_value(next_article_planning_checklist)
    for text in texts_to_scan:
        check_text(text)

    blockers = sorted(list(set(blockers)))
    status = "FAILED_WITH_BLOCKERS" if failed else "PASSED_WITH_REVIEW_ONLY_BLOCKERS"

    report = {
        "schema_version": "6.0.0",
        "validation_status": status,
        "runtime_truth": False,
        "next_article_planning_validated": True,
        "blockers": blockers,
        "blocker_count": len(blockers)
    }

    return report, blockers
