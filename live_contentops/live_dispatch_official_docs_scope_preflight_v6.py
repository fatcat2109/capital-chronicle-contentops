"""V6 Live Dispatch Official-Docs and Live-Scope Preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_OFFICIAL_DOCS_AND_SCOPE_PREFLIGHT_FROM_READINESS_V0"
READINESS_TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_READINESS_PREFLIGHT_FROM_EXECUTION_PAYLOADS_V0"
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


@dataclass(frozen=True)
class LiveDispatchScopePreflightPacket:
    schema_version: str
    task_label: str
    live_dispatch_scope_preflight_id: str
    official_docs_declaration_id: str
    live_scope_declaration_id: str
    operator_id: str
    created_at_manual: str
    live_dispatch_readiness_preflight_id: str
    live_dispatch_readiness_preflight_sha256: str
    live_dispatch_readiness_declaration_id: str
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
    official_docs_declared_reviewed: bool
    official_docs_source_rows: list[dict[str, Any]]
    action_class: str
    dispatch_family: str
    platforms: list[str]
    credential_key_names_only: list[str]
    account_binding_later_required: bool
    endpoint_allowlist_later_required: bool
    payload_hash_later_required: bool
    explicit_operator_approval_later_required: bool
    kill_switch_required: bool
    manual_fallback_required: bool
    live_write_request_budget_later: int
    timeout_policy_later: str
    retry_policy_later: str
    audit_redaction_required: bool
    combined_payload_hash: str
    live_dispatch_scope_preflight_available: bool
    eligible_for_supervised_live_gate: bool
    official_docs_scope_declared_ready: bool
    live_scope_declared_ready: bool
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


def _normalize_path(p: str | Path) -> str:
    return str(Path(p).resolve()).lower().replace("\\", "/")


def _has_secret_marker(value: str) -> bool:
    lowered = value.lower()
    # Bypass schema/rule field names to avoid false positives
    lowered = lowered.replace("credential_key_names_only", "")
    lowered = lowered.replace("credentials_required_later", "")
    lowered = lowered.replace("non_secret_label_only", "")
    lowered = lowered.replace("non-secret", "")
    lowered = lowered.replace("non_secret", "")
    lowered = lowered.replace("bind_non_secret_destination_labels_only_not_live_dispatch", "")
    lowered = lowered.replace("approve_local_dispatch_execution_preparation_only_not_live_send", "")
    lowered = lowered.replace("dispatch_execution_preparation_only", "")
    lowered = lowered.replace("local_dispatch_execution_payload_pending_live_gate", "")
    lowered = lowered.replace("mark_ready_for_future_live_dispatch_gate_only_not_send", "")
    lowered = lowered.replace("future_live_dispatch_gate_preflight_only", "")
    lowered = lowered.replace("declare_official_docs_reviewed_for_future_gate_only", "")
    lowered = lowered.replace("official_docs_scope_preflight_only", "")
    lowered = lowered.replace("mark_scope_ready_for_future_supervised_live_gate_only_not_send", "")
    lowered = lowered.replace("live_scope_preflight_only", "")
    lowered = lowered.replace("official_docs_operator_declared_reference", "")
    lowered = lowered.replace("webhook_behavior", "")
    lowered = lowered.replace("auth_model", "")
    lowered = lowered.replace("endpoint_allowlist", "")
    return any(marker in lowered for marker in SECRET_MARKERS)


def load_json_packet(path: Path, malformed_label: str) -> Any:
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(val, dict):
            raise ValueError(malformed_label)
        return val
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def _validate_readiness_packet(ready: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    # Required fields verification
    required_keys = [
        "schema_version",
        "task_label",
        "live_dispatch_readiness_preflight_id",
        "live_dispatch_readiness_declaration_id",
        "local_dispatch_execution_payload_manifest_id",
        "local_dispatch_execution_payload_manifest_sha256",
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
        "combined_payload_hash",
        "live_dispatch_readiness_preflight_available",
        "eligible_for_future_live_dispatch_gate",
        "live_dispatch_readiness_preflight_approved"
    ]
    for key in required_keys:
        if ready.get(key) is None:
            blockers.append(f"readiness_field_missing_{key}")

    if ready.get("task_label") != READINESS_TASK_LABEL:
        blockers.append("readiness_task_label_invalid")

    # Hard validation checks on readiness state flags
    gating_rules = {
        "live_dispatch_readiness_preflight_available": True,
        "eligible_for_future_live_dispatch_gate": True,
        "live_dispatch_readiness_preflight_approved": True,
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
        "official_docs_required": True,
        "credentials_required_later": True,
        "destination_binding_required_later": True,
        "endpoint_allowlist_required_later": True,
        "payload_hash_required_later": True,
        "explicit_operator_approval_required_later": True,
        "kill_switch_required": True,
    }
    for field_name, expected in gating_rules.items():
        if ready.get(field_name) != expected:
            blockers.append(f"readiness_field_{field_name}_invalid")

    if ready.get("public_url") is not None:
        blockers.append("readiness_public_url_not_null")
    if ready.get("public_metrics") is not None:
        blockers.append("readiness_public_metrics_not_null")

    if ready.get("platform_action_class") != "supervised_dispatch_future_gate":
        blockers.append("readiness_platform_action_class_invalid")
    if ready.get("dispatch_family") != "substack_discord_dispatch_family":
        blockers.append("readiness_dispatch_family_invalid")

    if ready.get("blockers"):
        blockers.append("readiness_blockers_not_empty")

    # Element counts verification
    if not isinstance(ready.get("execution_preparation_json_files"), list) or len(ready.get("execution_preparation_json_files", [])) != 2:
        blockers.append("readiness_execution_preparation_json_files_count_invalid")
    if not isinstance(ready.get("execution_preparation_json_hashes"), dict) or len(ready.get("execution_preparation_json_hashes", {})) != 2:
        blockers.append("readiness_execution_preparation_json_hashes_count_invalid")
    if not isinstance(ready.get("execution_preparation_markdown_files"), list) or len(ready.get("execution_preparation_markdown_files", [])) != 2:
        blockers.append("readiness_execution_preparation_markdown_files_count_invalid")
    if not isinstance(ready.get("execution_preparation_markdown_hashes"), dict) or len(ready.get("execution_preparation_markdown_hashes", {})) != 2:
        blockers.append("readiness_execution_preparation_markdown_hashes_count_invalid")

    destinations = ready.get("destinations", [])
    if not isinstance(destinations, list) or len(destinations) != 2:
        blockers.append("readiness_destinations_count_invalid")
    else:
        platforms = [d.get("platform") for d in destinations if isinstance(d, dict)]
        if sorted(platforms) != ["discord", "substack"]:
            blockers.append("readiness_destinations_platforms_invalid")

    if not isinstance(ready.get("credential_key_names_only"), list):
        blockers.append("readiness_credential_key_names_only_invalid_type")

    return blockers


def _validate_docs_declaration(docs: dict[str, Any], readiness: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    # Required fields verification
    required_keys = [
        "schema_version",
        "official_docs_declaration_id",
        "operator_id",
        "created_at_manual",
        "live_dispatch_readiness_preflight_id",
        "combined_payload_hash",
        "docs_review_mode",
        "source_rows",
        "declaration_decision",
        "approval_phrase",
        "approval_scope",
        "notes"
    ]
    for key in required_keys:
        if docs.get(key) is None:
            blockers.append(f"docs_field_missing_{key}")

    # Matching with readiness packet
    if docs.get("live_dispatch_readiness_preflight_id") != readiness.get("live_dispatch_readiness_preflight_id"):
        blockers.append("docs_readiness_preflight_id_mismatch")
    if docs.get("combined_payload_hash") != readiness.get("combined_payload_hash"):
        blockers.append("docs_combined_payload_hash_mismatch")

    if docs.get("docs_review_mode") != "operator_declared_official_docs_review_only":
        blockers.append("docs_docs_review_mode_invalid")

    # Decision validation
    dec = docs.get("declaration_decision")
    if dec not in ["mark_official_docs_review_declared", "reject", "defer"]:
        blockers.append("docs_decision_invalid")
    elif dec in ["reject", "defer"]:
        blockers.append(f"docs_declaration_rejected_or_deferred_{dec}")
    elif dec == "mark_official_docs_review_declared":
        if docs.get("approval_phrase") != "DECLARE_OFFICIAL_DOCS_REVIEWED_FOR_FUTURE_GATE_ONLY":
            blockers.append("docs_approval_phrase_invalid")
        if docs.get("approval_scope") != "official_docs_scope_preflight_only":
            blockers.append("docs_approval_scope_invalid")

    notes = docs.get("notes")
    if notes is None or not isinstance(notes, str):
        blockers.append("docs_notes_missing_or_invalid")

    # Source rows validation
    source_rows = docs.get("source_rows")
    if not isinstance(source_rows, list) or len(source_rows) != 2:
        blockers.append("docs_source_rows_count_invalid")
    else:
        platforms_found = []
        for idx, row in enumerate(source_rows):
            if not isinstance(row, dict):
                blockers.append(f"docs_source_row_index_{idx}_not_dict")
                continue

            row_req = [
                "platform",
                "source_kind",
                "source_label",
                "official_docs_reviewed",
                "doc_topics_reviewed",
                "operator_notes"
            ]
            for rk in row_req:
                if row.get(rk) is None:
                    blockers.append(f"docs_source_row_index_{idx}_missing_{rk}")

            platform = row.get("platform")
            if platform not in ["substack", "discord"]:
                blockers.append(f"docs_source_row_index_{idx}_platform_invalid")
            else:
                platforms_found.append(platform)

            if row.get("source_kind") != "official_docs_operator_declared_reference":
                blockers.append(f"docs_source_row_index_{idx}_source_kind_invalid")
            
            label = row.get("source_label")
            if not isinstance(label, str) or not label.strip():
                blockers.append(f"docs_source_row_index_{idx}_source_label_invalid")

            if row.get("official_docs_reviewed") is not True:
                blockers.append(f"docs_source_row_index_{idx}_official_docs_reviewed_not_true")

            topics = row.get("doc_topics_reviewed")
            allowed_topics = {
                "auth_model", "endpoint_allowlist", "webhook_behavior",
                "rate_limits", "errors", "permissions", "app_review", "manual_fallback"
            }
            if not isinstance(topics, list) or not topics:
                blockers.append(f"docs_source_row_index_{idx}_doc_topics_reviewed_invalid")
            else:
                for topic in topics:
                    if topic not in allowed_topics:
                        blockers.append(f"docs_source_row_index_{idx}_doc_topics_reviewed_value_invalid_{topic}")

            op_notes = row.get("operator_notes")
            if not isinstance(op_notes, str):
                blockers.append(f"docs_source_row_index_{idx}_operator_notes_invalid")

            # Content safety check: no URLs, webhook links, secrets, app IDs, etc.
            row_serialized = json.dumps(row)
            if "http://" in row_serialized or "https://" in row_serialized:
                blockers.append(f"docs_source_row_index_{idx}_url_detected")

            if _has_secret_marker(row_serialized):
                blockers.append(f"docs_source_row_index_{idx}_secret_marker_detected")

        if len(platforms_found) != 2 or sorted(platforms_found) != ["discord", "substack"]:
            blockers.append("docs_source_rows_platforms_mismatch")

    return blockers


def _validate_credential_keys_scope(keys: list[str]) -> list[str]:
    blockers: list[str] = []
    for key in keys:
        if not isinstance(key, str) or not key:
            blockers.append("scope_credential_key_name_invalid_type")
            continue
        if not re.match(r"^[A-Za-z0-9_-]+$", key):
            blockers.append(f"scope_credential_key_name_character_violation_{key}")
            continue
        if len(key) > 64:
            blockers.append(f"scope_credential_key_name_length_violation_{key}")
            continue
        hex_parts = re.findall(r"[0-9a-fA-F]{16,}", key)
        if hex_parts:
            blockers.append(f"scope_credential_key_name_hex_value_detected_{key}")
            continue
    return blockers


def _validate_scope_declaration(scope: dict[str, Any], readiness: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    # Required fields verification
    required_keys = [
        "schema_version",
        "live_scope_declaration_id",
        "operator_id",
        "created_at_manual",
        "live_dispatch_readiness_preflight_id",
        "combined_payload_hash",
        "action_class",
        "dispatch_family",
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
        "declaration_decision",
        "approval_phrase",
        "approval_scope",
        "notes"
    ]
    for key in required_keys:
        if scope.get(key) is None:
            blockers.append(f"scope_field_missing_{key}")

    # Matching with readiness packet
    if scope.get("live_dispatch_readiness_preflight_id") != readiness.get("live_dispatch_readiness_preflight_id"):
        blockers.append("scope_readiness_preflight_id_mismatch")
    if scope.get("combined_payload_hash") != readiness.get("combined_payload_hash"):
        blockers.append("scope_combined_payload_hash_mismatch")

    if scope.get("action_class") != "supervised_live_dispatch_future_gate":
        blockers.append("scope_action_class_invalid")
    if scope.get("dispatch_family") != "substack_discord_dispatch_family":
        blockers.append("scope_dispatch_family_invalid")

    if scope.get("platforms") != ["substack", "discord"]:
        blockers.append("scope_platforms_invalid")

    # Match key list with readiness
    scope_keys = scope.get("credential_key_names_only", [])
    ready_keys = readiness.get("credential_key_names_only", [])
    if not isinstance(scope_keys, list) or scope_keys != ready_keys:
        blockers.append("scope_credential_key_names_only_mismatch")

    blockers.extend(_validate_credential_keys_scope(scope_keys))

    # Required flags validation
    flags_rules = {
        "account_binding_later_required": True,
        "endpoint_allowlist_later_required": True,
        "payload_hash_later_required": True,
        "explicit_operator_approval_later_required": True,
        "kill_switch_required": True,
        "manual_fallback_required": True,
        "audit_redaction_required": True,
    }
    for field_name, expected in flags_rules.items():
        if scope.get(field_name) != expected:
            blockers.append(f"scope_field_{field_name}_invalid")

    # Budget & policy validation
    budget = scope.get("live_write_request_budget_later")
    if not isinstance(budget, int) or budget < 1 or budget > 3:
        blockers.append("scope_live_write_request_budget_later_invalid")

    timeout = scope.get("timeout_policy_later")
    if not isinstance(timeout, str) or not timeout.strip() or any(c.isdigit() for c in timeout):
        blockers.append("scope_timeout_policy_later_invalid")

    if scope.get("retry_policy_later") != "no_hidden_retry":
        blockers.append("scope_retry_policy_later_invalid")

    # Decision validation
    dec = scope.get("declaration_decision")
    if dec not in ["mark_scope_ready_for_future_supervised_live_gate", "reject", "defer"]:
        blockers.append("scope_decision_invalid")
    elif dec in ["reject", "defer"]:
        blockers.append(f"scope_declaration_rejected_or_deferred_{dec}")
    elif dec == "mark_scope_ready_for_future_supervised_live_gate":
        if scope.get("approval_phrase") != "MARK_SCOPE_READY_FOR_FUTURE_SUPERVISED_LIVE_GATE_ONLY_NOT_SEND":
            blockers.append("scope_approval_phrase_invalid")
        if scope.get("approval_scope") != "live_scope_preflight_only":
            blockers.append("scope_approval_scope_invalid")

    notes = scope.get("notes")
    if notes is None or not isinstance(notes, str):
        blockers.append("scope_notes_missing_or_invalid")

    return blockers


def _check_declaration_safety(decl_packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    # Popping credential key names and scanning
    decl_copy = dict(decl_packet)
    decl_copy.pop("credential_key_names_only", None)
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

    return blockers


def make_live_dispatch_scope_preflight_packet(
    readiness_packet: Any,
    docs_declaration: Any,
    scope_declaration: Any,
) -> LiveDispatchScopePreflightPacket:
    blockers: list[str] = []

    readiness_is_dict = isinstance(readiness_packet, dict)
    if not readiness_is_dict:
        blockers.append("malformed_live_dispatch_readiness_preflight_packet_json")

    docs_is_dict = isinstance(docs_declaration, dict)
    if not docs_is_dict:
        blockers.append("malformed_operator_official_docs_declaration_json")

    scope_is_dict = isinstance(scope_declaration, dict)
    if not scope_is_dict:
        blockers.append("malformed_operator_live_scope_declaration_json")

    # Secret scanner checks
    if readiness_is_dict:
        ready_copy = dict(readiness_packet)
        ready_copy.pop("credential_key_names_only", None)
        if _has_secret_marker(json.dumps(ready_copy)):
            blockers.append("readiness_secret_marker_detected")

    if docs_is_dict:
        blockers.extend(_check_declaration_safety(docs_declaration, "docs"))
    if scope_is_dict:
        blockers.extend(_check_declaration_safety(scope_declaration, "scope"))

    # Instantiate placeholder vars
    official_docs_declaration_id = ""
    live_scope_declaration_id = ""
    operator_id = ""
    created_at_manual = ""
    live_dispatch_readiness_preflight_id = ""
    live_dispatch_readiness_preflight_sha256 = ""
    live_dispatch_readiness_declaration_id = ""
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
    official_docs_source_rows: list[dict[str, Any]] = []
    action_class = ""
    dispatch_family = ""
    platforms: list[str] = []
    credential_key_names_only: list[str] = []
    account_binding_later_required = False
    endpoint_allowlist_later_required = False
    payload_hash_later_required = False
    explicit_operator_approval_later_required = False
    kill_switch_required = False
    manual_fallback_required = False
    live_write_request_budget_later = 0
    timeout_policy_later = ""
    retry_policy_later = ""
    audit_redaction_required = False
    combined_payload_hash = ""

    # Execute validations
    if readiness_is_dict and "readiness_secret_marker_detected" not in blockers:
        blockers.extend(_validate_readiness_packet(readiness_packet))

        live_dispatch_readiness_preflight_id = str(readiness_packet.get("live_dispatch_readiness_preflight_id") or "")
        live_dispatch_readiness_declaration_id = str(readiness_packet.get("live_dispatch_readiness_declaration_id") or "")
        local_dispatch_execution_payload_manifest_id = str(readiness_packet.get("local_dispatch_execution_payload_manifest_id") or "")
        operator_supervised_dispatch_review_decision_packet_id = str(readiness_packet.get("operator_supervised_dispatch_review_decision_packet_id") or "")
        local_destination_binding_preflight_id = str(readiness_packet.get("local_destination_binding_preflight_id") or "")
        destination_binding_id = str(readiness_packet.get("destination_binding_id") or "")
        local_dispatch_payload_manifest_id = str(readiness_packet.get("local_dispatch_payload_manifest_id") or "")
        operator_dispatch_review_decision_packet_id = str(readiness_packet.get("operator_dispatch_review_decision_packet_id") or "")
        local_dispatch_preflight_id = str(readiness_packet.get("local_dispatch_preflight_id") or "")
        local_active_outbox_manifest_id = str(readiness_packet.get("local_active_outbox_manifest_id") or "")
        operator_active_outbox_review_decision_id = str(readiness_packet.get("operator_active_outbox_review_decision_id") or "")
        active_outbox_eligibility_id = str(readiness_packet.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(readiness_packet.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(readiness_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(readiness_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(readiness_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(readiness_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(readiness_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(readiness_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(readiness_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(readiness_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(readiness_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(readiness_packet.get("canonical_slug") or "")
        canonical_title = str(readiness_packet.get("canonical_title") or "")
        execution_preparation_json_files = readiness_packet.get("execution_preparation_json_files", [])
        execution_preparation_json_hashes = readiness_packet.get("execution_preparation_json_hashes", {})
        execution_preparation_markdown_files = readiness_packet.get("execution_preparation_markdown_files", [])
        execution_preparation_markdown_hashes = readiness_packet.get("execution_preparation_markdown_hashes", {})
        destinations = readiness_packet.get("destinations", [])
        combined_payload_hash = str(readiness_packet.get("combined_payload_hash") or "")

        # Compute readiness SHA256 only if there are no secret markers
        ready_copy = dict(readiness_packet)
        ready_copy.pop("credential_key_names_only", None)
        if not _has_secret_marker(json.dumps(ready_copy)):
            live_dispatch_readiness_preflight_sha256 = hashlib.sha256(_canonical_json(readiness_packet).encode("utf-8")).hexdigest()

        if docs_is_dict:
            blockers.extend(_validate_docs_declaration(docs_declaration, readiness_packet))
            official_docs_declaration_id = str(docs_declaration.get("official_docs_declaration_id") or "")
            official_docs_source_rows = docs_declaration.get("source_rows", [])

        if scope_is_dict:
            blockers.extend(_validate_scope_declaration(scope_declaration, readiness_packet))
            live_scope_declaration_id = str(scope_declaration.get("live_scope_declaration_id") or "")
            operator_id = str(scope_declaration.get("operator_id") or "")
            created_at_manual = str(scope_declaration.get("created_at_manual") or "")
            action_class = str(scope_declaration.get("action_class") or "")
            dispatch_family = str(scope_declaration.get("dispatch_family") or "")
            platforms = scope_declaration.get("platforms", [])
            credential_key_names_only = scope_declaration.get("credential_key_names_only", [])
            account_binding_later_required = bool(scope_declaration.get("account_binding_later_required"))
            endpoint_allowlist_later_required = bool(scope_declaration.get("endpoint_allowlist_later_required"))
            payload_hash_later_required = bool(scope_declaration.get("payload_hash_later_required"))
            explicit_operator_approval_later_required = bool(scope_declaration.get("explicit_operator_approval_later_required"))
            kill_switch_required = bool(scope_declaration.get("kill_switch_required"))
            manual_fallback_required = bool(scope_declaration.get("manual_fallback_required"))
            live_write_request_budget_later = int(scope_declaration.get("live_write_request_budget_later") or 0)
            timeout_policy_later = str(scope_declaration.get("timeout_policy_later") or "")
            retry_policy_later = str(scope_declaration.get("retry_policy_later") or "")
            audit_redaction_required = bool(scope_declaration.get("audit_redaction_required"))

    blockers = sorted(set(blockers))
    prepared = not blockers

    official_docs_scope_declared_ready = (
        prepared and docs_is_dict and (docs_declaration.get("declaration_decision") == "mark_official_docs_review_declared")
    )
    live_scope_declared_ready = (
        prepared and scope_is_dict and (scope_declaration.get("declaration_decision") == "mark_scope_ready_for_future_supervised_live_gate")
    )
    eligible = prepared and official_docs_scope_declared_ready and live_scope_declared_ready

    # Check for secret exposure in execution outputs
    has_secrets = (
        "readiness_secret_marker_detected" in blockers or
        "docs_secret_marker_detected" in blockers or
        "scope_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        official_docs_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_scope_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_dispatch_readiness_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        live_dispatch_readiness_preflight_sha256 = ""
        live_dispatch_readiness_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
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
        official_docs_source_rows = []
        platforms = []
        credential_key_names_only = []
        combined_payload_hash = ""

    intake_material = {
        "live_dispatch_readiness_preflight_id": live_dispatch_readiness_preflight_id,
        "official_docs_declaration_id": official_docs_declaration_id,
        "live_scope_declaration_id": live_scope_declaration_id,
        "blockers": blockers,
    }
    live_dispatch_scope_preflight_id = f"live_dispatch_scope_preflight_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("live_dispatch_scope_preflight_blocked_pending_operator_repair")

    return LiveDispatchScopePreflightPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        live_dispatch_scope_preflight_id=live_dispatch_scope_preflight_id,
        official_docs_declaration_id=official_docs_declaration_id,
        live_scope_declaration_id=live_scope_declaration_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        live_dispatch_readiness_preflight_id=live_dispatch_readiness_preflight_id,
        live_dispatch_readiness_preflight_sha256=live_dispatch_readiness_preflight_sha256,
        live_dispatch_readiness_declaration_id=live_dispatch_readiness_declaration_id,
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
        official_docs_declared_reviewed=official_docs_scope_declared_ready,
        official_docs_source_rows=official_docs_source_rows,
        action_class=action_class,
        dispatch_family=dispatch_family,
        platforms=platforms,
        credential_key_names_only=credential_key_names_only,
        account_binding_later_required=account_binding_later_required,
        endpoint_allowlist_later_required=endpoint_allowlist_later_required,
        payload_hash_later_required=payload_hash_later_required,
        explicit_operator_approval_later_required=explicit_operator_approval_later_required,
        kill_switch_required=kill_switch_required,
        manual_fallback_required=manual_fallback_required,
        live_write_request_budget_later=live_write_request_budget_later,
        timeout_policy_later=timeout_policy_later,
        retry_policy_later=retry_policy_later,
        audit_redaction_required=audit_redaction_required,
        combined_payload_hash=combined_payload_hash,
        live_dispatch_scope_preflight_available=prepared,
        eligible_for_supervised_live_gate=eligible,
        official_docs_scope_declared_ready=official_docs_scope_declared_ready,
        live_scope_declared_ready=live_scope_declared_ready,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Live Dispatch Official-Docs and Live-Scope Preflight CLI")
    parser.add_argument("readiness_packet", help="Path to live dispatch readiness preflight packet JSON")
    parser.add_argument("docs_declaration", help="Path to operator official docs declaration JSON")
    parser.add_argument("scope_declaration", help="Path to operator live scope declaration JSON")
    parser.add_argument("--output-file", required=True, help="Path to write live dispatch scope preflight packet")

    args = parser.parse_args(argv)

    try:
        readiness = load_json_packet(Path(args.readiness_packet), "malformed_live_dispatch_readiness_preflight_packet_json")
        docs = load_json_packet(Path(args.docs_declaration), "malformed_operator_official_docs_declaration_json")
        scope = load_json_packet(Path(args.scope_declaration), "malformed_operator_live_scope_declaration_json")

        packet = make_live_dispatch_scope_preflight_packet(readiness, docs, scope)

        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")

        if not packet.live_dispatch_scope_preflight_available:
            return 1
        return 0

    except ValueError as val_err:
        # Construct fallback blocked packet on ValueError
        packet = LiveDispatchScopePreflightPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            live_dispatch_scope_preflight_id=f"live_dispatch_scope_preflight_blocked_{str(val_err)}",
            official_docs_declaration_id="",
            live_scope_declaration_id="",
            operator_id="",
            created_at_manual="",
            live_dispatch_readiness_preflight_id="",
            live_dispatch_readiness_preflight_sha256="",
            live_dispatch_readiness_declaration_id="",
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
            official_docs_declared_reviewed=False,
            official_docs_source_rows=[],
            action_class="",
            dispatch_family="",
            platforms=[],
            credential_key_names_only=[],
            account_binding_later_required=False,
            endpoint_allowlist_later_required=False,
            payload_hash_later_required=False,
            explicit_operator_approval_later_required=False,
            kill_switch_required=False,
            manual_fallback_required=False,
            live_write_request_budget_later=0,
            timeout_policy_later="",
            retry_policy_later="",
            audit_redaction_required=False,
            combined_payload_hash="",
            live_dispatch_scope_preflight_available=False,
            eligible_for_supervised_live_gate=False,
            official_docs_scope_declared_ready=False,
            live_scope_declared_ready=False,
            blockers=[str(val_err)],
            warnings=["live_dispatch_scope_preflight_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
