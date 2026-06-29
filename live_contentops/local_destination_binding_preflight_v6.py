"""V6 Local Destination Binding Preflight from Dispatch Payloads."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MANIFEST_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PAYLOAD_PREPARATION_FROM_OPERATOR_DECISION_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DESTINATION_BINDING_PREFLIGHT_FROM_DISPATCH_PAYLOADS_V0"
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
class LocalDestinationBindingPreflightPacket:
    schema_version: str
    task_label: str
    local_destination_binding_preflight_id: str
    destination_binding_id: str
    operator_id: str
    created_at_manual: str
    local_dispatch_payload_manifest_id: str
    local_dispatch_payload_manifest_sha256: str
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
    prepared_dispatch_payload_json_files: list[str]
    prepared_dispatch_payload_json_hashes: dict[str, str]
    prepared_dispatch_payload_markdown_files: list[str]
    prepared_dispatch_payload_markdown_hashes: dict[str, str]
    destinations: list[dict[str, Any]]
    combined_payload_hash: str
    destination_binding_preflight_available: bool
    eligible_for_supervised_dispatch_gate: bool
    destination_binding_created: bool
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
    lowered = lowered.replace("verified no secrets bound", "")
    lowered = lowered.replace("no secrets bound", "")
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
    if packet.get("local_dispatch_payload_prepared") is not True:
        blockers.append("manifest_local_dispatch_payload_not_prepared")
    if packet.get("dispatch_payload_created") is not True:
        blockers.append("manifest_dispatch_payload_not_created")
    if packet.get("dispatch_execution_payload_created") is not False:
        blockers.append("manifest_dispatch_execution_payload_created_not_false")
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

    # Required fields check
    required_keys = [
        "local_dispatch_payload_manifest_id",
        "operator_dispatch_review_decision_packet_id",
        "operator_dispatch_decision_sha256",
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
        "dispatch_payload_dir",
    ]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"manifest_{key}_missing")

    # Count checks
    jsons = packet.get("prepared_dispatch_payload_json_files", [])
    if not isinstance(jsons, list) or len(jsons) != 2:
        blockers.append("manifest_prepared_dispatch_payload_json_files_count_invalid")

    mds = packet.get("prepared_dispatch_payload_markdown_files", [])
    if not isinstance(mds, list) or len(mds) != 2:
        blockers.append("manifest_prepared_dispatch_payload_markdown_files_count_invalid")

    hashes = packet.get("prepared_dispatch_payload_hashes", {})
    if not isinstance(hashes, dict) or len(hashes) != 2:
        blockers.append("manifest_prepared_dispatch_payload_hashes_count_invalid")

    src_entry_hashes = packet.get("source_active_outbox_entry_hashes", {})
    if not isinstance(src_entry_hashes, dict) or len(src_entry_hashes) != 2:
        blockers.append("manifest_source_active_outbox_entry_hashes_count_invalid")

    src_payload_hashes = packet.get("source_active_outbox_payload_hashes", {})
    if not isinstance(src_payload_hashes, dict) or len(src_payload_hashes) != 2:
        blockers.append("manifest_source_active_outbox_payload_hashes_count_invalid")

    return blockers


def _validate_prepared_json_packet(entry: dict[str, Any], manifest: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if entry.get("task_label") != MANIFEST_TASK_LABEL:
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
    if entry.get("combined_payload_hash") != manifest.get("combined_payload_hash"):
        blockers.append(f"{prefix}_combined_payload_hash_mismatch")
    if entry.get("operator_dispatch_review_decision_packet_id") != manifest.get("operator_dispatch_review_decision_packet_id"):
        blockers.append(f"{prefix}_operator_dispatch_review_decision_packet_id_mismatch")
    if entry.get("local_dispatch_preflight_id") != manifest.get("local_dispatch_preflight_id"):
        blockers.append(f"{prefix}_local_dispatch_preflight_id_mismatch")
    if entry.get("local_active_outbox_manifest_id") != manifest.get("local_active_outbox_manifest_id"):
        blockers.append(f"{prefix}_local_active_outbox_manifest_id_mismatch")
    if entry.get("canonical_slug") != manifest.get("canonical_slug"):
        blockers.append(f"{prefix}_canonical_slug_mismatch")
    if entry.get("canonical_title") != manifest.get("canonical_title"):
        blockers.append(f"{prefix}_canonical_title_mismatch")

    # Match payload markdown file
    entry_md = entry.get("payload_markdown_file")
    if not entry_md:
        blockers.append(f"{prefix}_payload_markdown_file_missing")
    else:
        npath = _normalize_path(entry_md)
        manifest_mds_normalized = [_normalize_path(p) for p in manifest.get("prepared_dispatch_payload_markdown_files", [])]
        if npath not in manifest_mds_normalized:
            blockers.append(f"{prefix}_payload_markdown_file_not_in_manifest")
        else:
            # Find matching hash
            expected_hash = None
            for k, v in manifest.get("prepared_dispatch_payload_hashes", {}).items():
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


def _validate_destination_binding(binding: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    
    # Required keys
    req_keys = [
        "schema_version",
        "destination_binding_id",
        "operator_id",
        "created_at_manual",
        "local_dispatch_payload_manifest_id",
        "combined_payload_hash",
        "destinations",
        "approval_phrase",
        "approval_scope",
    ]
    for key in req_keys:
        if not binding.get(key):
            blockers.append(f"binding_{key}_missing")
    
    if "notes" not in binding or not isinstance(binding.get("notes"), str):
        blockers.append("binding_notes_missing_or_invalid")

    if binding.get("local_dispatch_payload_manifest_id") != manifest.get("local_dispatch_payload_manifest_id"):
        blockers.append("binding_local_dispatch_payload_manifest_id_mismatch")
    if binding.get("combined_payload_hash") != manifest.get("combined_payload_hash"):
        blockers.append("binding_combined_payload_hash_mismatch")

    if binding.get("approval_phrase") != "BIND_NON_SECRET_DESTINATION_LABELS_ONLY_NOT_LIVE_DISPATCH":
        blockers.append("binding_approval_phrase_invalid")
    if binding.get("approval_scope") != "destination_label_preflight_only":
        blockers.append("binding_approval_scope_invalid")

    destinations = binding.get("destinations", [])
    if not isinstance(destinations, list) or len(destinations) != 2:
        blockers.append("binding_destinations_count_invalid")
        return blockers

    platforms_seen = []
    for i, dest in enumerate(destinations):
        prefix = f"binding_destination_{i}"
        if not isinstance(dest, dict):
            blockers.append(f"{prefix}_not_dict")
            continue

        req_dest_fields = [
            "platform",
            "destination_label",
            "destination_type",
            "destination_binding_kind",
            "manual_operator_confirmed",
        ]
        for key in req_dest_fields:
            if not dest.get(key) and dest.get(key) is not True and dest.get(key) is not False:
                blockers.append(f"{prefix}_{key}_missing")

        platform = dest.get("platform")
        if platform not in ["substack", "discord"]:
            blockers.append(f"{prefix}_platform_invalid")
        else:
            platforms_seen.append(platform)

        label = dest.get("destination_label")
        if not label or not isinstance(label, str):
            blockers.append(f"{prefix}_destination_label_invalid")

        dest_type = dest.get("destination_type")
        if dest_type not in ["manual_review_target", "draft_console_target", "webhook_family_target"]:
            blockers.append(f"{prefix}_destination_type_invalid")

        binding_kind = dest.get("destination_binding_kind")
        if binding_kind != "non_secret_label_only":
            blockers.append(f"{prefix}_destination_binding_kind_invalid")

        if dest.get("manual_operator_confirmed") is not True:
            blockers.append(f"{prefix}_manual_operator_confirmed_not_true")

        # Scan destination object for raw credentials, identifiers, tokens, etc.
        serialized_dest = json.dumps(dest)
        if _has_secret_marker(serialized_dest):
            blockers.append(f"{prefix}_secret_marker_detected")

        clean_dest = serialized_dest.lower()
        clean_dest = clean_dest.replace("webhook_family_target", "")
        for key in ["channel_id", "account_id", "app_id", "workspace_id", "bot_token", "url", "webhook"]:
            if key in clean_dest:
                blockers.append(f"{prefix}_raw_platform_identifier_detected")

        lowered_dest = serialized_dest.lower()
        if "login" in lowered_dest or "credential" in lowered_dest or "permission" in lowered_dest or "scope" in lowered_dest or "readiness" in lowered_dest or "dispatch" in lowered_dest or "public" in lowered_dest:
            blockers.append(f"{prefix}_live_claim_detected")

    if len(platforms_seen) != 2 or len(set(platforms_seen)) != 2:
        blockers.append("binding_destinations_platforms_mismatch")

    # Scan overall binding json string
    serialized_binding = json.dumps(binding)
    if _has_secret_marker(serialized_binding):
        blockers.append("binding_secret_marker_detected")

    # Safe warning check
    lowered_binding = serialized_binding.lower()
    for marker in PUBLIC_READY_MARKERS:
        if marker in lowered_binding:
            blockers.append(f"binding_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in lowered_binding:
            blockers.append(f"binding_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in lowered_binding:
            blockers.append(f"binding_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(lowered_binding):
            blockers.append("binding_financial_advice_or_signal_framing_detected")
            break

    # Webhook or dispatch tokens check
    live_send_markers = ["webhook_url", "channel_id", "bot_token", "dispatch_allowed: true", "publish: true"]
    for marker in live_send_markers:
        if marker in lowered_binding:
            blockers.append("binding_live_send_instructions_detected")

    return blockers


def make_local_destination_binding_preflight_packet(
    manifest_packet: Any,
    prepared_jsons: list[Path],
    prepared_json_packets: dict[str, Any],
    prepared_mds: list[Path],
    prepared_md_texts: dict[str, str],
    destination_binding_json: Any,
) -> LocalDestinationBindingPreflightPacket:
    blockers: list[str] = []

    manifest_is_dict = isinstance(manifest_packet, dict)
    if not manifest_is_dict:
        blockers.append("malformed_local_dispatch_payload_manifest_json")

    binding_is_dict = isinstance(destination_binding_json, dict)
    if not binding_is_dict:
        blockers.append("malformed_operator_destination_binding_json")

    # Scan manifest for secrets
    if manifest_is_dict and _has_secret_marker(json.dumps(manifest_packet)):
        blockers.append("manifest_secret_marker_detected")

    local_dispatch_payload_manifest_id = ""
    local_dispatch_payload_manifest_sha256 = ""
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
    manifest_payload_file_hashes: dict[str, str] = {}
    destination_binding_id = ""
    operator_id = ""
    created_at_manual = ""
    destinations_out: list[dict[str, Any]] = []

    if manifest_is_dict and "manifest_secret_marker_detected" not in blockers:
        blockers.extend(_validate_manifest_packet(manifest_packet))
        
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

        for k, v in manifest_packet.get("prepared_dispatch_payload_hashes", {}).items():
            manifest_payload_file_hashes[_normalize_path(k)] = str(v)

        # Enforce exact JSON path matching
        supplied_json_normalized = [_normalize_path(p) for p in prepared_jsons]
        manifest_jsons_normalized = [_normalize_path(p) for p in manifest_packet.get("prepared_dispatch_payload_json_files", [])]

        if len(prepared_jsons) != 2:
            blockers.append("prepared_json_file_paths_count_invalid")
        if len(set(supplied_json_normalized)) != len(supplied_json_normalized):
            blockers.append("prepared_json_file_paths_duplicate_detected")
        if supplied_json_normalized != manifest_jsons_normalized:
            blockers.append("prepared_json_file_paths_order_mismatch")

        # Enforce exact markdown path matching
        supplied_md_normalized = [_normalize_path(p) for p in prepared_mds]
        manifest_mds_normalized = [_normalize_path(p) for p in manifest_packet.get("prepared_dispatch_payload_markdown_files", [])]

        if len(prepared_mds) != 2:
            blockers.append("prepared_markdown_file_paths_count_invalid")
        if len(set(supplied_md_normalized)) != len(supplied_md_normalized):
            blockers.append("prepared_markdown_file_paths_duplicate_detected")
        if supplied_md_normalized != manifest_mds_normalized:
            blockers.append("prepared_markdown_file_paths_order_mismatch")

    # Validate prepared JSON packets
    prepared_dispatch_payload_json_hashes: dict[str, str] = {}
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

        # Scan JSON for secrets
        if _has_secret_marker(json.dumps(json_data)):
            blockers.append("prepared_json_secret_marker_detected")
            continue

        platform = json_data.get("platform") or ""
        blockers.extend(_validate_prepared_json_packet(json_data, manifest_packet, f"prepared_json_{platform}"))
        
        # Compute JSON hash if no secrets
        if "prepared_json_secret_marker_detected" not in blockers:
            prepared_dispatch_payload_json_hashes[npath] = hashlib.sha256(_canonical_json(json_data).encode("utf-8")).hexdigest()

    # Validate markdown texts
    prepared_dispatch_payload_markdown_hashes: dict[str, str] = {}
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
            fhash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            prepared_dispatch_payload_markdown_hashes[npath] = fhash
            
            # Compare to manifest hash
            expected = manifest_payload_file_hashes.get(npath)
            if expected and fhash != expected:
                blockers.append(f"markdown_hash_mismatch_{path.name}")

    # Validate operator destination binding
    if binding_is_dict and "binding_secret_marker_detected" not in blockers:
        blockers.extend(_validate_destination_binding(destination_binding_json, manifest_packet))
        
        destination_binding_id = str(destination_binding_json.get("destination_binding_id") or "")
        operator_id = str(destination_binding_json.get("operator_id") or "")
        created_at_manual = str(destination_binding_json.get("created_at_manual") or "")
        destinations_out = destination_binding_json.get("destinations", [])

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "manifest_secret_marker_detected" in blockers or
        "prepared_json_secret_marker_detected" in blockers or
        "binding_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
        local_dispatch_payload_manifest_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        local_dispatch_payload_manifest_sha256 = ""
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
        destinations_out = []
        destination_binding_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"

    elif manifest_is_dict and not has_secrets:
        local_dispatch_payload_manifest_sha256 = hashlib.sha256(_canonical_json(manifest_packet).encode("utf-8")).hexdigest()
        prepared_dispatch_payload_json_files = [_normalize_path(p) for p in prepared_jsons]
        prepared_dispatch_payload_markdown_files = [_normalize_path(p) for p in prepared_mds]

    # Deterministic local destination binding preflight packet ID
    intake_material = {
        "local_dispatch_payload_manifest_id": local_dispatch_payload_manifest_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
        "destination_binding_id": destination_binding_id,
    }
    local_destination_binding_preflight_id = f"local_destination_binding_preflight_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("local_destination_binding_preflight_blocked_pending_operator_repair")

    return LocalDestinationBindingPreflightPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        local_destination_binding_preflight_id=local_destination_binding_preflight_id,
        destination_binding_id=destination_binding_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        local_dispatch_payload_manifest_id=local_dispatch_payload_manifest_id,
        local_dispatch_payload_manifest_sha256=local_dispatch_payload_manifest_sha256,
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
        prepared_dispatch_payload_json_files=prepared_dispatch_payload_json_files,
        prepared_dispatch_payload_json_hashes=prepared_dispatch_payload_json_hashes,
        prepared_dispatch_payload_markdown_files=prepared_dispatch_payload_markdown_files,
        prepared_dispatch_payload_markdown_hashes=prepared_dispatch_payload_markdown_hashes,
        destinations=destinations_out,
        combined_payload_hash=combined_payload_hash,
        destination_binding_preflight_available=available,
        eligible_for_supervised_dispatch_gate=available,
        destination_binding_created=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_local_destination_binding_preflight_packet(
    packet: LocalDestinationBindingPreflightPacket,
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    packet_path = out_path / f"{packet.local_destination_binding_preflight_id}.json"
    with open(packet_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(packet), f, indent=2, sort_keys=True)
        f.write("\n")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local destination binding preflight contract")
    parser.add_argument("manifest_packet")
    parser.add_argument("--json-files", nargs="+", required=True)
    parser.add_argument("--markdown-files", nargs="+", required=True)
    parser.add_argument("--destination-binding", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        manifest = load_json_packet(Path(args.manifest_packet), "malformed_local_dispatch_payload_manifest_json")
        binding = load_json_packet(Path(args.destination_binding), "malformed_operator_destination_binding_json")
        
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
        packet = LocalDestinationBindingPreflightPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            local_destination_binding_preflight_id="local_destination_binding_preflight_blocked",
            destination_binding_id="",
            operator_id="",
            created_at_manual="",
            local_dispatch_payload_manifest_id="",
            local_dispatch_payload_manifest_sha256="",
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
            prepared_dispatch_payload_json_files=[],
            prepared_dispatch_payload_json_hashes={},
            prepared_dispatch_payload_markdown_files=[],
            prepared_dispatch_payload_markdown_hashes={},
            destinations=[],
            combined_payload_hash="",
            destination_binding_preflight_available=False,
            eligible_for_supervised_dispatch_gate=False,
            destination_binding_created=False,
            blockers=[blocker],
            warnings=["local_destination_binding_preflight_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        packet_path = out_path / f"{packet.local_destination_binding_preflight_id}.json"
        with open(packet_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(asdict(packet), f, indent=2, sort_keys=True)
            f.write("\n")
        return 1

    packet = make_local_destination_binding_preflight_packet(manifest, json_paths, json_packets, md_paths, md_texts, binding)
    write_local_destination_binding_preflight_packet(packet, Path(args.output_dir))

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
