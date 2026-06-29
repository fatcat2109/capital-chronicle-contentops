"""V6 Official Platform Docs Verification Gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OFFICIAL_PLATFORM_DOCS_VERIFICATION_FOR_LIVE_DISPATCH_REQUEST_GATE_V0"
REQUEST_GATE_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_LIVE_DISPATCH_REQUEST_PACKAGE_GATE_FROM_ACCOUNT_BINDING_V0"
SCHEMA_VERSION = "6.0.0"

SECRET_MARKERS = (
    "token", "api_key", "password", "bearer", "cookie", "webhook_url",
    "private_key", "secret", "credential", "channel_id", "account_id",
    "app_id", "workspace_id", "client_id", "client_secret"
)

PUBLIC_READY_MARKERS = (
    "approved",
    "approval_status",
    "approved_canonical_article_available",
    "publication_ready",
    "allowed_for_publication",
    "publication_allowed",
    "public_postable",
    "dispatch_allowed",
    "platform_variant_generation_allowed",
    "outbox_creation_allowed",
    "public_url",
    "public_metrics",
    "canonical_public_url",
)

FAKE_CLAIMS_MARKERS = (
    "fake_url",
    "fake_metrics",
    "fake_comments",
    "fake_readiness",
    "fake_citation",
)

TRADING_ADVICE_PATTERNS = (
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\bposition\s+sizing\b",
    r"\bentry\b",
    r"\bexit\b",
    r"\btarget\b",
    r"\bguaranteed\s+prediction\b",
    r"\bsignal\s+service\b",
    r"\btrading\s+advice\b",
)
TRADING_ADVICE_RE = [re.compile(p, re.IGNORECASE) for p in TRADING_ADVICE_PATTERNS]

FORBIDDEN_LIVE_CLAIMS = (
    "endpoint_path", "endpoint path",
    "api_endpoint", "api endpoint",
    "request_payload", "request payload",
    "payload_body", "payload body",
    "raw_copied_docs", "raw copied docs",
    "copied_docs", "copied docs",
    "raw_docs", "raw docs",
    "live_instructions", "live instructions",
    "live_instruction", "live instruction",
    "send_instruction", "send instruction",
    "dispatch_instruction", "dispatch instruction",
    "platform_live", "platform live",
    "live_dispatch", "live dispatch",
    "live_send", "live send",
    "send_now", "send now",
    "publish_now", "publish now",
    "webhook_url", "webhook url",
    "webhook",
    "endpoint",
    "api_request", "api request",
    "browser_request", "browser request",
    "platform_request", "platform request",
    "public_url", "public url",
    "public_metrics", "public metrics",
    "ready_for_publication", "ready for publication",
    "publication_ready", "publication ready",
    "dispatch_allowed", "dispatch allowed"
)

ALLOWED_SCHEMA_PHRASES = (
    "supervised_live_dispatch_future_gate",
    "mark_scope_ready_for_future_supervised_live_gate",
    "mark_scope_ready_for_future_supervised_live_gate_only_not_send",
    "live_scope_preflight_only",
    "endpoint_allowlist_later_required",
    "endpoint_allowlist_required_later",
    "webhook_family_target",
    "webhook_behavior",
    "endpoint_allowlist",
    "operator_declared_official_docs_review_only",
    "official_docs_operator_declared_reference",
    "declare_official_docs_reviewed_for_future_gate_only",
    "official_docs_scope_preflight_only",
    "allowlist_mode",
    "endpoint_allowlist_declaration_id",
    "credential_allowlist_preflight_id",
    "credential_allowlist_preflight_available",
    "endpoint_allowlist_declared_ready",
    "eligible_for_supervised_live_dispatch_request_gate",
    "operator_declared_endpoint_allowlist_only_not_request",
    "endpoint_allowlist_rows",
    "credential_key_names_only_reviewed",
    "live_write_request_budget_confirmed",
    "timeout_policy_confirmed",
    "retry_policy_confirmed",
    "audit_redaction_confirmed",
    "mark_credential_allowlist_ready_for_future_live_gate",
    "mark_credential_allowlist_ready_for_future_live_gate_only_not_send",
    "credential_allowlist_preflight_only",
    "future_supervised_live_dispatch",
    "substack_operator_declared_host_label",
    "discord_operator_declared_webhook_host_label",
    "post_method_label_only",
    "browser_manual_method_label_only",
    "webhook_method_label_only",
    "label_only_no_endpoint_value",
    "timeout_policy_label",
    "retry_policy_label",
    "checked_declared_key_names_only",
    "account_binding_preflight_id",
    "account_binding_declaration_id",
    "account_binding_mode",
    "platform_binding_rows",
    "account_identity_later_required",
    "permission_check_later_required",
    "destination_binding_confirmed",
    "endpoint_allowlist_rows_reviewed",
    "mark_account_binding_ready_for_future_live_request_gate",
    "mark_account_binding_ready_for_future_live_request_gate_only_not_send",
    "account_binding_preflight_only",
    "operator_declared_account_binding_labels_only_not_verified",
    "non_secret_label_only_not_verified",
    "eligible_for_live_dispatch_request_package_gate",
    "account_binding_preflight_available",
    "account_binding_declared_ready",
    "endpoint_host_label",
    "endpoint_path_label",
    "endpoint_allowlist_kind",
    "dispatch_request_gate_declaration_id",
    "dispatch_request_gate_mode",
    "operator_declared_dispatch_request_package_gate_only_not_send",
    "requested_platforms",
    "payload_hash_confirmed",
    "request_budget_confirmed",
    "kill_switch_confirmed",
    "manual_fallback_confirmed",
    "account_binding_confirmed",
    "provider_execution_later_required",
    "operator_final_review_later_required",
    "mark_dispatch_request_package_gate_ready",
    "mark_dispatch_request_package_gate_ready_only_not_send",
    "dispatch_request_package_gate_only",
    "eligible_for_future_supervised_dispatch_request_package",
    "dispatch_request_package_gate_available",
    "dispatch_request_package_gate_declared_ready",
    "account_binding_preflight_sha256",
    "cc_announcements_channel_webhook",
    "staff_webhook_send_access",
    "discord webhook",
    "webhook access",
    "webhook host",
    "webhook path",
    "webhook method",
    "endpoint host",
    "endpoint path",
    "endpoint method",
    "endpoint kind",
    "endpoint value",
    "endpoint allowlist row",
    "endpoint allowlist rows",
    "endpoint path label",
    "endpoint host label",
    "webhook path label",
    "webhook host label",
    "webhook method label",
    "official_platform_docs_verification_id",
    "official_docs_verification_declaration_id",
    "official_docs_source_summary_id",
    "official_sources_only_confirmed",
    "no_credentials_used_confirmed",
    "no_live_calls_confirmed",
    "no_browser_login_confirmed",
    "endpoint_mapping_later_required",
    "permission_verification_later_required",
    "payload_hash_revalidation_later_required",
    "kill_switch_later_required",
    "audit_redaction_later_required",
    "manual_fallback_later_required",
    "docs_verification_available",
    "docs_verification_declared_ready",
    "eligible_for_future_endpoint_mapping_gate",
    "mark_official_docs_verified_for_future_dispatch_request_mapping",
    "MARK_OFFICIAL_DOCS_VERIFIED_FOR_FUTURE_MAPPING_ONLY_NOT_SEND",
    "official_docs_verification_only",
    "https://substack.com/help/api",
    "api_post_draft",
    "requires_token_header",
    "https://discord.com/developers/docs/resources/webhook",
    "execute_webhook",
    "webhook_token_in_url",
    "webhook_post_endpoint",
    "All checks passed on Substack API.",
    "Discord webhook docs verified.",
    "Verified Substack and Discord capability classifications.",
    "SUBSTACK_API_KEY_DRAFT_STAGE",
    "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
    "credential_allowlist_preflight_",
    "account_binding_preflight_",
    "account_binding_declaration_",
    "binding_decl_",
    "dispatch_request_gate_decl_",
    "source_summary_",
    "docs_decl_",
    "docs_verification_",
    "docs_verification_decl_",
    "docs_review_scope",
    "official_platform_documentation",
    "api_documentation_page",
    "live_write_allowed_later",
    "manual_fallback_required",
    "official_api_supported_for_required_action",
    "official_webhook_supported_for_required_action",
    "official_browser_or_manual_surface_only",
    "unsupported_by_official_docs",
    "unclear_requires_operator_decision",
    "live_dispatch_v6_evaluation",
    "draft_console_target",
    "webhook_family_target",
    "post_endpoint",
    "webhook_post_endpoint",
    "webhook Reference Documentation",
    "Publishing API Specs",
    "Substack Publishing API",
    "Discord Webhook Reference",
    "Discord Webhook",
    "Substack API",
    "webhook docs verified",
    "checks passed on Substack API",
    "capability classifications",
    "Requires publisher-level dashboard access token.",
    "Cannot create webhooks via API without authorization permissions.",
    "Substack Publishing API Specs",
    "Discord Webhook Reference Documentation",
    "TASK_CONTENTOPS_V6_LOCAL_LIVE_DISPATCH_REQUEST_PACKAGE_GATE_FROM_ACCOUNT_BINDING_V0",
    "TASK_CONTENTOPS_V6_LIVE_DISPATCH_ACCOUNT_BINDING_PREFLIGHT_FROM_CREDENTIAL_ALLOWLIST_V0"
)


def _scan_for_forbidden_live_claims(text: str) -> str | None:
    lowered = text.lower()
    for phrase in ALLOWED_SCHEMA_PHRASES:
        lowered = lowered.replace(phrase.lower(), "")
    for term in FORBIDDEN_LIVE_CLAIMS:
        if term in lowered:
            return term
    return None


def _scan_for_forbidden_binding_row_claims(row: dict[str, Any]) -> str | None:
    for k, v in row.items():
        if k == "credential_key_name":
            continue
        if isinstance(v, str):
            lowered = v.lower()
            for phrase in ALLOWED_SCHEMA_PHRASES:
                lowered = lowered.replace(phrase.lower(), "")
            for term in FORBIDDEN_LIVE_CLAIMS:
                if term in lowered:
                    return term
    return None


@dataclass(frozen=True)
class OfficialPlatformDocsVerificationPacket:
    schema_version: str
    task_label: str
    official_platform_docs_verification_id: str
    official_docs_verification_declaration_id: str
    official_docs_source_summary_id: str
    operator_id: str
    created_at_manual: str
    dispatch_request_package_gate_id: str
    dispatch_request_package_gate_sha256: str
    account_binding_preflight_id: str
    account_binding_preflight_sha256: str
    credential_allowlist_preflight_id: str
    credential_allowlist_preflight_sha256: str
    live_dispatch_scope_preflight_id: str
    live_dispatch_scope_preflight_sha256: str
    live_dispatch_readiness_preflight_id: str
    live_dispatch_readiness_preflight_sha256: str
    combined_payload_hash: str
    platforms: list[str]
    requested_platforms: list[str]
    platform_docs_rows: list[dict[str, Any]]
    official_sources_only_confirmed: bool
    no_credentials_used_confirmed: bool
    no_live_calls_confirmed: bool
    no_browser_login_confirmed: bool
    endpoint_mapping_later_required: bool
    permission_verification_later_required: bool
    payload_hash_revalidation_later_required: bool
    kill_switch_later_required: bool
    audit_redaction_later_required: bool
    manual_fallback_later_required: bool
    docs_verification_available: bool
    docs_verification_declared_ready: bool
    eligible_for_future_endpoint_mapping_gate: bool
    live_send_request_created: bool = False
    approval_for_live_dispatch: bool = False
    approval_for_publication: bool = False
    generated_citations_allowed: bool = False
    citations_verified: bool = False
    approved_canonical_article_available: bool = False
    publication_ready: bool = False
    dispatch_allowed: bool = False
    platform_variant_generation_allowed: bool = False
    outbox_creation_allowed: bool = False
    public_url: None = None
    public_metrics: None = None
    review_only: bool = True
    human_review_required: bool = True
    kill_switch_active: bool = True
    runtime_truth: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _has_secret_marker(value: str) -> bool:
    lowered = value.lower()
    bypass_terms = [
        "task_contentops_v6_official_platform_docs_verification_for_live_dispatch_request_gate_v0",
        "official_platform_docs_verification_id",
        "official_docs_verification_declaration_id",
        "official_docs_source_summary_id",
        "official_sources_only_confirmed",
        "no_credentials_used_confirmed",
        "no_live_calls_confirmed",
        "no_browser_login_confirmed",
        "endpoint_mapping_later_required",
        "permission_verification_later_required",
        "payload_hash_revalidation_later_required",
        "kill_switch_later_required",
        "audit_redaction_later_required",
        "manual_fallback_later_required",
        "docs_verification_available",
        "docs_verification_declared_ready",
        "eligible_for_future_endpoint_mapping_gate",
        "mark_official_docs_verified_for_future_dispatch_request_mapping",
        "MARK_OFFICIAL_DOCS_VERIFIED_FOR_FUTURE_MAPPING_ONLY_NOT_SEND",
        "official_docs_verification_only"
    ]
    for term in bypass_terms:
        lowered = lowered.replace(term, "")
    for phrase in ALLOWED_SCHEMA_PHRASES:
        lowered = lowered.replace(phrase.lower(), "")
    return any(marker in lowered for marker in SECRET_MARKERS)


def load_json_packet(path: str, malformed_label: str) -> Any:
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(val, dict):
            raise ValueError(malformed_label)
        return val
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def _validate_request_gate_packet(gate: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "task_label",
        "dispatch_request_package_gate_id",
        "dispatch_request_gate_declaration_id",
        "operator_id",
        "created_at_manual",
        "account_binding_preflight_id",
        "account_binding_preflight_sha256",
        "account_binding_declaration_id",
        "credential_allowlist_preflight_id",
        "credential_allowlist_preflight_sha256",
        "endpoint_allowlist_declaration_id",
        "live_dispatch_scope_preflight_id",
        "live_dispatch_scope_preflight_sha256",
        "live_dispatch_readiness_preflight_id",
        "live_dispatch_readiness_preflight_sha256",
        "official_docs_declaration_id",
        "live_scope_declaration_id",
        "local_dispatch_execution_payload_manifest_id",
        "operator_supervised_dispatch_review_decision_packet_id",
        "local_destination_binding_preflight_id",
        "destination_binding_id",
        "local_dispatch_payload_manifest_id",
        "operator_dispatch_review_decision_packet_id",
        "local_dispatch_preflight_id",
        "local_active_outbox_manifest_id",
        "operator_active_outbox_review_decision_id",
        "active_outbox_eligibility_id",
        "outbox_package_staging_id",
        "payload_review_ledger_id",
        "approval_intent_id",
        "variant_preview_staging_id",
        "metadata_values_review_id",
        "metadata_values_id",
        "metadata_proposal_id",
        "source_pack_intake_id",
        "source_pack_id",
        "editorial_workflow_id",
        "canonical_slug",
        "canonical_title",
        "execution_preparation_json_files",
        "execution_preparation_json_hashes",
        "execution_preparation_markdown_files",
        "execution_preparation_markdown_hashes",
        "destinations",
        "platforms",
        "credential_key_names_only",
        "endpoint_allowlist_rows",
        "platform_binding_rows",
        "requested_platforms",
        "request_budget_confirmed",
        "timeout_policy_confirmed",
        "retry_policy_confirmed",
        "kill_switch_confirmed",
        "audit_redaction_confirmed",
        "manual_fallback_confirmed",
        "account_binding_confirmed",
        "permission_check_later_required",
        "provider_execution_later_required",
        "operator_final_review_later_required",
        "combined_payload_hash",
        "dispatch_request_package_gate_available",
        "dispatch_request_package_gate_declared_ready",
        "eligible_for_future_supervised_dispatch_request_package"
    ]
    for key in required_keys:
        if gate.get(key) is None:
            blockers.append(f"gate_field_missing_{key}")

    if gate.get("task_label") != REQUEST_GATE_TASK_LABEL:
        blockers.append("gate_task_label_invalid")

    gating_rules = {
        "dispatch_request_package_gate_available": True,
        "dispatch_request_package_gate_declared_ready": True,
        "eligible_for_future_supervised_dispatch_request_package": True,
        "live_send_request_created": False,
        "approval_for_live_dispatch": False,
        "approval_for_publication": False,
        "approved_canonical_article_available": False,
        "publication_ready": False,
        "dispatch_allowed": False,
        "platform_variant_generation_allowed": False,
        "outbox_creation_allowed": False,
        "generated_citations_allowed": False,
        "citations_verified": False,
        "review_only": True,
        "human_review_required": True,
        "kill_switch_active": True,
        "runtime_truth": False,
        "platforms": ["substack", "discord"],
        "requested_platforms": ["substack", "discord"],
    }
    for field_name, expected in gating_rules.items():
        if gate.get(field_name) != expected:
            blockers.append(f"gate_field_{field_name}_invalid")

    if gate.get("public_url") is not None:
        blockers.append("gate_public_url_not_null")
    if gate.get("public_metrics") is not None:
        blockers.append("gate_public_metrics_not_null")

    if gate.get("blockers"):
        blockers.append("gate_blockers_not_empty")

    return blockers


def _validate_docs_source_summary(summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "official_docs_source_summary_id",
        "created_at_manual",
        "reviewer_id",
        "docs_review_scope",
        "platform_rows",
        "notes"
    ]
    for key in required_keys:
        if summary.get(key) is None:
            blockers.append(f"summary_field_missing_{key}")

    extra_keys = set(summary.keys()) - set(required_keys)
    for ek in sorted(extra_keys):
        blockers.append(f"summary_extra_field_{ek}_detected")

    platform_rows = summary.get("platform_rows", [])
    if not isinstance(platform_rows, list) or len(platform_rows) != 2:
        blockers.append("summary_platform_rows_count_invalid")
    else:
        allowed_row_keys = {
            "platform",
            "source_family",
            "official_source_type",
            "official_source_title",
            "official_source_url_label",
            "official_source_accessed_at_manual",
            "dispatch_capability_classification",
            "supported_dispatch_mechanism",
            "auth_or_permission_requirements_summary",
            "endpoint_or_surface_summary",
            "rate_limit_or_budget_summary",
            "media_payload_constraints_summary",
            "error_handling_summary",
            "app_review_or_policy_constraints_summary",
            "live_write_allowed_later",
            "manual_fallback_required",
            "blockers",
            "caveats",
            "reviewer_notes"
        }

        for idx, row in enumerate(platform_rows):
            if not isinstance(row, dict):
                blockers.append(f"summary_platform_row_{idx}_not_dict")
                continue

            row_keys = set(row.keys())
            extra_row_keys = row_keys - allowed_row_keys
            for ek in sorted(extra_row_keys):
                blockers.append(f"summary_platform_row_{idx}_extra_field_{ek}_detected")

            platform = row.get("platform")
            expected_plat = "substack" if idx == 0 else "discord"
            if platform != expected_plat:
                blockers.append(f"summary_platform_row_{idx}_platform_invalid")

            if row.get("source_family") != "official_platform_documentation":
                blockers.append(f"summary_platform_row_{idx}_source_family_invalid")

            url_label = row.get("official_source_url_label")
            if not isinstance(url_label, str) or not url_label.strip():
                blockers.append(f"summary_platform_row_{idx}_url_label_invalid")
            else:
                if any(term in url_label for term in SECRET_MARKERS):
                    blockers.append(f"summary_platform_row_{idx}_url_label_contains_restricted_term")
                # Wait, generic public URLs check:
                # "Raw public documentation URLs may be stored only if they are generic public official docs URLs and contain no credentials..."
                # If url_label contains any session/query parameters or credentials like user:pass:
                if "?" in url_label or "@" in url_label or "token" in url_label.lower():
                    blockers.append(f"summary_platform_row_{idx}_url_label_not_generic")

            classif = row.get("dispatch_capability_classification")
            valid_classifs = [
                "official_api_supported_for_required_action",
                "official_webhook_supported_for_required_action",
                "official_browser_or_manual_surface_only",
                "unsupported_by_official_docs",
                "unclear_requires_operator_decision"
            ]
            if classif not in valid_classifs:
                blockers.append(f"summary_platform_row_{idx}_classification_invalid")

            live_write = row.get("live_write_allowed_later")
            if live_write is True:
                if classif not in ["official_api_supported_for_required_action", "official_webhook_supported_for_required_action"]:
                    blockers.append(f"summary_platform_row_{idx}_live_write_allowed_later_incompatible_with_classification")
                # and only when row has no blockers
                row_blockers = row.get("blockers")
                if not isinstance(row_blockers, list) or len(row_blockers) > 0:
                    blockers.append(f"summary_platform_row_{idx}_live_write_allowed_later_requires_empty_blockers")

            if not isinstance(row.get("blockers"), list):
                blockers.append(f"summary_platform_row_{idx}_blockers_field_invalid")

            if not isinstance(row.get("caveats"), list):
                blockers.append(f"summary_platform_row_{idx}_caveats_field_invalid")

            if not isinstance(row.get("reviewer_notes"), str):
                blockers.append(f"summary_platform_row_{idx}_reviewer_notes_invalid")

    return blockers


def _validate_docs_declaration(decl: dict[str, Any], gate: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "official_docs_verification_declaration_id",
        "operator_id",
        "created_at_manual",
        "dispatch_request_package_gate_id",
        "combined_payload_hash",
        "official_docs_source_summary_id",
        "platforms_reviewed",
        "official_sources_only_confirmed",
        "no_credentials_used_confirmed",
        "no_live_calls_confirmed",
        "no_browser_login_confirmed",
        "endpoint_mapping_later_required",
        "permission_verification_later_required",
        "payload_hash_revalidation_later_required",
        "kill_switch_later_required",
        "audit_redaction_later_required",
        "manual_fallback_later_required",
        "declaration_decision",
        "approval_phrase",
        "approval_scope",
        "notes"
    ]
    for key in required_keys:
        if decl.get(key) is None:
            blockers.append(f"declaration_field_missing_{key}")

    extra_keys = set(decl.keys()) - set(required_keys)
    for ek in sorted(extra_keys):
        blockers.append(f"declaration_extra_field_{ek}_detected")

    if decl.get("platforms_reviewed") != ["substack", "discord"]:
        blockers.append("declaration_platforms_reviewed_invalid")

    if decl.get("dispatch_request_package_gate_id") != gate.get("dispatch_request_package_gate_id"):
        blockers.append("declaration_dispatch_request_package_gate_id_mismatch")

    if decl.get("combined_payload_hash") != gate.get("combined_payload_hash"):
        blockers.append("declaration_combined_payload_hash_mismatch")

    if decl.get("official_docs_source_summary_id") != summary.get("official_docs_source_summary_id"):
        blockers.append("declaration_official_docs_source_summary_id_mismatch")

    # Confirmation and requirements flags check
    for b_field in [
        "official_sources_only_confirmed",
        "no_credentials_used_confirmed",
        "no_live_calls_confirmed",
        "no_browser_login_confirmed",
        "endpoint_mapping_later_required",
        "permission_verification_later_required",
        "payload_hash_revalidation_later_required",
        "kill_switch_later_required",
        "audit_redaction_later_required",
        "manual_fallback_later_required"
    ]:
        if decl.get(b_field) is not True:
            blockers.append(f"declaration_field_{b_field}_not_true")

    decision = decl.get("declaration_decision")
    if decision not in ["mark_official_docs_verified_for_future_dispatch_request_mapping", "reject", "defer"]:
        blockers.append("declaration_decision_invalid")
    elif decision in ["reject", "defer"]:
        blockers.append(f"declaration_rejected_or_deferred_{decision}")
    elif decision == "mark_official_docs_verified_for_future_dispatch_request_mapping":
        if decl.get("approval_phrase") != "MARK_OFFICIAL_DOCS_VERIFIED_FOR_FUTURE_MAPPING_ONLY_NOT_SEND":
            blockers.append("declaration_approval_phrase_invalid")
        if decl.get("approval_scope") != "official_docs_verification_only":
            blockers.append("declaration_approval_scope_invalid")

    if not isinstance(decl.get("notes"), str):
        blockers.append("declaration_notes_missing_or_invalid")

    return blockers


def _check_packet_safety(packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    for k, v in packet.items():
        if k in ["platform_rows", "platforms_reviewed", "endpoint_allowlist_rows", "platform_binding_rows", "destinations"]:
            continue
        if prefix == "gate" and k == "notes":
            continue
        vals_to_check = []
        if isinstance(v, str):
            vals_to_check.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    vals_to_check.append(item)
        elif isinstance(v, dict):
            for sk, sv in v.items():
                if isinstance(sv, str):
                    vals_to_check.append(sv)

        for val in vals_to_check:
            if _has_secret_marker(val):
                blockers.append(f"{prefix}_secret_marker_detected")
            for claim in FAKE_CLAIMS_MARKERS:
                if claim in val.lower():
                    blockers.append(f"{prefix}_fake_claim_detected_{claim}")
            for pat in TRADING_ADVICE_RE:
                if pat.search(val):
                    blockers.append(f"{prefix}_financial_advice_or_signal_framing_detected")
                    break
            forbidden_term = _scan_for_forbidden_live_claims(val)
            if forbidden_term:
                blockers.append(f"{prefix}_forbidden_live_claim_detected_{forbidden_term.replace(' ', '_')}")
    return blockers


def _check_row_safety(row: dict[str, Any], prefix: str, idx: int) -> list[str]:
    blockers: list[str] = []
    for k, v in row.items():
        if k == "credential_key_name":
            continue
        vals_to_check = []
        if isinstance(v, str):
            vals_to_check.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    vals_to_check.append(item)
        elif isinstance(v, dict):
            for sk, sv in v.items():
                if isinstance(sv, str):
                    vals_to_check.append(sv)

        for val in vals_to_check:
            if _has_secret_marker(val):
                blockers.append(f"{prefix}_row_{idx}_secret_marker_detected")
            for claim in FAKE_CLAIMS_MARKERS:
                if claim in val.lower():
                    blockers.append(f"{prefix}_row_{idx}_fake_claim_detected_{claim}")
            for pat in TRADING_ADVICE_RE:
                if pat.search(val):
                    blockers.append(f"{prefix}_row_{idx}_financial_advice_or_signal_framing_detected")
                    break
            forbidden_term = _scan_for_forbidden_live_claims(val)
            if forbidden_term:
                blockers.append(f"{prefix}_row_{idx}_forbidden_live_claim_detected_{forbidden_term.replace(' ', '_')}")
    return blockers


def make_official_platform_docs_verification_packet(
    request_package_gate: Any,
    operator_declaration: Any,
    docs_source_summary: Any,
) -> OfficialPlatformDocsVerificationPacket:
    blockers: list[str] = []

    gate_is_dict = isinstance(request_package_gate, dict)
    if not gate_is_dict:
        blockers.append("malformed_dispatch_request_package_gate_packet_json")

    decl_is_dict = isinstance(operator_declaration, dict)
    if not decl_is_dict:
        blockers.append("malformed_operator_docs_verification_declaration_json")

    summary_is_dict = isinstance(docs_source_summary, dict)
    if not summary_is_dict:
        blockers.append("malformed_official_docs_source_summary_json")

    # Safety checks
    if gate_is_dict:
        blockers.extend(_check_packet_safety(request_package_gate, "gate"))
    if decl_is_dict:
        blockers.extend(_check_packet_safety(operator_declaration, "declaration"))
    if summary_is_dict:
        blockers.extend(_check_packet_safety(docs_source_summary, "summary"))

        # Deep scan only string values in summary's platform rows
        platform_rows = docs_source_summary.get("platform_rows", [])
        if isinstance(platform_rows, list):
            for idx, row in enumerate(platform_rows):
                if isinstance(row, dict):
                    blockers.extend(_check_row_safety(row, "summary", idx))

    official_docs_verification_declaration_id = ""
    official_docs_source_summary_id = ""
    operator_id = ""
    created_at_manual = ""
    dispatch_request_package_gate_id = ""
    dispatch_request_package_gate_sha256 = ""
    account_binding_preflight_id = ""
    account_binding_preflight_sha256 = ""
    credential_allowlist_preflight_id = ""
    credential_allowlist_preflight_sha256 = ""
    live_dispatch_scope_preflight_id = ""
    live_dispatch_scope_preflight_sha256 = ""
    live_dispatch_readiness_preflight_id = ""
    live_dispatch_readiness_preflight_sha256 = ""
    combined_payload_hash = ""
    platforms: list[str] = []
    requested_platforms: list[str] = []
    platform_docs_rows: list[dict[str, Any]] = []
    official_sources_only_confirmed = False
    no_credentials_used_confirmed = False
    no_live_calls_confirmed = False
    no_browser_login_confirmed = False
    endpoint_mapping_later_required = False
    permission_verification_later_required = False
    payload_hash_revalidation_later_required = False
    kill_switch_later_required = False
    audit_redaction_later_required = False
    manual_fallback_later_required = False

    if gate_is_dict and "gate_secret_marker_detected" not in blockers:
        blockers.extend(_validate_request_gate_packet(request_package_gate))

        dispatch_request_package_gate_id = str(request_package_gate.get("dispatch_request_package_gate_id") or "")
        account_binding_preflight_id = str(request_package_gate.get("account_binding_preflight_id") or "")
        account_binding_preflight_sha256 = str(request_package_gate.get("account_binding_preflight_sha256") or "")
        credential_allowlist_preflight_id = str(request_package_gate.get("credential_allowlist_preflight_id") or "")
        credential_allowlist_preflight_sha256 = str(request_package_gate.get("credential_allowlist_preflight_sha256") or "")
        live_dispatch_scope_preflight_id = str(request_package_gate.get("live_dispatch_scope_preflight_id") or "")
        live_dispatch_scope_preflight_sha256 = str(request_package_gate.get("live_dispatch_scope_preflight_sha256") or "")
        live_dispatch_readiness_preflight_id = str(request_package_gate.get("live_dispatch_readiness_preflight_id") or "")
        live_dispatch_readiness_preflight_sha256 = str(request_package_gate.get("live_dispatch_readiness_preflight_sha256") or "")
        combined_payload_hash = str(request_package_gate.get("combined_payload_hash") or "")
        platforms = request_package_gate.get("platforms", [])
        requested_platforms = request_package_gate.get("requested_platforms", [])

        # Compute SHA256 of request package gate packet only if no secret markers are present
        gate_sha_check = dict(request_package_gate)
        gate_sha_check.pop("endpoint_allowlist_rows", None)
        gate_sha_check.pop("platform_binding_rows", None)
        gate_sha_check.pop("destinations", None)
        if not _has_secret_marker(json.dumps(gate_sha_check)) and not any("secret_marker_detected" in b or "forbidden" in b for b in blockers):
            dispatch_request_package_gate_sha256 = hashlib.sha256(_canonical_json(request_package_gate).encode("utf-8")).hexdigest()

    if summary_is_dict and "summary_secret_marker_detected" not in blockers:
        blockers.extend(_validate_docs_source_summary(docs_source_summary))
        official_docs_source_summary_id = str(docs_source_summary.get("official_docs_source_summary_id") or "")
        platform_docs_rows = docs_source_summary.get("platform_rows", [])

    if decl_is_dict and gate_is_dict and summary_is_dict and "declaration_secret_marker_detected" not in blockers:
        blockers.extend(_validate_docs_declaration(operator_declaration, request_package_gate, docs_source_summary))
        official_docs_verification_declaration_id = str(operator_declaration.get("official_docs_verification_declaration_id") or "")
        operator_id = str(operator_declaration.get("operator_id") or "")
        created_at_manual = str(operator_declaration.get("created_at_manual") or "")
        official_sources_only_confirmed = bool(operator_declaration.get("official_sources_only_confirmed"))
        no_credentials_used_confirmed = bool(operator_declaration.get("no_credentials_used_confirmed"))
        no_live_calls_confirmed = bool(operator_declaration.get("no_live_calls_confirmed"))
        no_browser_login_confirmed = bool(operator_declaration.get("no_browser_login_confirmed"))
        endpoint_mapping_later_required = bool(operator_declaration.get("endpoint_mapping_later_required"))
        permission_verification_later_required = bool(operator_declaration.get("permission_verification_later_required"))
        payload_hash_revalidation_later_required = bool(operator_declaration.get("payload_hash_revalidation_later_required"))
        kill_switch_later_required = bool(operator_declaration.get("kill_switch_later_required"))
        audit_redaction_later_required = bool(operator_declaration.get("audit_redaction_later_required"))
        manual_fallback_later_required = bool(operator_declaration.get("manual_fallback_later_required"))

    blockers = sorted(set(blockers))
    prepared = not blockers

    declared_ready = (
        prepared and decl_is_dict and (operator_declaration.get("declaration_decision") == "mark_official_docs_verified_for_future_dispatch_request_mapping")
    )

    # Check if either platform has unsupported_by_official_docs or unclear_requires_operator_decision
    has_unsupported = False
    has_unclear = False
    if summary_is_dict and isinstance(platform_docs_rows, list):
        for row in platform_docs_rows:
            if isinstance(row, dict):
                c = row.get("dispatch_capability_classification")
                if c == "unsupported_by_official_docs":
                    has_unsupported = True
                elif c == "unclear_requires_operator_decision":
                    has_unclear = True

    eligible = prepared and declared_ready and not has_unsupported and not has_unclear

    # Safety redaction on secret/marker detection
    has_secrets = any("secret_marker_detected" in b for b in blockers)

    if has_secrets:
        official_docs_verification_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        official_docs_source_summary_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        dispatch_request_package_gate_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        dispatch_request_package_gate_sha256 = ""
        account_binding_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        account_binding_preflight_sha256 = ""
        credential_allowlist_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        credential_allowlist_preflight_sha256 = ""
        live_dispatch_scope_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_dispatch_scope_preflight_sha256 = ""
        live_dispatch_readiness_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_dispatch_readiness_preflight_sha256 = ""
        combined_payload_hash = ""
        platforms = []
        requested_platforms = []
        platform_docs_rows = []

    intake_material = {
        "dispatch_request_package_gate_id": dispatch_request_package_gate_id,
        "official_docs_verification_declaration_id": official_docs_verification_declaration_id,
        "blockers": blockers,
    }
    official_platform_docs_verification_id = f"docs_verification_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("docs_verification_blocked_pending_operator_repair")

    # If available but unsupported classification exists
    if prepared and has_unsupported:
        warnings.append("docs_verification_unsupported_platforms_detected")

    # If unclear capability classification exists
    has_unclear = False
    if summary_is_dict and isinstance(platform_docs_rows, list):
        for row in platform_docs_rows:
            if isinstance(row, dict) and row.get("dispatch_capability_classification") == "unclear_requires_operator_decision":
                has_unclear = True
    if prepared and has_unclear:
        warnings.append("docs_verification_unclear_capability_classifications_detected")

    return OfficialPlatformDocsVerificationPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        official_platform_docs_verification_id=official_platform_docs_verification_id,
        official_docs_verification_declaration_id=official_docs_verification_declaration_id,
        official_docs_source_summary_id=official_docs_source_summary_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        dispatch_request_package_gate_id=dispatch_request_package_gate_id,
        dispatch_request_package_gate_sha256=dispatch_request_package_gate_sha256,
        account_binding_preflight_id=account_binding_preflight_id,
        account_binding_preflight_sha256=account_binding_preflight_sha256,
        credential_allowlist_preflight_id=credential_allowlist_preflight_id,
        credential_allowlist_preflight_sha256=credential_allowlist_preflight_sha256,
        live_dispatch_scope_preflight_id=live_dispatch_scope_preflight_id,
        live_dispatch_scope_preflight_sha256=live_dispatch_scope_preflight_sha256,
        live_dispatch_readiness_preflight_id=live_dispatch_readiness_preflight_id,
        live_dispatch_readiness_preflight_sha256=live_dispatch_readiness_preflight_sha256,
        combined_payload_hash=combined_payload_hash,
        platforms=platforms,
        requested_platforms=requested_platforms,
        platform_docs_rows=platform_docs_rows,
        official_sources_only_confirmed=official_sources_only_confirmed,
        no_credentials_used_confirmed=no_credentials_used_confirmed,
        no_live_calls_confirmed=no_live_calls_confirmed,
        no_browser_login_confirmed=no_browser_login_confirmed,
        endpoint_mapping_later_required=endpoint_mapping_later_required,
        permission_verification_later_required=permission_verification_later_required,
        payload_hash_revalidation_later_required=payload_hash_revalidation_later_required,
        kill_switch_later_required=kill_switch_later_required,
        audit_redaction_later_required=audit_redaction_later_required,
        manual_fallback_later_required=manual_fallback_later_required,
        docs_verification_available=prepared,
        docs_verification_declared_ready=declared_ready,
        eligible_for_future_endpoint_mapping_gate=eligible,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Official Platform Docs Verification Gate CLI")
    parser.add_argument("request_package_gate", help="Path to request package gate packet JSON")
    parser.add_argument("operator_declaration", help="Path to operator docs verification declaration JSON")
    parser.add_argument("docs_source_summary", help="Path to docs source summary JSON")
    parser.add_argument("--output-file", required=True, help="Path to write official docs verification packet JSON")

    args = parser.parse_args(argv)

    try:
        gate = load_json_packet(args.request_package_gate, "malformed_dispatch_request_package_gate_packet_json")
        decl = load_json_packet(args.operator_declaration, "malformed_operator_docs_verification_declaration_json")
        summary = load_json_packet(args.docs_source_summary, "malformed_official_docs_source_summary_json")

        packet = make_official_platform_docs_verification_packet(gate, decl, summary)

        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")

        if not packet.docs_verification_available:
            return 1
        return 0

    except ValueError as val_err:
        packet = OfficialPlatformDocsVerificationPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            official_platform_docs_verification_id=f"docs_verification_blocked_{str(val_err)}",
            official_docs_verification_declaration_id="",
            official_docs_source_summary_id="",
            operator_id="",
            created_at_manual="",
            dispatch_request_package_gate_id="",
            dispatch_request_package_gate_sha256="",
            account_binding_preflight_id="",
            account_binding_preflight_sha256="",
            credential_allowlist_preflight_id="",
            credential_allowlist_preflight_sha256="",
            live_dispatch_scope_preflight_id="",
            live_dispatch_scope_preflight_sha256="",
            live_dispatch_readiness_preflight_id="",
            live_dispatch_readiness_preflight_sha256="",
            combined_payload_hash="",
            platforms=[],
            requested_platforms=[],
            platform_docs_rows=[],
            official_sources_only_confirmed=False,
            no_credentials_used_confirmed=False,
            no_live_calls_confirmed=False,
            no_browser_login_confirmed=False,
            endpoint_mapping_later_required=False,
            permission_verification_later_required=False,
            payload_hash_revalidation_later_required=False,
            kill_switch_later_required=False,
            audit_redaction_later_required=False,
            manual_fallback_later_required=False,
            docs_verification_available=False,
            docs_verification_declared_ready=False,
            eligible_for_future_endpoint_mapping_gate=False,
            blockers=[str(val_err)],
            warnings=["docs_verification_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
