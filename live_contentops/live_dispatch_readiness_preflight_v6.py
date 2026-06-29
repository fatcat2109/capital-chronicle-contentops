"""V6 Live Dispatch Readiness Preflight from Execution Payloads."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MANIFEST_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_EXECUTION_PAYLOAD_PREPARATION_FROM_SUPERVISED_DECISION_V0"
PAYLOAD_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_EXECUTION_PAYLOAD_PREPARATION_FROM_SUPERVISED_DECISION_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LIVE_DISPATCH_READINESS_PREFLIGHT_FROM_EXECUTION_PAYLOADS_V0"
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
class LiveDispatchReadinessPreflightPacket:
    schema_version: str
    task_label: str
    live_dispatch_readiness_preflight_id: str
    live_dispatch_readiness_declaration_id: str
    operator_id: str
    created_at_manual: str
    local_dispatch_execution_payload_manifest_id: str
    local_dispatch_execution_payload_manifest_sha256: str
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
    platform_action_class: str
    dispatch_family: str
    official_docs_required: bool
    credentials_required_later: bool
    credential_key_names_only: list[str]
    destination_binding_required_later: bool
    endpoint_allowlist_required_later: bool
    payload_hash_required_later: bool
    explicit_operator_approval_required_later: bool
    kill_switch_required: bool
    combined_payload_hash: str
    live_dispatch_readiness_preflight_available: bool
    eligible_for_future_live_dispatch_gate: bool
    live_dispatch_readiness_preflight_approved: bool
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
    lowered = lowered.replace("non_secret_label_only", "")
    lowered = lowered.replace("bind_non_secret_destination_labels_only_not_live_dispatch", "")
    lowered = lowered.replace("approve_local_dispatch_execution_preparation_only_not_live_send", "")
    lowered = lowered.replace("dispatch_execution_preparation_only", "")
    lowered = lowered.replace("local_dispatch_execution_payload_pending_live_gate", "")
    lowered = lowered.replace("mark_ready_for_future_live_dispatch_gate_only_not_send", "")
    lowered = lowered.replace("future_live_dispatch_gate_preflight_only", "")
    lowered = lowered.replace("credential_key_names_only", "")
    lowered = lowered.replace("credentials_required_later", "")
    lowered = lowered.replace("non_secret", "")
    lowered = lowered.replace("non-secret", "")
    return any(marker in lowered for marker in SECRET_MARKERS)


def load_json_packet(path: Path, malformed_label: str) -> Any:
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(val, dict):
            raise ValueError(malformed_label)
        return val
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def load_text_file(path: Path, malformed_label: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def _normalize_path(p: str | Path) -> str:
    return str(Path(p).resolve()).lower().replace("\\", "/")


def _check_public_and_live_fields(packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    false_fields = [
        "approved_canonical_article_available",
        "publication_ready",
        "dispatch_allowed",
        "platform_variant_generation_allowed",
        "outbox_creation_allowed",
    ]
    null_fields = ["public_url", "public_metrics"]
    for field_name in false_fields:
        if packet.get(field_name) is not False:
            blockers.append(f"{prefix}_{field_name}_not_false")
    for field_name in null_fields:
        if packet.get(field_name) is not None:
            blockers.append(f"{prefix}_{field_name}_not_null")
    return blockers


def _validate_manifest_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != MANIFEST_TASK_LABEL:
        blockers.append("manifest_task_label_invalid")
    if packet.get("local_dispatch_execution_prepared") is not True:
        blockers.append("manifest_local_dispatch_execution_not_prepared")
    if packet.get("dispatch_execution_payload_created") is not True:
        blockers.append("manifest_dispatch_execution_payload_created_not_true")
    if packet.get("live_send_request_created") is not False:
        blockers.append("manifest_live_send_request_created_not_false")
    if packet.get("approval_for_live_dispatch") is not False:
        blockers.append("manifest_approval_for_live_dispatch_not_false")
    if packet.get("approval_for_publication") is not False:
        blockers.append("manifest_approval_for_publication_not_false")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("manifest_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("manifest_citations_verified_not_false")

    blockers.extend(_check_public_and_live_fields(packet, "manifest"))

    if packet.get("review_only") is not True:
        blockers.append("manifest_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("manifest_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("manifest_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("manifest_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("manifest_has_blockers")

    # Counts
    jsons = packet.get("prepared_dispatch_payload_json_files", [])
    if not isinstance(jsons, list) or len(jsons) != 2:
        blockers.append("manifest_prepared_dispatch_payload_json_files_count_invalid")

    json_hashes = packet.get("prepared_dispatch_payload_json_hashes", {})
    if not isinstance(json_hashes, dict) or len(json_hashes) != 2:
        blockers.append("manifest_prepared_dispatch_payload_json_hashes_count_invalid")

    mds = packet.get("prepared_dispatch_payload_markdown_files", [])
    if not isinstance(mds, list) or len(mds) != 2:
        blockers.append("manifest_prepared_dispatch_payload_markdown_files_count_invalid")

    md_hashes = packet.get("prepared_dispatch_payload_markdown_hashes", {})
    if not isinstance(md_hashes, dict) or len(md_hashes) != 2:
        blockers.append("manifest_prepared_dispatch_payload_markdown_hashes_count_invalid")

    exec_jsons = packet.get("execution_preparation_json_files", [])
    if not isinstance(exec_jsons, list) or len(exec_jsons) != 2:
        blockers.append("manifest_execution_preparation_json_files_count_invalid")

    exec_mds = packet.get("execution_preparation_markdown_files", [])
    if not isinstance(exec_mds, list) or len(exec_mds) != 2:
        blockers.append("manifest_execution_preparation_markdown_files_count_invalid")

    exec_hashes = packet.get("execution_preparation_file_hashes", {})
    if not isinstance(exec_hashes, dict) or len(exec_hashes) != 4:
        blockers.append("manifest_execution_preparation_file_hashes_count_invalid")

    destinations = packet.get("destinations", [])
    if not isinstance(destinations, list) or len(destinations) != 2:
        blockers.append("manifest_destinations_count_invalid")

    required_keys = [
        "local_dispatch_execution_payload_manifest_id",
        "operator_supervised_dispatch_review_decision_packet_id",
        "operator_supervised_dispatch_decision_sha256",
        "local_destination_binding_preflight_id",
        "local_destination_binding_preflight_sha256",
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
        "combined_payload_hash",
    ]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"manifest_{key}_missing")

    return blockers


def _validate_execution_json_packet(entry: dict[str, Any], manifest: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if entry.get("task_label") != PAYLOAD_TASK_LABEL:
        blockers.append(f"{prefix}_task_label_invalid")

    platform = entry.get("platform")
    if platform not in ["substack", "discord"]:
        blockers.append(f"{prefix}_platform_invalid")

    if entry.get("preparation_status") != "local_dispatch_execution_payload_pending_live_gate":
        blockers.append(f"{prefix}_preparation_status_invalid")

    if entry.get("local_dispatch_execution_prepared") is not True:
        blockers.append(f"{prefix}_local_dispatch_execution_prepared_not_true")
    if entry.get("dispatch_execution_payload_created") is not True:
        blockers.append(f"{prefix}_dispatch_execution_payload_created_not_true")
    if entry.get("live_send_request_created") is not False:
        blockers.append(f"{prefix}_live_send_request_created_not_false")
    if entry.get("approval_for_live_dispatch") is not False:
        blockers.append(f"{prefix}_approval_for_live_dispatch_not_false")
    if entry.get("dispatch_allowed") is not False:
        blockers.append(f"{prefix}_dispatch_allowed_not_false")
    if entry.get("approval_for_publication") is not False:
        blockers.append(f"{prefix}_approval_for_publication_not_false")
    if entry.get("publication_ready") is not False:
        blockers.append(f"{prefix}_publication_ready_not_false")
    if entry.get("public_url") is not None:
        blockers.append(f"{prefix}_public_url_not_null")
    if entry.get("public_metrics") is not None:
        blockers.append(f"{prefix}_public_metrics_not_null")
    if entry.get("review_only") is not True:
        blockers.append(f"{prefix}_review_only_not_true")
    if entry.get("human_review_required") is not True:
        blockers.append(f"{prefix}_human_review_required_not_true")
    if entry.get("kill_switch_active") is not True:
        blockers.append(f"{prefix}_kill_switch_active_not_true")
    if entry.get("runtime_truth") is not False:
        blockers.append(f"{prefix}_runtime_truth_not_false")
    if entry.get("blockers"):
        blockers.append(f"{prefix}_has_blockers")

    # Match references
    if entry.get("combined_payload_hash") != manifest.get("combined_payload_hash"):
        blockers.append(f"{prefix}_combined_payload_hash_mismatch")
    if entry.get("operator_supervised_dispatch_review_decision_packet_id") != manifest.get("operator_supervised_dispatch_review_decision_packet_id"):
        blockers.append(f"{prefix}_operator_supervised_dispatch_review_decision_packet_id_mismatch")
    if entry.get("local_destination_binding_preflight_id") != manifest.get("local_destination_binding_preflight_id"):
        blockers.append(f"{prefix}_local_destination_binding_preflight_id_mismatch")
    if entry.get("local_dispatch_payload_manifest_id") != manifest.get("local_dispatch_payload_manifest_id"):
        blockers.append(f"{prefix}_local_dispatch_payload_manifest_id_mismatch")
    if entry.get("canonical_slug") != manifest.get("canonical_slug"):
        blockers.append(f"{prefix}_canonical_slug_mismatch")
    if entry.get("canonical_title") != manifest.get("canonical_title"):
        blockers.append(f"{prefix}_canonical_title_mismatch")

    # Match destinations
    expected_dest = None
    for d in manifest.get("destinations", []):
        if d.get("platform") == platform:
            expected_dest = d
            break
    if _canonical_json(entry.get("destination")) != _canonical_json(expected_dest):
        blockers.append(f"{prefix}_destination_mismatch")

    # Match markdown snapshot file
    md_snap = entry.get("markdown_snapshot_file")
    if not md_snap:
        blockers.append(f"{prefix}_markdown_snapshot_file_missing")
    else:
        npath = _normalize_path(md_snap)
        manifest_mds_normalized = [_normalize_path(p) for p in manifest.get("execution_preparation_markdown_files", [])]
        if npath not in manifest_mds_normalized:
            blockers.append(f"{prefix}_markdown_snapshot_file_not_in_manifest")
        else:
            # Find matching hash
            expected_hash = None
            for k, v in manifest.get("execution_preparation_file_hashes", {}).items():
                if _normalize_path(k) == npath:
                    expected_hash = v
                    break
            if entry.get("markdown_snapshot_sha256") != expected_hash:
                blockers.append(f"{prefix}_markdown_snapshot_sha256_mismatch")

    # Match source payload files and hashes
    source_json = entry.get("source_prepared_dispatch_payload_json_file")
    if not source_json:
        blockers.append(f"{prefix}_source_prepared_dispatch_payload_json_file_missing")
    else:
        npath = _normalize_path(source_json)
        manifest_jsons_normalized = [_normalize_path(p) for p in manifest.get("prepared_dispatch_payload_json_files", [])]
        if npath not in manifest_jsons_normalized:
            blockers.append(f"{prefix}_source_prepared_dispatch_payload_json_file_not_in_manifest")
        else:
            expected_hash = None
            for k, v in manifest.get("prepared_dispatch_payload_json_hashes", {}).items():
                if _normalize_path(k) == npath:
                    expected_hash = v
                    break
            if entry.get("source_prepared_dispatch_payload_json_sha256") != expected_hash:
                blockers.append(f"{prefix}_source_prepared_dispatch_payload_json_sha256_mismatch")

    source_md = entry.get("source_prepared_dispatch_payload_markdown_file")
    if not source_md:
        blockers.append(f"{prefix}_source_prepared_dispatch_payload_markdown_file_missing")
    else:
        npath = _normalize_path(source_md)
        manifest_mds_normalized = [_normalize_path(p) for p in manifest.get("prepared_dispatch_payload_markdown_files", [])]
        if npath not in manifest_mds_normalized:
            blockers.append(f"{prefix}_source_prepared_dispatch_payload_markdown_file_not_in_manifest")
        else:
            expected_hash = None
            for k, v in manifest.get("prepared_dispatch_payload_markdown_hashes", {}).items():
                if _normalize_path(k) == npath:
                    expected_hash = v
                    break
            if entry.get("source_prepared_dispatch_payload_markdown_sha256") != expected_hash:
                blockers.append(f"{prefix}_source_prepared_dispatch_payload_markdown_sha256_mismatch")

    return blockers


def _validate_preview_text(text: str, platform: str) -> list[str]:
    blockers: list[str] = []
    if not text.strip():
        blockers.append(f"prepared_{platform}_empty")
        return blockers

    # Scan for secrets
    if _has_secret_marker(text):
        blockers.append(f"prepared_{platform}_secret_marker_detected")

    # Safe warning check
    if platform == "substack":
        if "LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION" not in text:
            blockers.append("prepared_substack_warning_missing")
    elif platform == "discord":
        if "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH" not in text:
            blockers.append("prepared_discord_warning_missing")

    lowered = text.lower()
    lowered = lowered.replace("local preview only - not approved for publication", "")
    lowered = lowered.replace("local preview only - not approved for discord dispatch", "")

    # Prohibited claims
    for marker in PUBLIC_READY_MARKERS:
        if marker in lowered:
            blockers.append(f"prepared_{platform}_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"prepared_{platform}_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"prepared_{platform}_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(lowered):
            blockers.append(f"prepared_{platform}_financial_advice_or_signal_framing_detected")
            break

    # Webhook or dispatch tokens check
    live_send_markers = ["webhook_url", "channel_id", "bot_token", "dispatch_allowed: true", "publish: true"]
    for marker in live_send_markers:
        if marker in lowered:
            blockers.append(f"prepared_{platform}_live_send_instructions_detected")

    return blockers


def _validate_credential_keys(keys: list[str]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(keys, list):
        blockers.append("declaration_credential_key_names_only_not_list")
        return blockers

    if not keys:
        blockers.append("declaration_credential_key_names_only_empty")

    for key in keys:
        if not isinstance(key, str) or not key:
            blockers.append("declaration_credential_key_name_invalid_type")
            continue
        # Enforce strict variable name pattern
        if not re.match(r"^[A-Za-z0-9_-]+$", key):
            blockers.append(f"declaration_credential_key_name_character_violation_{key}")
            continue
        if len(key) > 64:
            blockers.append(f"declaration_credential_key_name_length_violation_{key}")
            continue
        # Does not contain hex-like values
        hex_parts = re.findall(r"[0-9a-fA-F]{16,}", key)
        if hex_parts:
            blockers.append(f"declaration_credential_key_name_hex_value_detected_{key}")
            continue

    return blockers


def _validate_declaration(decl: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    
    # Required fields
    required_keys = [
        "schema_version",
        "live_dispatch_readiness_declaration_id",
        "operator_id",
        "created_at_manual",
        "local_dispatch_execution_payload_manifest_id",
        "combined_payload_hash",
        "platform_action_class",
        "dispatch_family",
        "reviewed_execution_preparation_json_files",
        "reviewed_execution_preparation_markdown_files",
        "reviewed_destinations",
        "decision",
        "approval_phrase",
        "approval_scope",
    ]
    for key in required_keys:
        if decl.get(key) is None:
            blockers.append(f"declaration_{key}_missing")

    # Hard codes validation
    if decl.get("platform_action_class") != "supervised_dispatch_future_gate":
        blockers.append("declaration_platform_action_class_invalid")
    if decl.get("dispatch_family") != "substack_discord_dispatch_family":
        blockers.append("declaration_dispatch_family_invalid")
    if decl.get("official_docs_required") is not True:
        blockers.append("declaration_official_docs_required_not_true")
    if decl.get("credentials_required_later") is not True:
        blockers.append("declaration_credentials_required_later_not_true")
    if decl.get("destination_binding_required_later") is not True:
        blockers.append("declaration_destination_binding_required_later_not_true")
    if decl.get("endpoint_allowlist_required_later") is not True:
        blockers.append("declaration_endpoint_allowlist_required_later_not_true")
    if decl.get("payload_hash_required_later") is not True:
        blockers.append("declaration_payload_hash_required_later_not_true")
    if decl.get("explicit_operator_approval_required_later") is not True:
        blockers.append("declaration_explicit_operator_approval_required_later_not_true")
    if decl.get("kill_switch_required") is not True:
        blockers.append("declaration_kill_switch_required_not_true")

    # Decision validation
    dec = decl.get("decision")
    if dec not in ["mark_ready_for_future_live_dispatch_gate", "reject", "defer"]:
        blockers.append("declaration_decision_value_invalid")
    
    if dec == "mark_ready_for_future_live_dispatch_gate":
        if decl.get("approval_phrase") != "MARK_READY_FOR_FUTURE_LIVE_DISPATCH_GATE_ONLY_NOT_SEND":
            blockers.append("declaration_approval_phrase_invalid")
        if decl.get("approval_scope") != "future_live_dispatch_gate_preflight_only":
            blockers.append("declaration_approval_scope_invalid")
    elif dec in ["reject", "defer"]:
        blockers.append(f"declaration_rejected_or_deferred_{dec}")

    # Match manifest references
    if decl.get("local_dispatch_execution_payload_manifest_id") != manifest.get("local_dispatch_execution_payload_manifest_id"):
        blockers.append("declaration_manifest_id_mismatch")
    if decl.get("combined_payload_hash") != manifest.get("combined_payload_hash"):
        blockers.append("declaration_combined_payload_hash_mismatch")

    # Match files with manifest
    rev_jsons = decl.get("reviewed_execution_preparation_json_files", [])
    man_jsons = manifest.get("execution_preparation_json_files", [])
    if [_normalize_path(p) for p in rev_jsons] != [_normalize_path(p) for p in man_jsons]:
        blockers.append("declaration_reviewed_execution_preparation_json_files_mismatch")

    rev_mds = decl.get("reviewed_execution_preparation_markdown_files", [])
    man_mds = manifest.get("execution_preparation_markdown_files", [])
    if [_normalize_path(p) for p in rev_mds] != [_normalize_path(p) for p in man_mds]:
        blockers.append("declaration_reviewed_execution_preparation_markdown_files_mismatch")

    rev_destinations = decl.get("reviewed_destinations", [])
    man_destinations = manifest.get("destinations", [])
    if _canonical_json(rev_destinations) != _canonical_json(man_destinations):
        blockers.append("declaration_reviewed_destinations_mismatch")

    # Validate credential key names list
    blockers.extend(_validate_credential_keys(decl.get("credential_key_names_only", [])))

    # Scan overall declaration for secrets/env lines
    if "notes" not in decl or not isinstance(decl["notes"], str):
        blockers.append("declaration_notes_missing_or_invalid")

    return blockers


def make_live_dispatch_readiness_preflight_packet(
    manifest_packet: Any,
    execution_jsons: list[Path],
    execution_json_packets: dict[str, Any],
    execution_mds: list[Path],
    execution_md_texts: dict[str, str],
    declaration_packet: Any,
) -> LiveDispatchReadinessPreflightPacket:
    blockers: list[str] = []

    manifest_is_dict = isinstance(manifest_packet, dict)
    if not manifest_is_dict:
        blockers.append("malformed_local_dispatch_execution_payload_manifest_json")

    declaration_is_dict = isinstance(declaration_packet, dict)
    if not declaration_is_dict:
        blockers.append("malformed_operator_live_dispatch_readiness_declaration_json")

    # Scan for secrets in json strings
    if manifest_is_dict and _has_secret_marker(json.dumps(manifest_packet)):
        blockers.append("manifest_secret_marker_detected")
    if declaration_is_dict:
        decl_copy = dict(declaration_packet)
        decl_copy.pop("credential_key_names_only", None)
        if _has_secret_marker(json.dumps(decl_copy)):
            blockers.append("declaration_secret_marker_detected")

    live_dispatch_readiness_declaration_id = ""
    operator_id = ""
    created_at_manual = ""
    local_dispatch_execution_payload_manifest_id = ""
    local_dispatch_execution_payload_manifest_sha256 = ""
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
    destinations: list[dict[str, Any]] = []
    platform_action_class = ""
    dispatch_family = ""
    official_docs_required = False
    credentials_required_later = False
    credential_key_names_only: list[str] = []
    destination_binding_required_later = False
    endpoint_allowlist_required_later = False
    payload_hash_required_later = False
    explicit_operator_approval_required_later = False
    kill_switch_required = False
    combined_payload_hash = ""

    execution_prep_json_files: list[str] = []
    execution_prep_json_hashes: dict[str, str] = {}
    execution_prep_markdown_files: list[str] = []
    execution_prep_markdown_hashes: dict[str, str] = {}

    if manifest_is_dict and "manifest_secret_marker_detected" not in blockers:
        blockers.extend(_validate_manifest_packet(manifest_packet))

        local_dispatch_execution_payload_manifest_id = str(manifest_packet.get("local_dispatch_execution_payload_manifest_id") or "")
        operator_supervised_dispatch_review_decision_packet_id = str(manifest_packet.get("operator_supervised_dispatch_review_decision_packet_id") or "")
        local_destination_binding_preflight_id = str(manifest_packet.get("local_destination_binding_preflight_id") or "")
        destination_binding_id = str(manifest_packet.get("destination_binding_id") or "")
        local_dispatch_payload_manifest_id = str(manifest_packet.get("local_dispatch_payload_manifest_id") or "")
        operator_dispatch_review_decision_packet_id = str(manifest_packet.get("operator_dispatch_review_decision_packet_id") or "")
        local_dispatch_preflight_id = str(manifest_packet.get("local_dispatch_preflight_id") or "")
        local_active_outbox_manifest_id = str(manifest_packet.get("local_active_outbox_manifest_id") or "")
        operator_active_outbox_review_decision_id = str(manifest_packet.get("operator_active_outbox_review_decision_id") or "")
        active_outbox_eligibility_id = str(manifest_packet.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(manifest_packet.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(manifest_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(manifest_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(manifest_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(manifest_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(manifest_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(manifest_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(manifest_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(manifest_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(manifest_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(manifest_packet.get("canonical_slug") or "")
        canonical_title = str(manifest_packet.get("canonical_title") or "")
        combined_payload_hash = str(manifest_packet.get("combined_payload_hash") or "")
        destinations = manifest_packet.get("destinations", [])

        if "declaration_secret_marker_detected" not in blockers and declaration_is_dict:
            blockers.extend(_validate_declaration(declaration_packet, manifest_packet))

            live_dispatch_readiness_declaration_id = str(declaration_packet.get("live_dispatch_readiness_declaration_id") or "")
            operator_id = str(declaration_packet.get("operator_id") or "")
            created_at_manual = str(declaration_packet.get("created_at_manual") or "")
            platform_action_class = str(declaration_packet.get("platform_action_class") or "")
            dispatch_family = str(declaration_packet.get("dispatch_family") or "")
            official_docs_required = bool(declaration_packet.get("official_docs_required"))
            credentials_required_later = bool(declaration_packet.get("credentials_required_later"))
            credential_key_names_only = list(declaration_packet.get("credential_key_names_only") or [])
            destination_binding_required_later = bool(declaration_packet.get("destination_binding_required_later"))
            endpoint_allowlist_required_later = bool(declaration_packet.get("endpoint_allowlist_required_later"))
            payload_hash_required_later = bool(declaration_packet.get("payload_hash_required_later"))
            explicit_operator_approval_required_later = bool(declaration_packet.get("explicit_operator_approval_required_later"))
            kill_switch_required = bool(declaration_packet.get("kill_switch_required"))

        # Compute manifest SHA256
        local_dispatch_execution_payload_manifest_sha256 = hashlib.sha256(_canonical_json(manifest_packet).encode("utf-8")).hexdigest()

        # Path matching checks
        supplied_jsons_normalized = [_normalize_path(p) for p in execution_jsons]
        reviewed_jsons_normalized = [_normalize_path(p) for p in manifest_packet.get("execution_preparation_json_files", [])]

        if len(execution_jsons) != 2:
            blockers.append("execution_json_file_paths_count_invalid")
        if len(set(supplied_jsons_normalized)) != len(supplied_jsons_normalized):
            blockers.append("execution_json_file_paths_duplicate_detected")
        if supplied_jsons_normalized != reviewed_jsons_normalized:
            blockers.append("execution_json_file_paths_order_mismatch")

        supplied_mds_normalized = [_normalize_path(p) for p in execution_mds]
        reviewed_mds_normalized = [_normalize_path(p) for p in manifest_packet.get("execution_preparation_markdown_files", [])]

        if len(execution_mds) != 2:
            blockers.append("execution_markdown_file_paths_count_invalid")
        if len(set(supplied_mds_normalized)) != len(supplied_mds_normalized):
            blockers.append("execution_markdown_file_paths_duplicate_detected")
        if supplied_mds_normalized != reviewed_mds_normalized:
            blockers.append("execution_markdown_file_paths_order_mismatch")

    # Validate execution JSONs
    for path in execution_jsons:
        npath = _normalize_path(path)
        json_data = None
        for k, v in execution_json_packets.items():
            if _normalize_path(k) == npath:
                json_data = v
                break

        if json_data is None:
            blockers.append(f"execution_json_packet_missing_{path.name}")
            continue

        if not isinstance(json_data, dict):
            blockers.append(f"execution_json_packet_malformed_{path.name}")
            continue

        if _has_secret_marker(json.dumps(json_data)):
            blockers.append("execution_json_secret_marker_detected")
            continue

        platform = json_data.get("platform") or ""
        blockers.extend(_validate_execution_json_packet(json_data, manifest_packet, f"execution_json_{platform}"))

        if "execution_json_secret_marker_detected" not in blockers:
            comp_hash = hashlib.sha256(_canonical_json(json_data).encode("utf-8")).hexdigest()
            execution_prep_json_hashes[npath] = comp_hash

            # Compare to manifest's execution preparation JSON hash
            expected = manifest_packet.get("execution_preparation_file_hashes", {}).get(npath)
            if expected and comp_hash != expected:
                blockers.append(f"execution_json_hash_mismatch_{path.name}")

    # Validate execution MDs
    for path in execution_mds:
        npath = _normalize_path(path)
        text = None
        for k, v in execution_md_texts.items():
            if _normalize_path(k) == npath:
                text = v
                break

        if text is None:
            blockers.append(f"execution_markdown_text_missing_{path.name}")
            continue

        platform = "substack" if "substack" in path.name.lower() else "discord"
        blockers.extend(_validate_preview_text(text, platform))

        has_file_secrets = _has_secret_marker(text)
        if not has_file_secrets:
            comp_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            execution_prep_markdown_hashes[npath] = comp_hash

            # Compare to manifest's execution preparation MD hash
            expected = manifest_packet.get("execution_preparation_file_hashes", {}).get(npath)
            if expected and comp_hash != expected:
                blockers.append(f"execution_markdown_hash_mismatch_{path.name}")

    blockers = sorted(set(blockers))
    prepared = not blockers
    approved = prepared and (declaration_packet.get("decision") == "mark_ready_for_future_live_dispatch_gate") if declaration_is_dict else False

    has_secrets = (
        "manifest_secret_marker_detected" in blockers or
        "declaration_secret_marker_detected" in blockers or
        "execution_json_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        live_dispatch_readiness_declaration_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_dispatch_execution_payload_manifest_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_dispatch_execution_payload_manifest_sha256 = ""
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
        destinations = []
        platform_action_class = ""
        dispatch_family = ""
        official_docs_required = False
        credentials_required_later = False
        credential_key_names_only = []
        destination_binding_required_later = False
        endpoint_allowlist_required_later = False
        payload_hash_required_later = False
        explicit_operator_approval_required_later = False
        kill_switch_required = False
        combined_payload_hash = ""
        execution_prep_json_files = []
        execution_prep_json_hashes = {}
        execution_prep_markdown_files = []
        execution_prep_markdown_hashes = {}
    else:
        execution_prep_json_files = [_normalize_path(p) for p in execution_jsons]
        execution_prep_markdown_files = [_normalize_path(p) for p in execution_mds]

    intake_material = {
        "live_dispatch_readiness_declaration_id": live_dispatch_readiness_declaration_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    live_dispatch_readiness_preflight_id = f"live_dispatch_readiness_preflight_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("live_dispatch_readiness_preflight_blocked_pending_operator_repair")

    return LiveDispatchReadinessPreflightPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        live_dispatch_readiness_preflight_id=live_dispatch_readiness_preflight_id,
        live_dispatch_readiness_declaration_id=live_dispatch_readiness_declaration_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        local_dispatch_execution_payload_manifest_id=local_dispatch_execution_payload_manifest_id,
        local_dispatch_execution_payload_manifest_sha256=local_dispatch_execution_payload_manifest_sha256,
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
        execution_preparation_json_files=execution_prep_json_files,
        execution_preparation_json_hashes=execution_prep_json_hashes,
        execution_preparation_markdown_files=execution_prep_markdown_files,
        execution_preparation_markdown_hashes=execution_prep_markdown_hashes,
        destinations=destinations,
        platform_action_class=platform_action_class,
        dispatch_family=dispatch_family,
        official_docs_required=official_docs_required,
        credentials_required_later=credentials_required_later,
        credential_key_names_only=credential_key_names_only,
        destination_binding_required_later=destination_binding_required_later,
        endpoint_allowlist_required_later=endpoint_allowlist_required_later,
        payload_hash_required_later=payload_hash_required_later,
        explicit_operator_approval_required_later=explicit_operator_approval_required_later,
        kill_switch_required=kill_switch_required,
        combined_payload_hash=combined_payload_hash,
        live_dispatch_readiness_preflight_available=prepared,
        eligible_for_future_live_dispatch_gate=prepared,
        live_dispatch_readiness_preflight_approved=approved,
        blockers=blockers,
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 live dispatch readiness preflight contract")
    parser.add_argument("manifest")
    parser.add_argument("declaration")
    parser.add_argument("--json-files", nargs="+", required=True)
    parser.add_argument("--markdown-files", nargs="+", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args(argv)

    try:
        manifest = load_json_packet(Path(args.manifest), "malformed_local_dispatch_execution_payload_manifest_json")
        declaration = load_json_packet(Path(args.declaration), "malformed_operator_live_dispatch_readiness_declaration_json")

        json_paths = [Path(p) for p in args.json_files]
        json_packets: dict[str, Any] = {}
        for path in json_paths:
            pkt = load_json_packet(path, f"execution_json_packet_malformed_{path.name}")
            json_packets[str(path)] = pkt

        md_paths = [Path(p) for p in args.markdown_files]
        md_texts: dict[str, str] = {}
        for path in md_paths:
            text = load_text_file(path, f"preview_file_text_missing_{path.name}")
            md_texts[str(path)] = text
    except ValueError as exc:
        blocker = str(exc)
        packet = LiveDispatchReadinessPreflightPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            live_dispatch_readiness_preflight_id="live_dispatch_readiness_preflight_blocked",
            live_dispatch_readiness_declaration_id="",
            operator_id="",
            created_at_manual="",
            local_dispatch_execution_payload_manifest_id="",
            local_dispatch_execution_payload_manifest_sha256="",
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
            platform_action_class="",
            dispatch_family="",
            official_docs_required=False,
            credentials_required_later=False,
            credential_key_names_only=[],
            destination_binding_required_later=False,
            endpoint_allowlist_required_later=False,
            payload_hash_required_later=False,
            explicit_operator_approval_required_later=False,
            kill_switch_required=False,
            combined_payload_hash="",
            live_dispatch_readiness_preflight_available=False,
            eligible_for_future_live_dispatch_gate=False,
            live_dispatch_readiness_preflight_approved=False,
            blockers=[blocker],
            warnings=["live_dispatch_readiness_preflight_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(asdict(packet), f, indent=2, sort_keys=True)
            f.write("\n")
        return 1

    packet = make_live_dispatch_readiness_preflight_packet(manifest, json_paths, json_packets, md_paths, md_texts, declaration)
    out_path = Path(args.output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(packet), f, indent=2, sort_keys=True)
        f.write("\n")

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
