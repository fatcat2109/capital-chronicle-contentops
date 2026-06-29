"""V6 Local Outbox Package Staging from Payload Review Ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

LEDGER_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_PAYLOAD_REVIEW_HASH_AND_APPROVAL_LEDGER_STRENGTHENING_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_OUTBOX_PACKAGE_STAGING_FROM_PAYLOAD_REVIEW_LEDGER_V0"
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
class LocalOutboxPackageStagingManifest:
    schema_version: str
    task_label: str
    outbox_package_staging_id: str
    payload_review_ledger_id: str
    payload_review_ledger_sha256: str
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
    package_dir: str
    staged_payload_files: list[str]
    staged_payload_file_hashes: dict[str, str]
    source_preview_file_hashes: dict[str, str]
    combined_payload_hash: str
    outbox_package_staged: bool
    outbox_package_preview_only: bool = True
    active_outbox_entry_created: bool = False
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


def _validate_ledger_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != LEDGER_TASK_LABEL:
        blockers.append("ledger_task_label_invalid")
    if packet.get("payload_review_hash_available") is not True:
        blockers.append("ledger_payload_review_hash_not_available")
    if packet.get("approval_intent_recorded") is not True:
        blockers.append("ledger_approval_intent_not_recorded")
    if packet.get("approval_for_dispatch") is not False:
        blockers.append("ledger_approval_for_dispatch_not_false")
    if packet.get("approval_for_outbox_creation") is not False:
        blockers.append("ledger_approval_for_outbox_creation_not_false")
    if packet.get("approval_for_publication") is not False:
        blockers.append("ledger_approval_for_publication_not_false")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("ledger_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("ledger_citations_verified_not_false")

    blockers.extend(_check_public_and_live_fields(packet, "ledger"))

    if packet.get("review_only") is not True:
        blockers.append("ledger_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("ledger_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("ledger_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("ledger_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("ledger_has_blockers")

    # Required IDs and text values check
    required_keys = [
        "payload_review_ledger_id",
        "approval_intent_id",
        "variant_preview_staging_id",
        "variant_preview_staging_sha256",
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
            blockers.append(f"ledger_{key}_missing")

    # Checked file count
    p_hashes = packet.get("preview_file_hashes", {})
    if not isinstance(p_hashes, dict) or len(p_hashes) != 2:
        blockers.append("ledger_preview_file_hashes_count_invalid")

    reviewed_files = packet.get("reviewed_preview_files", [])
    if not isinstance(reviewed_files, list) or len(reviewed_files) != 2:
        blockers.append("ledger_reviewed_preview_files_count_invalid")

    if packet.get("approval_phrase") != "REVIEWED_LOCAL_PREVIEWS_ONLY_NOT_APPROVED_FOR_DISPATCH":
        blockers.append("ledger_approval_phrase_invalid")

    if packet.get("approval_scope") != "payload_review_hash_only":
        blockers.append("ledger_approval_scope_invalid")

    return blockers


def _validate_preview_text(text: str, platform: str) -> list[str]:
    blockers: list[str] = []
    if not text.strip():
        blockers.append(f"preview_{platform}_empty")
        return blockers

    # Scan for secrets
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


def make_local_outbox_package_staging_manifest(
    ledger_packet: Any,
    preview_file_paths: list[Path],
    preview_file_texts: dict[str, str],
    output_dir: Path,
) -> LocalOutboxPackageStagingManifest:
    blockers: list[str] = []

    ledger_is_dict = isinstance(ledger_packet, dict)
    if not ledger_is_dict:
        blockers.append("malformed_payload_review_ledger_json")

    # Scan ledger for secrets
    if ledger_is_dict and _has_secret_marker(json.dumps(ledger_packet)):
        blockers.append("ledger_secret_marker_detected")

    payload_review_ledger_id = ""
    payload_review_ledger_sha256 = ""
    approval_intent_id = ""
    variant_preview_staging_id = ""
    variant_preview_staging_sha256 = ""
    metadata_values_review_id = ""
    metadata_values_id = ""
    metadata_proposal_id = ""
    source_pack_intake_id = ""
    source_pack_id = ""
    editorial_workflow_id = ""
    canonical_slug = ""
    canonical_title = ""
    combined_payload_hash = ""
    source_preview_file_hashes: dict[str, str] = {}

    if ledger_is_dict and "ledger_secret_marker_detected" not in blockers:
        blockers.extend(_validate_ledger_packet(ledger_packet))
        
        payload_review_ledger_id = str(ledger_packet.get("payload_review_ledger_id") or "")
        approval_intent_id = str(ledger_packet.get("approval_intent_id") or "")
        variant_preview_staging_id = str(ledger_packet.get("variant_preview_staging_id") or "")
        variant_preview_staging_sha256 = str(ledger_packet.get("variant_preview_staging_sha256") or "")
        metadata_values_review_id = str(ledger_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(ledger_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(ledger_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(ledger_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(ledger_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(ledger_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(ledger_packet.get("canonical_slug") or "")
        canonical_title = str(ledger_packet.get("canonical_title") or "")
        combined_payload_hash = str(ledger_packet.get("combined_payload_hash") or "")

        # Ledger previews source hashes
        for k, v in ledger_packet.get("preview_file_hashes", {}).items():
            source_preview_file_hashes[_normalize_path(k)] = str(v)

        # Enforce exact, duplicate-proof, ordered path matching
        supplied_normalized = [_normalize_path(p) for p in preview_file_paths]
        ledger_normalized = [_normalize_path(p) for p in ledger_packet.get("reviewed_preview_files", [])]

        if len(preview_file_paths) != 2:
            blockers.append("preview_file_paths_count_invalid")
        if len(set(supplied_normalized)) != len(supplied_normalized):
            blockers.append("preview_file_paths_duplicate_detected")
        if supplied_normalized != ledger_normalized:
            blockers.append("preview_file_paths_order_mismatch")

    # Preview file texts validation, hashing, and revalidation
    computed_preview_file_hashes: dict[str, str] = {}
    for path in preview_file_paths:
        npath = _normalize_path(path)
        # Use case-insensitive path-normalization lookup
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
            fhash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            computed_preview_file_hashes[npath] = fhash
            
            # Compare to ledger hash
            ledger_expected = source_preview_file_hashes.get(npath)
            if ledger_expected and fhash != ledger_expected:
                blockers.append(f"preview_file_hash_mismatch_{path.name}")

    # Revalidate combined payload hash
    if ledger_is_dict and "ledger_secret_marker_detected" not in blockers and not any(f"preview_file_text_missing" in b for b in blockers):
        sorted_preview_paths = sorted(computed_preview_file_hashes.keys())
        ordered_hashes = [computed_preview_file_hashes.get(p, "") for p in sorted_preview_paths]
        
        combined_payload_material = {
            "variant_preview_staging_id": variant_preview_staging_id,
            "ordered_preview_file_paths": sorted_preview_paths,
            "ordered_preview_file_hashes": ordered_hashes,
            "approval_intent_id": approval_intent_id,
            "approval_phrase": ledger_packet.get("approval_phrase"),
            "approval_scope": ledger_packet.get("approval_scope"),
        }
        computed_combined_hash = hashlib.sha256(_canonical_json(combined_payload_material).encode("utf-8")).hexdigest()
        if computed_combined_hash != combined_payload_hash:
            blockers.append("combined_payload_hash_mismatch")

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "ledger_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
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
        # Clear hashes
        payload_review_ledger_sha256 = ""
        computed_preview_file_hashes = {}
        source_preview_file_hashes = {}

    elif ledger_is_dict and not has_secrets:
        payload_review_ledger_sha256 = hashlib.sha256(_canonical_json(ledger_packet).encode("utf-8")).hexdigest()

    # Staging paths and setup
    package_dir = ""
    staged_payload_files: list[str] = []
    staged_payload_file_hashes: dict[str, str] = {}

    if available:
        package_dirname = f"{canonical_slug}_{combined_payload_hash[:16]}"
        package_dir_path = Path(output_dir) / package_dirname
        package_dir = str(package_dir_path.resolve()).replace("\\", "/")
        
        staged_payload_files = [
            str((package_dir_path / "substack_preview.md").resolve()).replace("\\", "/"),
            str((package_dir_path / "discord_preview.md").resolve()).replace("\\", "/"),
        ]
        
        # Staged hashes match computed preview file hashes
        staged_payload_file_hashes[staged_payload_files[0]] = computed_preview_file_hashes.get(_normalize_path(preview_file_paths[0]), "")
        staged_payload_file_hashes[staged_payload_files[1]] = computed_preview_file_hashes.get(_normalize_path(preview_file_paths[1]), "")

    # Deterministic outbox package staging ID
    intake_material = {
        "payload_review_ledger_id": payload_review_ledger_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    outbox_package_staging_id = f"outbox_package_staging_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("outbox_package_staging_blocked_pending_operator_repair")

    return LocalOutboxPackageStagingManifest(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        outbox_package_staging_id=outbox_package_staging_id,
        payload_review_ledger_id=payload_review_ledger_id,
        payload_review_ledger_sha256=payload_review_ledger_sha256,
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
        package_dir=package_dir,
        staged_payload_files=staged_payload_files,
        staged_payload_file_hashes=staged_payload_file_hashes,
        source_preview_file_hashes=source_preview_file_hashes,
        combined_payload_hash=combined_payload_hash,
        outbox_package_staged=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_local_outbox_package(
    manifest: LocalOutboxPackageStagingManifest,
    preview_file_paths: list[Path],
    preview_file_texts: dict[str, str],
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Write manifest first
    manifest_path = out_path / f"{manifest.outbox_package_staging_id}.json"
    manifest_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not manifest.outbox_package_staged:
        return manifest_path

    # Copy files into staging directory
    package_dir_path = Path(manifest.package_dir)
    package_dir_path.mkdir(parents=True, exist_ok=True)

    for path in preview_file_paths:
        npath = _normalize_path(path)
        text = None
        for k, v in preview_file_texts.items():
            if _normalize_path(k) == npath:
                text = v
                break
        
        target_name = "substack_preview.md" if "substack" in path.name.lower() else "discord_preview.md"
        target_path = package_dir_path / target_name
        target_path.write_text(text, encoding="utf-8")

    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local outbox package staging contract")
    parser.add_argument("ledger_packet")
    parser.add_argument("--preview-files", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        ledger = load_json_packet(Path(args.ledger_packet), "malformed_payload_review_ledger_json")
        preview_paths = [Path(p) for p in args.preview_files]
        preview_texts: dict[str, str] = {}
        for path in preview_paths:
            text = load_text_file(path, f"preview_file_text_missing_{path.name}")
            preview_texts[str(path)] = text
    except ValueError as exc:
        blocker = str(exc)
        manifest = LocalOutboxPackageStagingManifest(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            outbox_package_staging_id="outbox_package_staging_blocked",
            payload_review_ledger_id="",
            payload_review_ledger_sha256="",
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
            package_dir="",
            staged_payload_files=[],
            staged_payload_file_hashes={},
            source_preview_file_hashes={},
            combined_payload_hash="",
            outbox_package_staged=False,
            blockers=[blocker],
            warnings=["outbox_package_staging_blocked_pending_operator_repair"],
        )
        # Write manifest to output dir
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_path = out_path / f"{manifest.outbox_package_staging_id}.json"
        manifest_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    manifest = make_local_outbox_package_staging_manifest(ledger, preview_paths, preview_texts, Path(args.output_dir))
    write_local_outbox_package(manifest, preview_paths, preview_texts, Path(args.output_dir))

    return 1 if manifest.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
