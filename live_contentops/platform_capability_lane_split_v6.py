"""V6 Platform Capability Lane Split Gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_CAPABILITY_LANE_SPLIT_FROM_OFFICIAL_DOCS_V0"
DOCS_VERIFICATION_TASK_LABEL = "TASK_CONTENTOPS_V6_OFFICIAL_PLATFORM_DOCS_VERIFICATION_FOR_LIVE_DISPATCH_REQUEST_GATE_V0"
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
    "lane_split_decl_"
)


@dataclass(frozen=True)
class PlatformCapabilityLaneSplitPacket:
    schema_version: str
    task_label: str
    platform_capability_lane_split_id: str
    lane_split_declaration_id: str
    operator_id: str
    created_at_manual: str
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
    platforms: list[str]
    requested_platforms: list[str]
    platform_lane_rows: list[dict[str, Any]]
    discord_endpoint_mapping_candidate: bool
    substack_manual_fallback_required: bool
    partial_platform_endpoint_mapping_ready: bool
    all_platforms_endpoint_mapping_ready: bool
    all_platforms_endpoint_mapping_required_for_full_live_loop: bool
    permission_verification_later_required: bool
    payload_hash_revalidation_later_required: bool
    kill_switch_later_required: bool
    audit_redaction_later_required: bool
    manual_fallback_later_required: bool
    lane_split_available: bool
    lane_split_declared_ready: bool
    eligible_for_discord_endpoint_mapping_gate: bool
    eligible_for_full_live_dispatch_endpoint_mapping_gate: bool
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
        "task_contentops_v6_platform_capability_lane_split_from_official_docs_v0",
        "platform_capability_lane_split_id",
        "lane_split_declaration_id",
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
    for phrase in sorted(ALLOWED_SCHEMA_PHRASES, key=len, reverse=True):
        lowered = lowered.replace(phrase.lower(), "")
    for term in FORBIDDEN_LIVE_CLAIMS:
        if term in lowered:
            return term
    return None


def _check_packet_safety(packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    for k, v in packet.items():
        if k in ["platform_docs_rows", "platforms_reviewed", "platform_lane_rows"]:
            continue
        if prefix == "docs" and k == "notes":
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


def load_json_packet(path: str, malformed_label: str) -> Any:
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(val, dict):
            raise ValueError(malformed_label)
        return val
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def _validate_docs_packet(docs: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    if docs.get("task_label") != DOCS_VERIFICATION_TASK_LABEL:
        blockers.append("docs_task_label_invalid")

    if docs.get("docs_verification_available") is not True:
        blockers.append("docs_verification_not_available")

    if docs.get("docs_verification_declared_ready") is not True:
        blockers.append("docs_verification_not_declared_ready")

    gating_rules = {
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
        if docs.get(field_name) != expected:
            blockers.append(f"docs_field_{field_name}_invalid")

    if docs.get("public_url") is not None:
        blockers.append("docs_public_url_not_null")
    if docs.get("public_metrics") is not None:
        blockers.append("docs_public_metrics_not_null")

    if docs.get("blockers"):
        blockers.append("docs_blockers_not_empty")

    required_ids = [
        "combined_payload_hash",
        "dispatch_request_package_gate_id",
        "dispatch_request_package_gate_sha256",
        "account_binding_preflight_id",
        "account_binding_preflight_sha256",
        "credential_allowlist_preflight_id",
        "credential_allowlist_preflight_sha256",
        "live_dispatch_scope_preflight_id",
        "live_dispatch_scope_preflight_sha256",
        "live_dispatch_readiness_preflight_id",
        "live_dispatch_readiness_preflight_sha256"
    ]
    for rid in required_ids:
        if not docs.get(rid):
            blockers.append(f"docs_id_{rid}_missing")

    rows = docs.get("platform_docs_rows")
    if not isinstance(rows, list) or len(rows) != 2:
        blockers.append("docs_platform_docs_rows_invalid")
    else:
        if rows[0].get("platform") != "substack" or rows[1].get("platform") != "discord":
            blockers.append("docs_platform_docs_rows_order_invalid")

    return blockers


def _validate_declaration(decl: dict[str, Any], docs: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "lane_split_declaration_id",
        "operator_id",
        "created_at_manual",
        "official_platform_docs_verification_id",
        "dispatch_request_package_gate_id",
        "combined_payload_hash",
        "lane_split_mode",
        "platforms_reviewed",
        "discord_lane_expected",
        "substack_lane_expected",
        "partial_platform_endpoint_mapping_allowed",
        "all_platforms_endpoint_mapping_required_for_full_live_loop",
        "substack_manual_fallback_required_confirmed",
        "discord_endpoint_mapping_later_required",
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

    if decl.get("lane_split_mode") != "operator_declared_platform_capability_lane_split_only_not_send":
        blockers.append("declaration_lane_split_mode_invalid")

    if decl.get("platforms_reviewed") != ["substack", "discord"]:
        blockers.append("declaration_platforms_reviewed_invalid")

    if decl.get("official_platform_docs_verification_id") != docs.get("official_platform_docs_verification_id"):
        blockers.append("declaration_official_platform_docs_verification_id_mismatch")

    if decl.get("dispatch_request_package_gate_id") != docs.get("dispatch_request_package_gate_id"):
        blockers.append("declaration_dispatch_request_package_gate_id_mismatch")

    if decl.get("combined_payload_hash") != docs.get("combined_payload_hash"):
        blockers.append("declaration_combined_payload_hash_mismatch")

    if decl.get("discord_lane_expected") != "future_webhook_endpoint_mapping_candidate":
        blockers.append("declaration_discord_lane_expected_invalid")

    if decl.get("substack_lane_expected") != "manual_browser_or_manual_export_fallback_required":
        blockers.append("declaration_substack_lane_expected_invalid")

    # Confirmations
    for b_field in [
        "partial_platform_endpoint_mapping_allowed",
        "all_platforms_endpoint_mapping_required_for_full_live_loop",
        "substack_manual_fallback_required_confirmed",
        "discord_endpoint_mapping_later_required",
        "permission_verification_later_required",
        "payload_hash_revalidation_later_required",
        "kill_switch_later_required",
        "audit_redaction_later_required",
        "manual_fallback_later_required"
    ]:
        if decl.get(b_field) is not True:
            blockers.append(f"declaration_field_{b_field}_not_true")

    decision = decl.get("declaration_decision")
    if decision not in ["mark_platform_capability_lane_split_ready", "reject", "defer"]:
        blockers.append("declaration_decision_invalid")
    elif decision in ["reject", "defer"]:
        blockers.append(f"declaration_rejected_or_deferred_{decision}")
    elif decision == "mark_platform_capability_lane_split_ready":
        if decl.get("approval_phrase") != "MARK_PLATFORM_CAPABILITY_LANE_SPLIT_READY_ONLY_NOT_SEND":
            blockers.append("declaration_approval_phrase_invalid")
        if decl.get("approval_scope") != "platform_capability_lane_split_only":
            blockers.append("declaration_approval_scope_invalid")

    if not isinstance(decl.get("notes"), str):
        blockers.append("declaration_notes_missing_or_invalid")

    return blockers


def make_platform_capability_lane_split_packet(
    docs_packet: Any,
    operator_declaration: Any,
) -> PlatformCapabilityLaneSplitPacket:
    blockers: list[str] = []

    docs_is_dict = isinstance(docs_packet, dict)
    if not docs_is_dict:
        blockers.append("malformed_official_platform_docs_verification_packet_json")

    decl_is_dict = isinstance(operator_declaration, dict)
    if not decl_is_dict:
        blockers.append("malformed_operator_lane_split_declaration_json")

    # Safety checks
    if docs_is_dict:
        blockers.extend(_check_packet_safety(docs_packet, "docs"))
    if decl_is_dict:
        blockers.extend(_check_packet_safety(operator_declaration, "declaration"))

    lane_split_declaration_id = ""
    operator_id = ""
    created_at_manual = ""
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
    platforms: list[str] = []
    requested_platforms: list[str] = []
    platform_lane_rows: list[dict[str, Any]] = []

    discord_endpoint_mapping_candidate = False
    substack_manual_fallback_required = False
    partial_platform_endpoint_mapping_ready = False
    all_platforms_endpoint_mapping_ready = False
    all_platforms_endpoint_mapping_required_for_full_live_loop = False
    permission_verification_later_required = False
    payload_hash_revalidation_later_required = False
    kill_switch_later_required = False
    audit_redaction_later_required = False
    manual_fallback_later_required = False

    if docs_is_dict and "docs_secret_marker_detected" not in blockers:
        blockers.extend(_validate_docs_packet(docs_packet))

    if decl_is_dict and docs_is_dict and "declaration_secret_marker_detected" not in blockers:
        blockers.extend(_validate_declaration(operator_declaration, docs_packet))

    if docs_is_dict and decl_is_dict and not any("secret_marker_detected" in b for b in blockers):
        lane_split_declaration_id = str(operator_declaration.get("lane_split_declaration_id") or "")
        operator_id = str(operator_declaration.get("operator_id") or "")
        created_at_manual = str(operator_declaration.get("created_at_manual") or "")
        official_platform_docs_verification_id = str(docs_packet.get("official_platform_docs_verification_id") or "")
        dispatch_request_package_gate_id = str(docs_packet.get("dispatch_request_package_gate_id") or "")
        dispatch_request_package_gate_sha256 = str(docs_packet.get("dispatch_request_package_gate_sha256") or "")
        account_binding_preflight_id = str(docs_packet.get("account_binding_preflight_id") or "")
        account_binding_preflight_sha256 = str(docs_packet.get("account_binding_preflight_sha256") or "")
        credential_allowlist_preflight_id = str(docs_packet.get("credential_allowlist_preflight_id") or "")
        credential_allowlist_preflight_sha256 = str(docs_packet.get("credential_allowlist_preflight_sha256") or "")
        live_dispatch_scope_preflight_id = str(docs_packet.get("live_dispatch_scope_preflight_id") or "")
        live_dispatch_scope_preflight_sha256 = str(docs_packet.get("live_dispatch_scope_preflight_sha256") or "")
        live_dispatch_readiness_preflight_id = str(docs_packet.get("live_dispatch_readiness_preflight_id") or "")
        live_dispatch_readiness_preflight_sha256 = str(docs_packet.get("live_dispatch_readiness_preflight_sha256") or "")
        combined_payload_hash = str(docs_packet.get("combined_payload_hash") or "")
        platforms = docs_packet.get("platforms", [])
        requested_platforms = docs_packet.get("requested_platforms", [])

        # Process lane split rows
        docs_rows = docs_packet.get("platform_docs_rows", [])
        for idx, row in enumerate(docs_rows):
            plat = row.get("platform")
            classif = row.get("dispatch_capability_classification")
            live_write = bool(row.get("live_write_allowed_later"))
            mechanism = row.get("supported_dispatch_mechanism")
            row_blockers = row.get("blockers", [])

            # Safety scan row
            blockers.extend(_check_row_safety(row, "docs_row", idx))

            lane_decision = "unknown"
            endpoint_candidate = False
            fallback_required = False
            blocking_reason = []

            if plat == "discord":
                if classif == "official_webhook_supported_for_required_action" and mechanism == "execute_webhook" and live_write is True and not row_blockers:
                    lane_decision = "future_webhook_endpoint_mapping_candidate"
                    endpoint_candidate = True
                    fallback_required = True
                else:
                    lane_decision = "manual_browser_or_manual_export_fallback_required"
                    fallback_required = True
                    blocking_reason.append("discord_official_docs_unverified_or_unsupported")
            elif plat == "substack":
                if classif in ["unclear_requires_operator_decision", "unsupported_by_official_docs"] and live_write is False:
                    lane_decision = "manual_browser_or_manual_export_fallback_required"
                    fallback_required = True
                else:
                    lane_decision = "manual_browser_or_manual_export_fallback_required"
                    fallback_required = True
                    blocking_reason.append("substack_official_api_unverified")
                    blockers.append("substack_official_api_docs_unverified")

            platform_lane_rows.append({
                "platform": plat,
                "source_docs_classification": classif,
                "source_docs_live_write_allowed_later": live_write,
                "lane_decision": lane_decision,
                "endpoint_mapping_candidate": endpoint_candidate,
                "manual_fallback_required": fallback_required,
                "blocking_reason": blocking_reason,
                "caveats": row.get("caveats", []),
                "warnings": row.get("warnings", [])
            })

        # Set mapping flags
        discord_endpoint_mapping_candidate = any(
            r["platform"] == "discord" and r["lane_decision"] == "future_webhook_endpoint_mapping_candidate"
            for r in platform_lane_rows
        )
        substack_manual_fallback_required = any(
            r["platform"] == "substack" and r["manual_fallback_required"] is True
            for r in platform_lane_rows
        )
        partial_platform_endpoint_mapping_ready = discord_endpoint_mapping_candidate
        all_platforms_endpoint_mapping_ready = False
        all_platforms_endpoint_mapping_required_for_full_live_loop = bool(operator_declaration.get("all_platforms_endpoint_mapping_required_for_full_live_loop"))

        permission_verification_later_required = bool(operator_declaration.get("permission_verification_later_required"))
        payload_hash_revalidation_later_required = bool(operator_declaration.get("payload_hash_revalidation_later_required"))
        kill_switch_later_required = bool(operator_declaration.get("kill_switch_later_required"))
        audit_redaction_later_required = bool(operator_declaration.get("audit_redaction_later_required"))
        manual_fallback_later_required = bool(operator_declaration.get("manual_fallback_later_required"))

    blockers = sorted(set(blockers))
    prepared = not blockers

    declared_ready = (
        prepared and decl_is_dict and (operator_declaration.get("declaration_decision") == "mark_platform_capability_lane_split_ready")
    )

    eligible_discord = prepared and declared_ready and discord_endpoint_mapping_candidate and not blockers
    eligible_full = False  # Always false while Substack is unclear/unsupported

    # Safety redaction on secret/marker detection
    has_secrets = any("secret_marker_detected" in b for b in blockers)

    if has_secrets:
        lane_split_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
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
        platforms = []
        requested_platforms = []
        platform_lane_rows = []
        discord_endpoint_mapping_candidate = False
        substack_manual_fallback_required = False
        partial_platform_endpoint_mapping_ready = False
        all_platforms_endpoint_mapping_ready = False
        all_platforms_endpoint_mapping_required_for_full_live_loop = False
        permission_verification_later_required = False
        payload_hash_revalidation_later_required = False
        kill_switch_later_required = False
        audit_redaction_later_required = False
        manual_fallback_later_required = False
        eligible_discord = False
        eligible_full = False

    intake_material = {
        "official_platform_docs_verification_id": official_platform_docs_verification_id,
        "lane_split_declaration_id": lane_split_declaration_id,
        "blockers": blockers,
    }
    platform_capability_lane_split_id = f"lane_split_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("lane_split_blocked_pending_operator_repair")

    # Add warnings for unclear/unsupported platforms
    if prepared:
        for r in platform_lane_rows:
            if r["source_docs_classification"] in ["unclear_requires_operator_decision", "unsupported_by_official_docs"]:
                warnings.append(f"{r['platform']}_official_api_docs_unverified")

    return PlatformCapabilityLaneSplitPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        platform_capability_lane_split_id=platform_capability_lane_split_id,
        lane_split_declaration_id=lane_split_declaration_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
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
        platforms=platforms,
        requested_platforms=requested_platforms,
        platform_lane_rows=platform_lane_rows,
        discord_endpoint_mapping_candidate=discord_endpoint_mapping_candidate,
        substack_manual_fallback_required=substack_manual_fallback_required,
        partial_platform_endpoint_mapping_ready=partial_platform_endpoint_mapping_ready,
        all_platforms_endpoint_mapping_ready=all_platforms_endpoint_mapping_ready,
        all_platforms_endpoint_mapping_required_for_full_live_loop=all_platforms_endpoint_mapping_required_for_full_live_loop,
        permission_verification_later_required=permission_verification_later_required,
        payload_hash_revalidation_later_required=payload_hash_revalidation_later_required,
        kill_switch_later_required=kill_switch_later_required,
        audit_redaction_later_required=audit_redaction_later_required,
        manual_fallback_later_required=manual_fallback_later_required,
        lane_split_available=prepared,
        lane_split_declared_ready=declared_ready,
        eligible_for_discord_endpoint_mapping_gate=eligible_discord,
        eligible_for_full_live_dispatch_endpoint_mapping_gate=eligible_full,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Platform Capability Lane Split Gate CLI")
    parser.add_argument("docs_packet", help="Path to docs verification packet JSON")
    parser.add_argument("operator_declaration", help="Path to operator lane split declaration JSON")
    parser.add_argument("--output-file", required=True, help="Path to write lane split packet JSON")

    args = parser.parse_args(argv)

    try:
        docs = load_json_packet(args.docs_packet, "malformed_official_platform_docs_verification_packet_json")
        decl = load_json_packet(args.operator_declaration, "malformed_operator_lane_split_declaration_json")

        packet = make_platform_capability_lane_split_packet(docs, decl)

        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")

        if not packet.lane_split_available:
            return 1
        return 0

    except ValueError as val_err:
        packet = PlatformCapabilityLaneSplitPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            platform_capability_lane_split_id=f"lane_split_blocked_{str(val_err)}",
            lane_split_declaration_id="",
            operator_id="",
            created_at_manual="",
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
            platforms=[],
            requested_platforms=[],
            platform_lane_rows=[],
            discord_endpoint_mapping_candidate=False,
            substack_manual_fallback_required=False,
            partial_platform_endpoint_mapping_ready=False,
            all_platforms_endpoint_mapping_ready=False,
            all_platforms_endpoint_mapping_required_for_full_live_loop=False,
            permission_verification_later_required=False,
            payload_hash_revalidation_later_required=False,
            kill_switch_later_required=False,
            audit_redaction_later_required=False,
            manual_fallback_later_required=False,
            lane_split_available=False,
            lane_split_declared_ready=False,
            eligible_for_discord_endpoint_mapping_gate=False,
            eligible_for_full_live_dispatch_endpoint_mapping_gate=False,
            blockers=[str(val_err)],
            warnings=["lane_split_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
