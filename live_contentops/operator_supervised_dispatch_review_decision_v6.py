"""V6 Operator Supervised Dispatch Review Decision from Destination Preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PREFLIGHT_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DESTINATION_BINDING_PREFLIGHT_FROM_DISPATCH_PAYLOADS_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_SUPERVISED_DISPATCH_REVIEW_DECISION_FROM_DESTINATION_PREFLIGHT_V0"
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
class OperatorSupervisedDispatchReviewDecisionPacket:
    schema_version: str
    task_label: str
    operator_supervised_dispatch_review_decision_packet_id: str
    operator_supervised_dispatch_decision_id: str
    operator_id: str
    created_at_manual: str
    local_destination_binding_preflight_id: str
    local_destination_binding_preflight_sha256: str
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
    reviewed_prepared_dispatch_payload_json_files: list[str]
    reviewed_prepared_dispatch_payload_json_hashes: dict[str, str]
    reviewed_prepared_dispatch_payload_markdown_files: list[str]
    reviewed_prepared_dispatch_payload_markdown_hashes: dict[str, str]
    reviewed_destinations: list[dict[str, Any]]
    combined_payload_hash: str
    decision: str
    approval_phrase: str
    approval_scope: str
    dispatch_execution_preparation_approved: bool
    supervised_dispatch_review_decision_available: bool
    dispatch_execution_payload_created: bool = False
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


def _validate_preflight_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != PREFLIGHT_TASK_LABEL:
        blockers.append("preflight_task_label_invalid")
    if packet.get("destination_binding_preflight_available") is not True:
        blockers.append("preflight_destination_binding_preflight_not_available")
    if packet.get("eligible_for_supervised_dispatch_gate") is not True:
        blockers.append("preflight_eligible_for_supervised_dispatch_gate_not_true")
    if packet.get("destination_binding_created") is not True:
        blockers.append("preflight_destination_binding_created_not_true")
    if packet.get("dispatch_execution_payload_created") is not False:
        blockers.append("preflight_dispatch_execution_payload_created_not_false")
    if packet.get("live_send_request_created") is not False:
        blockers.append("preflight_live_send_request_created_not_false")
    if packet.get("approval_for_live_dispatch") is not False:
        blockers.append("preflight_approval_for_live_dispatch_not_false")
    if packet.get("approval_for_publication") is not False:
        blockers.append("preflight_approval_for_publication_not_false")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("preflight_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("preflight_citations_verified_not_false")

    blockers.extend(_check_public_and_live_fields(packet, "preflight"))

    if packet.get("review_only") is not True:
        blockers.append("preflight_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("preflight_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("preflight_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("preflight_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("preflight_has_blockers")

    # Count checks
    jsons = packet.get("prepared_dispatch_payload_json_files", [])
    if not isinstance(jsons, list) or len(jsons) != 2:
        blockers.append("preflight_prepared_dispatch_payload_json_files_count_invalid")

    json_hashes = packet.get("prepared_dispatch_payload_json_hashes", {})
    if not isinstance(json_hashes, dict) or len(json_hashes) != 2:
        blockers.append("preflight_prepared_dispatch_payload_json_hashes_count_invalid")

    mds = packet.get("prepared_dispatch_payload_markdown_files", [])
    if not isinstance(mds, list) or len(mds) != 2:
        blockers.append("preflight_prepared_dispatch_payload_markdown_files_count_invalid")

    md_hashes = packet.get("prepared_dispatch_payload_markdown_hashes", {})
    if not isinstance(md_hashes, dict) or len(md_hashes) != 2:
        blockers.append("preflight_prepared_dispatch_payload_markdown_hashes_count_invalid")

    destinations = packet.get("destinations", [])
    if not isinstance(destinations, list) or len(destinations) != 2:
        blockers.append("preflight_destinations_count_invalid")

    required_keys = [
        "local_destination_binding_preflight_id",
        "destination_binding_id",
        "operator_id",
        "created_at_manual",
        "local_dispatch_payload_manifest_id",
        "local_dispatch_payload_manifest_sha256",
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
            blockers.append(f"preflight_{key}_missing")

    return blockers


def _validate_decision_packet(decision_packet: dict[str, Any], preflight: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    
    # Required keys
    req_keys = [
        "schema_version",
        "operator_supervised_dispatch_decision_id",
        "operator_id",
        "created_at_manual",
        "local_destination_binding_preflight_id",
        "local_dispatch_payload_manifest_id",
        "destination_binding_id",
        "combined_payload_hash",
        "reviewed_prepared_dispatch_payload_json_files",
        "reviewed_prepared_dispatch_payload_markdown_files",
        "reviewed_destinations",
        "decision",
        "approval_phrase",
        "approval_scope",
    ]
    for key in req_keys:
        if not decision_packet.get(key):
            blockers.append(f"decision_{key}_missing")

    if "notes" not in decision_packet or not isinstance(decision_packet.get("notes"), str):
        blockers.append("decision_notes_missing_or_invalid")

    decision = decision_packet.get("decision")
    if decision not in ["approve_dispatch_execution_preparation", "reject", "defer"]:
        blockers.append("decision_value_invalid")

    if decision == "approve_dispatch_execution_preparation":
        if decision_packet.get("approval_phrase") != "APPROVE_LOCAL_DISPATCH_EXECUTION_PREPARATION_ONLY_NOT_LIVE_SEND":
            blockers.append("decision_approval_phrase_invalid")
        if decision_packet.get("approval_scope") != "dispatch_execution_preparation_only":
            blockers.append("decision_approval_scope_invalid")
    else:
        blockers.append(f"decision_rejected_or_deferred_{decision}")

    # Matching values against preflight
    if decision_packet.get("local_destination_binding_preflight_id") != preflight.get("local_destination_binding_preflight_id"):
        blockers.append("decision_local_destination_binding_preflight_id_mismatch")
    if decision_packet.get("local_dispatch_payload_manifest_id") != preflight.get("local_dispatch_payload_manifest_id"):
        blockers.append("decision_local_dispatch_payload_manifest_id_mismatch")
    if decision_packet.get("destination_binding_id") != preflight.get("destination_binding_id"):
        blockers.append("decision_destination_binding_id_mismatch")
    if decision_packet.get("combined_payload_hash") != preflight.get("combined_payload_hash"):
        blockers.append("decision_combined_payload_hash_mismatch")

    # Order preserved path matching for JSON files
    rev_jsons = decision_packet.get("reviewed_prepared_dispatch_payload_json_files", [])
    pre_jsons = preflight.get("prepared_dispatch_payload_json_files", [])
    if not isinstance(rev_jsons, list):
        blockers.append("decision_reviewed_prepared_dispatch_payload_json_files_not_list")
    else:
        rev_jsons_norm = [_normalize_path(p) for p in rev_jsons]
        pre_jsons_norm = [_normalize_path(p) for p in pre_jsons]
        if rev_jsons_norm != pre_jsons_norm:
            blockers.append("decision_reviewed_prepared_dispatch_payload_json_files_mismatch")

    # Order preserved path matching for markdown files
    rev_mds = decision_packet.get("reviewed_prepared_dispatch_payload_markdown_files", [])
    pre_mds = preflight.get("prepared_dispatch_payload_markdown_files", [])
    if not isinstance(rev_mds, list):
        blockers.append("decision_reviewed_prepared_dispatch_payload_markdown_files_not_list")
    else:
        rev_mds_norm = [_normalize_path(p) for p in rev_mds]
        pre_mds_norm = [_normalize_path(p) for p in pre_mds]
        if rev_mds_norm != pre_mds_norm:
            blockers.append("decision_reviewed_prepared_dispatch_payload_markdown_files_mismatch")

    # Destinations check
    rev_destinations = decision_packet.get("reviewed_destinations", [])
    pre_destinations = preflight.get("destinations", [])
    if not isinstance(rev_destinations, list) or len(rev_destinations) != 2:
        blockers.append("decision_reviewed_destinations_count_invalid")
    else:
        rev_canon = _canonical_json(rev_destinations)
        pre_canon = _canonical_json(pre_destinations)
        if rev_canon != pre_canon:
            blockers.append("decision_reviewed_destinations_mismatch")

    # Scan overall decision packet for credentials, identifiers, tokens, webhooks etc.
    serialized_dec = json.dumps(decision_packet)
    if _has_secret_marker(serialized_dec):
        blockers.append("decision_secret_marker_detected")

    clean_dec = serialized_dec.lower()
    clean_dec = clean_dec.replace("webhook_family_target", "")
    for key in ["channel_id", "account_id", "app_id", "workspace_id", "bot_token", "url", "webhook"]:
        if key in clean_dec:
            blockers.append("decision_raw_platform_identifier_detected")

    lowered_dec = serialized_dec.lower()
    for marker in PUBLIC_READY_MARKERS:
        if marker in lowered_dec:
            blockers.append(f"decision_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in lowered_dec:
            blockers.append(f"decision_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in lowered_dec:
            blockers.append(f"decision_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(lowered_dec):
            blockers.append("decision_financial_advice_or_signal_framing_detected")
            break

    # Webhook or dispatch tokens check
    live_send_markers = ["webhook_url", "channel_id", "bot_token", "dispatch_allowed: true", "publish: true"]
    for marker in live_send_markers:
        if marker in lowered_dec:
            blockers.append("decision_live_send_instructions_detected")

    return blockers


def make_operator_supervised_dispatch_review_decision_packet(
    preflight_packet: Any,
    operator_decision_json: Any,
) -> OperatorSupervisedDispatchReviewDecisionPacket:
    blockers: list[str] = []

    preflight_is_dict = isinstance(preflight_packet, dict)
    if not preflight_is_dict:
        blockers.append("malformed_local_destination_binding_preflight_json")

    decision_is_dict = isinstance(operator_decision_json, dict)
    if not decision_is_dict:
        blockers.append("malformed_operator_supervised_dispatch_decision_json")

    # Scan preflight for secrets
    if preflight_is_dict and _has_secret_marker(json.dumps(preflight_packet)):
        blockers.append("preflight_secret_marker_detected")

    operator_supervised_dispatch_decision_id = ""
    operator_id = ""
    created_at_manual = ""
    local_destination_binding_preflight_id = ""
    local_destination_binding_preflight_sha256 = ""
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
    reviewed_prepared_dispatch_payload_json_files: list[str] = []
    reviewed_prepared_dispatch_payload_json_hashes: dict[str, str] = {}
    reviewed_prepared_dispatch_payload_markdown_files: list[str] = []
    reviewed_prepared_dispatch_payload_markdown_hashes: dict[str, str] = {}
    reviewed_destinations: list[dict[str, Any]] = []
    combined_payload_hash = ""
    decision_val = ""
    approval_phrase = ""
    approval_scope = ""
    dispatch_execution_preparation_approved = False

    if preflight_is_dict and "preflight_secret_marker_detected" not in blockers:
        blockers.extend(_validate_preflight_packet(preflight_packet))

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
        combined_payload_hash = str(preflight_packet.get("combined_payload_hash") or "")

    if decision_is_dict:
        blockers.extend(_validate_decision_packet(operator_decision_json, preflight_packet))

        operator_supervised_dispatch_decision_id = str(operator_decision_json.get("operator_supervised_dispatch_decision_id") or "")
        operator_id = str(operator_decision_json.get("operator_id") or "")
        created_at_manual = str(operator_decision_json.get("created_at_manual") or "")
        decision_val = str(operator_decision_json.get("decision") or "")
        approval_phrase = str(operator_decision_json.get("approval_phrase") or "")
        approval_scope = str(operator_decision_json.get("approval_scope") or "")

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "preflight_secret_marker_detected" in blockers or
        "decision_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
        operator_supervised_dispatch_decision_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_destination_binding_preflight_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_destination_binding_preflight_sha256 = ""
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
        reviewed_prepared_dispatch_payload_json_files = []
        reviewed_prepared_dispatch_payload_json_hashes = {}
        reviewed_prepared_dispatch_payload_markdown_files = []
        reviewed_prepared_dispatch_payload_markdown_hashes = {}
        reviewed_destinations = []
        combined_payload_hash = ""
        decision_val = ""
        approval_phrase = ""
        approval_scope = ""

    else:
        if preflight_is_dict:
            local_destination_binding_preflight_sha256 = hashlib.sha256(_canonical_json(preflight_packet).encode("utf-8")).hexdigest()
            reviewed_prepared_dispatch_payload_json_files = preflight_packet.get("prepared_dispatch_payload_json_files", [])
            reviewed_prepared_dispatch_payload_json_hashes = preflight_packet.get("prepared_dispatch_payload_json_hashes", {})
            reviewed_prepared_dispatch_payload_markdown_files = preflight_packet.get("prepared_dispatch_payload_markdown_files", [])
            reviewed_prepared_dispatch_payload_markdown_hashes = preflight_packet.get("prepared_dispatch_payload_markdown_hashes", {})
            reviewed_destinations = preflight_packet.get("destinations", [])

        if available and decision_val == "approve_dispatch_execution_preparation":
            dispatch_execution_preparation_approved = True

    # Deterministic packet ID
    intake_material = {
        "local_destination_binding_preflight_id": local_destination_binding_preflight_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
        "operator_supervised_dispatch_decision_id": operator_supervised_dispatch_decision_id,
    }
    operator_supervised_dispatch_review_decision_packet_id = f"operator_supervised_dispatch_review_decision_packet_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("operator_supervised_dispatch_review_decision_blocked_pending_operator_repair")

    return OperatorSupervisedDispatchReviewDecisionPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        operator_supervised_dispatch_review_decision_packet_id=operator_supervised_dispatch_review_decision_packet_id,
        operator_supervised_dispatch_decision_id=operator_supervised_dispatch_decision_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        local_destination_binding_preflight_id=local_destination_binding_preflight_id,
        local_destination_binding_preflight_sha256=local_destination_binding_preflight_sha256,
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
        reviewed_prepared_dispatch_payload_json_files=reviewed_prepared_dispatch_payload_json_files,
        reviewed_prepared_dispatch_payload_json_hashes=reviewed_prepared_dispatch_payload_json_hashes,
        reviewed_prepared_dispatch_payload_markdown_files=reviewed_prepared_dispatch_payload_markdown_files,
        reviewed_prepared_dispatch_payload_markdown_hashes=reviewed_prepared_dispatch_payload_markdown_hashes,
        reviewed_destinations=reviewed_destinations,
        combined_payload_hash=combined_payload_hash,
        decision=decision_val,
        approval_phrase=approval_phrase,
        approval_scope=approval_scope,
        dispatch_execution_preparation_approved=dispatch_execution_preparation_approved,
        supervised_dispatch_review_decision_available=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_operator_supervised_dispatch_review_decision_packet(
    packet: OperatorSupervisedDispatchReviewDecisionPacket,
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    packet_path = out_path / f"{packet.operator_supervised_dispatch_review_decision_packet_id}.json"
    with open(packet_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(packet), f, indent=2, sort_keys=True)
        f.write("\n")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 operator supervised dispatch review decision contract")
    parser.add_argument("preflight_packet")
    parser.add_argument("decision_packet")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        preflight = load_json_packet(Path(args.preflight_packet), "malformed_local_destination_binding_preflight_json")
        decision = load_json_packet(Path(args.decision_packet), "malformed_operator_supervised_dispatch_decision_json")
    except ValueError as exc:
        blocker = str(exc)
        packet = OperatorSupervisedDispatchReviewDecisionPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            operator_supervised_dispatch_review_decision_packet_id="operator_supervised_dispatch_review_decision_packet_blocked",
            operator_supervised_dispatch_decision_id="",
            operator_id="",
            created_at_manual="",
            local_destination_binding_preflight_id="",
            local_destination_binding_preflight_sha256="",
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
            reviewed_prepared_dispatch_payload_json_files=[],
            reviewed_prepared_dispatch_payload_json_hashes={},
            reviewed_prepared_dispatch_payload_markdown_files=[],
            reviewed_prepared_dispatch_payload_markdown_hashes={},
            reviewed_destinations=[],
            combined_payload_hash="",
            decision="",
            approval_phrase="",
            approval_scope="",
            dispatch_execution_preparation_approved=False,
            supervised_dispatch_review_decision_available=False,
            blockers=[blocker],
            warnings=["operator_supervised_dispatch_review_decision_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        packet_path = out_path / f"{packet.operator_supervised_dispatch_review_decision_packet_id}.json"
        with open(packet_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(asdict(packet), f, indent=2, sort_keys=True)
            f.write("\n")
        return 1

    packet = make_operator_supervised_dispatch_review_decision_packet(preflight, decision)
    write_operator_supervised_dispatch_review_decision_packet(packet, Path(args.output_dir))

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
