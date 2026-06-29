"""V6 Local Live Dispatch Request Package Gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_LIVE_DISPATCH_REQUEST_PACKAGE_GATE_FROM_ACCOUNT_BINDING_V0"
ACCOUNT_BINDING_PREFLIGHT_TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_ACCOUNT_BINDING_PREFLIGHT_FROM_CREDENTIAL_ALLOWLIST_V0"
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
)


def _scan_for_forbidden_live_claims(text: str) -> str | None:
    lowered = text.lower()
    for phrase in ALLOWED_SCHEMA_PHRASES:
        lowered = lowered.replace(phrase.lower(), "")
    for term in FORBIDDEN_LIVE_CLAIMS:
        if term in lowered:
            return term
    return None


@dataclass(frozen=True)
class DispatchRequestPackageGatePacket:
    schema_version: str
    task_label: str
    dispatch_request_package_gate_id: str
    dispatch_request_gate_declaration_id: str
    operator_id: str
    created_at_manual: str
    account_binding_preflight_id: str
    account_binding_preflight_sha256: str
    account_binding_declaration_id: str
    credential_allowlist_preflight_id: str
    credential_allowlist_preflight_sha256: str
    endpoint_allowlist_declaration_id: str
    live_dispatch_scope_preflight_id: str
    live_dispatch_scope_preflight_sha256: str
    live_dispatch_readiness_preflight_id: str
    live_dispatch_readiness_preflight_sha256: str
    official_docs_declaration_id: str
    live_scope_declaration_id: str
    local_dispatch_execution_payload_manifest_id: str
    operator_supervised_dispatch_review_decision_packet_id: str
    local_destination_binding_preflight_id: str
    destination_binding_id: str
    local_dispatch_payload_manifest_id: str
    operator_dispatch_review_decision_packet_id: str
    local_dispatch_preflight_id: str
    local_active_outbox_manifest_id: str
    operator_active_outbox_review_decision_id: str
    active_outbox_eligibility_id: str
    outbox_package_staging_id: str
    payload_review_ledger_id: str
    approval_intent_id: str
    variant_preview_staging_id: str
    metadata_values_review_id: str
    metadata_values_id: str
    metadata_proposal_id: str
    source_pack_intake_id: str
    source_pack_id: str
    editorial_workflow_id: str
    canonical_slug: str
    canonical_title: str
    execution_preparation_json_files: list[str]
    execution_preparation_json_hashes: dict[str, str]
    execution_preparation_markdown_files: list[str]
    execution_preparation_markdown_hashes: dict[str, str]
    destinations: list[dict[str, Any]]
    platforms: list[str]
    credential_key_names_only: list[str]
    endpoint_allowlist_rows: list[dict[str, Any]]
    platform_binding_rows: list[dict[str, Any]]
    requested_platforms: list[str]
    request_budget_confirmed: int
    timeout_policy_confirmed: str
    retry_policy_confirmed: str
    kill_switch_confirmed: bool
    audit_redaction_confirmed: bool
    manual_fallback_confirmed: bool
    account_binding_confirmed: bool
    permission_check_later_required: bool
    provider_execution_later_required: bool
    operator_final_review_later_required: bool
    combined_payload_hash: str
    dispatch_request_package_gate_available: bool
    dispatch_request_package_gate_declared_ready: bool
    eligible_for_future_supervised_dispatch_request_package: bool
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
    # Bypass schema/rule keywords to prevent false positives
    bypass_terms = [
        "task_contentops_v6_live_dispatch_credential_and_allowlist_preflight_from_scope_v0",
        "task_contentops_v6_live_dispatch_account_binding_preflight_from_credential_allowlist_v0",
        "task_contentops_v6_local_live_dispatch_request_package_gate_from_account_binding_v0",
        "credential_allowlist_preflight_available",
        "credential_allowlist_preflight_sha256",
        "credential_allowlist_preflight_id",
        "credential_allowlist_preflight_",
        "credential_presence_complete",
        "credential_presence_rows",
        "credential_presence_mode",
        "credential_presence_",
        "credential_key_names_only_reviewed",
        "credential_key_names_only",
        "credential_key_name",
        "credential_allowlist",
        "credential_presence",
        "account_binding_preflight_available",
        "account_binding_declared_ready",
        "account_binding_preflight_id",
        "account_binding_preflight_sha256",
        "account_binding_preflight_",
        "account_binding_declaration_id",
        "account_binding_declaration_",
        "account_binding_mode",
        "platform_binding_rows",
        "endpoint_allowlist_rows_reviewed",
        "endpoint_allowlist_rows_",
        "endpoint_allowlist_rows",
        "webhook_family_target",
        "non_secret_label_only",
        "webhook_method_label_only",
        "discord_operator_declared_webhook_host_label",
        "discord_operator_declared_webhook_path_label",
        "mark_credential_allowlist_ready_for_future_live_gate_only_not_send",
        "mark_credential_allowlist_ready_for_future_live_gate",
        "credential_allowlist_preflight_only",
        "endpoint_allowlist_declared_ready",
        "eligible_for_supervised_live_dispatch_request_gate",
        "mark_account_binding_ready_for_future_live_request_gate_only_not_send",
        "mark_account_binding_ready_for_future_live_request_gate",
        "account_binding_preflight_only",
        "operator_declared_account_binding_labels_only_not_verified",
        "non_secret_label_only_not_verified",
        "eligible_for_live_dispatch_request_package_gate",
        "checked_declared_key_names_only",
        "account_identity_later_required",
        "account_identity",
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
    ]
    for term in bypass_terms:
        lowered = lowered.replace(term, "")
    return any(marker in lowered for marker in SECRET_MARKERS)


def load_json_packet(path: str, malformed_label: str) -> Any:
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(val, dict):
            raise ValueError(malformed_label)
        return val
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def _validate_preflight_packet(preflight: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "task_label",
        "account_binding_preflight_id",
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
        "account_identity_later_required",
        "permission_check_later_required",
        "destination_binding_confirmed",
        "audit_redaction_confirmed",
        "combined_payload_hash",
        "account_binding_preflight_available",
        "account_binding_declared_ready",
        "eligible_for_live_dispatch_request_package_gate"
    ]
    for key in required_keys:
        if preflight.get(key) is None:
            blockers.append(f"preflight_field_missing_{key}")

    if preflight.get("task_label") != ACCOUNT_BINDING_PREFLIGHT_TASK_LABEL:
        blockers.append("preflight_task_label_invalid")

    gating_rules = {
        "account_binding_preflight_available": True,
        "account_binding_declared_ready": True,
        "eligible_for_live_dispatch_request_package_gate": True,
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
        "credential_presence_mode": "checked_declared_key_names_only",
        "credential_presence_complete": True,
        "account_identity_later_required": True,
        "permission_check_later_required": True,
        "destination_binding_confirmed": True,
        "audit_redaction_confirmed": True,
    }
    for field_name, expected in gating_rules.items():
        if preflight.get(field_name) != expected:
            blockers.append(f"preflight_field_{field_name}_invalid")

    if preflight.get("public_url") is not None:
        blockers.append("preflight_public_url_not_null")
    if preflight.get("public_metrics") is not None:
        blockers.append("preflight_public_metrics_not_null")

    if preflight.get("blockers"):
        blockers.append("preflight_blockers_not_empty")

    allowlist_rows = preflight.get("endpoint_allowlist_rows", [])
    if not isinstance(allowlist_rows, list) or len(allowlist_rows) != 2:
        blockers.append("preflight_endpoint_allowlist_rows_count_invalid")
    else:
        platforms_found = [row.get("platform") for row in allowlist_rows if isinstance(row, dict)]
        if platforms_found != ["substack", "discord"]:
            blockers.append("preflight_endpoint_allowlist_rows_platforms_invalid")

    binding_rows = preflight.get("platform_binding_rows", [])
    if not isinstance(binding_rows, list) or len(binding_rows) != 2:
        blockers.append("preflight_platform_binding_rows_count_invalid")
    else:
        platforms_found = [row.get("platform") for row in binding_rows if isinstance(row, dict)]
        if platforms_found != ["substack", "discord"]:
            blockers.append("preflight_platform_binding_rows_platforms_invalid")

    return blockers


def _validate_request_declaration(decl: dict[str, Any], preflight: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "dispatch_request_gate_declaration_id",
        "operator_id",
        "created_at_manual",
        "account_binding_preflight_id",
        "combined_payload_hash",
        "dispatch_request_gate_mode",
        "requested_platforms",
        "payload_hash_confirmed",
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
        "declaration_decision",
        "approval_phrase",
        "approval_scope",
        "notes"
    ]
    for key in required_keys:
        if decl.get(key) is None:
            blockers.append(f"declaration_field_missing_{key}")

    # Extra keys in declaration fail closed
    extra_keys = set(decl.keys()) - set(required_keys)
    for ek in sorted(extra_keys):
        blockers.append(f"declaration_extra_field_{ek}_detected")

    if decl.get("account_binding_preflight_id") != preflight.get("account_binding_preflight_id"):
        blockers.append("declaration_preflight_id_mismatch")

    if decl.get("dispatch_request_gate_mode") != "operator_declared_dispatch_request_package_gate_only_not_send":
        blockers.append("declaration_dispatch_request_gate_mode_invalid")

    req_platforms = decl.get("requested_platforms", [])
    if req_platforms != ["substack", "discord"]:
        blockers.append("declaration_requested_platforms_invalid")

    # Mismatches with preflight settings
    if decl.get("payload_hash_confirmed") != preflight.get("combined_payload_hash"):
        blockers.append("declaration_payload_hash_confirmed_mismatch")
    if decl.get("combined_payload_hash") != preflight.get("combined_payload_hash"):
        blockers.append("declaration_combined_payload_hash_mismatch")

    if decl.get("request_budget_confirmed") != preflight.get("live_write_request_budget_confirmed"):
        blockers.append("declaration_request_budget_confirmed_mismatch")

    if decl.get("timeout_policy_confirmed") != preflight.get("timeout_policy_confirmed"):
        blockers.append("declaration_timeout_policy_confirmed_mismatch")

    if decl.get("retry_policy_confirmed") != preflight.get("retry_policy_confirmed"):
        blockers.append("declaration_retry_policy_confirmed_mismatch")

    # Confirmation bools validation
    for b_field in [
        "kill_switch_confirmed",
        "audit_redaction_confirmed",
        "manual_fallback_confirmed",
        "account_binding_confirmed",
        "permission_check_later_required",
        "provider_execution_later_required",
        "operator_final_review_later_required"
    ]:
        if decl.get(b_field) is not True:
            blockers.append(f"declaration_field_{b_field}_not_true")

    # Decision validation
    dec = decl.get("declaration_decision")
    if dec not in ["mark_dispatch_request_package_gate_ready", "reject", "defer"]:
        blockers.append("declaration_decision_invalid")
    elif dec in ["reject", "defer"]:
        blockers.append(f"declaration_rejected_or_deferred_{dec}")
    elif dec == "mark_dispatch_request_package_gate_ready":
        if decl.get("approval_phrase") != "MARK_DISPATCH_REQUEST_PACKAGE_GATE_READY_ONLY_NOT_SEND":
            blockers.append("declaration_approval_phrase_invalid")
        if decl.get("approval_scope") != "dispatch_request_package_gate_only":
            blockers.append("declaration_approval_scope_invalid")

    notes = decl.get("notes")
    if notes is None or not isinstance(notes, str):
        blockers.append("declaration_notes_missing_or_invalid")

    return blockers


def _check_declaration_safety(decl_packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    # Popping platforms and notes and scanning
    decl_copy = dict(decl_packet)
    decl_copy.pop("requested_platforms", None)
    serialized = json.dumps(decl_copy)

    if _has_secret_marker(serialized):
        blockers.append(f"{prefix}_secret_marker_detected")

    # Check fake claims
    for claim in FAKE_CLAIMS_MARKERS:
        if claim in serialized.lower():
            blockers.append(f"{prefix}_fake_claim_detected_{claim}")

    # Check trading/financial advice or signal framing
    for pat in TRADING_ADVICE_RE:
        if pat.search(serialized):
            blockers.append(f"{prefix}_financial_advice_or_signal_framing_detected")
            break

    # Check forbidden live claims
    forbidden_term = _scan_for_forbidden_live_claims(serialized)
    if forbidden_term:
        blockers.append(f"{prefix}_forbidden_live_claim_detected_{forbidden_term.replace(' ', '_')}")

    return blockers


def make_dispatch_request_package_gate_packet(
    preflight_packet: Any,
    dispatch_request_declaration: Any,
) -> DispatchRequestPackageGatePacket:
    blockers: list[str] = []

    preflight_is_dict = isinstance(preflight_packet, dict)
    if not preflight_is_dict:
        blockers.append("malformed_live_dispatch_account_binding_preflight_packet_json")

    decl_is_dict = isinstance(dispatch_request_declaration, dict)
    if not decl_is_dict:
        blockers.append("malformed_operator_dispatch_request_declaration_json")

    # Secret scanner safety checks
    if preflight_is_dict:
        ready_copy = dict(preflight_packet)
        ready_copy.pop("credential_key_names_only", None)
        ready_copy.pop("endpoint_allowlist_rows", None)
        ready_copy.pop("platform_binding_rows", None)
        ready_copy.pop("destinations", None)
        if _has_secret_marker(json.dumps(ready_copy)):
            blockers.append("preflight_secret_marker_detected")

    if decl_is_dict:
        blockers.extend(_check_declaration_safety(dispatch_request_declaration, "declaration"))

    # Initial placeholder values
    dispatch_request_gate_declaration_id = ""
    operator_id = ""
    created_at_manual = ""
    account_binding_preflight_id = ""
    account_binding_preflight_sha256 = ""
    account_binding_declaration_id = ""
    credential_allowlist_preflight_id = ""
    credential_allowlist_preflight_sha256 = ""
    endpoint_allowlist_declaration_id = ""
    live_dispatch_scope_preflight_id = ""
    live_dispatch_scope_preflight_sha256 = ""
    live_dispatch_readiness_preflight_id = ""
    live_dispatch_readiness_preflight_sha256 = ""
    official_docs_declaration_id = ""
    live_scope_declaration_id = ""
    local_dispatch_execution_payload_manifest_id = ""
    operator_supervised_dispatch_review_decision_packet_id = ""
    local_destination_binding_preflight_id = ""
    destination_binding_id = ""
    local_dispatch_payload_manifest_id = ""
    operator_dispatch_review_decision_packet_id = ""
    local_dispatch_preflight_id = ""
    local_active_outbox_manifest_id = ""
    operator_active_outbox_review_decision_id = ""
    active_outbox_eligibility_id = ""
    outbox_package_staging_id = ""
    payload_review_ledger_id = ""
    approval_intent_id = ""
    variant_preview_staging_id = ""
    metadata_values_review_id = ""
    metadata_values_id = ""
    metadata_proposal_id = ""
    source_pack_intake_id = ""
    source_pack_id = ""
    editorial_workflow_id = ""
    canonical_slug = ""
    canonical_title = ""
    execution_preparation_json_files: list[str] = []
    execution_preparation_json_hashes: dict[str, str] = {}
    execution_preparation_markdown_files: list[str] = []
    execution_preparation_markdown_hashes: dict[str, str] = {}
    destinations: list[dict[str, Any]] = []
    platforms: list[str] = []
    credential_key_names_only: list[str] = []
    endpoint_allowlist_rows: list[dict[str, Any]] = []
    platform_binding_rows: list[dict[str, Any]] = []
    requested_platforms: list[str] = []
    request_budget_confirmed = 0
    timeout_policy_confirmed = ""
    retry_policy_confirmed = ""
    kill_switch_confirmed = False
    audit_redaction_confirmed = False
    manual_fallback_confirmed = False
    account_binding_confirmed = False
    permission_check_later_required = False
    provider_execution_later_required = False
    operator_final_review_later_required = False
    combined_payload_hash = ""

    if preflight_is_dict and "preflight_secret_marker_detected" not in blockers:
        blockers.extend(_validate_preflight_packet(preflight_packet))

        account_binding_preflight_id = str(preflight_packet.get("account_binding_preflight_id") or "")
        account_binding_declaration_id = str(preflight_packet.get("account_binding_declaration_id") or "")
        credential_allowlist_preflight_id = str(preflight_packet.get("credential_allowlist_preflight_id") or "")
        credential_allowlist_preflight_sha256 = str(preflight_packet.get("credential_allowlist_preflight_sha256") or "")
        endpoint_allowlist_declaration_id = str(preflight_packet.get("endpoint_allowlist_declaration_id") or "")
        live_dispatch_scope_preflight_id = str(preflight_packet.get("live_dispatch_scope_preflight_id") or "")
        live_dispatch_scope_preflight_sha256 = str(preflight_packet.get("live_dispatch_scope_preflight_sha256") or "")
        live_dispatch_readiness_preflight_id = str(preflight_packet.get("live_dispatch_readiness_preflight_id") or "")
        live_dispatch_readiness_preflight_sha256 = str(preflight_packet.get("live_dispatch_readiness_preflight_sha256") or "")
        official_docs_declaration_id = str(preflight_packet.get("official_docs_declaration_id") or "")
        live_scope_declaration_id = str(preflight_packet.get("live_scope_declaration_id") or "")
        local_dispatch_execution_payload_manifest_id = str(preflight_packet.get("local_dispatch_execution_payload_manifest_id") or "")
        operator_supervised_dispatch_review_decision_packet_id = str(preflight_packet.get("operator_supervised_dispatch_review_decision_packet_id") or "")
        local_destination_binding_preflight_id = str(preflight_packet.get("local_destination_binding_preflight_id") or "")
        destination_binding_id = str(preflight_packet.get("destination_binding_id") or "")
        local_dispatch_payload_manifest_id = str(preflight_packet.get("local_dispatch_payload_manifest_id") or "")
        operator_dispatch_review_decision_packet_id = str(preflight_packet.get("operator_dispatch_review_decision_packet_id") or "")
        local_dispatch_preflight_id = str(preflight_packet.get("local_dispatch_preflight_id") or "")
        local_active_outbox_manifest_id = str(preflight_packet.get("local_active_outbox_manifest_id") or "")
        operator_active_outbox_review_decision_id = str(preflight_packet.get("operator_active_outbox_review_decision_id") or "")
        active_outbox_eligibility_id = str(preflight_packet.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(preflight_packet.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(preflight_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(preflight_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(preflight_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(preflight_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(preflight_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(preflight_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(preflight_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(preflight_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(preflight_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(preflight_packet.get("canonical_slug") or "")
        canonical_title = str(preflight_packet.get("canonical_title") or "")
        execution_preparation_json_files = preflight_packet.get("execution_preparation_json_files", [])
        execution_preparation_json_hashes = preflight_packet.get("execution_preparation_json_hashes", {})
        execution_preparation_markdown_files = preflight_packet.get("execution_preparation_markdown_files", [])
        execution_preparation_markdown_hashes = preflight_packet.get("execution_preparation_markdown_hashes", {})
        destinations = preflight_packet.get("destinations", [])
        platforms = preflight_packet.get("platforms", [])
        credential_key_names_only = preflight_packet.get("credential_key_names_only", [])
        endpoint_allowlist_rows = preflight_packet.get("endpoint_allowlist_rows", [])
        platform_binding_rows = preflight_packet.get("platform_binding_rows", [])
        combined_payload_hash = str(preflight_packet.get("combined_payload_hash") or "")

        # Compute SHA256 of preflight packet only if no secret markers are present
        preflight_sha_check = dict(preflight_packet)
        preflight_sha_check.pop("credential_key_names_only", None)
        preflight_sha_check.pop("endpoint_allowlist_rows", None)
        preflight_sha_check.pop("platform_binding_rows", None)
        preflight_sha_check.pop("destinations", None)
        if not _has_secret_marker(json.dumps(preflight_sha_check)) and not any("secret_marker_detected" in b for b in blockers):
            account_binding_preflight_sha256 = hashlib.sha256(_canonical_json(preflight_packet).encode("utf-8")).hexdigest()

        if decl_is_dict and "declaration_secret_marker_detected" not in blockers:
            blockers.extend(_validate_request_declaration(dispatch_request_declaration, preflight_packet))
            dispatch_request_gate_declaration_id = str(dispatch_request_declaration.get("dispatch_request_gate_declaration_id") or "")
            operator_id = str(dispatch_request_declaration.get("operator_id") or "")
            created_at_manual = str(dispatch_request_declaration.get("created_at_manual") or "")
            requested_platforms = dispatch_request_declaration.get("requested_platforms", [])
            request_budget_confirmed = int(dispatch_request_declaration.get("request_budget_confirmed") or 0)
            timeout_policy_confirmed = str(dispatch_request_declaration.get("timeout_policy_confirmed") or "")
            retry_policy_confirmed = str(dispatch_request_declaration.get("retry_policy_confirmed") or "")
            kill_switch_confirmed = bool(dispatch_request_declaration.get("kill_switch_confirmed"))
            audit_redaction_confirmed = bool(dispatch_request_declaration.get("audit_redaction_confirmed"))
            manual_fallback_confirmed = bool(dispatch_request_declaration.get("manual_fallback_confirmed"))
            account_binding_confirmed = bool(dispatch_request_declaration.get("account_binding_confirmed"))
            permission_check_later_required = bool(dispatch_request_declaration.get("permission_check_later_required"))
            provider_execution_later_required = bool(dispatch_request_declaration.get("provider_execution_later_required"))
            operator_final_review_later_required = bool(dispatch_request_declaration.get("operator_final_review_later_required"))

    blockers = sorted(set(blockers))
    prepared = not blockers

    declared_ready = (
        prepared and decl_is_dict and (dispatch_request_declaration.get("declaration_decision") == "mark_dispatch_request_package_gate_ready")
    )

    eligible = prepared and declared_ready

    # Safety redaction on secret/marker detection
    has_secrets = (
        "preflight_secret_marker_detected" in blockers or
        "declaration_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        dispatch_request_gate_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        account_binding_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        account_binding_preflight_sha256 = ""
        account_binding_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        credential_allowlist_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        credential_allowlist_preflight_sha256 = ""
        endpoint_allowlist_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_dispatch_scope_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_dispatch_scope_preflight_sha256 = ""
        live_dispatch_readiness_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_dispatch_readiness_preflight_sha256 = ""
        official_docs_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_scope_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_dispatch_execution_payload_manifest_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_supervised_dispatch_review_decision_packet_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_destination_binding_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        destination_binding_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_dispatch_payload_manifest_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_dispatch_review_decision_packet_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_dispatch_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_active_outbox_manifest_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_active_outbox_review_decision_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        active_outbox_eligibility_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        outbox_package_staging_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        payload_review_ledger_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        approval_intent_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        variant_preview_staging_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_values_review_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_values_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_proposal_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_intake_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        editorial_workflow_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_slug = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_title = "[REDACTED_SECRET_MARKER_DETECTED]"
        execution_preparation_json_files = []
        execution_preparation_json_hashes = {}
        execution_preparation_markdown_files = []
        execution_preparation_markdown_hashes = {}
        destinations = []
        platforms = []
        credential_key_names_only = []
        endpoint_allowlist_rows = []
        platform_binding_rows = []
        requested_platforms = []
        combined_payload_hash = ""

    intake_material = {
        "account_binding_preflight_id": account_binding_preflight_id,
        "dispatch_request_gate_declaration_id": dispatch_request_gate_declaration_id,
        "blockers": blockers,
    }
    dispatch_request_package_gate_id = f"dispatch_request_gate_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("dispatch_request_package_gate_blocked_pending_operator_repair")

    return DispatchRequestPackageGatePacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        dispatch_request_package_gate_id=dispatch_request_package_gate_id,
        dispatch_request_gate_declaration_id=dispatch_request_gate_declaration_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        account_binding_preflight_id=account_binding_preflight_id,
        account_binding_preflight_sha256=account_binding_preflight_sha256,
        account_binding_declaration_id=account_binding_declaration_id,
        credential_allowlist_preflight_id=credential_allowlist_preflight_id,
        credential_allowlist_preflight_sha256=credential_allowlist_preflight_sha256,
        endpoint_allowlist_declaration_id=endpoint_allowlist_declaration_id,
        live_dispatch_scope_preflight_id=live_dispatch_scope_preflight_id,
        live_dispatch_scope_preflight_sha256=live_dispatch_scope_preflight_sha256,
        live_dispatch_readiness_preflight_id=live_dispatch_readiness_preflight_id,
        live_dispatch_readiness_preflight_sha256=live_dispatch_readiness_preflight_sha256,
        official_docs_declaration_id=official_docs_declaration_id,
        live_scope_declaration_id=live_scope_declaration_id,
        local_dispatch_execution_payload_manifest_id=local_dispatch_execution_payload_manifest_id,
        operator_supervised_dispatch_review_decision_packet_id=operator_supervised_dispatch_review_decision_packet_id,
        local_destination_binding_preflight_id=local_destination_binding_preflight_id,
        destination_binding_id=destination_binding_id,
        local_dispatch_payload_manifest_id=local_dispatch_payload_manifest_id,
        operator_dispatch_review_decision_packet_id=operator_dispatch_review_decision_packet_id,
        local_dispatch_preflight_id=local_dispatch_preflight_id,
        local_active_outbox_manifest_id=local_active_outbox_manifest_id,
        operator_active_outbox_review_decision_id=operator_active_outbox_review_decision_id,
        active_outbox_eligibility_id=active_outbox_eligibility_id,
        outbox_package_staging_id=outbox_package_staging_id,
        payload_review_ledger_id=payload_review_ledger_id,
        approval_intent_id=approval_intent_id,
        variant_preview_staging_id=variant_preview_staging_id,
        metadata_values_review_id=metadata_values_review_id,
        metadata_values_id=metadata_values_id,
        metadata_proposal_id=metadata_proposal_id,
        source_pack_intake_id=source_pack_intake_id,
        source_pack_id=source_pack_id,
        editorial_workflow_id=editorial_workflow_id,
        canonical_slug=canonical_slug,
        canonical_title=canonical_title,
        execution_preparation_json_files=execution_preparation_json_files,
        execution_preparation_json_hashes=execution_preparation_json_hashes,
        execution_preparation_markdown_files=execution_preparation_markdown_files,
        execution_preparation_markdown_hashes=execution_preparation_markdown_hashes,
        destinations=destinations,
        platforms=platforms,
        credential_key_names_only=credential_key_names_only,
        endpoint_allowlist_rows=endpoint_allowlist_rows,
        platform_binding_rows=platform_binding_rows,
        requested_platforms=requested_platforms,
        request_budget_confirmed=request_budget_confirmed,
        timeout_policy_confirmed=timeout_policy_confirmed,
        retry_policy_confirmed=retry_policy_confirmed,
        kill_switch_confirmed=kill_switch_confirmed,
        audit_redaction_confirmed=audit_redaction_confirmed,
        manual_fallback_confirmed=manual_fallback_confirmed,
        account_binding_confirmed=account_binding_confirmed,
        permission_check_later_required=permission_check_later_required,
        provider_execution_later_required=provider_execution_later_required,
        operator_final_review_later_required=operator_final_review_later_required,
        combined_payload_hash=combined_payload_hash,
        dispatch_request_package_gate_available=prepared,
        dispatch_request_package_gate_declared_ready=declared_ready,
        eligible_for_future_supervised_dispatch_request_package=eligible,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Local Live Dispatch Request Package Gate CLI")
    parser.add_argument("account_binding_preflight", help="Path to account-binding preflight packet JSON")
    parser.add_argument("dispatch_request_declaration", help="Path to operator dispatch-request declaration JSON")
    parser.add_argument("--output-file", required=True, help="Path to write request package gate packet")

    args = parser.parse_args(argv)

    try:
        preflight = load_json_packet(args.account_binding_preflight, "malformed_live_dispatch_account_binding_preflight_packet_json")
        decl = load_json_packet(args.dispatch_request_declaration, "malformed_operator_dispatch_request_declaration_json")

        packet = make_dispatch_request_package_gate_packet(preflight, decl)

        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")

        if not packet.dispatch_request_package_gate_available:
            return 1
        return 0

    except ValueError as val_err:
        packet = DispatchRequestPackageGatePacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            dispatch_request_package_gate_id=f"dispatch_request_gate_blocked_{str(val_err)}",
            dispatch_request_gate_declaration_id="",
            operator_id="",
            created_at_manual="",
            account_binding_preflight_id="",
            account_binding_preflight_sha256="",
            account_binding_declaration_id="",
            credential_allowlist_preflight_id="",
            credential_allowlist_preflight_sha256="",
            endpoint_allowlist_declaration_id="",
            live_dispatch_scope_preflight_id="",
            live_dispatch_scope_preflight_sha256="",
            live_dispatch_readiness_preflight_id="",
            live_dispatch_readiness_preflight_sha256="",
            official_docs_declaration_id="",
            live_scope_declaration_id="",
            local_dispatch_execution_payload_manifest_id="",
            operator_supervised_dispatch_review_decision_packet_id="",
            local_destination_binding_preflight_id="",
            destination_binding_id="",
            local_dispatch_payload_manifest_id="",
            operator_dispatch_review_decision_packet_id="",
            local_dispatch_preflight_id="",
            local_active_outbox_manifest_id="",
            operator_active_outbox_review_decision_id="",
            active_outbox_eligibility_id="",
            outbox_package_staging_id="",
            payload_review_ledger_id="",
            approval_intent_id="",
            variant_preview_staging_id="",
            metadata_values_review_id="",
            metadata_values_id="",
            metadata_proposal_id="",
            source_pack_intake_id="",
            source_pack_id="",
            editorial_workflow_id="",
            canonical_slug="",
            canonical_title="",
            execution_preparation_json_files=[],
            execution_preparation_json_hashes={},
            execution_preparation_markdown_files=[],
            execution_preparation_markdown_hashes={},
            destinations=[],
            platforms=[],
            credential_key_names_only=[],
            endpoint_allowlist_rows=[],
            platform_binding_rows=[],
            requested_platforms=[],
            request_budget_confirmed=0,
            timeout_policy_confirmed="",
            retry_policy_confirmed="",
            kill_switch_confirmed=False,
            audit_redaction_confirmed=False,
            manual_fallback_confirmed=False,
            account_binding_confirmed=False,
            permission_check_later_required=False,
            provider_execution_later_required=False,
            operator_final_review_later_required=False,
            combined_payload_hash="",
            dispatch_request_package_gate_available=False,
            dispatch_request_package_gate_declared_ready=False,
            eligible_for_future_supervised_dispatch_request_package=False,
            blockers=[str(val_err)],
            warnings=["dispatch_request_package_gate_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
