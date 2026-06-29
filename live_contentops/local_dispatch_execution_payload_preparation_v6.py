"""V6 Local Dispatch Execution Payload Preparation from Supervised Decision."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DECISION_TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_SUPERVISED_DISPATCH_REVIEW_DECISION_FROM_DESTINATION_PREFLIGHT_V0"
PREFLIGHT_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DESTINATION_BINDING_PREFLIGHT_FROM_DISPATCH_PAYLOADS_V0"
PAYLOAD_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PAYLOAD_PREPARATION_FROM_OPERATOR_DECISION_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_EXECUTION_PAYLOAD_PREPARATION_FROM_SUPERVISED_DECISION_V0"
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
class LocalDispatchExecutionPayloadManifest:
    schema_version: str
    task_label: str
    local_dispatch_execution_payload_manifest_id: str
    operator_supervised_dispatch_review_decision_packet_id: str
    operator_supervised_dispatch_decision_sha256: str
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
    execution_preparation_dir: str
    prepared_dispatch_payload_json_files: list[str]
    prepared_dispatch_payload_json_hashes: dict[str, str]
    prepared_dispatch_payload_markdown_files: list[str]
    prepared_dispatch_payload_markdown_hashes: dict[str, str]
    execution_preparation_json_files: list[str]
    execution_preparation_markdown_files: list[str]
    execution_preparation_file_hashes: dict[str, str]
    destinations: list[dict[str, Any]]
    combined_payload_hash: str
    local_dispatch_execution_prepared: bool
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


@dataclass(frozen=True)
class ExecutionPreparationPayload:
    schema_version: str
    task_label: str
    execution_preparation_payload_id: str
    platform: str
    preparation_status: str
    destination: dict[str, Any]
    markdown_snapshot_file: str
    markdown_snapshot_sha256: str
    source_prepared_dispatch_payload_json_file: str
    source_prepared_dispatch_payload_json_sha256: str
    source_prepared_dispatch_payload_markdown_file: str
    source_prepared_dispatch_payload_markdown_sha256: str
    combined_payload_hash: str
    operator_supervised_dispatch_review_decision_packet_id: str
    local_destination_binding_preflight_id: str
    local_dispatch_payload_manifest_id: str
    canonical_slug: str
    canonical_title: str
    local_dispatch_execution_prepared: bool
    dispatch_execution_payload_created: bool = True
    live_send_request_created: bool = False
    approval_for_live_dispatch: bool = False
    dispatch_allowed: bool = False
    approval_for_publication: bool = False
    publication_ready: bool = False
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


def _validate_decision_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != DECISION_TASK_LABEL:
        blockers.append("decision_task_label_invalid")
    if packet.get("supervised_dispatch_review_decision_available") is not True:
        blockers.append("decision_supervised_dispatch_review_decision_not_available")
    if packet.get("dispatch_execution_preparation_approved") is not True:
        blockers.append("decision_dispatch_execution_preparation_not_approved")
    if packet.get("decision") != "approve_dispatch_execution_preparation":
        blockers.append("decision_value_invalid")
    if packet.get("approval_phrase") != "APPROVE_LOCAL_DISPATCH_EXECUTION_PREPARATION_ONLY_NOT_LIVE_SEND":
        blockers.append("decision_approval_phrase_invalid")
    if packet.get("approval_scope") != "dispatch_execution_preparation_only":
        blockers.append("decision_approval_scope_invalid")

    if packet.get("dispatch_execution_payload_created") is not False:
        blockers.append("decision_dispatch_execution_payload_created_not_false")
    if packet.get("live_send_request_created") is not False:
        blockers.append("decision_live_send_request_created_not_false")
    if packet.get("approval_for_live_dispatch") is not False:
        blockers.append("decision_approval_for_live_dispatch_not_false")
    if packet.get("approval_for_publication") is not False:
        blockers.append("decision_approval_for_publication_not_false")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("decision_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("decision_citations_verified_not_false")

    blockers.extend(_check_public_and_live_fields(packet, "decision"))

    if packet.get("review_only") is not True:
        blockers.append("decision_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("decision_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("decision_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("decision_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("decision_has_blockers")

    # Required keys count
    jsons = packet.get("reviewed_prepared_dispatch_payload_json_files", [])
    if not isinstance(jsons, list) or len(jsons) != 2:
        blockers.append("decision_reviewed_prepared_dispatch_payload_json_files_count_invalid")
    
    json_hashes = packet.get("reviewed_prepared_dispatch_payload_json_hashes", {})
    if not isinstance(json_hashes, dict) or len(json_hashes) != 2:
        blockers.append("decision_reviewed_prepared_dispatch_payload_json_hashes_count_invalid")

    mds = packet.get("reviewed_prepared_dispatch_payload_markdown_files", [])
    if not isinstance(mds, list) or len(mds) != 2:
        blockers.append("decision_reviewed_prepared_dispatch_payload_markdown_files_count_invalid")

    md_hashes = packet.get("reviewed_prepared_dispatch_payload_markdown_hashes", {})
    if not isinstance(md_hashes, dict) or len(md_hashes) != 2:
        blockers.append("decision_reviewed_prepared_dispatch_payload_markdown_hashes_count_invalid")

    destinations = packet.get("reviewed_destinations", [])
    if not isinstance(destinations, list) or len(destinations) != 2:
        blockers.append("decision_reviewed_destinations_count_invalid")

    required_keys = [
        "operator_supervised_dispatch_review_decision_packet_id",
        "operator_supervised_dispatch_decision_id",
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
            blockers.append(f"decision_{key}_missing")

    return blockers


def _validate_preflight_packet(packet: dict[str, Any], decision: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != PREFLIGHT_TASK_LABEL:
        blockers.append("preflight_task_label_invalid")
    if packet.get("local_destination_binding_preflight_id") != decision.get("local_destination_binding_preflight_id"):
        blockers.append("preflight_id_mismatch")
    if packet.get("local_dispatch_payload_manifest_id") != decision.get("local_dispatch_payload_manifest_id"):
        blockers.append("preflight_manifest_id_mismatch")
    if packet.get("destination_binding_id") != decision.get("destination_binding_id"):
        blockers.append("preflight_destination_binding_id_mismatch")
    if packet.get("combined_payload_hash") != decision.get("combined_payload_hash"):
        blockers.append("preflight_combined_payload_hash_mismatch")

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
    if packet.get("dispatch_allowed") is not False:
        blockers.append("preflight_dispatch_allowed_not_false")
    if packet.get("approval_for_publication") is not False:
        blockers.append("preflight_approval_for_publication_not_false")
    if packet.get("publication_ready") is not False:
        blockers.append("preflight_publication_ready_not_false")
    if packet.get("public_url") is not None:
        blockers.append("preflight_public_url_not_null")
    if packet.get("public_metrics") is not None:
        blockers.append("preflight_public_metrics_not_null")
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

    # Match files with decision
    rev_jsons = decision.get("reviewed_prepared_dispatch_payload_json_files", [])
    pre_jsons = packet.get("prepared_dispatch_payload_json_files", [])
    if [_normalize_path(p) for p in pre_jsons] != [_normalize_path(p) for p in rev_jsons]:
        blockers.append("preflight_prepared_dispatch_payload_json_files_mismatch")

    rev_mds = decision.get("reviewed_prepared_dispatch_payload_markdown_files", [])
    pre_mds = packet.get("prepared_dispatch_payload_markdown_files", [])
    if [_normalize_path(p) for p in pre_mds] != [_normalize_path(p) for p in rev_mds]:
        blockers.append("preflight_prepared_dispatch_payload_markdown_files_mismatch")

    # Match JSON hashes
    rev_json_hashes = decision.get("reviewed_prepared_dispatch_payload_json_hashes", {})
    pre_json_hashes = packet.get("prepared_dispatch_payload_json_hashes", {})
    rev_json_hashes_norm = {_normalize_path(k): v for k, v in rev_json_hashes.items()}
    pre_json_hashes_norm = {_normalize_path(k): v for k, v in pre_json_hashes.items()}
    if rev_json_hashes_norm != pre_json_hashes_norm:
        blockers.append("preflight_prepared_dispatch_payload_json_hashes_mismatch")

    # Match MD hashes
    rev_md_hashes = decision.get("reviewed_prepared_dispatch_payload_markdown_hashes", {})
    pre_md_hashes = packet.get("prepared_dispatch_payload_markdown_hashes", {})
    rev_md_hashes_norm = {_normalize_path(k): v for k, v in rev_md_hashes.items()}
    pre_md_hashes_norm = {_normalize_path(k): v for k, v in pre_md_hashes.items()}
    if rev_md_hashes_norm != pre_md_hashes_norm:
        blockers.append("preflight_prepared_dispatch_payload_markdown_hashes_mismatch")

    # Match destinations
    rev_destinations = decision.get("reviewed_destinations", [])
    pre_destinations = packet.get("destinations", [])
    if _canonical_json(pre_destinations) != _canonical_json(rev_destinations):
        blockers.append("preflight_destinations_mismatch")

    return blockers


def _validate_prepared_json_packet(entry: dict[str, Any], decision: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if entry.get("task_label") != PAYLOAD_TASK_LABEL:
        blockers.append(f"{prefix}_task_label_invalid")
    
    platform = entry.get("platform")
    if platform not in ["substack", "discord"]:
        blockers.append(f"{prefix}_platform_invalid")

    if entry.get("preparation_status") != "local_dispatch_payload_pending_supervised_dispatch_gate":
        blockers.append(f"{prefix}_preparation_status_invalid")

    if entry.get("dispatch_payload_created") is not True:
        blockers.append(f"{prefix}_dispatch_payload_created_not_true")
    if entry.get("dispatch_execution_payload_created") is not False:
        blockers.append(f"{prefix}_dispatch_execution_payload_created_not_false")
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
    if entry.get("combined_payload_hash") != decision.get("combined_payload_hash"):
        blockers.append(f"{prefix}_combined_payload_hash_mismatch")
    if entry.get("operator_dispatch_review_decision_packet_id") != decision.get("operator_dispatch_review_decision_packet_id"):
        blockers.append(f"{prefix}_operator_dispatch_review_decision_packet_id_mismatch")
    if entry.get("local_dispatch_preflight_id") != decision.get("local_dispatch_preflight_id"):
        blockers.append(f"{prefix}_local_dispatch_preflight_id_mismatch")
    if entry.get("local_active_outbox_manifest_id") != decision.get("local_active_outbox_manifest_id"):
        blockers.append(f"{prefix}_local_active_outbox_manifest_id_mismatch")
    if entry.get("canonical_slug") != decision.get("canonical_slug"):
        blockers.append(f"{prefix}_canonical_slug_mismatch")
    if entry.get("canonical_title") != decision.get("canonical_title"):
        blockers.append(f"{prefix}_canonical_title_mismatch")

    # Match payload markdown file
    entry_md = entry.get("payload_markdown_file")
    if not entry_md:
        blockers.append(f"{prefix}_payload_markdown_file_missing")
    else:
        npath = _normalize_path(entry_md)
        decision_mds_normalized = [_normalize_path(p) for p in decision.get("reviewed_prepared_dispatch_payload_markdown_files", [])]
        if npath not in decision_mds_normalized:
            blockers.append(f"{prefix}_payload_markdown_file_not_in_decision")
        else:
            # Find matching hash
            expected_hash = None
            for k, v in decision.get("reviewed_prepared_dispatch_payload_markdown_hashes", {}).items():
                if _normalize_path(k) == npath:
                    expected_hash = v
                    break
            
            if entry.get("payload_markdown_sha256") != expected_hash:
                blockers.append(f"{prefix}_payload_markdown_sha256_mismatch")

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


def make_local_dispatch_execution_payload_manifest(
    decision_packet: Any,
    preflight_packet: Any,
    prepared_jsons: list[Path],
    prepared_json_packets: dict[str, Any],
    prepared_mds: list[Path],
    prepared_md_texts: dict[str, str],
    output_dir: Path,
) -> LocalDispatchExecutionPayloadManifest:
    blockers: list[str] = []

    decision_is_dict = isinstance(decision_packet, dict)
    if not decision_is_dict:
        blockers.append("malformed_operator_supervised_dispatch_review_decision_json")

    preflight_is_dict = isinstance(preflight_packet, dict)
    if not preflight_is_dict:
        blockers.append("malformed_local_destination_binding_preflight_json")

    # Scan decision/preflight for secrets
    if decision_is_dict and _has_secret_marker(json.dumps(decision_packet)):
        blockers.append("decision_secret_marker_detected")
    if preflight_is_dict and _has_secret_marker(json.dumps(preflight_packet)):
        blockers.append("preflight_secret_marker_detected")

    operator_supervised_dispatch_review_decision_packet_id = ""
    operator_supervised_dispatch_decision_sha256 = ""
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
    combined_payload_hash = ""
    destinations: list[dict[str, Any]] = []

    prepared_payload_json_files: list[str] = []
    prepared_payload_json_hashes: dict[str, str] = {}
    prepared_payload_markdown_files: list[str] = []
    prepared_payload_markdown_hashes: dict[str, str] = {}

    if decision_is_dict and "decision_secret_marker_detected" not in blockers:
        blockers.extend(_validate_decision_packet(decision_packet))
        
        operator_supervised_dispatch_review_decision_packet_id = str(decision_packet.get("operator_supervised_dispatch_review_decision_packet_id") or "")
        local_destination_binding_preflight_id = str(decision_packet.get("local_destination_binding_preflight_id") or "")
        destination_binding_id = str(decision_packet.get("destination_binding_id") or "")
        local_dispatch_payload_manifest_id = str(decision_packet.get("local_dispatch_payload_manifest_id") or "")
        operator_dispatch_review_decision_packet_id = str(decision_packet.get("operator_dispatch_review_decision_packet_id") or "")
        local_dispatch_preflight_id = str(decision_packet.get("local_dispatch_preflight_id") or "")
        local_active_outbox_manifest_id = str(decision_packet.get("local_active_outbox_manifest_id") or "")
        operator_active_outbox_review_decision_id = str(decision_packet.get("operator_active_outbox_review_decision_id") or "")
        active_outbox_eligibility_id = str(decision_packet.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(decision_packet.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(decision_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(decision_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(decision_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(decision_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(decision_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(decision_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(decision_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(decision_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(decision_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(decision_packet.get("canonical_slug") or "")
        canonical_title = str(decision_packet.get("canonical_title") or "")
        combined_payload_hash = str(decision_packet.get("combined_payload_hash") or "")
        destinations = decision_packet.get("reviewed_destinations", [])

        # Match Preflight
        if preflight_is_dict and "preflight_secret_marker_detected" not in blockers:
            blockers.extend(_validate_preflight_packet(preflight_packet, decision_packet))

            # Verify manifest SHA256 matches preflight packet's local_destination_binding_preflight_sha256
            computed_preflight_sha256 = hashlib.sha256(_canonical_json(preflight_packet).encode("utf-8")).hexdigest()
            if computed_preflight_sha256 != decision_packet.get("local_destination_binding_preflight_sha256"):
                blockers.append("decision_preflight_sha256_mismatch")

        # Match supplied paths with reviewed files list
        supplied_jsons_normalized = [_normalize_path(p) for p in prepared_jsons]
        reviewed_jsons_normalized = [_normalize_path(p) for p in decision_packet.get("reviewed_prepared_dispatch_payload_json_files", [])]

        if len(prepared_jsons) != 2:
            blockers.append("prepared_json_file_paths_count_invalid")
        if len(set(supplied_jsons_normalized)) != len(supplied_jsons_normalized):
            blockers.append("prepared_json_file_paths_duplicate_detected")
        if supplied_jsons_normalized != reviewed_jsons_normalized:
            blockers.append("prepared_json_file_paths_order_mismatch")

        supplied_mds_normalized = [_normalize_path(p) for p in prepared_mds]
        reviewed_mds_normalized = [_normalize_path(p) for p in decision_packet.get("reviewed_prepared_dispatch_payload_markdown_files", [])]

        if len(prepared_mds) != 2:
            blockers.append("prepared_markdown_file_paths_count_invalid")
        if len(set(supplied_mds_normalized)) != len(supplied_mds_normalized):
            blockers.append("prepared_markdown_file_paths_duplicate_detected")
        if supplied_mds_normalized != reviewed_mds_normalized:
            blockers.append("prepared_markdown_file_paths_order_mismatch")

    # Validate prepared JSONs
    for path in prepared_jsons:
        npath = _normalize_path(path)
        json_data = None
        for k, v in prepared_json_packets.items():
            if _normalize_path(k) == npath:
                json_data = v
                break

        if json_data is None:
            blockers.append(f"prepared_json_packet_missing_{path.name}")
            continue

        if not isinstance(json_data, dict):
            blockers.append(f"prepared_json_packet_malformed_{path.name}")
            continue

        if _has_secret_marker(json.dumps(json_data)):
            blockers.append("prepared_json_secret_marker_detected")
            continue

        platform = json_data.get("platform") or ""
        blockers.extend(_validate_prepared_json_packet(json_data, decision_packet, f"prepared_json_{platform}"))
        
        if "prepared_json_secret_marker_detected" not in blockers:
            comp_hash = hashlib.sha256(_canonical_json(json_data).encode("utf-8")).hexdigest()
            prepared_payload_json_hashes[npath] = comp_hash
            
            # Compare to decision's reviewed json hash
            expected = decision_packet.get("reviewed_prepared_dispatch_payload_json_hashes", {}).get(npath)
            if expected and comp_hash != expected:
                blockers.append(f"json_hash_mismatch_{path.name}")

    # Validate prepared MDs
    for path in prepared_mds:
        npath = _normalize_path(path)
        text = None
        for k, v in prepared_md_texts.items():
            if _normalize_path(k) == npath:
                text = v
                break

        if text is None:
            blockers.append(f"prepared_markdown_text_missing_{path.name}")
            continue

        platform = "substack" if "substack" in path.name.lower() else "discord"
        blockers.extend(_validate_preview_text(text, platform))
        
        has_file_secrets = _has_secret_marker(text)
        if not has_file_secrets:
            comp_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            prepared_payload_markdown_hashes[npath] = comp_hash
            
            # Compare to decision's reviewed md hash
            expected = decision_packet.get("reviewed_prepared_dispatch_payload_markdown_hashes", {}).get(npath)
            if expected and comp_hash != expected:
                blockers.append(f"markdown_hash_mismatch_{path.name}")

    blockers = sorted(set(blockers))
    prepared = not blockers

    has_secrets = (
        "decision_secret_marker_detected" in blockers or
        "preflight_secret_marker_detected" in blockers or
        "prepared_json_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    execution_dir_str = ""
    execution_prep_jsons: list[str] = []
    execution_prep_mds: list[str] = []

    if has_secrets:
        # Redact IDs
        operator_supervised_dispatch_review_decision_packet_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_supervised_dispatch_decision_sha256 = ""
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
        combined_payload_hash = ""
        prepared_dispatch_payload_json_files = []
        prepared_dispatch_payload_json_hashes = {}
        prepared_dispatch_payload_markdown_files = []
        prepared_dispatch_payload_markdown_hashes = {}
        destinations = []

    elif decision_is_dict and not has_secrets:
        operator_supervised_dispatch_decision_sha256 = hashlib.sha256(_canonical_json(decision_packet).encode("utf-8")).hexdigest()
        local_destination_binding_preflight_sha256 = decision_packet.get("local_destination_binding_preflight_sha256") or ""
        prepared_dispatch_payload_json_files = [_normalize_path(p) for p in prepared_jsons]
        prepared_dispatch_payload_markdown_files = [_normalize_path(p) for p in prepared_mds]

        if prepared:
            dir_name = f"{canonical_slug}_{combined_payload_hash[:16]}"
            execution_dir_str = _normalize_path(output_dir / dir_name)
            
            execution_prep_jsons = [
                _normalize_path(Path(execution_dir_str) / "substack_execution_preparation.json"),
                _normalize_path(Path(execution_dir_str) / "discord_execution_preparation.json"),
            ]
            execution_prep_mds = [
                _normalize_path(Path(execution_dir_str) / "substack_execution_preparation.md"),
                _normalize_path(Path(execution_dir_str) / "discord_execution_preparation.md"),
            ]

    # Deterministic manifest ID
    intake_material = {
        "operator_supervised_dispatch_review_decision_packet_id": operator_supervised_dispatch_review_decision_packet_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    local_dispatch_execution_payload_manifest_id = f"local_dispatch_execution_payload_manifest_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("local_dispatch_execution_payload_preparation_blocked_pending_operator_repair")

    return LocalDispatchExecutionPayloadManifest(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        local_dispatch_execution_payload_manifest_id=local_dispatch_execution_payload_manifest_id,
        operator_supervised_dispatch_review_decision_packet_id=operator_supervised_dispatch_review_decision_packet_id,
        operator_supervised_dispatch_decision_sha256=operator_supervised_dispatch_decision_sha256,
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
        execution_preparation_dir=execution_dir_str,
        prepared_dispatch_payload_json_files=prepared_dispatch_payload_json_files,
        prepared_dispatch_payload_json_hashes=prepared_payload_json_hashes,
        prepared_dispatch_payload_markdown_files=prepared_dispatch_payload_markdown_files,
        prepared_dispatch_payload_markdown_hashes=prepared_payload_markdown_hashes,
        execution_preparation_json_files=execution_prep_jsons,
        execution_preparation_markdown_files=execution_prep_mds,
        execution_preparation_file_hashes={}, # Populated during write
        destinations=destinations,
        combined_payload_hash=combined_payload_hash,
        local_dispatch_execution_prepared=prepared,
        dispatch_execution_payload_created=prepared,
        blockers=blockers,
        warnings=warnings,
    )


def write_local_dispatch_execution_payloads(
    manifest: LocalDispatchExecutionPayloadManifest,
    decision_packet: dict,
    prepared_jsons: list[Path],
    prepared_json_packets: dict[str, Any],
    prepared_mds: list[Path],
    prepared_md_texts: dict[str, str],
    output_dir: Path,
) -> Path:
    if not manifest.local_dispatch_execution_prepared or manifest.blockers:
        # Blocked: write blocked manifest only to output_dir root
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_path = out_path / f"{manifest.local_dispatch_execution_payload_manifest_id}.json"
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(asdict(manifest), f, indent=2, sort_keys=True)
            f.write("\n")
        return manifest_path

    # Clean write target directory
    exec_dir = Path(manifest.execution_preparation_dir)
    exec_dir.mkdir(parents=True, exist_ok=True)

    # Write markdown files
    substack_md_path = Path(manifest.execution_preparation_markdown_files[0])
    discord_md_path = Path(manifest.execution_preparation_markdown_files[1])

    # Find the corresponding text
    norm_md_texts = {_normalize_path(k): v for k, v in prepared_md_texts.items()}
    substack_text = ""
    discord_text = ""
    for path in prepared_mds:
        npath = _normalize_path(path)
        found_text = norm_md_texts[npath]
        if "substack" in npath:
            substack_text = found_text
        else:
            discord_text = found_text

    with open(substack_md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(substack_text)
    with open(discord_md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(discord_text)

    # Find source json hashes and files
    substack_json_file = ""
    substack_json_sha256 = ""
    discord_json_file = ""
    discord_json_sha256 = ""

    for path in prepared_jsons:
        npath = _normalize_path(path)
        fhash = manifest.prepared_dispatch_payload_json_hashes[npath]
        if "substack" in npath:
            substack_json_file = npath
            substack_json_sha256 = fhash
        else:
            discord_json_file = npath
            discord_json_sha256 = fhash

    # Find destinations
    substack_dest = {}
    discord_dest = {}
    for dest in manifest.destinations:
        if dest.get("platform") == "substack":
            substack_dest = dest
        elif dest.get("platform") == "discord":
            discord_dest = dest

    # Build and write prepared JSON files
    substack_json_data = ExecutionPreparationPayload(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        execution_preparation_payload_id=f"execution_preparation_payload_substack_{manifest.combined_payload_hash[:16]}",
        platform="substack",
        preparation_status="local_dispatch_execution_payload_pending_live_gate",
        destination=substack_dest,
        markdown_snapshot_file=manifest.execution_preparation_markdown_files[0],
        markdown_snapshot_sha256=manifest.prepared_dispatch_payload_markdown_hashes[manifest.prepared_dispatch_payload_markdown_files[0]],
        source_prepared_dispatch_payload_json_file=substack_json_file,
        source_prepared_dispatch_payload_json_sha256=substack_json_sha256,
        source_prepared_dispatch_payload_markdown_file=_normalize_path(prepared_mds[0]) if "substack" in _normalize_path(prepared_mds[0]) else _normalize_path(prepared_mds[1]),
        source_prepared_dispatch_payload_markdown_sha256=manifest.prepared_dispatch_payload_markdown_hashes[manifest.prepared_dispatch_payload_markdown_files[0]],
        combined_payload_hash=manifest.combined_payload_hash,
        operator_supervised_dispatch_review_decision_packet_id=manifest.operator_supervised_dispatch_review_decision_packet_id,
        local_destination_binding_preflight_id=manifest.local_destination_binding_preflight_id,
        local_dispatch_payload_manifest_id=manifest.local_dispatch_payload_manifest_id,
        canonical_slug=manifest.canonical_slug,
        canonical_title=manifest.canonical_title,
        local_dispatch_execution_prepared=True,
    )
    substack_json_path = Path(manifest.execution_preparation_json_files[0])
    with open(substack_json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(substack_json_data), f, indent=2, sort_keys=True)
        f.write("\n")

    discord_json_data = ExecutionPreparationPayload(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        execution_preparation_payload_id=f"execution_preparation_payload_discord_{manifest.combined_payload_hash[:16]}",
        platform="discord",
        preparation_status="local_dispatch_execution_payload_pending_live_gate",
        destination=discord_dest,
        markdown_snapshot_file=manifest.execution_preparation_markdown_files[1],
        markdown_snapshot_sha256=manifest.prepared_dispatch_payload_markdown_hashes[manifest.prepared_dispatch_payload_markdown_files[1]],
        source_prepared_dispatch_payload_json_file=discord_json_file,
        source_prepared_dispatch_payload_json_sha256=discord_json_sha256,
        source_prepared_dispatch_payload_markdown_file=_normalize_path(prepared_mds[1]) if "discord" in _normalize_path(prepared_mds[1]) else _normalize_path(prepared_mds[0]),
        source_prepared_dispatch_payload_markdown_sha256=manifest.prepared_dispatch_payload_markdown_hashes[manifest.prepared_dispatch_payload_markdown_files[1]],
        combined_payload_hash=manifest.combined_payload_hash,
        operator_supervised_dispatch_review_decision_packet_id=manifest.operator_supervised_dispatch_review_decision_packet_id,
        local_destination_binding_preflight_id=manifest.local_destination_binding_preflight_id,
        local_dispatch_payload_manifest_id=manifest.local_dispatch_payload_manifest_id,
        canonical_slug=manifest.canonical_slug,
        canonical_title=manifest.canonical_title,
        local_dispatch_execution_prepared=True,
    )
    discord_json_path = Path(manifest.execution_preparation_json_files[1])
    with open(discord_json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(discord_json_data), f, indent=2, sort_keys=True)
        f.write("\n")

    # Compute execution preparation file hashes after writing
    exec_hashes = {
        manifest.execution_preparation_markdown_files[0]: hashlib.sha256(substack_md_path.read_bytes()).hexdigest(),
        manifest.execution_preparation_markdown_files[1]: hashlib.sha256(discord_md_path.read_bytes()).hexdigest(),
        manifest.execution_preparation_json_files[0]: hashlib.sha256(substack_json_path.read_bytes()).hexdigest(),
        manifest.execution_preparation_json_files[1]: hashlib.sha256(discord_json_path.read_bytes()).hexdigest(),
    }

    # Update manifest execution_preparation_file_hashes
    manifest_data = asdict(manifest)
    manifest_data["execution_preparation_file_hashes"] = exec_hashes

    # Write manifest JSON inside the directory
    manifest_path = exec_dir / "local_dispatch_execution_payload_manifest.json"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)
        f.write("\n")

    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local dispatch execution payload preparation contract")
    parser.add_argument("decision_packet")
    parser.add_argument("preflight_packet")
    parser.add_argument("--json-files", nargs="+", required=True)
    parser.add_argument("--markdown-files", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        decision = load_json_packet(Path(args.decision_packet), "malformed_operator_supervised_dispatch_review_decision_json")
        preflight = load_json_packet(Path(args.preflight_packet), "malformed_local_destination_binding_preflight_json")
        
        json_paths = [Path(p) for p in args.json_files]
        json_packets: dict[str, Any] = {}
        for path in json_paths:
            pkt = load_json_packet(path, f"prepared_json_packet_malformed_{path.name}")
            json_packets[str(path)] = pkt

        md_paths = [Path(p) for p in args.markdown_files]
        md_texts: dict[str, str] = {}
        for path in md_paths:
            text = load_text_file(path, f"preview_file_text_missing_{path.name}")
            md_texts[str(path)] = text
    except ValueError as exc:
        blocker = str(exc)
        manifest = LocalDispatchExecutionPayloadManifest(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            local_dispatch_execution_payload_manifest_id="local_dispatch_execution_payload_manifest_blocked",
            operator_supervised_dispatch_review_decision_packet_id="",
            operator_supervised_dispatch_decision_sha256="",
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
            execution_preparation_dir="",
            prepared_dispatch_payload_json_files=[],
            prepared_dispatch_payload_json_hashes={},
            prepared_dispatch_payload_markdown_files=[],
            prepared_dispatch_payload_markdown_hashes={},
            execution_preparation_json_files=[],
            execution_preparation_markdown_files=[],
            execution_preparation_file_hashes={},
            destinations=[],
            combined_payload_hash="",
            local_dispatch_execution_prepared=False,
            dispatch_execution_payload_created=False,
            blockers=[blocker],
            warnings=["local_dispatch_execution_payload_preparation_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_path = out_path / f"{manifest.local_dispatch_execution_payload_manifest_id}.json"
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(asdict(manifest), f, indent=2, sort_keys=True)
            f.write("\n")
        return 1

    manifest = make_local_dispatch_execution_payload_manifest(decision, preflight, json_paths, json_packets, md_paths, md_texts, Path(args.output_dir))
    write_local_dispatch_execution_payloads(manifest, decision, json_paths, json_packets, md_paths, md_texts, Path(args.output_dir))

    return 1 if manifest.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
