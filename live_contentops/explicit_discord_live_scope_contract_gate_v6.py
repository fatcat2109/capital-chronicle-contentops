"""V6 Explicit Discord Live Scope Contract Gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_EXPLICIT_DISCORD_LIVE_SCOPE_CONTRACT_GATE_FROM_SUPERVISED_LIVE_PILOT_PLANNING_V0"
PILOT_PLANNING_TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_PILOT_GATE_PLANNING_FROM_FINAL_MANUAL_REVIEW_V0"
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
    "TASK_CONTENTOPS_V6_LIVE_DISPATCH_ACCOUNT_BINDING_PREFLIGHT_FROM_CREDENTIAL_ALLOWLIST_V0",
    "Substack official API publishing documentation not verified from official public docs; manual/browser fallback or later operator-provided official source required.",
    "substack_official_api_docs_unverified",
    "operator_declared_platform_capability_lane_split_only_not_send",
    "future_webhook_endpoint_mapping_candidate",
    "manual_browser_or_manual_export_fallback_required",
    "mark_platform_capability_lane_split_ready",
    "MARK_PLATFORM_CAPABILITY_LANE_SPLIT_READY_ONLY_NOT_SEND",
    "platform_capability_lane_split_only",
    "docs_verification_unclear_capability_classifications_detected",
    "sample_packet_non_runtime",
    "platform_capability_lane_split_id",
    "lane_split_declaration_id",
    "TASK_CONTENTOPS_V6_OFFICIAL_PLATFORM_DOCS_VERIFICATION_FOR_LIVE_DISPATCH_REQUEST_GATE_V0",
    "TASK_CONTENTOPS_V6_PLATFORM_CAPABILITY_LANE_SPLIT_FROM_OFFICIAL_DOCS_V0",
    "lane_split_decl_",
    "operator_declared_discord_endpoint_mapping_labels_only_not_request",
    "discord_execute_webhook_label_only",
    "discord_operator_declared_webhook_host_label",
    "discord_operator_declared_webhook_path_label",
    "webhook_method_label_only",
    "mark_discord_endpoint_mapping_preflight_ready",
    "MARK_DISCORD_ENDPOINT_MAPPING_PREFLIGHT_READY_ONLY_NOT_SEND",
    "discord_endpoint_mapping_preflight_only",
    "discord_endpoint_mapping_preflight_id",
    "discord_endpoint_mapping_declaration_id",
    "eligible_for_discord_webhook_value_binding_gate",
    "TASK_CONTENTOPS_V6_DISCORD_ENDPOINT_MAPPING_PREFLIGHT_FROM_CAPABILITY_LANE_SPLIT_V0",
    "discord_endpoint_decl_",
    "discord_endpoint_preflight_",
    "Verified Discord label-only endpoint mapping.",
    "Verified capability split lanes.",
    "operator_declared_discord_webhook_value_binding_presence_only_not_value",
    "discord_webhook_value_binding_preflight_only",
    "mark_discord_webhook_value_binding_preflight_ready",
    "MARK_DISCORD_WEBHOOK_VALUE_BINDING_PREFLIGHT_READY_ONLY_NOT_SEND",
    "discord_webhook_value_binding_declaration_id",
    "discord_webhook_value_binding_preflight_id",
    "eligible_for_discord_permission_probe_gate",
    "discord_webhook_value_binding_preflight_available",
    "discord_webhook_value_binding_preflight_declared_ready",
    "discord_webhook_url_secret_value_later",
    "process_env_exact_key_membership_only",
    "discord_credential_presence_deferred",
    "discord_credential_presence_missing",
    "discord_webhook_value_binding_decl_",
    "discord_webhook_value_binding_preflight_",
    "Verified Discord webhook value presence binding.",
    "operator_declared_discord_permission_probe_preflight_only_not_call",
    "discord_permission_probe_preflight_only",
    "mark_discord_permission_probe_preflight_ready",
    "MARK_DISCORD_PERMISSION_PROBE_PREFLIGHT_READY_ONLY_NOT_CALL",
    "discord_permission_probe_declaration_id",
    "discord_permission_probe_preflight_id",
    "eligible_for_discord_dry_run_payload_gate",
    "permission_probe_preflight_available",
    "permission_probe_preflight_declared_ready",
    "discord_webhook_permission_probe_later_not_now",
    "discord_permission_probe_decl_",
    "discord_permission_probe_preflight_",
    "Verified Discord webhook permission probe.",
    "TASK_CONTENTOPS_V6_DISCORD_WEBHOOK_VALUE_BINDING_PREFLIGHT_FROM_ENDPOINT_MAPPING_V0",
    "TASK_CONTENTOPS_V6_DISCORD_PERMISSION_PROBE_PREFLIGHT_FROM_WEBHOOK_VALUE_BINDING_V0",
    "operator_declared_discord_dry_run_payload_gate_only_not_send",
    "discord_dry_run_payload_gate_only",
    "mark_discord_dry_run_payload_gate_ready",
    "MARK_DISCORD_DRY_RUN_PAYLOAD_GATE_READY_ONLY_NOT_SEND",
    "discord_dry_run_payload_declaration_id",
    "discord_dry_run_payload_gate_id",
    "eligible_for_operator_payload_review_gate",
    "discord_dry_run_payload_gate_available",
    "discord_dry_run_payload_gate_declared_ready",
    "discord_text_or_embed_preview_non_runtime",
    "operator_supplied_preview_text_only",
    "discord_dry_run_payload_decl_",
    "discord_dry_run_payload_gate_",
    "Verified Discord dry-run payload gate.",
    "TASK_CONTENTOPS_V6_DISCORD_DRY_RUN_PAYLOAD_GATE_FROM_PERMISSION_PROBE_PREFLIGHT_V0",
    "operator_declared_discord_payload_review_gate_only_not_send",
    "discord_operator_payload_review_gate_only",
    "mark_discord_operator_payload_review_gate_ready",
    "MARK_DISCORD_OPERATOR_PAYLOAD_REVIEW_GATE_READY_ONLY_NOT_SEND",
    "discord_operator_payload_review_declaration_id",
    "discord_operator_payload_review_gate_id",
    "eligible_for_discord_request_policy_gate",
    "discord_operator_payload_review_gate_available",
    "discord_operator_payload_review_gate_declared_ready",
    "approve_payload_hash_for_next_local_gate_only",
    "discord_operator_payload_review_decl_",
    "discord_operator_payload_review_gate_",
    "Verified Discord operator payload review gate.",
    "TASK_CONTENTOPS_V6_DISCORD_OPERATOR_PAYLOAD_REVIEW_GATE_FROM_DRY_RUN_PAYLOAD_V0",
    "operator_declared_discord_request_policy_gate_only_not_request",
    "discord_request_policy_gate_only",
    "mark_discord_request_policy_gate_ready",
    "MARK_DISCORD_REQUEST_POLICY_GATE_READY_ONLY_NOT_REQUEST",
    "discord_request_policy_declaration_id",
    "discord_request_policy_gate_id",
    "eligible_for_discord_supervised_request_package_staging_gate",
    "discord_request_policy_gate_available",
    "discord_request_policy_gate_declared_ready",
    "approve_request_policy_for_next_local_gate_only",
    "single_supervised_request_later",
    "bounded_timeout_required_later",
    "no_hidden_retry",
    "discord_request_policy_decl_",
    "discord_request_policy_gate_",
    "Verified Discord request policy gate.",
    "TASK_CONTENTOPS_V6_DISCORD_REQUEST_POLICY_GATE_FROM_OPERATOR_PAYLOAD_REVIEW_V0",
    "operator_declared_discord_supervised_request_package_staging_only_not_request",
    "discord_supervised_request_package_staging_only",
    "mark_discord_supervised_request_package_staging_ready",
    "MARK_DISCORD_SUPERVISED_REQUEST_PACKAGE_STAGING_READY_ONLY_NOT_REQUEST",
    "discord_supervised_request_package_staging_declaration_id",
    "discord_supervised_request_package_staging_id",
    "eligible_for_discord_final_manual_execution_review_gate",
    "discord_supervised_request_package_staging_available",
    "discord_supervised_request_package_staging_declared_ready",
    "approve_non_executable_request_package_shell_for_next_local_gate_only",
    "non_executable_discord_supervised_request_package_shell",
    "discord_supervised_request_package_staging_decl_",
    "discord_supervised_request_package_staging_gate_",
    "Verified Discord supervised request package staging.",
    "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_REQUEST_PACKAGE_STAGING_FROM_REQUEST_POLICY_V0",
    "operator_declared_discord_final_manual_execution_review_only_not_live",
    "discord_final_manual_execution_review_only",
    "mark_discord_final_manual_execution_review_ready",
    "MARK_DISCORD_FINAL_MANUAL_EXECUTION_REVIEW_READY_ONLY_NOT_LIVE",
    "discord_final_manual_execution_review_declaration_id",
    "discord_final_manual_execution_review_gate_id",
    "discord_final_manual_execution_review_id",
    "eligible_for_discord_supervised_live_pilot_gate_planning",
    "approve_final_manual_execution_review_for_future_supervised_live_pilot_gate_only",
    "discord_final_manual_execution_review_decl_",
    "discord_final_manual_execution_review_gate_",
    "Verified Discord final manual execution review.",
    "TASK_CONTENTOPS_V6_DISCORD_FINAL_MANUAL_EXECUTION_REVIEW_FROM_REQUEST_PACKAGE_STAGING_V0",
    "operator_declared_discord_supervised_live_pilot_gate_planning_only_not_live",
    "future_supervised_discord_webhook_send_pilot_not_now",
    "single_supervised_request_future_scope",
    "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
    "discord_supervised_live_pilot_gate_planning_only",
    "mark_discord_supervised_live_pilot_gate_planning_ready",
    "MARK_DISCORD_SUPERVISED_LIVE_PILOT_GATE_PLANNING_READY_ONLY_NOT_LIVE",
    "discord_supervised_live_pilot_gate_planning_declaration_id",
    "discord_supervised_live_pilot_gate_planning_id",
    "eligible_for_future_explicit_discord_live_scope_contract_gate",
    "approve_live_pilot_plan_for_future_explicit_live_scope_only",
    "discord_supervised_live_pilot_gate_planning_decl_",
    "discord_supervised_live_pilot_gate_planning_gate_",
    "Verified Discord supervised live pilot planning.",
    "TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_PILOT_GATE_PLANNING_FROM_FINAL_MANUAL_REVIEW_V0",
    "operator_declared_explicit_discord_live_scope_contract_only_not_live",
    "supervised_discord_webhook_send_pilot_future_scope_only",
    "discord_webhook",
    "scoped_action_class",
    "scoped_platform_family",
    "scoped_endpoint_family_label",
    "scoped_credential_key_name",
    "scoped_payload_hash",
    "scoped_request_budget",
    "scoped_max_request_count",
    "scoped_timeout_seconds",
    "scoped_max_retries",
    "scoped_hidden_retry_allowed",
    "scoped_idempotency_required",
    "scoped_kill_switch_required",
    "scoped_audit_redaction_required",
    "scoped_manual_fallback_required",
    "scoped_permission_probe_required_later",
    "scoped_payload_hash_revalidation_required",
    "scoped_exact_operator_approval_required_later",
    "scoped_destination_binding_required_later",
    "scoped_request_artifact_creation_required_later",
    "approve_explicit_discord_live_scope_contract_for_future_materialization_only",
    "next_supervised_live_pilot_materialization_required",
    "explicit_discord_live_scope_contract_gate_only",
    "explicit_discord_live_scope_contract_gate_available",
    "explicit_discord_live_scope_contract_gate_declared_ready",
    "eligible_for_supervised_live_pilot_materialization_gate",
    "mark_explicit_discord_live_scope_contract_gate_ready",
    "MARK_EXPLICIT_DISCORD_LIVE_SCOPE_CONTRACT_READY_ONLY_NOT_LIVE",
    "explicit_discord_live_scope_contract_declaration_id",
    "explicit_discord_live_scope_contract_gate_id",
    "Verified explicit Discord live scope contract.",
    "TASK_CONTENTOPS_V6_EXPLICIT_DISCORD_LIVE_SCOPE_CONTRACT_GATE_FROM_SUPERVISED_LIVE_PILOT_PLANNING_V0"
)


@dataclass(frozen=True)
class ExplicitDiscordLiveScopeContractGatePacket:
    schema_version: str
    task_label: str
    explicit_discord_live_scope_contract_gate_id: str
    explicit_discord_live_scope_contract_declaration_id: str
    operator_id: str
    created_at_manual: str
    discord_supervised_live_pilot_gate_planning_id: str
    discord_final_manual_execution_review_id: str
    discord_supervised_request_package_staging_id: str
    discord_request_policy_gate_id: str
    discord_operator_payload_review_gate_id: str
    discord_dry_run_payload_gate_id: str
    discord_permission_probe_preflight_id: str
    discord_webhook_value_binding_preflight_id: str
    discord_endpoint_mapping_preflight_id: str
    platform_capability_lane_split_id: str
    official_platform_docs_verification_id: str
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
    platform: str
    scoped_action_class: str
    scoped_platform_family: str
    scoped_endpoint_family_label: str
    scoped_credential_key_name: str
    scoped_payload_hash: str
    scoped_request_budget: str
    scoped_max_request_count: int
    scoped_timeout_seconds: int
    scoped_max_retries: int
    scoped_hidden_retry_allowed: bool
    scoped_idempotency_required: bool
    scoped_kill_switch_required: bool
    scoped_audit_redaction_required: bool
    scoped_manual_fallback_required: bool
    scoped_permission_probe_required_later: bool
    scoped_payload_hash_revalidation_required: bool
    scoped_exact_operator_approval_required_later: bool
    scoped_destination_binding_required_later: bool
    scoped_request_artifact_creation_required_later: bool
    operator_live_scope_contract_decision: str
    live_dispatch_approval_granted: bool
    publication_approval_granted: bool
    executable_request_artifact_creation_allowed: bool
    webhook_value_read_allowed: bool
    discord_api_call_allowed: bool
    webhook_send_test_allowed: bool
    endpoint_url_value_allowed: bool
    channel_identity_value_allowed: bool
    http_headers_included: bool
    http_body_included: bool
    curl_command_included: bool
    browser_instruction_included: bool
    public_url_included: bool
    metrics_included: bool
    explicit_discord_live_scope_contract_gate_available: bool
    explicit_discord_live_scope_contract_gate_declared_ready: bool
    eligible_for_supervised_live_pilot_materialization_gate: bool
    eligible_for_full_live_dispatch_endpoint_mapping_gate: bool
    next_supervised_live_pilot_materialization_required: bool
    substack_manual_fallback_required: bool
    all_platforms_endpoint_mapping_ready: bool
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
        "task_contentops_v6_explicit_discord_live_scope_contract_gate_from_supervised_live_pilot_planning_v0",
        "task_contentops_v6_discord_supervised_live_pilot_gate_planning_from_final_manual_review_v0",
        "explicit_discord_live_scope_contract_gate_id",
        "explicit_discord_live_scope_contract_declaration_id",
        "discord_supervised_live_pilot_gate_planning_id",
        "discord_final_manual_execution_review_id",
        "discord_supervised_request_package_staging_id",
        "discord_request_policy_gate_id",
        "discord_operator_payload_review_gate_id",
        "discord_dry_run_payload_gate_id",
        "discord_permission_probe_preflight_id",
        "discord_webhook_value_binding_preflight_id",
        "discord_endpoint_mapping_preflight_id",
        "platform_capability_lane_split_id",
        "official_platform_docs_verification_id",
        "dispatch_request_package_gate_id",
        "account_binding_preflight_id",
        "credential_allowlist_preflight_id",
        "live_dispatch_scope_preflight_id",
        "live_dispatch_readiness_preflight_id"
    ]
    for term in bypass_terms:
        lowered = lowered.replace(term, "")
    for phrase in sorted(ALLOWED_SCHEMA_PHRASES, key=len, reverse=True):
        lowered = lowered.replace(phrase.lower(), "")
    return any(marker in lowered for marker in SECRET_MARKERS)


def _scan_for_forbidden_live_claims(text: str) -> str | None:
    lowered = text.lower()
    compound_forbidden = [
        "api_endpoint", "api endpoint", "endpoint_path", "endpoint path",
        "request_payload", "request payload", "payload_body", "payload body",
        "raw_copied_docs", "raw copied docs", "copied_docs", "copied docs",
        "raw_docs", "raw docs", "live_instructions", "live instructions",
        "live_instruction", "live instruction", "send_instruction", "send instruction",
        "dispatch_instruction", "dispatch instruction", "platform_live", "platform live",
        "live_dispatch", "live dispatch", "live_send", "live send", "send_now", "send now",
        "publish_now", "publish now"
    ]
    for term in compound_forbidden:
        if term in lowered:
            return term

    for phrase in sorted(ALLOWED_SCHEMA_PHRASES, key=len, reverse=True):
        lowered = lowered.replace(phrase.lower(), "")
    for term in FORBIDDEN_LIVE_CLAIMS:
        if term in lowered:
            return term
    return None


def _check_packet_safety(packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    for k, v in packet.items():
        if k in ["platform_lane_rows", "platforms_reviewed", "platform_docs_rows"]:
            continue
        if prefix == "preflight" and k == "notes":
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


def load_json_packet(path: str, malformed_label: str) -> Any:
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(val, dict):
            raise ValueError(malformed_label)
        return val
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def _validate_preflight_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    if packet.get("task_label") != PILOT_PLANNING_TASK_LABEL:
        blockers.append("preflight_task_label_invalid")

    if packet.get("discord_supervised_live_pilot_gate_planning_available") is not True:
        blockers.append("preflight_not_available")

    if packet.get("discord_supervised_live_pilot_gate_planning_declared_ready") is not True:
        blockers.append("preflight_not_declared_ready")

    if packet.get("eligible_for_future_explicit_discord_live_scope_contract_gate") is not True:
        blockers.append("preflight_eligible_for_future_explicit_discord_live_scope_contract_gate_invalid")

    gating_rules = {
        "eligible_for_full_live_dispatch_endpoint_mapping_gate": False,
        "all_platforms_endpoint_mapping_ready": False,
        "platform": "discord",
        "planned_action_class": "future_supervised_discord_webhook_send_pilot_not_now",
        "planned_endpoint_family_label": "discord_execute_webhook_label_only",
        "planned_credential_key_name": "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK",
        "planned_request_budget": "single_supervised_request_future_scope",
        "planned_max_request_count": 1,
        "planned_max_retries": 0,
        "planned_hidden_retry_allowed": False,
        "planned_idempotency_required": True,
        "planned_kill_switch_required": True,
        "planned_audit_redaction_required": True,
        "planned_manual_fallback_required": True,
        "planned_permission_probe_required_later": True,
        "planned_payload_hash_revalidation_required": True,
        "planned_exact_operator_approval_required_later": True,
        "operator_live_pilot_planning_decision": "approve_live_pilot_plan_for_future_explicit_live_scope_only",
        "live_dispatch_approval_granted": False,
        "publication_approval_granted": False,
        "executable_request_artifact_creation_allowed": False,
        "webhook_value_read_allowed": False,
        "discord_api_call_allowed": False,
        "webhook_send_test_allowed": False,
        "endpoint_url_value_allowed": False,
        "channel_identity_value_allowed": False,
        "http_headers_included": False,
        "http_body_included": False,
        "curl_command_included": False,
        "browser_instruction_included": False,
        "public_url_included": False,
        "metrics_included": False,
        "next_explicit_live_scope_required": True,
        "substack_manual_fallback_required": True,
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
    }
    for field_name, expected in gating_rules.items():
        if packet.get(field_name) != expected:
            blockers.append(f"preflight_field_{field_name}_invalid")

    t_sec = packet.get("planned_timeout_seconds")
    if not isinstance(t_sec, int) or isinstance(t_sec, bool) or t_sec < 5 or t_sec > 30:
        blockers.append("preflight_planned_timeout_seconds_invalid")

    if packet.get("public_url") is not None:
        blockers.append("preflight_public_url_not_null")
    if packet.get("public_metrics") is not None:
        blockers.append("preflight_public_metrics_not_null")

    if packet.get("blockers"):
        blockers.append("preflight_blockers_not_empty")

    if not packet.get("planned_payload_hash"):
        blockers.append("preflight_planned_payload_hash_missing")

    required_ids = [
        "discord_supervised_live_pilot_gate_planning_id",
        "discord_final_manual_execution_review_id",
        "discord_supervised_request_package_staging_id",
        "discord_request_policy_gate_id",
        "discord_operator_payload_review_gate_id",
        "discord_dry_run_payload_gate_id",
        "discord_permission_probe_preflight_id",
        "discord_webhook_value_binding_preflight_id",
        "discord_endpoint_mapping_preflight_id",
        "platform_capability_lane_split_id",
        "official_platform_docs_verification_id",
        "dispatch_request_package_gate_id",
        "dispatch_request_package_gate_sha256",
        "account_binding_preflight_id",
        "account_binding_preflight_sha256",
        "credential_allowlist_preflight_id",
        "credential_allowlist_preflight_sha256",
        "live_dispatch_scope_preflight_id",
        "live_dispatch_scope_preflight_sha256",
        "live_dispatch_readiness_preflight_id",
        "live_dispatch_readiness_preflight_sha256",
        "combined_payload_hash"
    ]
    for rid in required_ids:
        if not packet.get(rid):
            blockers.append(f"preflight_id_{rid}_missing")

    return blockers


def _validate_declaration(decl: dict[str, Any], preflight: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "explicit_discord_live_scope_contract_declaration_id",
        "operator_id",
        "created_at_manual",
        "discord_supervised_live_pilot_gate_planning_id",
        "discord_final_manual_execution_review_id",
        "discord_supervised_request_package_staging_id",
        "discord_request_policy_gate_id",
        "discord_operator_payload_review_gate_id",
        "discord_dry_run_payload_gate_id",
        "discord_permission_probe_preflight_id",
        "discord_webhook_value_binding_preflight_id",
        "discord_endpoint_mapping_preflight_id",
        "platform_capability_lane_split_id",
        "official_platform_docs_verification_id",
        "dispatch_request_package_gate_id",
        "combined_payload_hash",
        "platform",
        "live_scope_contract_mode",
        "scoped_action_class",
        "scoped_platform_family",
        "scoped_endpoint_family_label",
        "scoped_credential_key_name",
        "scoped_payload_hash",
        "scoped_request_budget",
        "scoped_max_request_count",
        "scoped_timeout_seconds",
        "scoped_max_retries",
        "scoped_hidden_retry_allowed",
        "scoped_idempotency_required",
        "scoped_kill_switch_required",
        "scoped_audit_redaction_required",
        "scoped_manual_fallback_required",
        "scoped_permission_probe_required_later",
        "scoped_payload_hash_revalidation_required",
        "scoped_exact_operator_approval_required_later",
        "scoped_destination_binding_required_later",
        "scoped_request_artifact_creation_required_later",
        "live_dispatch_approval_granted",
        "publication_approval_granted",
        "executable_request_artifact_creation_allowed",
        "webhook_value_read_allowed",
        "discord_api_call_allowed",
        "webhook_send_test_allowed",
        "endpoint_url_value_allowed",
        "channel_identity_value_allowed",
        "http_headers_included",
        "http_body_included",
        "curl_command_included",
        "browser_instruction_included",
        "public_url_included",
        "metrics_included",
        "operator_live_scope_contract_decision",
        "next_supervised_live_pilot_materialization_required",
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

    if decl.get("live_scope_contract_mode") != "operator_declared_explicit_discord_live_scope_contract_only_not_live":
        blockers.append("declaration_live_scope_contract_mode_invalid")

    if decl.get("platform") != "discord":
        blockers.append("declaration_platform_invalid")

    if decl.get("scoped_action_class") != "supervised_discord_webhook_send_pilot_future_scope_only":
        blockers.append("declaration_scoped_action_class_invalid")

    if decl.get("scoped_platform_family") != "discord_webhook":
        blockers.append("declaration_scoped_platform_family_invalid")

    if decl.get("scoped_endpoint_family_label") != "discord_execute_webhook_label_only":
        blockers.append("declaration_scoped_endpoint_family_label_invalid")

    if decl.get("scoped_credential_key_name") != "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK":
        blockers.append("declaration_scoped_credential_key_name_invalid")

    if decl.get("scoped_payload_hash") != preflight.get("planned_payload_hash"):
        blockers.append("declaration_scoped_payload_hash_mismatch")

    if decl.get("scoped_request_budget") != "single_supervised_request_future_scope":
        blockers.append("declaration_scoped_request_budget_invalid")

    if decl.get("scoped_max_request_count") != preflight.get("planned_max_request_count"):
        blockers.append("declaration_scoped_max_request_count_mismatch")

    if decl.get("scoped_max_request_count") != 1:
        blockers.append("declaration_scoped_max_request_count_invalid")

    if decl.get("scoped_timeout_seconds") != preflight.get("planned_timeout_seconds"):
        blockers.append("declaration_scoped_timeout_seconds_mismatch")

    t_sec = decl.get("scoped_timeout_seconds")
    if not isinstance(t_sec, int) or isinstance(t_sec, bool) or t_sec < 5 or t_sec > 30:
        blockers.append("declaration_scoped_timeout_seconds_invalid")

    if decl.get("scoped_max_retries") != 0:
        blockers.append("declaration_scoped_max_retries_invalid")

    if decl.get("scoped_hidden_retry_allowed") is not False:
        blockers.append("declaration_scoped_hidden_retry_allowed_not_false")

    # Scoped required confirmations must be True
    for f in [
        "scoped_idempotency_required",
        "scoped_kill_switch_required",
        "scoped_audit_redaction_required",
        "scoped_manual_fallback_required",
        "scoped_permission_probe_required_later",
        "scoped_payload_hash_revalidation_required",
        "scoped_exact_operator_approval_required_later",
        "scoped_destination_binding_required_later",
        "scoped_request_artifact_creation_required_later"
    ]:
        if decl.get(f) is not True:
            blockers.append(f"declaration_field_{f}_not_true")

    # Safety/execution-approval flags must be False
    for b_field in [
        "live_dispatch_approval_granted",
        "publication_approval_granted",
        "executable_request_artifact_creation_allowed",
        "webhook_value_read_allowed",
        "discord_api_call_allowed",
        "webhook_send_test_allowed",
        "endpoint_url_value_allowed",
        "channel_identity_value_allowed",
        "http_headers_included",
        "http_body_included",
        "curl_command_included",
        "browser_instruction_included",
        "public_url_included",
        "metrics_included"
    ]:
        if decl.get(b_field) is not False:
            blockers.append(f"declaration_field_{b_field}_not_false")

    if decl.get("discord_supervised_live_pilot_gate_planning_id") != preflight.get("discord_supervised_live_pilot_gate_planning_id"):
        blockers.append("declaration_discord_supervised_live_pilot_gate_planning_id_mismatch")

    if decl.get("discord_final_manual_execution_review_id") != preflight.get("discord_final_manual_execution_review_id"):
        blockers.append("declaration_discord_final_manual_execution_review_id_mismatch")

    if decl.get("discord_supervised_request_package_staging_id") != preflight.get("discord_supervised_request_package_staging_id"):
        blockers.append("declaration_discord_supervised_request_package_staging_id_mismatch")

    if decl.get("discord_request_policy_gate_id") != preflight.get("discord_request_policy_gate_id"):
        blockers.append("declaration_discord_request_policy_gate_id_mismatch")

    if decl.get("discord_operator_payload_review_gate_id") != preflight.get("discord_operator_payload_review_gate_id"):
        blockers.append("declaration_discord_operator_payload_review_gate_id_mismatch")

    if decl.get("discord_dry_run_payload_gate_id") != preflight.get("discord_dry_run_payload_gate_id"):
        blockers.append("declaration_discord_dry_run_payload_gate_id_mismatch")

    if decl.get("discord_permission_probe_preflight_id") != preflight.get("discord_permission_probe_preflight_id"):
        blockers.append("declaration_discord_permission_probe_preflight_id_mismatch")

    if decl.get("discord_webhook_value_binding_preflight_id") != preflight.get("discord_webhook_value_binding_preflight_id"):
        blockers.append("declaration_discord_webhook_value_binding_preflight_id_mismatch")

    if decl.get("discord_endpoint_mapping_preflight_id") != preflight.get("discord_endpoint_mapping_preflight_id"):
        blockers.append("declaration_discord_endpoint_mapping_preflight_id_mismatch")

    if decl.get("platform_capability_lane_split_id") != preflight.get("platform_capability_lane_split_id"):
        blockers.append("declaration_platform_capability_lane_split_id_mismatch")

    if decl.get("official_platform_docs_verification_id") != preflight.get("official_platform_docs_verification_id"):
        blockers.append("declaration_official_platform_docs_verification_id_mismatch")

    if decl.get("dispatch_request_package_gate_id") != preflight.get("dispatch_request_package_gate_id"):
        blockers.append("declaration_dispatch_request_package_gate_id_mismatch")

    if decl.get("combined_payload_hash") != preflight.get("combined_payload_hash"):
        blockers.append("declaration_combined_payload_hash_mismatch")

    contract_decision = decl.get("operator_live_scope_contract_decision")
    if contract_decision not in ["approve_explicit_discord_live_scope_contract_for_future_materialization_only", "reject", "defer"]:
        blockers.append("declaration_operator_live_scope_contract_decision_invalid")
    elif contract_decision in ["reject", "defer"]:
        blockers.append(f"declaration_operator_live_scope_contract_rejected_or_deferred_{contract_decision}")

    if decl.get("next_supervised_live_pilot_materialization_required") is not True:
        blockers.append("declaration_next_supervised_live_pilot_materialization_required_not_true")

    decision = decl.get("declaration_decision")
    if decision not in ["mark_explicit_discord_live_scope_contract_gate_ready", "reject", "defer"]:
        blockers.append("declaration_decision_invalid")
    elif decision in ["reject", "defer"]:
        blockers.append(f"declaration_rejected_or_deferred_{decision}")
    elif decision == "mark_explicit_discord_live_scope_contract_gate_ready":
        if decl.get("approval_phrase") != "MARK_EXPLICIT_DISCORD_LIVE_SCOPE_CONTRACT_READY_ONLY_NOT_LIVE":
            blockers.append("declaration_approval_phrase_invalid")
        if decl.get("approval_scope") != "explicit_discord_live_scope_contract_gate_only":
            blockers.append("declaration_approval_scope_invalid")

    if not isinstance(decl.get("notes"), str):
        blockers.append("declaration_notes_missing_or_invalid")

    return blockers


def make_explicit_discord_live_scope_contract_gate_packet(
    preflight_packet: Any,
    operator_declaration: Any
) -> ExplicitDiscordLiveScopeContractGatePacket:
    blockers: list[str] = []

    preflight_is_dict = isinstance(preflight_packet, dict)
    if not preflight_is_dict:
        blockers.append("malformed_discord_supervised_live_pilot_gate_planning_packet_json")

    decl_is_dict = isinstance(operator_declaration, dict)
    if not decl_is_dict:
        blockers.append("malformed_operator_explicit_discord_live_scope_contract_declaration_json")

    # Safety checks
    if preflight_is_dict:
        blockers.extend(_check_packet_safety(preflight_packet, "preflight"))
    if decl_is_dict:
        blockers.extend(_check_packet_safety(operator_declaration, "declaration"))

    explicit_discord_live_scope_contract_declaration_id = ""
    operator_id = ""
    created_at_manual = ""
    discord_supervised_live_pilot_gate_planning_id = ""
    discord_final_manual_execution_review_id = ""
    discord_supervised_request_package_staging_id = ""
    discord_request_policy_gate_id = ""
    discord_operator_payload_review_gate_id = ""
    discord_dry_run_payload_gate_id = ""
    discord_permission_probe_preflight_id = ""
    discord_webhook_value_binding_preflight_id = ""
    discord_endpoint_mapping_preflight_id = ""
    platform_capability_lane_split_id = ""
    official_platform_docs_verification_id = ""
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
    platform = ""
    scoped_action_class = ""
    scoped_platform_family = ""
    scoped_endpoint_family_label = ""
    scoped_credential_key_name = ""
    scoped_payload_hash = ""
    scoped_request_budget = ""
    scoped_max_request_count = 0
    scoped_timeout_seconds = 0
    scoped_max_retries = 0
    scoped_hidden_retry_allowed = False
    scoped_idempotency_required = False
    scoped_kill_switch_required = False
    scoped_audit_redaction_required = False
    scoped_manual_fallback_required = False
    scoped_permission_probe_required_later = False
    scoped_payload_hash_revalidation_required = False
    scoped_exact_operator_approval_required_later = False
    scoped_destination_binding_required_later = False
    scoped_request_artifact_creation_required_later = False
    operator_live_scope_contract_decision = ""

    live_dispatch_approval_granted = False
    publication_approval_granted = False
    executable_request_artifact_creation_allowed = False
    webhook_value_read_allowed = False
    discord_api_call_allowed = False
    webhook_send_test_allowed = False
    endpoint_url_value_allowed = False
    channel_identity_value_allowed = False
    http_headers_included = False
    http_body_included = False
    curl_command_included = False
    browser_instruction_included = False
    public_url_included = False
    metrics_included = False

    substack_manual_fallback_required = True

    if preflight_is_dict and "preflight_secret_marker_detected" not in blockers:
        blockers.extend(_validate_preflight_packet(preflight_packet))

    if decl_is_dict and preflight_is_dict and "declaration_secret_marker_detected" not in blockers:
        blockers.extend(_validate_declaration(operator_declaration, preflight_packet))

    if preflight_is_dict and decl_is_dict and not any("secret_marker_detected" in b for b in blockers):
        explicit_discord_live_scope_contract_declaration_id = str(operator_declaration.get("explicit_discord_live_scope_contract_declaration_id") or "")
        operator_id = str(operator_declaration.get("operator_id") or "")
        created_at_manual = str(operator_declaration.get("created_at_manual") or "")
        discord_supervised_live_pilot_gate_planning_id = str(preflight_packet.get("discord_supervised_live_pilot_gate_planning_id") or "")
        discord_final_manual_execution_review_id = str(preflight_packet.get("discord_final_manual_execution_review_id") or "")
        discord_supervised_request_package_staging_id = str(preflight_packet.get("discord_supervised_request_package_staging_id") or "")
        discord_request_policy_gate_id = str(preflight_packet.get("discord_request_policy_gate_id") or "")
        discord_operator_payload_review_gate_id = str(preflight_packet.get("discord_operator_payload_review_gate_id") or "")
        discord_dry_run_payload_gate_id = str(preflight_packet.get("discord_dry_run_payload_gate_id") or "")
        discord_permission_probe_preflight_id = str(preflight_packet.get("discord_permission_probe_preflight_id") or "")
        discord_webhook_value_binding_preflight_id = str(preflight_packet.get("discord_webhook_value_binding_preflight_id") or "")
        discord_endpoint_mapping_preflight_id = str(preflight_packet.get("discord_endpoint_mapping_preflight_id") or "")
        platform_capability_lane_split_id = str(preflight_packet.get("platform_capability_lane_split_id") or "")
        official_platform_docs_verification_id = str(preflight_packet.get("official_platform_docs_verification_id") or "")
        dispatch_request_package_gate_id = str(preflight_packet.get("dispatch_request_package_gate_id") or "")
        dispatch_request_package_gate_sha256 = str(preflight_packet.get("dispatch_request_package_gate_sha256") or "")
        account_binding_preflight_id = str(preflight_packet.get("account_binding_preflight_id") or "")
        account_binding_preflight_sha256 = str(preflight_packet.get("account_binding_preflight_sha256") or "")
        credential_allowlist_preflight_id = str(preflight_packet.get("credential_allowlist_preflight_id") or "")
        credential_allowlist_preflight_sha256 = str(preflight_packet.get("credential_allowlist_preflight_sha256") or "")
        live_dispatch_scope_preflight_id = str(preflight_packet.get("live_dispatch_scope_preflight_id") or "")
        live_dispatch_scope_preflight_sha256 = str(preflight_packet.get("live_dispatch_scope_preflight_sha256") or "")
        live_dispatch_readiness_preflight_id = str(preflight_packet.get("live_dispatch_readiness_preflight_id") or "")
        live_dispatch_readiness_preflight_sha256 = str(preflight_packet.get("live_dispatch_readiness_preflight_sha256") or "")
        combined_payload_hash = str(preflight_packet.get("combined_payload_hash") or "")

        platform = str(operator_declaration.get("platform") or "")
        scoped_action_class = str(operator_declaration.get("scoped_action_class") or "")
        scoped_platform_family = str(operator_declaration.get("scoped_platform_family") or "")
        scoped_endpoint_family_label = str(operator_declaration.get("scoped_endpoint_family_label") or "")
        scoped_credential_key_name = str(operator_declaration.get("scoped_credential_key_name") or "")
        scoped_payload_hash = str(operator_declaration.get("scoped_payload_hash") or "")
        scoped_request_budget = str(operator_declaration.get("scoped_request_budget") or "")
        scoped_max_request_count = int(operator_declaration.get("scoped_max_request_count") or 0)
        scoped_timeout_seconds = int(operator_declaration.get("scoped_timeout_seconds") or 0)
        scoped_max_retries = int(operator_declaration.get("scoped_max_retries") or 0)
        scoped_hidden_retry_allowed = bool(operator_declaration.get("scoped_hidden_retry_allowed"))
        scoped_idempotency_required = bool(operator_declaration.get("scoped_idempotency_required"))
        scoped_kill_switch_required = bool(operator_declaration.get("scoped_kill_switch_required"))
        scoped_audit_redaction_required = bool(operator_declaration.get("scoped_audit_redaction_required"))
        scoped_manual_fallback_required = bool(operator_declaration.get("scoped_manual_fallback_required"))
        scoped_permission_probe_required_later = bool(operator_declaration.get("scoped_permission_probe_required_later"))
        scoped_payload_hash_revalidation_required = bool(operator_declaration.get("scoped_payload_hash_revalidation_required"))
        scoped_exact_operator_approval_required_later = bool(operator_declaration.get("scoped_exact_operator_approval_required_later"))
        scoped_destination_binding_required_later = bool(operator_declaration.get("scoped_destination_binding_required_later"))
        scoped_request_artifact_creation_required_later = bool(operator_declaration.get("scoped_request_artifact_creation_required_later"))
        operator_live_scope_contract_decision = str(operator_declaration.get("operator_live_scope_contract_decision") or "")

        substack_manual_fallback_required = bool(preflight_packet.get("substack_manual_fallback_required"))

    blockers = sorted(set(blockers))
    prepared = not blockers

    declared_ready = (
        prepared and decl_is_dict and (operator_declaration.get("declaration_decision") == "mark_explicit_discord_live_scope_contract_gate_ready")
    )

    eligible_materialization = False
    if (
        prepared
        and declared_ready
        and scoped_payload_hash == preflight_packet.get("planned_payload_hash")
        and scoped_max_request_count == 1
        and scoped_max_retries == 0
        and not scoped_hidden_retry_allowed
        and scoped_idempotency_required
        and scoped_kill_switch_required
        and scoped_audit_redaction_required
        and scoped_manual_fallback_required
        and scoped_permission_probe_required_later
        and scoped_payload_hash_revalidation_required
        and scoped_exact_operator_approval_required_later
        and scoped_destination_binding_required_later
        and scoped_request_artifact_creation_required_later
        and operator_live_scope_contract_decision == "approve_explicit_discord_live_scope_contract_for_future_materialization_only"
    ):
        eligible_materialization = True

    # Safety redaction on secret/marker detection
    has_secrets = any("secret_marker_detected" in b for b in blockers)

    if has_secrets:
        explicit_discord_live_scope_contract_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_supervised_live_pilot_gate_planning_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_final_manual_execution_review_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_supervised_request_package_staging_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_request_policy_gate_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_operator_payload_review_gate_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_dry_run_payload_gate_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_permission_probe_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_webhook_value_binding_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        discord_endpoint_mapping_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        platform_capability_lane_split_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        official_platform_docs_verification_id = "[REDACTED_SECRET_MARKER_DETECTED]"
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
        platform = ""
        scoped_payload_hash = ""
        eligible_materialization = False

    intake_material = {
        "discord_supervised_live_pilot_gate_planning_id": discord_supervised_live_pilot_gate_planning_id,
        "explicit_discord_live_scope_contract_declaration_id": explicit_discord_live_scope_contract_declaration_id,
        "blockers": blockers,
    }
    explicit_discord_live_scope_contract_gate_id = f"explicit_discord_live_scope_contract_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("explicit_discord_live_scope_contract_gate_blocked_pending_operator_repair")

    if prepared:
        warnings.append("substack_official_api_docs_unverified")

    return ExplicitDiscordLiveScopeContractGatePacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        explicit_discord_live_scope_contract_gate_id=explicit_discord_live_scope_contract_gate_id,
        explicit_discord_live_scope_contract_declaration_id=explicit_discord_live_scope_contract_declaration_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        discord_supervised_live_pilot_gate_planning_id=discord_supervised_live_pilot_gate_planning_id,
        discord_final_manual_execution_review_id=discord_final_manual_execution_review_id,
        discord_supervised_request_package_staging_id=discord_supervised_request_package_staging_id,
        discord_request_policy_gate_id=discord_request_policy_gate_id,
        discord_operator_payload_review_gate_id=discord_operator_payload_review_gate_id,
        discord_dry_run_payload_gate_id=discord_dry_run_payload_gate_id,
        discord_permission_probe_preflight_id=discord_permission_probe_preflight_id,
        discord_webhook_value_binding_preflight_id=discord_webhook_value_binding_preflight_id,
        discord_endpoint_mapping_preflight_id=discord_endpoint_mapping_preflight_id,
        platform_capability_lane_split_id=platform_capability_lane_split_id,
        official_platform_docs_verification_id=official_platform_docs_verification_id,
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
        platform=platform,
        scoped_action_class=scoped_action_class,
        scoped_platform_family=scoped_platform_family,
        scoped_endpoint_family_label=scoped_endpoint_family_label,
        scoped_credential_key_name=scoped_credential_key_name,
        scoped_payload_hash=scoped_payload_hash,
        scoped_request_budget=scoped_request_budget,
        scoped_max_request_count=scoped_max_request_count,
        scoped_timeout_seconds=scoped_timeout_seconds,
        scoped_max_retries=scoped_max_retries,
        scoped_hidden_retry_allowed=scoped_hidden_retry_allowed,
        scoped_idempotency_required=scoped_idempotency_required,
        scoped_kill_switch_required=scoped_kill_switch_required,
        scoped_audit_redaction_required=scoped_audit_redaction_required,
        scoped_manual_fallback_required=scoped_manual_fallback_required,
        scoped_permission_probe_required_later=scoped_permission_probe_required_later,
        scoped_payload_hash_revalidation_required=scoped_payload_hash_revalidation_required,
        scoped_exact_operator_approval_required_later=scoped_exact_operator_approval_required_later,
        scoped_destination_binding_required_later=scoped_destination_binding_required_later,
        scoped_request_artifact_creation_required_later=scoped_request_artifact_creation_required_later,
        operator_live_scope_contract_decision=operator_live_scope_contract_decision,
        live_dispatch_approval_granted=live_dispatch_approval_granted,
        publication_approval_granted=publication_approval_granted,
        executable_request_artifact_creation_allowed=executable_request_artifact_creation_allowed,
        webhook_value_read_allowed=webhook_value_read_allowed,
        discord_api_call_allowed=discord_api_call_allowed,
        webhook_send_test_allowed=webhook_send_test_allowed,
        endpoint_url_value_allowed=endpoint_url_value_allowed,
        channel_identity_value_allowed=channel_identity_value_allowed,
        http_headers_included=http_headers_included,
        http_body_included=http_body_included,
        curl_command_included=curl_command_included,
        browser_instruction_included=browser_instruction_included,
        public_url_included=public_url_included,
        metrics_included=metrics_included,
        explicit_discord_live_scope_contract_gate_available=prepared,
        explicit_discord_live_scope_contract_gate_declared_ready=declared_ready,
        eligible_for_supervised_live_pilot_materialization_gate=eligible_materialization,
        eligible_for_full_live_dispatch_endpoint_mapping_gate=False,
        next_supervised_live_pilot_materialization_required=True,
        substack_manual_fallback_required=substack_manual_fallback_required,
        all_platforms_endpoint_mapping_ready=False,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Explicit Discord Live Scope Contract Gate CLI")
    parser.add_argument("preflight_packet", help="Path to Discord supervised live pilot planning packet JSON")
    parser.add_argument("operator_declaration", help="Path to operator live scope contract declaration JSON")
    parser.add_argument("--output-file", required=True, help="Path to write explicit Discord live scope contract gate packet JSON")

    args = parser.parse_args(argv)

    try:
        preflight = load_json_packet(args.preflight_packet, "malformed_discord_supervised_live_pilot_gate_planning_packet_json")
        decl = load_json_packet(args.operator_declaration, "malformed_operator_explicit_discord_live_scope_contract_declaration_json")

        packet = make_explicit_discord_live_scope_contract_gate_packet(preflight, decl)

        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")

        if not packet.explicit_discord_live_scope_contract_gate_available:
            return 1
        return 0

    except ValueError as val_err:
        packet = ExplicitDiscordLiveScopeContractGatePacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            explicit_discord_live_scope_contract_gate_id=f"explicit_discord_live_scope_contract_blocked_{str(val_err)}",
            explicit_discord_live_scope_contract_declaration_id="",
            operator_id="",
            created_at_manual="",
            discord_supervised_live_pilot_gate_planning_id="",
            discord_final_manual_execution_review_id="",
            discord_supervised_request_package_staging_id="",
            discord_request_policy_gate_id="",
            discord_operator_payload_review_gate_id="",
            discord_dry_run_payload_gate_id="",
            discord_permission_probe_preflight_id="",
            discord_webhook_value_binding_preflight_id="",
            discord_endpoint_mapping_preflight_id="",
            platform_capability_lane_split_id="",
            official_platform_docs_verification_id="",
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
            platform="",
            scoped_action_class="",
            scoped_platform_family="",
            scoped_endpoint_family_label="",
            scoped_credential_key_name="",
            scoped_payload_hash="",
            scoped_request_budget="",
            scoped_max_request_count=0,
            scoped_timeout_seconds=0,
            scoped_max_retries=0,
            scoped_hidden_retry_allowed=False,
            scoped_idempotency_required=False,
            scoped_kill_switch_required=False,
            scoped_audit_redaction_required=False,
            scoped_manual_fallback_required=False,
            scoped_permission_probe_required_later=False,
            scoped_payload_hash_revalidation_required=False,
            scoped_exact_operator_approval_required_later=False,
            scoped_destination_binding_required_later=False,
            scoped_request_artifact_creation_required_later=False,
            operator_live_scope_contract_decision="",
            live_dispatch_approval_granted=False,
            publication_approval_granted=False,
            executable_request_artifact_creation_allowed=False,
            webhook_value_read_allowed=False,
            discord_api_call_allowed=False,
            webhook_send_test_allowed=False,
            endpoint_url_value_allowed=False,
            channel_identity_value_allowed=False,
            http_headers_included=False,
            http_body_included=False,
            curl_command_included=False,
            browser_instruction_included=False,
            public_url_included=False,
            metrics_included=False,
            explicit_discord_live_scope_contract_gate_available=False,
            explicit_discord_live_scope_contract_gate_declared_ready=False,
            eligible_for_supervised_live_pilot_materialization_gate=False,
            eligible_for_full_live_dispatch_endpoint_mapping_gate=False,
            next_supervised_live_pilot_materialization_required=True,
            substack_manual_fallback_required=True,
            all_platforms_endpoint_mapping_ready=False,
            blockers=[str(val_err)],
            warnings=["explicit_discord_live_scope_contract_gate_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
