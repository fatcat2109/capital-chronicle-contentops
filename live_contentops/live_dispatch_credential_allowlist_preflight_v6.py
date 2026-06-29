"""V6 Live Dispatch Credential and Allowlist Preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_CREDENTIAL_AND_ALLOWLIST_PREFLIGHT_FROM_SCOPE_V0"
SCOPE_TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_OFFICIAL_DOCS_AND_SCOPE_PREFLIGHT_FROM_READINESS_V0"
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

CITATION_CLAIMS_MARKERS = (
    "citations_verified",
    "generated_citations_allowed",
    "citations_verified_true",
    "generated_citations",
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
    "mark_official_docs_review_declared",
    "supervised_dispatch_future_gate",
    "live_dispatch_readiness_preflight_id",
    "live_dispatch_readiness_preflight_sha256",
    "live_dispatch_readiness_declaration_id",
    "live_dispatch_scope_preflight_id",
    "live_dispatch_scope_preflight_available",
    "eligible_for_supervised_live_gate",
    "live_scope_declared_ready",
    "live_send_request_created",
    "approval_for_live_dispatch",
    "dispatch_family",
    "action_class",
    "webhook_url",
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
class CredentialAllowlistPreflightPacket:
    schema_version: str
    task_label: str
    credential_allowlist_preflight_id: str
    endpoint_allowlist_declaration_id: str
    operator_id: str
    created_at_manual: str
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
    credential_presence_mode: str
    credential_presence_rows: list[dict[str, Any]]
    credential_presence_complete: bool
    endpoint_allowlist_rows: list[dict[str, Any]]
    live_write_request_budget_confirmed: int
    timeout_policy_confirmed: str
    retry_policy_confirmed: str
    audit_redaction_confirmed: bool
    manual_fallback_required: bool
    combined_payload_hash: str
    credential_allowlist_preflight_available: bool
    endpoint_allowlist_declared_ready: bool
    eligible_for_supervised_live_dispatch_request_gate: bool
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
        "credential_key_names_only_reviewed",
        "credential_key_names_only",
        "credential_presence_mode",
        "credential_presence_rows",
        "credential_presence_complete",
        "checked_declared_key_names_only",
        "webhook_family_target",
        "non_secret_label_only",
        "webhook_method_label_only",
        "discord_operator_declared_webhook_host_label",
        "discord_operator_declared_webhook_path_label",
        "mark_credential_allowlist_ready_for_future_live_gate_only_not_send",
        "mark_credential_allowlist_ready_for_future_live_gate",
        "credential_allowlist_preflight_only",
        "credential_allowlist_preflight_id",
        "credential_allowlist_preflight_available",
        "endpoint_allowlist_declared_ready",
        "eligible_for_supervised_live_dispatch_request_gate",
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


def _validate_scope_packet(scope: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "task_label",
        "live_dispatch_scope_preflight_id",
        "official_docs_declaration_id",
        "live_scope_declaration_id",
        "live_dispatch_readiness_preflight_id",
        "live_dispatch_readiness_preflight_sha256",
        "live_dispatch_readiness_declaration_id",
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
        "account_binding_later_required",
        "endpoint_allowlist_later_required",
        "payload_hash_later_required",
        "explicit_operator_approval_later_required",
        "kill_switch_required",
        "manual_fallback_required",
        "live_write_request_budget_later",
        "timeout_policy_later",
        "retry_policy_later",
        "audit_redaction_required",
        "combined_payload_hash",
        "live_dispatch_scope_preflight_available",
        "eligible_for_supervised_live_gate",
        "official_docs_scope_declared_ready",
        "live_scope_declared_ready"
    ]
    for key in required_keys:
        if scope.get(key) is None:
            blockers.append(f"scope_field_missing_{key}")

    if scope.get("task_label") != SCOPE_TASK_LABEL:
        blockers.append("scope_task_label_invalid")

    gating_rules = {
        "live_dispatch_scope_preflight_available": True,
        "eligible_for_supervised_live_gate": True,
        "official_docs_scope_declared_ready": True,
        "live_scope_declared_ready": True,
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
        "account_binding_later_required": True,
        "endpoint_allowlist_later_required": True,
        "payload_hash_later_required": True,
        "explicit_operator_approval_later_required": True,
        "kill_switch_required": True,
        "manual_fallback_required": True,
        "audit_redaction_required": True,
        "action_class": "supervised_live_dispatch_future_gate",
        "dispatch_family": "substack_discord_dispatch_family",
        "platforms": ["substack", "discord"],
    }
    for field_name, expected in gating_rules.items():
        if scope.get(field_name) != expected:
            blockers.append(f"scope_field_{field_name}_invalid")

    if scope.get("public_url") is not None:
        blockers.append("scope_public_url_not_null")
    if scope.get("public_metrics") is not None:
        blockers.append("scope_public_metrics_not_null")

    if scope.get("blockers"):
        blockers.append("scope_blockers_not_empty")

    # Budget policy validation
    budget = scope.get("live_write_request_budget_later")
    if not isinstance(budget, int) or budget < 1 or budget > 3:
        blockers.append("scope_live_write_request_budget_later_invalid")

    if scope.get("retry_policy_later") != "no_hidden_retry":
        blockers.append("scope_retry_policy_later_invalid")

    # Element counts verification
    if not isinstance(scope.get("execution_preparation_json_files"), list) or len(scope.get("execution_preparation_json_files", [])) != 2:
        blockers.append("scope_execution_preparation_json_files_count_invalid")
    if not isinstance(scope.get("execution_preparation_json_hashes"), dict) or len(scope.get("execution_preparation_json_hashes", {})) != 2:
        blockers.append("scope_execution_preparation_json_hashes_count_invalid")
    if not isinstance(scope.get("execution_preparation_markdown_files"), list) or len(scope.get("execution_preparation_markdown_files", [])) != 2:
        blockers.append("scope_execution_preparation_markdown_files_count_invalid")
    if not isinstance(scope.get("execution_preparation_markdown_hashes"), dict) or len(scope.get("execution_preparation_markdown_hashes", {})) != 2:
        blockers.append("scope_execution_preparation_markdown_hashes_count_invalid")

    destinations = scope.get("destinations", [])
    if not isinstance(destinations, list) or len(destinations) != 2:
        blockers.append("scope_destinations_count_invalid")

    if not isinstance(scope.get("credential_key_names_only"), list):
        blockers.append("scope_credential_key_names_only_invalid_type")

    return blockers


def _validate_allowlist_declaration(decl: dict[str, Any], scope: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "endpoint_allowlist_declaration_id",
        "operator_id",
        "created_at_manual",
        "live_dispatch_scope_preflight_id",
        "combined_payload_hash",
        "allowlist_mode",
        "endpoint_allowlist_rows",
        "credential_key_names_only_reviewed",
        "live_write_request_budget_confirmed",
        "timeout_policy_confirmed",
        "retry_policy_confirmed",
        "audit_redaction_confirmed",
        "declaration_decision",
        "approval_phrase",
        "approval_scope",
        "notes"
    ]
    for key in required_keys:
        if decl.get(key) is None:
            blockers.append(f"allowlist_field_missing_{key}")

    # Extra keys in root declaration
    extra_keys = set(decl.keys()) - set(required_keys)
    for ek in sorted(extra_keys):
        blockers.append(f"allowlist_extra_field_{ek}_detected")

    if decl.get("live_dispatch_scope_preflight_id") != scope.get("live_dispatch_scope_preflight_id"):
        blockers.append("allowlist_scope_preflight_id_mismatch")
    if decl.get("combined_payload_hash") != scope.get("combined_payload_hash"):
        blockers.append("allowlist_combined_payload_hash_mismatch")

    if decl.get("allowlist_mode") != "operator_declared_endpoint_allowlist_only_not_request":
        blockers.append("allowlist_allowlist_mode_invalid")

    # Mismatches with scope preflight settings
    scope_keys = scope.get("credential_key_names_only", [])
    decl_keys = decl.get("credential_key_names_only_reviewed", [])
    if not isinstance(decl_keys, list) or decl_keys != scope_keys:
        blockers.append("allowlist_credential_key_names_only_reviewed_mismatch")

    if decl.get("live_write_request_budget_confirmed") != scope.get("live_write_request_budget_later"):
        blockers.append("allowlist_live_write_request_budget_confirmed_mismatch")

    if decl.get("timeout_policy_confirmed") != scope.get("timeout_policy_later"):
        blockers.append("allowlist_timeout_policy_confirmed_mismatch")

    if decl.get("retry_policy_confirmed") != scope.get("retry_policy_later"):
        blockers.append("allowlist_retry_policy_confirmed_mismatch")

    if decl.get("audit_redaction_confirmed") is not True:
        blockers.append("allowlist_audit_redaction_confirmed_not_true")

    # Decision validation
    dec = decl.get("declaration_decision")
    if dec not in ["mark_credential_allowlist_ready_for_future_live_gate", "reject", "defer"]:
        blockers.append("allowlist_decision_invalid")
    elif dec in ["reject", "defer"]:
        blockers.append(f"allowlist_declaration_rejected_or_deferred_{dec}")
    elif dec == "mark_credential_allowlist_ready_for_future_live_gate":
        if decl.get("approval_phrase") != "MARK_CREDENTIAL_ALLOWLIST_READY_FOR_FUTURE_LIVE_GATE_ONLY_NOT_SEND":
            blockers.append("allowlist_approval_phrase_invalid")
        if decl.get("approval_scope") != "credential_allowlist_preflight_only":
            blockers.append("allowlist_approval_scope_invalid")

    notes = decl.get("notes")
    if notes is None or not isinstance(notes, str):
        blockers.append("allowlist_notes_missing_or_invalid")

    # Rows validation
    rows = decl.get("endpoint_allowlist_rows", [])
    if not isinstance(rows, list) or len(rows) != 2:
        blockers.append("allowlist_rows_count_invalid")
    else:
        platforms_found = []
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                blockers.append(f"allowlist_row_index_{idx}_not_dict")
                continue

            row_req = [
                "platform",
                "action_family",
                "host_label",
                "path_label",
                "method_label",
                "endpoint_allowlist_kind",
                "request_budget",
                "timeout_policy_label",
                "retry_policy_label",
                "audit_redaction_required",
                "manual_fallback_required",
                "operator_notes"
            ]
            for rk in row_req:
                if row.get(rk) is None:
                    blockers.append(f"allowlist_row_index_{idx}_missing_{rk}")

            # Extra fields in row fail closed
            row_extra_keys = set(row.keys()) - set(row_req)
            for ek in sorted(row_extra_keys):
                blockers.append(f"allowlist_row_index_{idx}_extra_field_{ek}_detected")

            platform = row.get("platform")
            if platform not in ["substack", "discord"]:
                blockers.append(f"allowlist_row_index_{idx}_platform_invalid")
            else:
                platforms_found.append(platform)

            if row.get("action_family") != "future_supervised_live_dispatch":
                blockers.append(f"allowlist_row_index_{idx}_action_family_invalid")

            # host_label validation: non-empty, no URL or domain value
            host = row.get("host_label")
            if not isinstance(host, str) or not host.strip():
                blockers.append(f"allowlist_row_index_{idx}_host_label_missing")
            else:
                if "http://" in host or "https://" in host or "." in host or "/" in host:
                    blockers.append(f"allowlist_row_index_{idx}_host_label_contains_url_or_domain")

            # path_label validation: non-empty, not starting with /, no domain/http/api/webhook/etc.
            path = row.get("path_label")
            if not isinstance(path, str) or not path.strip():
                blockers.append(f"allowlist_row_index_{idx}_path_label_missing")
            else:
                if path.startswith("/"):
                    blockers.append(f"allowlist_row_index_{idx}_path_label_starts_with_slash")
                banned_path_terms = ["http", ".com", "api.", "webhook", "token", "channel", "account"]
                for term in banned_path_terms:
                    if term in path.lower():
                        blockers.append(f"allowlist_row_index_{idx}_path_label_contains_forbidden_term_{term}")

            method = row.get("method_label")
            if method not in ["post_method_label_only", "browser_manual_method_label_only", "webhook_method_label_only"]:
                blockers.append(f"allowlist_row_index_{idx}_method_label_invalid")

            if row.get("endpoint_allowlist_kind") != "label_only_no_endpoint_value":
                blockers.append(f"allowlist_row_index_{idx}_endpoint_allowlist_kind_invalid")

            budget_val = row.get("request_budget")
            scope_budget = scope.get("live_write_request_budget_later", 0)
            if not isinstance(budget_val, int) or budget_val < 1 or budget_val > scope_budget:
                blockers.append(f"allowlist_row_index_{idx}_request_budget_invalid")

            if row.get("timeout_policy_label") != scope.get("timeout_policy_later"):
                blockers.append(f"allowlist_row_index_{idx}_timeout_policy_label_mismatch")

            if row.get("retry_policy_label") != scope.get("retry_policy_later"):
                blockers.append(f"allowlist_row_index_{idx}_retry_policy_label_mismatch")

            if row.get("audit_redaction_required") is not True:
                blockers.append(f"allowlist_row_index_{idx}_audit_redaction_required_not_true")

            if row.get("manual_fallback_required") is not True:
                blockers.append(f"allowlist_row_index_{idx}_manual_fallback_required_not_true")

            op_notes = row.get("operator_notes")
            if not isinstance(op_notes, str):
                blockers.append(f"allowlist_row_index_{idx}_operator_notes_invalid")

            # Check safety in row text
            row_serialized = json.dumps(row)
            if _has_secret_marker(row_serialized):
                blockers.append(f"allowlist_row_index_{idx}_secret_marker_detected")

            forbidden_term = _scan_for_forbidden_live_claims(row_serialized)
            if forbidden_term:
                blockers.append(f"allowlist_row_index_{idx}_forbidden_live_claim_detected_{forbidden_term.replace(' ', '_')}")

        if len(platforms_found) != 2 or platforms_found != ["substack", "discord"]:
            blockers.append("allowlist_rows_platforms_invalid_order_or_values")

    return blockers


def _check_declaration_safety(decl_packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    # Popping credential key names and allowlist rows and scanning
    decl_copy = dict(decl_packet)
    decl_copy.pop("credential_key_names_only_reviewed", None)
    decl_copy.pop("endpoint_allowlist_rows", None)
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


def make_credential_allowlist_preflight_packet(
    scope_packet: Any,
    allowlist_declaration: Any,
    check_env: bool = False,
    env_mapping: Mapping[str, str] | None = None,
) -> CredentialAllowlistPreflightPacket:
    blockers: list[str] = []

    scope_is_dict = isinstance(scope_packet, dict)
    if not scope_is_dict:
        blockers.append("malformed_live_dispatch_scope_preflight_packet_json")

    decl_is_dict = isinstance(allowlist_declaration, dict)
    if not decl_is_dict:
        blockers.append("malformed_operator_endpoint_allowlist_declaration_json")

    # Secret scanner safety checks
    if scope_is_dict:
        ready_copy = dict(scope_packet)
        ready_copy.pop("credential_key_names_only", None)
        if _has_secret_marker(json.dumps(ready_copy)):
            blockers.append("scope_secret_marker_detected")

    if decl_is_dict:
        blockers.extend(_check_declaration_safety(allowlist_declaration, "allowlist"))

    # Initial placeholder values
    endpoint_allowlist_declaration_id = ""
    operator_id = ""
    created_at_manual = ""
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
    live_write_request_budget_confirmed = 0
    timeout_policy_confirmed = ""
    retry_policy_confirmed = ""
    audit_redaction_confirmed = False
    manual_fallback_required = False
    combined_payload_hash = ""

    if scope_is_dict and "scope_secret_marker_detected" not in blockers:
        blockers.extend(_validate_scope_packet(scope_packet))

        live_dispatch_scope_preflight_id = str(scope_packet.get("live_dispatch_scope_preflight_id") or "")
        live_dispatch_readiness_preflight_id = str(scope_packet.get("live_dispatch_readiness_preflight_id") or "")
        live_dispatch_readiness_preflight_sha256 = str(scope_packet.get("live_dispatch_readiness_preflight_sha256") or "")
        official_docs_declaration_id = str(scope_packet.get("official_docs_declaration_id") or "")
        live_scope_declaration_id = str(scope_packet.get("live_scope_declaration_id") or "")
        local_dispatch_execution_payload_manifest_id = str(scope_packet.get("local_dispatch_execution_payload_manifest_id") or "")
        operator_supervised_dispatch_review_decision_packet_id = str(scope_packet.get("operator_supervised_dispatch_review_decision_packet_id") or "")
        local_destination_binding_preflight_id = str(scope_packet.get("local_destination_binding_preflight_id") or "")
        destination_binding_id = str(scope_packet.get("destination_binding_id") or "")
        local_dispatch_payload_manifest_id = str(scope_packet.get("local_dispatch_payload_manifest_id") or "")
        operator_dispatch_review_decision_packet_id = str(scope_packet.get("operator_dispatch_review_decision_packet_id") or "")
        local_dispatch_preflight_id = str(scope_packet.get("local_dispatch_preflight_id") or "")
        local_active_outbox_manifest_id = str(scope_packet.get("local_active_outbox_manifest_id") or "")
        operator_active_outbox_review_decision_id = str(scope_packet.get("operator_active_outbox_review_decision_id") or "")
        active_outbox_eligibility_id = str(scope_packet.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(scope_packet.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(scope_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(scope_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(scope_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(scope_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(scope_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(scope_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(scope_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(scope_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(scope_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(scope_packet.get("canonical_slug") or "")
        canonical_title = str(scope_packet.get("canonical_title") or "")
        execution_preparation_json_files = scope_packet.get("execution_preparation_json_files", [])
        execution_preparation_json_hashes = scope_packet.get("execution_preparation_json_hashes", {})
        execution_preparation_markdown_files = scope_packet.get("execution_preparation_markdown_files", [])
        execution_preparation_markdown_hashes = scope_packet.get("execution_preparation_markdown_hashes", {})
        destinations = scope_packet.get("destinations", [])
        platforms = scope_packet.get("platforms", [])
        credential_key_names_only = scope_packet.get("credential_key_names_only", [])
        combined_payload_hash = str(scope_packet.get("combined_payload_hash") or "")

        # Compute scope preflight SHA256 canonical JSON
        scope_copy = dict(scope_packet)
        scope_copy.pop("credential_key_names_only", None)
        if not _has_secret_marker(json.dumps(scope_copy)):
            live_dispatch_scope_preflight_sha256 = hashlib.sha256(_canonical_json(scope_packet).encode("utf-8")).hexdigest()

        if decl_is_dict and "allowlist_secret_marker_detected" not in blockers:
            blockers.extend(_validate_allowlist_declaration(allowlist_declaration, scope_packet))
            endpoint_allowlist_declaration_id = str(allowlist_declaration.get("endpoint_allowlist_declaration_id") or "")
            operator_id = str(allowlist_declaration.get("operator_id") or "")
            created_at_manual = str(allowlist_declaration.get("created_at_manual") or "")
            endpoint_allowlist_rows = allowlist_declaration.get("endpoint_allowlist_rows", [])
            live_write_request_budget_confirmed = int(allowlist_declaration.get("live_write_request_budget_confirmed") or 0)
            timeout_policy_confirmed = str(allowlist_declaration.get("timeout_policy_confirmed") or "")
            retry_policy_confirmed = str(allowlist_declaration.get("retry_policy_confirmed") or "")
            audit_redaction_confirmed = bool(allowlist_declaration.get("audit_redaction_confirmed"))
            manual_fallback_required = True

    # Credential presence checking logic
    credential_presence_rows: list[dict[str, Any]] = []
    credential_presence_complete = False
    credential_presence_mode = "not_checked"

    if scope_is_dict:
        if check_env:
            credential_presence_mode = "checked_declared_key_names_only"
            all_present = True
            for key in credential_key_names_only:
                is_present = False
                if env_mapping is not None:
                    is_present = key in env_mapping
                else:
                    is_present = getattr(os, "environ").get(key) is not None

                if not is_present:
                    all_present = False

                credential_presence_rows.append({
                    "key_name": key,
                    "present": is_present,
                    "checked_by_exact_declared_key_name": True,
                    "value_observed": False,
                    "value_length_observed": False,
                    "value_hash_observed": False,
                    "value_prefix_observed": False,
                    "value_suffix_observed": False
                })
            credential_presence_complete = all_present
            if not credential_presence_complete:
                blockers.append("credential_presence_incomplete")
        else:
            credential_presence_mode = "not_checked"

    blockers = sorted(set(blockers))
    severe_blockers = [b for b in blockers if b != "credential_presence_incomplete"]
    prepared = not severe_blockers

    endpoint_allowlist_declared_ready = (
        prepared and decl_is_dict and (allowlist_declaration.get("declaration_decision") == "mark_credential_allowlist_ready_for_future_live_gate")
    )

    eligible = (
        prepared and
        endpoint_allowlist_declared_ready and
        credential_presence_mode == "checked_declared_key_names_only" and
        credential_presence_complete and
        not blockers
    )

    # Safety redaction on secret/marker detection
    has_secrets = (
        "scope_secret_marker_detected" in blockers or
        "allowlist_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        endpoint_allowlist_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
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
        credential_presence_rows = []
        combined_payload_hash = ""

    intake_material = {
        "live_dispatch_scope_preflight_id": live_dispatch_scope_preflight_id,
        "endpoint_allowlist_declaration_id": endpoint_allowlist_declaration_id,
        "blockers": blockers,
    }
    credential_allowlist_preflight_id = f"credential_allowlist_preflight_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("credential_allowlist_preflight_blocked_pending_operator_repair")

    return CredentialAllowlistPreflightPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        credential_allowlist_preflight_id=credential_allowlist_preflight_id,
        endpoint_allowlist_declaration_id=endpoint_allowlist_declaration_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
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
        credential_presence_mode=credential_presence_mode,
        credential_presence_rows=credential_presence_rows,
        credential_presence_complete=credential_presence_complete,
        endpoint_allowlist_rows=endpoint_allowlist_rows,
        live_write_request_budget_confirmed=live_write_request_budget_confirmed,
        timeout_policy_confirmed=timeout_policy_confirmed,
        retry_policy_confirmed=retry_policy_confirmed,
        audit_redaction_confirmed=audit_redaction_confirmed,
        manual_fallback_required=manual_fallback_required,
        combined_payload_hash=combined_payload_hash,
        credential_allowlist_preflight_available=prepared,
        endpoint_allowlist_declared_ready=endpoint_allowlist_declared_ready,
        eligible_for_supervised_live_dispatch_request_gate=eligible,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Dispatch Credential and Allowlist Preflight CLI")
    parser.add_argument("scope_packet", help="Path to live dispatch official-docs/scope preflight packet JSON")
    parser.add_argument("allowlist_declaration", help="Path to operator endpoint allowlist declaration JSON")
    parser.add_argument("--check-env-presence", action="store_true", help="Check exact declared keys in process environment")
    parser.add_argument("--output-file", required=True, help="Path to write credential/allowlist preflight packet")

    args = parser.parse_args(argv)

    try:
        scope = load_json_packet(args.scope_packet, "malformed_live_dispatch_scope_preflight_packet_json")
        decl = load_json_packet(args.allowlist_declaration, "malformed_operator_endpoint_allowlist_declaration_json")

        packet = make_credential_allowlist_preflight_packet(scope, decl, check_env=args.check_env_presence)

        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")

        if not packet.credential_allowlist_preflight_available:
            return 1
        return 0

    except ValueError as val_err:
        packet = CredentialAllowlistPreflightPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            credential_allowlist_preflight_id=f"credential_allowlist_preflight_blocked_{str(val_err)}",
            endpoint_allowlist_declaration_id="",
            operator_id="",
            created_at_manual="",
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
            credential_presence_mode="not_checked",
            credential_presence_rows=[],
            credential_presence_complete=False,
            endpoint_allowlist_rows=[],
            live_write_request_budget_confirmed=0,
            timeout_policy_confirmed="",
            retry_policy_confirmed="",
            audit_redaction_confirmed=False,
            manual_fallback_required=False,
            combined_payload_hash="",
            credential_allowlist_preflight_available=False,
            endpoint_allowlist_declared_ready=False,
            eligible_for_supervised_live_dispatch_request_gate=False,
            blockers=[str(val_err)],
            warnings=["credential_allowlist_preflight_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
