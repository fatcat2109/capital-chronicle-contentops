"""V6 Local Payload Review/Hash and Approval Ledger Strengthening."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

STAGING_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_PLATFORM_VARIANT_PREVIEW_STAGING_FROM_METADATA_VALUES_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_PAYLOAD_REVIEW_HASH_AND_APPROVAL_LEDGER_STRENGTHENING_V0"
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
class PayloadReviewApprovalLedgerPacket:
    schema_version: str
    task_label: str
    payload_review_ledger_id: str
    approval_intent_id: str
    operator_id: str
    created_at_manual: str
    variant_preview_staging_id: str
    variant_preview_staging_sha256: str
    metadata_values_review_id: str
    metadata_values_id: str
    metadata_proposal_id: str
    source_pack_intake_id: str
    source_pack_id: str
    editorial_workflow_id: str
    canonical_slug: str
    canonical_title: str
    reviewed_preview_files: list[str]
    preview_file_hashes: dict[str, str]
    combined_payload_hash: str
    approval_phrase: str
    approval_scope: str
    payload_review_hash_available: bool
    approval_intent_recorded: bool
    approval_for_dispatch: bool = False
    approval_for_outbox_creation: bool = False
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


def _validate_staging_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != STAGING_TASK_LABEL:
        blockers.append("staging_task_label_invalid")
    if packet.get("variant_preview_staging_available") is not True:
        blockers.append("staging_not_available")
    if packet.get("variant_previews_generated") is not True:
        blockers.append("staging_previews_not_generated")
    if packet.get("preview_only") is not True:
        blockers.append("staging_preview_only_not_true")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("staging_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("staging_citations_verified_not_false")

    blockers.extend(_check_public_and_live_fields(packet, "staging"))

    if packet.get("review_only") is not True:
        blockers.append("staging_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("staging_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("staging_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("staging_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("staging_has_blockers")

    # IDs & metadata values existence check
    required_keys = [
        "metadata_values_review_id",
        "metadata_values_review_sha256",
        "metadata_values_id",
        "metadata_proposal_id",
        "source_pack_intake_id",
        "source_pack_id",
        "editorial_workflow_id",
        "canonical_slug",
        "canonical_title",
    ]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"staging_{key}_missing")

    # Check platforms and preview files count
    platforms = packet.get("preview_platforms", [])
    if not isinstance(platforms, list) or set(platforms) != {"substack", "discord"}:
        blockers.append("staging_preview_platforms_invalid")

    preview_files = packet.get("preview_files", [])
    if not isinstance(preview_files, list) or len(preview_files) != 2:
        blockers.append("staging_preview_files_count_invalid")

    return blockers


def _validate_preview_text(text: str, platform: str) -> list[str]:
    blockers: list[str] = []
    if not text.strip():
        blockers.append(f"preview_{platform}_empty")
        return blockers

    # Scan for secret-like markers
    if _has_secret_marker(text):
        blockers.append(f"preview_{platform}_secret_marker_detected")

    # Safe warning check
    if platform == "substack":
        if "LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION" not in text:
            blockers.append("preview_substack_warning_missing")
    elif platform == "discord":
        if "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH" not in text:
            blockers.append("preview_discord_warning_missing")

    lowered = text.lower()
    # Sanitize allowed warnings to prevent false-positive claim blockages
    lowered = lowered.replace("local preview only - not approved for publication", "")
    lowered = lowered.replace("local preview only - not approved for discord dispatch", "")
    
    # Prohibited claims
    for marker in PUBLIC_READY_MARKERS:
        if marker in lowered:
            blockers.append(f"preview_{platform}_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"preview_{platform}_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"preview_{platform}_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(lowered):
            blockers.append(f"preview_{platform}_financial_advice_or_signal_framing_detected")
            break

    # Webhook or dispatch tokens check
    live_send_markers = ["webhook_url", "channel_id", "bot_token", "dispatch_allowed: true", "publish: true"]
    for marker in live_send_markers:
        if marker in lowered:
            blockers.append(f"preview_{platform}_live_send_instructions_detected")

    return blockers


def _validate_intent(intent: dict[str, Any], staging_packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    required_keys = [
        "schema_version",
        "approval_intent_id",
        "operator_id",
        "created_at_manual",
        "variant_preview_staging_id",
        "reviewed_preview_files",
        "approval_phrase",
        "approval_scope",
        "notes",
    ]
    for key in required_keys:
        if key not in intent or intent[key] is None:
            blockers.append(f"intent_{key}_missing")
            
    if "notes" in intent and not isinstance(intent["notes"], str):
        blockers.append("intent_notes_not_string")

    if intent.get("variant_preview_staging_id") != staging_packet.get("variant_preview_staging_id"):
        blockers.append("intent_variant_preview_staging_id_mismatch")

    if intent.get("approval_phrase") != "REVIEWED_LOCAL_PREVIEWS_ONLY_NOT_APPROVED_FOR_DISPATCH":
        blockers.append("intent_approval_phrase_invalid")

    if intent.get("approval_scope") != "payload_review_hash_only":
        blockers.append("intent_approval_scope_invalid")

    return blockers


def make_payload_review_approval_ledger_packet(
    staging_packet: Any,
    preview_file_paths: list[Path],
    preview_file_texts: dict[str, str],
    approval_intent: Any,
) -> PayloadReviewApprovalLedgerPacket:
    blockers: list[str] = []

    staging_is_dict = isinstance(staging_packet, dict)
    if not staging_is_dict:
        blockers.append("malformed_variant_preview_staging_json")

    intent_is_dict = isinstance(approval_intent, dict)
    if not intent_is_dict:
        blockers.append("malformed_approval_intent_json")

    # Scan staging packet for secrets
    if staging_is_dict and _has_secret_marker(json.dumps(staging_packet)):
        blockers.append("staging_secret_marker_detected")

    # Scan approval intent for secrets
    if intent_is_dict and _has_secret_marker(json.dumps(approval_intent)):
        blockers.append("intent_secret_marker_detected")

    # Scan approval intent text/notes for claims & advice
    if intent_is_dict:
        intent_repr = _canonical_json(approval_intent).lower()
        # Sanitize allowed approval intent phrase and scope
        intent_clean = intent_repr
        intent_clean = intent_clean.replace("reviewed_local_previews_only_not_approved_for_dispatch", "")
        intent_clean = intent_clean.replace("payload_review_hash_only", "")
        for marker in PUBLIC_READY_MARKERS:
            if marker in intent_clean:
                blockers.append(f"intent_public_ready_or_approval_claim_detected_{marker}")
        for marker in FAKE_CLAIMS_MARKERS:
            if marker in intent_clean:
                blockers.append(f"intent_fake_readiness_or_metrics_claim_detected_{marker}")
        for marker in CITATION_CLAIMS_MARKERS:
            if marker in intent_clean:
                blockers.append(f"intent_citations_verified_or_generated_claim_detected_{marker}")
        for rx in TRADING_ADVICE_RE:
            if rx.search(intent_clean):
                blockers.append("intent_financial_advice_or_signal_framing_detected")
                break

    variant_preview_staging_id = ""
    metadata_values_review_id = ""
    metadata_values_id = ""
    metadata_proposal_id = ""
    source_pack_intake_id = ""
    source_pack_id = ""
    editorial_workflow_id = ""
    canonical_slug = ""
    canonical_title = ""
    variant_preview_staging_sha256 = ""
    approval_intent_id = ""
    operator_id = ""
    created_at_manual = ""
    approval_phrase = ""
    approval_scope = ""

    # Path normalization & comparisons
    if staging_is_dict and "staging_secret_marker_detected" not in blockers:
        blockers.extend(_validate_staging_packet(staging_packet))
        
        variant_preview_staging_id = str(staging_packet.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(staging_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(staging_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(staging_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(staging_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(staging_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(staging_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(staging_packet.get("canonical_slug") or "")
        canonical_title = str(staging_packet.get("canonical_title") or "")

        # Verify exact path matching
        supplied_normalized = [_normalize_path(p) for p in preview_file_paths]
        staging_normalized = [_normalize_path(p) for p in staging_packet.get("preview_files", [])]
        
        if set(supplied_normalized) != set(staging_normalized):
            blockers.append("preview_file_paths_mismatch")

        if len(preview_file_paths) != 2:
            blockers.append("preview_file_paths_count_invalid")

    if intent_is_dict and "intent_secret_marker_detected" not in blockers and staging_is_dict:
        blockers.extend(_validate_intent(approval_intent, staging_packet))
        
        approval_intent_id = str(approval_intent.get("approval_intent_id") or "")
        operator_id = str(approval_intent.get("operator_id") or "")
        created_at_manual = str(approval_intent.get("created_at_manual") or "")
        approval_phrase = str(approval_intent.get("approval_phrase") or "")
        approval_scope = str(approval_intent.get("approval_scope") or "")
        
        intent_normalized = [_normalize_path(p) for p in approval_intent.get("reviewed_preview_files", [])]
        supplied_normalized = [_normalize_path(p) for p in preview_file_paths]
        if set(intent_normalized) != set(supplied_normalized):
            blockers.append("intent_reviewed_preview_files_mismatch")

    # Preview file texts validation & hashing
    preview_file_hashes: dict[str, str] = {}
    for path in preview_file_paths:
        npath = _normalize_path(path)
        # Case-insensitive path-normalization lookup to resolve slash and drive differences
        text = None
        for k, v in preview_file_texts.items():
            if _normalize_path(k) == npath:
                text = v
                break

        if text is None:
            blockers.append(f"preview_file_text_missing_{path.name}")
            continue

        platform = "substack" if "substack" in path.name.lower() else "discord"
        blockers.extend(_validate_preview_text(text, platform))
        
        has_file_secrets = _has_secret_marker(text)
        if not has_file_secrets:
            # Deterministic hash over normalized UTF-8 contents
            preview_file_hashes[npath] = hashlib.sha256(text.encode("utf-8")).hexdigest()

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "staging_secret_marker_detected" in blockers or
        "intent_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
        metadata_values_review_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_values_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_proposal_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_intake_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        editorial_workflow_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_slug = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_title = "[REDACTED_SECRET_MARKER_DETECTED]"
        variant_preview_staging_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        approval_intent_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        # Clear hashes
        variant_preview_staging_sha256 = ""
        preview_file_hashes = {}

    elif staging_is_dict and not has_secrets:
        variant_preview_staging_sha256 = hashlib.sha256(_canonical_json(staging_packet).encode("utf-8")).hexdigest()

    # Compute combined_payload_hash
    combined_payload_hash = ""
    if available and not has_secrets:
        sorted_preview_paths = sorted(preview_file_hashes.keys())
        ordered_hashes = [preview_file_hashes[p] for p in sorted_preview_paths]
        combined_payload_material = {
            "variant_preview_staging_id": variant_preview_staging_id,
            "ordered_preview_file_paths": sorted_preview_paths,
            "ordered_preview_file_hashes": ordered_hashes,
            "approval_intent_id": approval_intent_id,
            "approval_phrase": approval_phrase,
            "approval_scope": approval_scope,
        }
        combined_payload_hash = hashlib.sha256(_canonical_json(combined_payload_material).encode("utf-8")).hexdigest()

    # Reviewed preview files output list (normalized)
    reviewed_preview_files_out = [_normalize_path(p) for p in preview_file_paths] if not has_secrets else []

    # Deterministic packet ID
    intake_material = {
        "variant_preview_staging_id": variant_preview_staging_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    payload_review_ledger_id = f"payload_review_ledger_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("payload_review_hash_blocked_pending_operator_repair")

    return PayloadReviewApprovalLedgerPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        payload_review_ledger_id=payload_review_ledger_id,
        approval_intent_id=approval_intent_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        variant_preview_staging_id=variant_preview_staging_id,
        variant_preview_staging_sha256=variant_preview_staging_sha256,
        metadata_values_review_id=metadata_values_review_id,
        metadata_values_id=metadata_values_id,
        metadata_proposal_id=metadata_proposal_id,
        source_pack_intake_id=source_pack_intake_id,
        source_pack_id=source_pack_id,
        editorial_workflow_id=editorial_workflow_id,
        canonical_slug=canonical_slug,
        canonical_title=canonical_title,
        reviewed_preview_files=reviewed_preview_files_out,
        preview_file_hashes=preview_file_hashes,
        combined_payload_hash=combined_payload_hash,
        approval_phrase=approval_phrase,
        approval_scope=approval_scope,
        payload_review_hash_available=available,
        approval_intent_recorded=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_payload_review_approval_ledger_packet(
    packet: PayloadReviewApprovalLedgerPacket,
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    packet_path = out_path / f"{packet.payload_review_ledger_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local payload review hash and approval ledger contract")
    parser.add_argument("staging_packet")
    parser.add_argument("approval_intent")
    parser.add_argument("--preview-files", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        staging = load_json_packet(Path(args.staging_packet), "malformed_variant_preview_staging_json")
        intent = load_json_packet(Path(args.approval_intent), "malformed_approval_intent_json")

        preview_paths = [Path(p) for p in args.preview_files]
        preview_texts: dict[str, str] = {}
        for path in preview_paths:
            text = load_text_file(path, f"preview_file_text_missing_{path.name}")
            preview_texts[str(path)] = text
    except ValueError as exc:
        blocker = str(exc)
        packet = PayloadReviewApprovalLedgerPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            payload_review_ledger_id="payload_review_ledger_blocked",
            approval_intent_id="",
            operator_id="",
            created_at_manual="",
            variant_preview_staging_id="",
            variant_preview_staging_sha256="",
            metadata_values_review_id="",
            metadata_values_id="",
            metadata_proposal_id="",
            source_pack_intake_id="",
            source_pack_id="",
            editorial_workflow_id="",
            canonical_slug="",
            canonical_title="",
            reviewed_preview_files=[],
            preview_file_hashes={},
            combined_payload_hash="",
            approval_phrase="",
            approval_scope="",
            payload_review_hash_available=False,
            approval_intent_recorded=False,
            blockers=[blocker],
            warnings=["payload_review_hash_blocked_pending_operator_repair"],
        )
        write_payload_review_approval_ledger_packet(packet, Path(args.output_dir))
        return 1

    packet = make_payload_review_approval_ledger_packet(staging, preview_paths, preview_texts, intent)
    write_payload_review_approval_ledger_packet(packet, Path(args.output_dir))

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
