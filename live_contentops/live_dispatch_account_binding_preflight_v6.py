"""V6 Live Dispatch Account Binding Preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_ACCOUNT_BINDING_PREFLIGHT_FROM_CREDENTIAL_ALLOWLIST_V0"
PREFLIGHT_TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_CREDENTIAL_AND_ALLOWLIST_PREFLIGHT_FROM_SCOPE_V0"
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
)


def _scan_for_forbidden_live_claims(text: str) -> str | None:
    lowered = text.lower()
    for phrase in ALLOWED_SCHEMA_PHRASES:
        lowered = lowered.replace(phrase.lower(), "")
    for term in FORBIDDEN_LIVE_CLAIMS:
        if term in lowered:
            return term
    return None


FORBIDDEN_BINDING_ROW_CLAIMS = (
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
    "api_request", "api request",
    "browser_request", "browser request",
    "platform_request", "platform request",
    "public_url", "public url",
    "public_metrics", "public metrics",
    "ready_for_publication", "ready for publication",
    "publication_ready", "publication ready",
    "dispatch_allowed", "dispatch allowed"
)


def _scan_for_forbidden_binding_row_claims(text: str) -> str | None:
    lowered = text.lower()
    for phrase in ALLOWED_SCHEMA_PHRASES:
        lowered = lowered.replace(phrase.lower(), "")
    for term in FORBIDDEN_BINDING_ROW_CLAIMS:
        if term in lowered:
            return term
    return None


@dataclass(frozen=True)
class AccountBindingPreflightPacket:
    schema_version: str
    task_label: str
    account_binding_preflight_id: str
    account_binding_declaration_id: str
    operator_id: str
    created_at_manual: str
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
    credential_presence_mode: str
    credential_presence_complete: bool
    endpoint_allowlist_rows: list[dict[str, Any]]
    platform_binding_rows: list[dict[str, Any]]
    account_identity_later_required: bool
    permission_check_later_required: bool
    destination_binding_confirmed: bool
    live_write_request_budget_confirmed: int
    timeout_policy_confirmed: str
    retry_policy_confirmed: str
    audit_redaction_confirmed: bool
    combined_payload_hash: str
    account_binding_preflight_available: bool
    account_binding_declared_ready: bool
    eligible_for_live_dispatch_request_package_gate: bool
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
        "credential_allowlist_preflight_id",
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
        "credential_presence_mode",
        "credential_presence_complete",
        "endpoint_allowlist_rows",
        "live_write_request_budget_confirmed",
        "timeout_policy_confirmed",
        "retry_policy_confirmed",
        "audit_redaction_confirmed",
        "combined_payload_hash",
        "credential_allowlist_preflight_available",
        "endpoint_allowlist_declared_ready",
        "eligible_for_supervised_live_dispatch_request_gate"
    ]
    for key in required_keys:
        if preflight.get(key) is None:
            blockers.append(f"preflight_field_missing_{key}")

    if preflight.get("task_label") != PREFLIGHT_TASK_LABEL:
        blockers.append("preflight_task_label_invalid")

    gating_rules = {
        "credential_allowlist_preflight_available": True,
        "endpoint_allowlist_declared_ready": True,
        "eligible_for_supervised_live_dispatch_request_gate": True,
        "credential_presence_mode": "checked_declared_key_names_only",
        "credential_presence_complete": True,
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

    rows = preflight.get("credential_presence_rows", [])
    if not isinstance(rows, list) or not rows:
        blockers.append("preflight_credential_presence_rows_invalid")
    else:
        for idx, row in enumerate(rows):
            row_req = {
                "checked_by_exact_declared_key_name": True,
                "present": True,
                "value_observed": False,
                "value_length_observed": False,
                "value_hash_observed": False,
                "value_prefix_observed": False,
                "value_suffix_observed": False,
            }
            for rk, rv in row_req.items():
                if row.get(rk) != rv:
                    blockers.append(f"preflight_credential_row_{idx}_field_{rk}_invalid")

    allowlist_rows = preflight.get("endpoint_allowlist_rows", [])
    if not isinstance(allowlist_rows, list) or len(allowlist_rows) != 2:
        blockers.append("preflight_endpoint_allowlist_rows_count_invalid")
    else:
        platforms_found = [row.get("platform") for row in allowlist_rows if isinstance(row, dict)]
        if platforms_found != ["substack", "discord"]:
            blockers.append("preflight_endpoint_allowlist_rows_platforms_invalid")

    return blockers


def _validate_binding_declaration(decl: dict[str, Any], preflight: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    required_keys = [
        "schema_version",
        "account_binding_declaration_id",
        "operator_id",
        "created_at_manual",
        "credential_allowlist_preflight_id",
        "combined_payload_hash",
        "account_binding_mode",
        "platform_binding_rows",
        "account_identity_later_required",
        "permission_check_later_required",
        "destination_binding_confirmed",
        "credential_key_names_only_reviewed",
        "endpoint_allowlist_rows_reviewed",
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
            blockers.append(f"binding_field_missing_{key}")

    # Extra keys in root declaration
    extra_keys = set(decl.keys()) - set(required_keys)
    for ek in sorted(extra_keys):
        blockers.append(f"binding_extra_field_{ek}_detected")

    if decl.get("credential_allowlist_preflight_id") != preflight.get("credential_allowlist_preflight_id"):
        blockers.append("binding_preflight_id_mismatch")
    if decl.get("combined_payload_hash") != preflight.get("combined_payload_hash"):
        blockers.append("binding_combined_payload_hash_mismatch")

    if decl.get("account_binding_mode") != "operator_declared_account_binding_labels_only_not_verified":
        blockers.append("binding_account_binding_mode_invalid")

    # Mismatches with preflight settings
    preflight_keys = preflight.get("credential_key_names_only", [])
    decl_keys = decl.get("credential_key_names_only_reviewed", [])
    if not isinstance(decl_keys, list) or decl_keys != preflight_keys:
        blockers.append("binding_credential_key_names_only_reviewed_mismatch")

    # endpoint_allowlist_rows_reviewed check
    preflight_allowlist = preflight.get("endpoint_allowlist_rows", [])
    decl_allowlist = decl.get("endpoint_allowlist_rows_reviewed", [])
    if _canonical_json(decl_allowlist) != _canonical_json(preflight_allowlist):
        blockers.append("binding_endpoint_allowlist_rows_reviewed_mismatch")

    if decl.get("live_write_request_budget_confirmed") != preflight.get("live_write_request_budget_confirmed"):
        blockers.append("binding_live_write_request_budget_confirmed_mismatch")

    if decl.get("timeout_policy_confirmed") != preflight.get("timeout_policy_confirmed"):
        blockers.append("binding_timeout_policy_confirmed_mismatch")

    if decl.get("retry_policy_confirmed") != preflight.get("retry_policy_confirmed"):
        blockers.append("binding_retry_policy_confirmed_mismatch")

    if decl.get("audit_redaction_confirmed") is not True:
        blockers.append("binding_audit_redaction_confirmed_not_true")

    if decl.get("account_identity_later_required") is not True:
        blockers.append("binding_account_identity_later_required_not_true")

    if decl.get("permission_check_later_required") is not True:
        blockers.append("binding_permission_check_later_required_not_true")

    if decl.get("destination_binding_confirmed") is not True:
        blockers.append("binding_destination_binding_confirmed_not_true")

    # Decision validation
    dec = decl.get("declaration_decision")
    if dec not in ["mark_account_binding_ready_for_future_live_request_gate", "reject", "defer"]:
        blockers.append("binding_decision_invalid")
    elif dec in ["reject", "defer"]:
        blockers.append(f"binding_declaration_rejected_or_deferred_{dec}")
    elif dec == "mark_account_binding_ready_for_future_live_request_gate":
        if decl.get("approval_phrase") != "MARK_ACCOUNT_BINDING_READY_FOR_FUTURE_LIVE_REQUEST_GATE_ONLY_NOT_SEND":
            blockers.append("binding_approval_phrase_invalid")
        if decl.get("approval_scope") != "account_binding_preflight_only":
            blockers.append("binding_approval_scope_invalid")

    notes = decl.get("notes")
    if notes is None or not isinstance(notes, str):
        blockers.append("binding_notes_missing_or_invalid")

    # Rows validation
    rows = decl.get("platform_binding_rows", [])
    if not isinstance(rows, list) or len(rows) != 2:
        blockers.append("binding_rows_count_invalid")
    else:
        platforms_found = []
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                blockers.append(f"binding_row_index_{idx}_not_dict")
                continue

            row_req = [
                "platform",
                "destination_label",
                "account_label",
                "permission_label",
                "binding_kind",
                "credential_key_name",
                "endpoint_host_label",
                "endpoint_path_label",
                "method_label",
                "operator_confirmed_destination",
                "operator_confirmed_account_context",
                "operator_notes"
            ]
            for rk in row_req:
                if row.get(rk) is None:
                    blockers.append(f"binding_row_index_{idx}_missing_{rk}")

            # Extra fields in row fail closed
            row_extra_keys = set(row.keys()) - set(row_req)
            for ek in sorted(row_extra_keys):
                blockers.append(f"binding_row_index_{idx}_extra_field_{ek}_detected")

            platform = row.get("platform")
            if platform not in ["substack", "discord"]:
                blockers.append(f"binding_row_index_{idx}_platform_invalid")
            else:
                platforms_found.append(platform)

            # destination_label/account_label/permission_label validation: non-empty, labels only, no URLs or domain/ID-like terms
            for label_field in ["destination_label", "account_label", "permission_label"]:
                val = row.get(label_field)
                if not isinstance(val, str) or not val.strip():
                    blockers.append(f"binding_row_index_{idx}_{label_field}_missing")
                else:
                    if "http://" in val or "https://" in val or "." in val or "/" in val:
                        blockers.append(f"binding_row_index_{idx}_{label_field}_contains_url_or_domain")
                    # ID-like term checks
                    if re.search(r"[0-9a-fA-F]{8,}", val):
                        blockers.append(f"binding_row_index_{idx}_{label_field}_contains_hex_id")

            if row.get("binding_kind") != "non_secret_label_only_not_verified":
                blockers.append(f"binding_row_index_{idx}_binding_kind_invalid")

            # credential_key_name matching
            cred_key = row.get("credential_key_name")
            matched_keys = [k for k in preflight_keys if k.lower().startswith(platform)]
            if cred_key not in matched_keys:
                blockers.append(f"binding_row_index_{idx}_credential_key_name_mismatch")

            # endpoint matching
            allowlist_row = next((r for r in preflight_allowlist if r.get("platform") == platform), None)
            if allowlist_row:
                if row.get("endpoint_host_label") != allowlist_row.get("host_label"):
                    blockers.append(f"binding_row_index_{idx}_endpoint_host_label_mismatch")
                if row.get("endpoint_path_label") != allowlist_row.get("path_label"):
                    blockers.append(f"binding_row_index_{idx}_endpoint_path_label_mismatch")
                if row.get("method_label") != allowlist_row.get("method_label"):
                    blockers.append(f"binding_row_index_{idx}_method_label_mismatch")
            else:
                blockers.append(f"binding_row_index_{idx}_endpoint_allowlist_row_not_found")

            if row.get("operator_confirmed_destination") is not True:
                blockers.append(f"binding_row_index_{idx}_operator_confirmed_destination_not_true")

            if row.get("operator_confirmed_account_context") is not True:
                blockers.append(f"binding_row_index_{idx}_operator_confirmed_account_context_not_true")

            op_notes = row.get("operator_notes")
            if not isinstance(op_notes, str):
                blockers.append(f"binding_row_index_{idx}_operator_notes_invalid")

            # Check safety in row text
            row_copy = dict(row)
            row_copy.pop("credential_key_name", None)
            row_serialized = json.dumps(row_copy)
            if _has_secret_marker(row_serialized):
                blockers.append(f"binding_row_index_{idx}_secret_marker_detected")

            forbidden_term = _scan_for_forbidden_binding_row_claims(row_serialized)
            if forbidden_term:
                blockers.append(f"binding_row_index_{idx}_forbidden_live_claim_detected_{forbidden_term.replace(' ', '_')}")

        if len(platforms_found) != 2 or platforms_found != ["substack", "discord"]:
            blockers.append("binding_rows_platforms_invalid_order_or_values")

    return blockers


def _check_declaration_safety(decl_packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    # Popping credential key names and allowlist rows and scanning
    decl_copy = dict(decl_packet)
    decl_copy.pop("credential_key_names_only_reviewed", None)
    decl_copy.pop("endpoint_allowlist_rows_reviewed", None)
    decl_copy.pop("platform_binding_rows", None)
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


def make_account_binding_preflight_packet(
    preflight_packet: Any,
    account_binding_declaration: Any,
) -> AccountBindingPreflightPacket:
    blockers: list[str] = []

    preflight_is_dict = isinstance(preflight_packet, dict)
    if not preflight_is_dict:
        blockers.append("malformed_live_dispatch_credential_allowlist_preflight_packet_json")

    decl_is_dict = isinstance(account_binding_declaration, dict)
    if not decl_is_dict:
        blockers.append("malformed_operator_account_binding_declaration_json")

    # Secret scanner safety checks
    if preflight_is_dict:
        ready_copy = dict(preflight_packet)
        ready_copy.pop("credential_key_names_only", None)
        ready_copy.pop("credential_presence_rows", None)
        ready_copy.pop("endpoint_allowlist_rows", None)
        ready_copy.pop("destinations", None)
        if _has_secret_marker(json.dumps(ready_copy)):
            blockers.append("preflight_secret_marker_detected")

    if decl_is_dict:
        blockers.extend(_check_declaration_safety(account_binding_declaration, "binding"))

    # Initial placeholder values
    account_binding_declaration_id = ""
    operator_id = ""
    created_at_manual = ""
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
    credential_presence_mode = ""
    credential_presence_complete = False
    endpoint_allowlist_rows: list[dict[str, Any]] = []
    platform_binding_rows: list[dict[str, Any]] = []
    account_identity_later_required = False
    permission_check_later_required = False
    destination_binding_confirmed = False
    live_write_request_budget_confirmed = 0
    timeout_policy_confirmed = ""
    retry_policy_confirmed = ""
    audit_redaction_confirmed = False
    combined_payload_hash = ""

    if preflight_is_dict and "preflight_secret_marker_detected" not in blockers:
        blockers.extend(_validate_preflight_packet(preflight_packet))

        credential_allowlist_preflight_id = str(preflight_packet.get("credential_allowlist_preflight_id") or "")
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
        credential_presence_mode = str(preflight_packet.get("credential_presence_mode") or "")
        credential_presence_complete = bool(preflight_packet.get("credential_presence_complete"))
        endpoint_allowlist_rows = preflight_packet.get("endpoint_allowlist_rows", [])
        combined_payload_hash = str(preflight_packet.get("combined_payload_hash") or "")

        # Compute SHA256 of preflight packet only if no secret markers are present
        preflight_copy = dict(preflight_packet)
        preflight_copy.pop("credential_key_names_only", None)
        if not _has_secret_marker(json.dumps(preflight_copy)):
            credential_allowlist_preflight_sha256 = hashlib.sha256(_canonical_json(preflight_packet).encode("utf-8")).hexdigest()

        if decl_is_dict and "binding_secret_marker_detected" not in blockers:
            blockers.extend(_validate_binding_declaration(account_binding_declaration, preflight_packet))
            account_binding_declaration_id = str(account_binding_declaration.get("account_binding_declaration_id") or "")
            operator_id = str(account_binding_declaration.get("operator_id") or "")
            created_at_manual = str(account_binding_declaration.get("created_at_manual") or "")
            platform_binding_rows = account_binding_declaration.get("platform_binding_rows", [])
            account_identity_later_required = bool(account_binding_declaration.get("account_identity_later_required"))
            permission_check_later_required = bool(account_binding_declaration.get("permission_check_later_required"))
            destination_binding_confirmed = bool(account_binding_declaration.get("destination_binding_confirmed"))
            live_write_request_budget_confirmed = int(account_binding_declaration.get("live_write_request_budget_confirmed") or 0)
            timeout_policy_confirmed = str(account_binding_declaration.get("timeout_policy_confirmed") or "")
            retry_policy_confirmed = str(account_binding_declaration.get("retry_policy_confirmed") or "")
            audit_redaction_confirmed = bool(account_binding_declaration.get("audit_redaction_confirmed"))

    blockers = sorted(set(blockers))
    prepared = not blockers

    account_binding_declared_ready = (
        prepared and decl_is_dict and (account_binding_declaration.get("declaration_decision") == "mark_account_binding_ready_for_future_live_request_gate")
    )

    eligible = prepared and account_binding_declared_ready

    # Safety redaction on secret/marker detection
    has_secrets = (
        "preflight_secret_marker_detected" in blockers or
        "binding_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        account_binding_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
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
        combined_payload_hash = ""

    intake_material = {
        "credential_allowlist_preflight_id": credential_allowlist_preflight_id,
        "account_binding_declaration_id": account_binding_declaration_id,
        "blockers": blockers,
    }
    account_binding_preflight_id = f"account_binding_preflight_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("account_binding_preflight_blocked_pending_operator_repair")

    return AccountBindingPreflightPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        account_binding_preflight_id=account_binding_preflight_id,
        account_binding_declaration_id=account_binding_declaration_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
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
        credential_presence_mode=credential_presence_mode,
        credential_presence_complete=credential_presence_complete,
        endpoint_allowlist_rows=endpoint_allowlist_rows,
        platform_binding_rows=platform_binding_rows,
        account_identity_later_required=account_identity_later_required,
        permission_check_later_required=permission_check_later_required,
        destination_binding_confirmed=destination_binding_confirmed,
        live_write_request_budget_confirmed=live_write_request_budget_confirmed,
        timeout_policy_confirmed=timeout_policy_confirmed,
        retry_policy_confirmed=retry_policy_confirmed,
        audit_redaction_confirmed=audit_redaction_confirmed,
        combined_payload_hash=combined_payload_hash,
        account_binding_preflight_available=prepared,
        account_binding_declared_ready=account_binding_declared_ready,
        eligible_for_live_dispatch_request_package_gate=eligible,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Dispatch Account Binding Preflight CLI")
    parser.add_argument("preflight_packet", help="Path to credential/allowlist preflight packet JSON")
    parser.add_argument("account_binding_declaration", help="Path to operator account-binding declaration JSON")
    parser.add_argument("--output-file", required=True, help="Path to write account-binding preflight packet")

    args = parser.parse_args(argv)

    try:
        preflight = load_json_packet(args.preflight_packet, "malformed_live_dispatch_credential_allowlist_preflight_packet_json")
        decl = load_json_packet(args.account_binding_declaration, "malformed_operator_account_binding_declaration_json")

        packet = make_account_binding_preflight_packet(preflight, decl)

        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")

        if not packet.account_binding_preflight_available:
            return 1
        return 0

    except ValueError as val_err:
        packet = AccountBindingPreflightPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            account_binding_preflight_id=f"account_binding_preflight_blocked_{str(val_err)}",
            account_binding_declaration_id="",
            operator_id="",
            created_at_manual="",
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
            credential_presence_mode="",
            credential_presence_complete=False,
            endpoint_allowlist_rows=[],
            platform_binding_rows=[],
            account_identity_later_required=False,
            permission_check_later_required=False,
            destination_binding_confirmed=False,
            live_write_request_budget_confirmed=0,
            timeout_policy_confirmed="",
            retry_policy_confirmed="",
            audit_redaction_confirmed=False,
            combined_payload_hash="",
            account_binding_preflight_available=False,
            account_binding_declared_ready=False,
            eligible_for_live_dispatch_request_package_gate=False,
            blockers=[str(val_err)],
            warnings=["account_binding_preflight_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
