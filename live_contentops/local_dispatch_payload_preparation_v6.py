"""V6 Local Dispatch Payload Preparation from Operator Decision."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DECISION_TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_DISPATCH_REVIEW_DECISION_FROM_PREFLIGHT_V0"
ENTRY_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_ACTIVE_OUTBOX_CREATION_FROM_OPERATOR_REVIEW_DECISION_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PAYLOAD_PREPARATION_FROM_OPERATOR_DECISION_V0"
SCHEMA_VERSION = "6.0.0"

SECRET_MARKERS = ("token", "api_key", "password", "bearer", "cookie", "webhook_url", "private_key", "secret", "credential")
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
class LocalDispatchPayloadManifest:
    schema_version: str
    task_label: str
    local_dispatch_payload_manifest_id: str
    operator_dispatch_review_decision_packet_id: str
    operator_dispatch_decision_sha256: str
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
    dispatch_payload_dir: str
    prepared_dispatch_payload_json_files: list[str]
    prepared_dispatch_payload_markdown_files: list[str]
    prepared_dispatch_payload_hashes: dict[str, str]
    source_active_outbox_entry_hashes: dict[str, str]
    source_active_outbox_payload_hashes: dict[str, str]
    combined_payload_hash: str
    local_dispatch_payload_prepared: bool
    dispatch_payload_created: bool = True
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
class PreparedDispatchPayload:
    schema_version: str
    task_label: str
    prepared_dispatch_payload_id: str
    platform: str
    payload_markdown_file: str
    payload_markdown_sha256: str
    source_active_outbox_entry_file: str
    source_active_outbox_entry_sha256: str
    source_active_outbox_payload_file: str
    source_active_outbox_payload_sha256: str
    combined_payload_hash: str
    operator_dispatch_review_decision_packet_id: str
    local_dispatch_preflight_id: str
    local_active_outbox_manifest_id: str
    canonical_slug: str
    canonical_title: str
    preparation_status: str = "local_dispatch_payload_pending_supervised_dispatch_gate"
    dispatch_payload_created: bool = True
    dispatch_execution_payload_created: bool = False
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
    if packet.get("dispatch_review_decision_available") is not True:
        blockers.append("decision_not_available")
    if packet.get("dispatch_payload_preparation_approved") is not True:
        blockers.append("decision_not_approved")
    if packet.get("approval_for_dispatch") is not True:
        blockers.append("decision_approval_for_dispatch_not_true")
    if packet.get("dispatch_payload_created") is not False:
        blockers.append("decision_dispatch_payload_created_not_false")
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

    if packet.get("decision") != "approve_dispatch_payload_preparation":
        blockers.append("decision_value_invalid")
    if packet.get("approval_phrase") != "APPROVE_LOCAL_DISPATCH_PAYLOAD_PREPARATION_ONLY_NOT_SEND":
        blockers.append("decision_approval_phrase_invalid")
    if packet.get("approval_scope") != "dispatch_payload_preparation_only":
        blockers.append("decision_approval_scope_invalid")

    # Required fields check
    required_keys = [
        "operator_dispatch_review_decision_packet_id",
        "operator_dispatch_decision_id",
        "local_dispatch_preflight_id",
        "local_dispatch_preflight_sha256",
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

    # Counts
    entries = packet.get("reviewed_active_outbox_entries", [])
    if not isinstance(entries, list) or len(entries) != 2:
        blockers.append("decision_reviewed_active_outbox_entries_count_invalid")

    entry_hashes = packet.get("reviewed_active_outbox_entry_hashes", {})
    if not isinstance(entry_hashes, dict) or len(entry_hashes) != 2:
        blockers.append("decision_reviewed_active_outbox_entry_hashes_count_invalid")

    payloads = packet.get("reviewed_active_outbox_payload_files", [])
    if not isinstance(payloads, list) or len(payloads) != 2:
        blockers.append("decision_reviewed_active_outbox_payload_files_count_invalid")

    payload_hashes = packet.get("reviewed_active_outbox_payload_file_hashes", {})
    if not isinstance(payload_hashes, dict) or len(payload_hashes) != 2:
        blockers.append("decision_reviewed_active_outbox_payload_file_hashes_count_invalid")

    return blockers


def _validate_entry_packet(entry: dict[str, Any], decision_packet: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if entry.get("task_label") != ENTRY_TASK_LABEL:
        blockers.append(f"{prefix}_task_label_invalid")
    
    platform = entry.get("platform")
    if platform not in ["substack", "discord"]:
        blockers.append(f"{prefix}_platform_invalid")

    if entry.get("entry_status") != "local_active_outbox_pending_dispatch_review":
        blockers.append(f"{prefix}_entry_status_invalid")

    if entry.get("dispatch_payload_created") is not False:
        blockers.append(f"{prefix}_dispatch_payload_created_not_false")
    if entry.get("dispatch_allowed") is not False:
        blockers.append(f"{prefix}_dispatch_allowed_not_false")
    if entry.get("approval_for_dispatch") is not False:
        blockers.append(f"{prefix}_approval_for_dispatch_not_false")
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
    if entry.get("combined_payload_hash") != decision_packet.get("combined_payload_hash"):
        blockers.append(f"{prefix}_combined_payload_hash_mismatch")
    if entry.get("operator_active_outbox_review_decision_id") != decision_packet.get("operator_active_outbox_review_decision_id"):
        blockers.append(f"{prefix}_operator_active_outbox_review_decision_id_mismatch")
    if entry.get("active_outbox_eligibility_id") != decision_packet.get("active_outbox_eligibility_id"):
        blockers.append(f"{prefix}_active_outbox_eligibility_id_mismatch")
    if entry.get("outbox_package_staging_id") != decision_packet.get("outbox_package_staging_id"):
        blockers.append(f"{prefix}_outbox_package_staging_id_mismatch")
    if entry.get("canonical_slug") != decision_packet.get("canonical_slug"):
        blockers.append(f"{prefix}_canonical_slug_mismatch")
    if entry.get("canonical_title") != decision_packet.get("canonical_title"):
        blockers.append(f"{prefix}_canonical_title_mismatch")

    # Match payload file
    entry_payload = entry.get("payload_file")
    if not entry_payload:
        blockers.append(f"{prefix}_payload_file_missing")
    else:
        npath = _normalize_path(entry_payload)
        decision_payloads_normalized = [_normalize_path(p) for p in decision_packet.get("reviewed_active_outbox_payload_files", [])]
        if npath not in decision_payloads_normalized:
            blockers.append(f"{prefix}_payload_file_not_in_decision")
        else:
            # Find matching hash
            expected_hash = None
            for k, v in decision_packet.get("reviewed_active_outbox_payload_file_hashes", {}).items():
                if _normalize_path(k) == npath:
                    expected_hash = v
                    break
            
            if entry.get("payload_sha256") != expected_hash:
                blockers.append(f"{prefix}_payload_sha256_mismatch")

    return blockers


def _validate_preview_text(text: str, platform: str) -> list[str]:
    blockers: list[str] = []
    if not text.strip():
        blockers.append(f"staged_{platform}_empty")
        return blockers

    # Scan for secrets
    if _has_secret_marker(text):
        blockers.append(f"staged_{platform}_secret_marker_detected")

    # Safe warning check
    if platform == "substack":
        if "LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION" not in text:
            blockers.append("staged_substack_warning_missing")
    elif platform == "discord":
        if "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH" not in text:
            blockers.append("staged_discord_warning_missing")

    lowered = text.lower()
    lowered = lowered.replace("local preview only - not approved for publication", "")
    lowered = lowered.replace("local preview only - not approved for discord dispatch", "")

    # Prohibited claims
    for marker in PUBLIC_READY_MARKERS:
        if marker in lowered:
            blockers.append(f"staged_{platform}_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"staged_{platform}_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"staged_{platform}_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(lowered):
            blockers.append(f"staged_{platform}_financial_advice_or_signal_framing_detected")
            break

    # Webhook or dispatch tokens check
    live_send_markers = ["webhook_url", "channel_id", "bot_token", "dispatch_allowed: true", "publish: true"]
    for marker in live_send_markers:
        if marker in lowered:
            blockers.append(f"staged_{platform}_live_send_instructions_detected")

    return blockers


def make_local_dispatch_payload_manifest(
    decision_packet: Any,
    entry_file_paths: list[Path],
    entry_packets: dict[str, Any],
    payload_file_paths: list[Path],
    payload_texts: dict[str, str],
    output_dir: Path,
) -> LocalDispatchPayloadManifest:
    blockers: list[str] = []

    decision_is_dict = isinstance(decision_packet, dict)
    if not decision_is_dict:
        blockers.append("malformed_operator_dispatch_review_decision_json")

    # Scan decision for secrets
    if decision_is_dict and _has_secret_marker(json.dumps(decision_packet)):
        blockers.append("decision_secret_marker_detected")

    operator_dispatch_review_decision_packet_id = ""
    operator_dispatch_decision_sha256 = ""
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
    decision_payload_file_hashes: dict[str, str] = {}
    source_active_outbox_entry_hashes: dict[str, str] = {}
    source_active_outbox_payload_hashes: dict[str, str] = {}

    if decision_is_dict and "decision_secret_marker_detected" not in blockers:
        blockers.extend(_validate_decision_packet(decision_packet))
        
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

        # Payload files expected hashes
        for k, v in decision_packet.get("reviewed_active_outbox_payload_file_hashes", {}).items():
            decision_payload_file_hashes[_normalize_path(k)] = str(v)

        # Enforce exact entry path matching
        supplied_entry_normalized = [_normalize_path(p) for p in entry_file_paths]
        reviewed_entries_normalized = [_normalize_path(p) for p in decision_packet.get("reviewed_active_outbox_entries", [])]

        if len(entry_file_paths) != 2:
            blockers.append("entry_file_paths_count_invalid")
        if len(set(supplied_entry_normalized)) != len(supplied_entry_normalized):
            blockers.append("entry_file_paths_duplicate_detected")
        if supplied_entry_normalized != reviewed_entries_normalized:
            blockers.append("entry_file_paths_order_mismatch")

        # Enforce exact payload path matching
        supplied_payload_normalized = [_normalize_path(p) for p in payload_file_paths]
        reviewed_payloads_normalized = [_normalize_path(p) for p in decision_packet.get("reviewed_active_outbox_payload_files", [])]

        if len(payload_file_paths) != 2:
            blockers.append("payload_file_paths_count_invalid")
        if len(set(supplied_payload_normalized)) != len(supplied_payload_normalized):
            blockers.append("payload_file_paths_duplicate_detected")
        if supplied_payload_normalized != reviewed_payloads_normalized:
            blockers.append("payload_file_paths_order_mismatch")

    # Validate entry JSON packets
    for path in entry_file_paths:
        npath = _normalize_path(path)
        entry_data = None
        for k, v in entry_packets.items():
            if _normalize_path(k) == npath:
                entry_data = v
                break

        if entry_data is None:
            blockers.append(f"entry_packet_missing_{path.name}")
            continue

        if not isinstance(entry_data, dict):
            blockers.append(f"entry_packet_malformed_{path.name}")
            continue

        # Scan entry JSON for secrets
        if _has_secret_marker(json.dumps(entry_data)):
            blockers.append("entry_secret_marker_detected")
            continue

        platform = entry_data.get("platform") or ""
        blockers.extend(_validate_entry_packet(entry_data, decision_packet, f"entry_{platform}"))
        
        # Compute entry hash if no secrets
        if "entry_secret_marker_detected" not in blockers:
            source_active_outbox_entry_hashes[npath] = hashlib.sha256(_canonical_json(entry_data).encode("utf-8")).hexdigest()

    # Validate payload markdown texts
    for path in payload_file_paths:
        npath = _normalize_path(path)
        text = None
        for k, v in payload_texts.items():
            if _normalize_path(k) == npath:
                text = v
                break

        if text is None:
            blockers.append(f"payload_text_missing_{path.name}")
            continue

        platform = "substack" if "substack" in path.name.lower() else "discord"
        blockers.extend(_validate_preview_text(text, platform))
        
        has_file_secrets = _has_secret_marker(text)
        if not has_file_secrets:
            fhash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            source_active_outbox_payload_hashes[npath] = fhash
            
            # Compare to decision hash
            expected = decision_payload_file_hashes.get(npath)
            if expected and fhash != expected:
                blockers.append(f"payload_hash_mismatch_{path.name}")

    blockers = sorted(set(blockers))
    prepared = not blockers

    has_secrets = (
        "decision_secret_marker_detected" in blockers or
        "entry_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
        operator_dispatch_review_decision_packet_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_dispatch_decision_sha256 = ""
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
        source_active_outbox_entry_hashes = {}
        source_active_outbox_payload_hashes = {}

    elif decision_is_dict and not has_secrets:
        operator_dispatch_decision_sha256 = hashlib.sha256(_canonical_json(decision_packet).encode("utf-8")).hexdigest()

    # Deterministic directory & files naming
    payload_dir_str = ""
    prepared_jsons: list[str] = []
    prepared_mds: list[str] = []
    prepared_hashes: dict[str, str] = {}

    if prepared and not has_secrets:
        dir_name = f"{canonical_slug}_{combined_payload_hash[:16]}"
        payload_dir_str = _normalize_path(output_dir / dir_name)
        
        prepared_jsons = [
            _normalize_path(Path(payload_dir_str) / "substack_dispatch_payload.json"),
            _normalize_path(Path(payload_dir_str) / "discord_dispatch_payload.json"),
        ]
        prepared_mds = [
            _normalize_path(Path(payload_dir_str) / "substack_dispatch_payload.md"),
            _normalize_path(Path(payload_dir_str) / "discord_dispatch_payload.md"),
        ]
        
        # Manifest prepared hashes will match the recomputed ones
        for k, v in source_active_outbox_payload_hashes.items():
            if "substack" in k.lower():
                prepared_hashes[prepared_mds[0]] = v
            else:
                prepared_hashes[prepared_mds[1]] = v

    intake_material = {
        "operator_dispatch_review_decision_packet_id": operator_dispatch_review_decision_packet_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    local_dispatch_payload_manifest_id = f"local_dispatch_payload_manifest_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not prepared:
        warnings.append("local_dispatch_payload_preparation_blocked_pending_operator_repair")

    return LocalDispatchPayloadManifest(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        local_dispatch_payload_manifest_id=local_dispatch_payload_manifest_id,
        operator_dispatch_review_decision_packet_id=operator_dispatch_review_decision_packet_id,
        operator_dispatch_decision_sha256=operator_dispatch_decision_sha256,
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
        dispatch_payload_dir=payload_dir_str,
        prepared_dispatch_payload_json_files=prepared_jsons,
        prepared_dispatch_payload_markdown_files=prepared_mds,
        prepared_dispatch_payload_hashes=prepared_hashes,
        source_active_outbox_entry_hashes=source_active_outbox_entry_hashes,
        source_active_outbox_payload_hashes=source_active_outbox_payload_hashes,
        combined_payload_hash=combined_payload_hash,
        local_dispatch_payload_prepared=prepared,
        blockers=blockers,
        warnings=warnings,
    )


def write_local_dispatch_payloads(
    manifest: LocalDispatchPayloadManifest,
    decision_packet: dict,
    entry_file_paths: list[Path],
    entry_packets: dict[str, Any],
    payload_file_paths: list[Path],
    payload_texts: dict[str, str],
    output_dir: Path,
) -> Path:
    if not manifest.local_dispatch_payload_prepared or manifest.blockers:
        # Blocked: write blocked manifest only to output_dir root
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_path = out_path / f"{manifest.local_dispatch_payload_manifest_id}.json"
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(asdict(manifest), f, indent=2, sort_keys=True)
            f.write("\n")
        return manifest_path

    # Clean write target directory
    payload_dir = Path(manifest.dispatch_payload_dir)
    payload_dir.mkdir(parents=True, exist_ok=True)

    # Write markdown files
    substack_md_path = Path(manifest.prepared_dispatch_payload_markdown_files[0])
    discord_md_path = Path(manifest.prepared_dispatch_payload_markdown_files[1])

    # Find the corresponding text
    substack_text = ""
    discord_text = ""
    for path in payload_file_paths:
        npath = _normalize_path(path)
        found_text = ""
        for k, v in payload_texts.items():
            if _normalize_path(k) == npath:
                found_text = v
                break
        if "substack" in npath:
            substack_text = found_text
        else:
            discord_text = found_text

    with open(substack_md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(substack_text)
    with open(discord_md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(discord_text)

    # Find source entry hashes and file paths
    substack_entry_file = ""
    substack_entry_sha256 = ""
    discord_entry_file = ""
    discord_entry_sha256 = ""

    for path in entry_file_paths:
        npath = _normalize_path(path)
        fhash = manifest.source_active_outbox_entry_hashes[npath]
        if "substack" in npath:
            substack_entry_file = npath
            substack_entry_sha256 = fhash
        else:
            discord_entry_file = npath
            discord_entry_sha256 = fhash

    # Build and write prepared JSON files
    substack_json_data = PreparedDispatchPayload(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        prepared_dispatch_payload_id=f"prepared_dispatch_payload_substack_{manifest.combined_payload_hash[:16]}",
        platform="substack",
        payload_markdown_file=manifest.prepared_dispatch_payload_markdown_files[0],
        payload_markdown_sha256=manifest.prepared_dispatch_payload_hashes[manifest.prepared_dispatch_payload_markdown_files[0]],
        source_active_outbox_entry_file=substack_entry_file,
        source_active_outbox_entry_sha256=substack_entry_sha256,
        source_active_outbox_payload_file=_normalize_path(payload_file_paths[0]) if "substack" in _normalize_path(payload_file_paths[0]) else _normalize_path(payload_file_paths[1]),
        source_active_outbox_payload_sha256=manifest.prepared_dispatch_payload_hashes[manifest.prepared_dispatch_payload_markdown_files[0]],
        combined_payload_hash=manifest.combined_payload_hash,
        operator_dispatch_review_decision_packet_id=manifest.operator_dispatch_review_decision_packet_id,
        local_dispatch_preflight_id=manifest.local_dispatch_preflight_id,
        local_active_outbox_manifest_id=manifest.local_active_outbox_manifest_id,
        canonical_slug=manifest.canonical_slug,
        canonical_title=manifest.canonical_title,
    )
    substack_json_path = Path(manifest.prepared_dispatch_payload_json_files[0])
    with open(substack_json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(substack_json_data), f, indent=2, sort_keys=True)
        f.write("\n")

    discord_json_data = PreparedDispatchPayload(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        prepared_dispatch_payload_id=f"prepared_dispatch_payload_discord_{manifest.combined_payload_hash[:16]}",
        platform="discord",
        payload_markdown_file=manifest.prepared_dispatch_payload_markdown_files[1],
        payload_markdown_sha256=manifest.prepared_dispatch_payload_hashes[manifest.prepared_dispatch_payload_markdown_files[1]],
        source_active_outbox_entry_file=discord_entry_file,
        source_active_outbox_entry_sha256=discord_entry_sha256,
        source_active_outbox_payload_file=_normalize_path(payload_file_paths[1]) if "discord" in _normalize_path(payload_file_paths[1]) else _normalize_path(payload_file_paths[0]),
        source_active_outbox_payload_sha256=manifest.prepared_dispatch_payload_hashes[manifest.prepared_dispatch_payload_markdown_files[1]],
        combined_payload_hash=manifest.combined_payload_hash,
        operator_dispatch_review_decision_packet_id=manifest.operator_dispatch_review_decision_packet_id,
        local_dispatch_preflight_id=manifest.local_dispatch_preflight_id,
        local_active_outbox_manifest_id=manifest.local_active_outbox_manifest_id,
        canonical_slug=manifest.canonical_slug,
        canonical_title=manifest.canonical_title,
    )
    discord_json_path = Path(manifest.prepared_dispatch_payload_json_files[1])
    with open(discord_json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(discord_json_data), f, indent=2, sort_keys=True)
        f.write("\n")

    # Write manifest JSON inside the directory
    manifest_path = payload_dir / "local_dispatch_payload_manifest.json"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(manifest), f, indent=2, sort_keys=True)
        f.write("\n")

    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local dispatch payload preparation contract")
    parser.add_argument("decision_packet")
    parser.add_argument("--entry-files", nargs="+", required=True)
    parser.add_argument("--payload-files", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        decision = load_json_packet(Path(args.decision_packet), "malformed_operator_dispatch_review_decision_json")
        
        entry_paths = [Path(p) for p in args.entry_files]
        entry_packets: dict[str, Any] = {}
        for path in entry_paths:
            pkt = load_json_packet(path, f"entry_packet_malformed_{path.name}")
            entry_packets[str(path)] = pkt

        payload_paths = [Path(p) for p in args.payload_files]
        payload_texts: dict[str, str] = {}
        for path in payload_paths:
            text = load_text_file(path, f"preview_file_text_missing_{path.name}")
            payload_texts[str(path)] = text
    except ValueError as exc:
        blocker = str(exc)
        manifest = LocalDispatchPayloadManifest(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            local_dispatch_payload_manifest_id="local_dispatch_payload_manifest_blocked",
            operator_dispatch_review_decision_packet_id="",
            operator_dispatch_decision_sha256="",
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
            dispatch_payload_dir="",
            prepared_dispatch_payload_json_files=[],
            prepared_dispatch_payload_markdown_files=[],
            prepared_dispatch_payload_hashes={},
            source_active_outbox_entry_hashes={},
            source_active_outbox_payload_hashes={},
            combined_payload_hash="",
            local_dispatch_payload_prepared=False,
            blockers=[blocker],
            warnings=["local_dispatch_payload_preparation_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_path = out_path / f"{manifest.local_dispatch_payload_manifest_id}.json"
        manifest_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    manifest = make_local_dispatch_payload_manifest(decision, entry_paths, entry_packets, payload_paths, payload_texts, Path(args.output_dir))
    write_local_dispatch_payloads(manifest, decision, entry_paths, entry_packets, payload_paths, payload_texts, Path(args.output_dir))

    return 1 if manifest.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
