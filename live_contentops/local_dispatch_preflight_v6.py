"""V6 Local Dispatch Preflight from Active Outbox."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MANIFEST_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_ACTIVE_OUTBOX_CREATION_FROM_OPERATOR_REVIEW_DECISION_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PREFLIGHT_FROM_ACTIVE_OUTBOX_V0"
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
class LocalDispatchPreflightPacket:
    schema_version: str
    task_label: str
    local_dispatch_preflight_id: str
    local_active_outbox_manifest_id: str
    local_active_outbox_manifest_sha256: str
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
    active_outbox_entries: list[str]
    active_outbox_entry_hashes: dict[str, str]
    active_outbox_payload_files: list[str]
    active_outbox_payload_file_hashes: dict[str, str]
    combined_payload_hash: str
    dispatch_preflight_available: bool
    eligible_for_operator_dispatch_review: bool
    dispatch_payload_created: bool = False
    approval_for_dispatch: bool = False
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
    if packet.get("local_active_outbox_created") is not True:
        blockers.append("manifest_local_active_outbox_not_created")
    if packet.get("active_outbox_entry_created") is not True:
        blockers.append("manifest_active_outbox_entry_not_created")
    if packet.get("dispatch_payload_created") is not False:
        blockers.append("manifest_dispatch_payload_created_not_false")
    if packet.get("approval_for_dispatch") is not False:
        blockers.append("manifest_approval_for_dispatch_not_false")
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
        "local_active_outbox_manifest_id",
        "operator_active_outbox_review_decision_id",
        "operator_review_decision_sha256",
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
        "active_outbox_dir",
    ]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"manifest_{key}_missing")

    # Count checks
    entries = packet.get("active_outbox_entries", [])
    if not isinstance(entries, list) or len(entries) != 2:
        blockers.append("manifest_active_outbox_entries_count_invalid")

    payloads = packet.get("active_outbox_payload_files", [])
    if not isinstance(payloads, list) or len(payloads) != 2:
        blockers.append("manifest_active_outbox_payload_files_count_invalid")

    hashes = packet.get("active_outbox_payload_file_hashes", {})
    if not isinstance(hashes, dict) or len(hashes) != 2:
        blockers.append("manifest_active_outbox_payload_file_hashes_count_invalid")

    src_hashes = packet.get("source_staged_payload_file_hashes", {})
    if not isinstance(src_hashes, dict) or len(src_hashes) != 2:
        blockers.append("manifest_source_staged_payload_file_hashes_count_invalid")

    return blockers


def _validate_entry_packet(entry: dict[str, Any], manifest: dict[str, Any], prefix: str) -> list[str]:
    blockers: list[str] = []
    if entry.get("task_label") != manifest.get("task_label"):
        blockers.append(f"{prefix}_task_label_mismatch")
    
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

    # Match IDs and references
    if entry.get("combined_payload_hash") != manifest.get("combined_payload_hash"):
        blockers.append(f"{prefix}_combined_payload_hash_mismatch")
    if entry.get("operator_active_outbox_review_decision_id") != manifest.get("operator_active_outbox_review_decision_id"):
        blockers.append(f"{prefix}_operator_active_outbox_review_decision_id_mismatch")
    if entry.get("active_outbox_eligibility_id") != manifest.get("active_outbox_eligibility_id"):
        blockers.append(f"{prefix}_active_outbox_eligibility_id_mismatch")
    if entry.get("outbox_package_staging_id") != manifest.get("outbox_package_staging_id"):
        blockers.append(f"{prefix}_outbox_package_staging_id_mismatch")
    if entry.get("canonical_slug") != manifest.get("canonical_slug"):
        blockers.append(f"{prefix}_canonical_slug_mismatch")
    if entry.get("canonical_title") != manifest.get("canonical_title"):
        blockers.append(f"{prefix}_canonical_title_mismatch")

    # Match payload file in manifest
    entry_payload = entry.get("payload_file")
    if not entry_payload:
        blockers.append(f"{prefix}_payload_file_missing")
    else:
        npath = _normalize_path(entry_payload)
        manifest_payload_normalized = [_normalize_path(p) for p in manifest.get("active_outbox_payload_files", [])]
        if npath not in manifest_payload_normalized:
            blockers.append(f"{prefix}_payload_file_not_in_manifest")
        else:
            # Find matching hash
            expected_hash = None
            for k, v in manifest.get("active_outbox_payload_file_hashes", {}).items():
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


def make_local_dispatch_preflight_packet(
    active_manifest: Any,
    entry_file_paths: list[Path],
    entry_packets: dict[str, Any],
    payload_file_paths: list[Path],
    payload_texts: dict[str, str],
) -> LocalDispatchPreflightPacket:
    blockers: list[str] = []

    manifest_is_dict = isinstance(active_manifest, dict)
    if not manifest_is_dict:
        blockers.append("malformed_local_active_outbox_manifest_json")

    # Scan manifest for secrets
    if manifest_is_dict and _has_secret_marker(json.dumps(active_manifest)):
        blockers.append("manifest_secret_marker_detected")

    local_active_outbox_manifest_id = ""
    local_active_outbox_manifest_sha256 = ""
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

    if manifest_is_dict and "manifest_secret_marker_detected" not in blockers:
        blockers.extend(_validate_manifest_packet(active_manifest))
        
        local_active_outbox_manifest_id = str(active_manifest.get("local_active_outbox_manifest_id") or "")
        operator_active_outbox_review_decision_id = str(active_manifest.get("operator_active_outbox_review_decision_id") or "")
        active_outbox_eligibility_id = str(active_manifest.get("active_outbox_eligibility_id") or "")
        outbox_package_staging_id = str(active_manifest.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(active_manifest.get("payload_review_ledger_id") or "")
        approval_intent_id = str(active_manifest.get("approval_intent_id") or "")
        variant_preview_staging_id = str(active_manifest.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(active_manifest.get("metadata_values_review_id") or "")
        metadata_values_id = str(active_manifest.get("metadata_values_id") or "")
        metadata_proposal_id = str(active_manifest.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(active_manifest.get("source_pack_intake_id") or "")
        source_pack_id = str(active_manifest.get("source_pack_id") or "")
        editorial_workflow_id = str(active_manifest.get("editorial_workflow_id") or "")
        canonical_slug = str(active_manifest.get("canonical_slug") or "")
        canonical_title = str(active_manifest.get("canonical_title") or "")
        combined_payload_hash = str(active_manifest.get("combined_payload_hash") or "")

        # Payload files expected hashes from manifest
        for k, v in active_manifest.get("active_outbox_payload_file_hashes", {}).items():
            manifest_payload_file_hashes[_normalize_path(k)] = str(v)

        # Enforce exact entry path matching
        supplied_entry_normalized = [_normalize_path(p) for p in entry_file_paths]
        manifest_entries_normalized = [_normalize_path(p) for p in active_manifest.get("active_outbox_entries", [])]

        if len(entry_file_paths) != 2:
            blockers.append("entry_file_paths_count_invalid")
        if len(set(supplied_entry_normalized)) != len(supplied_entry_normalized):
            blockers.append("entry_file_paths_duplicate_detected")
        if supplied_entry_normalized != manifest_entries_normalized:
            blockers.append("entry_file_paths_order_mismatch")

        # Enforce exact payload path matching
        supplied_payload_normalized = [_normalize_path(p) for p in payload_file_paths]
        manifest_payloads_normalized = [_normalize_path(p) for p in active_manifest.get("active_outbox_payload_files", [])]

        if len(payload_file_paths) != 2:
            blockers.append("payload_file_paths_count_invalid")
        if len(set(supplied_payload_normalized)) != len(supplied_payload_normalized):
            blockers.append("payload_file_paths_duplicate_detected")
        if supplied_payload_normalized != manifest_payloads_normalized:
            blockers.append("payload_file_paths_order_mismatch")

    # Validate entry JSON packets
    active_outbox_entry_hashes: dict[str, str] = {}
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
        blockers.extend(_validate_entry_packet(entry_data, active_manifest, f"entry_{platform}"))
        
        # Compute entry hash if no secrets
        if "entry_secret_marker_detected" not in blockers:
            active_outbox_entry_hashes[npath] = hashlib.sha256(_canonical_json(entry_data).encode("utf-8")).hexdigest()

    # Validate payload markdown texts
    computed_payload_hashes: dict[str, str] = {}
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
            computed_payload_hashes[npath] = fhash
            
            # Compare to manifest hash
            expected = manifest_payload_file_hashes.get(npath)
            if expected and fhash != expected:
                blockers.append(f"payload_hash_mismatch_{path.name}")

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "manifest_secret_marker_detected" in blockers or
        "entry_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
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
        local_active_outbox_manifest_sha256 = ""
        active_outbox_entry_hashes = {}
        computed_payload_hashes = {}

    elif manifest_is_dict and not has_secrets:
        local_active_outbox_manifest_sha256 = hashlib.sha256(_canonical_json(active_manifest).encode("utf-8")).hexdigest()

    # Staged entries and files lists
    entries_out = [_normalize_path(p) for p in entry_file_paths] if not has_secrets else []
    payloads_out = [_normalize_path(p) for p in payload_file_paths] if not has_secrets else []

    # Deterministic local dispatch preflight packet ID
    intake_material = {
        "local_active_outbox_manifest_id": local_active_outbox_manifest_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    local_dispatch_preflight_id = f"local_dispatch_preflight_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("local_dispatch_preflight_blocked_pending_operator_repair")

    return LocalDispatchPreflightPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        local_dispatch_preflight_id=local_dispatch_preflight_id,
        local_active_outbox_manifest_id=local_active_outbox_manifest_id,
        local_active_outbox_manifest_sha256=local_active_outbox_manifest_sha256,
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
        active_outbox_entries=entries_out,
        active_outbox_entry_hashes=active_outbox_entry_hashes,
        active_outbox_payload_files=payloads_out,
        active_outbox_payload_file_hashes=computed_payload_hashes,
        combined_payload_hash=combined_payload_hash,
        dispatch_preflight_available=available,
        eligible_for_operator_dispatch_review=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_local_dispatch_preflight_packet(
    packet: LocalDispatchPreflightPacket,
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    packet_path = out_path / f"{packet.local_dispatch_preflight_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local dispatch preflight contract")
    parser.add_argument("active_manifest")
    parser.add_argument("--entry-files", nargs="+", required=True)
    parser.add_argument("--payload-files", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        manifest = load_json_packet(Path(args.active_manifest), "malformed_local_active_outbox_manifest_json")
        
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
        packet = LocalDispatchPreflightPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            local_dispatch_preflight_id="local_dispatch_preflight_blocked",
            local_active_outbox_manifest_id="",
            local_active_outbox_manifest_sha256="",
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
            active_outbox_entries=[],
            active_outbox_entry_hashes={},
            active_outbox_payload_files=[],
            active_outbox_payload_file_hashes={},
            combined_payload_hash="",
            dispatch_preflight_available=False,
            eligible_for_operator_dispatch_review=False,
            blockers=[blocker],
            warnings=["local_dispatch_preflight_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        packet_path = out_path / f"{packet.local_dispatch_preflight_id}.json"
        packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    packet = make_local_dispatch_preflight_packet(manifest, entry_paths, entry_packets, payload_paths, payload_texts)
    write_local_dispatch_preflight_packet(packet, Path(args.output_dir))

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
