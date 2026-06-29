"""V6 Active Outbox Eligibility Gate from Local Package Staging."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

STAGING_TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_OUTBOX_PACKAGE_STAGING_FROM_PAYLOAD_REVIEW_LEDGER_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_ACTIVE_OUTBOX_ELIGIBILITY_GATE_FROM_LOCAL_PACKAGE_STAGING_V0"
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
class ActiveOutboxEligibilityPacket:
    schema_version: str
    task_label: str
    active_outbox_eligibility_id: str
    outbox_package_staging_id: str
    outbox_package_staging_sha256: str
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
    package_dir: str
    eligible_staged_payload_files: list[str]
    eligible_staged_payload_file_hashes: dict[str, str]
    combined_payload_hash: str
    active_outbox_eligibility_available: bool
    eligible_for_operator_outbox_review: bool
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


def _validate_staging_manifest(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != STAGING_TASK_LABEL:
        blockers.append("manifest_task_label_invalid")
    if packet.get("outbox_package_staged") is not True:
        blockers.append("manifest_package_not_staged")
    if packet.get("outbox_package_preview_only") is not True:
        blockers.append("manifest_package_not_preview_only")
    if packet.get("active_outbox_entry_created") is not False:
        blockers.append("manifest_active_outbox_entry_created_not_false")
    if packet.get("approval_for_dispatch") is not False:
        blockers.append("manifest_approval_for_dispatch_not_false")
    if packet.get("approval_for_outbox_creation") is not False:
        blockers.append("manifest_approval_for_outbox_creation_not_false")
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
        "outbox_package_staging_id",
        "payload_review_ledger_id",
        "payload_review_ledger_sha256",
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
        "package_dir",
        "combined_payload_hash",
    ]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"manifest_{key}_missing")

    # Checked file count
    s_files = packet.get("staged_payload_files", [])
    if not isinstance(s_files, list) or len(s_files) != 2:
        blockers.append("manifest_staged_payload_files_count_invalid")

    s_hashes = packet.get("staged_payload_file_hashes", {})
    if not isinstance(s_hashes, dict) or len(s_hashes) != 2:
        blockers.append("manifest_staged_payload_file_hashes_count_invalid")

    src_hashes = packet.get("source_preview_file_hashes", {})
    if not isinstance(src_hashes, dict) or len(src_hashes) != 2:
        blockers.append("manifest_source_preview_file_hashes_count_invalid")

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


def make_active_outbox_eligibility_packet(
    package_manifest: Any,
    staged_file_paths: list[Path],
    staged_file_texts: dict[str, str],
) -> ActiveOutboxEligibilityPacket:
    blockers: list[str] = []

    manifest_is_dict = isinstance(package_manifest, dict)
    if not manifest_is_dict:
        blockers.append("malformed_outbox_package_staging_json")

    # Scan manifest for secrets
    if manifest_is_dict and _has_secret_marker(json.dumps(package_manifest)):
        blockers.append("manifest_secret_marker_detected")

    outbox_package_staging_id = ""
    outbox_package_staging_sha256 = ""
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
    package_dir = ""
    combined_payload_hash = ""
    manifest_staged_file_hashes: dict[str, str] = {}

    if manifest_is_dict and "manifest_secret_marker_detected" not in blockers:
        blockers.extend(_validate_staging_manifest(package_manifest))
        
        outbox_package_staging_id = str(package_manifest.get("outbox_package_staging_id") or "")
        payload_review_ledger_id = str(package_manifest.get("payload_review_ledger_id") or "")
        approval_intent_id = str(package_manifest.get("approval_intent_id") or "")
        variant_preview_staging_id = str(package_manifest.get("variant_preview_staging_id") or "")
        metadata_values_review_id = str(package_manifest.get("metadata_values_review_id") or "")
        metadata_values_id = str(package_manifest.get("metadata_values_id") or "")
        metadata_proposal_id = str(package_manifest.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(package_manifest.get("source_pack_intake_id") or "")
        source_pack_id = str(package_manifest.get("source_pack_id") or "")
        editorial_workflow_id = str(package_manifest.get("editorial_workflow_id") or "")
        canonical_slug = str(package_manifest.get("canonical_slug") or "")
        canonical_title = str(package_manifest.get("canonical_title") or "")
        package_dir = str(package_manifest.get("package_dir") or "")
        combined_payload_hash = str(package_manifest.get("combined_payload_hash") or "")

        # Manifest staged files expected hashes
        for k, v in package_manifest.get("staged_payload_file_hashes", {}).items():
            manifest_staged_file_hashes[_normalize_path(k)] = str(v)

        # Enforce exact path matching
        supplied_normalized = [_normalize_path(p) for p in staged_file_paths]
        manifest_normalized = [_normalize_path(p) for p in package_manifest.get("staged_payload_files", [])]

        if len(staged_file_paths) != 2:
            blockers.append("preview_file_paths_count_invalid")
        if len(set(supplied_normalized)) != len(supplied_normalized):
            blockers.append("preview_file_paths_duplicate_detected")
        if supplied_normalized != manifest_normalized:
            blockers.append("preview_file_paths_order_mismatch")

    # Staged payload file texts validation & hashing
    computed_staged_file_hashes: dict[str, str] = {}
    for path in staged_file_paths:
        npath = _normalize_path(path)
        # Use case-insensitive path-normalization lookup
        text = None
        for k, v in staged_file_texts.items():
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
            computed_staged_file_hashes[npath] = fhash
            
            # Compare to manifest hash
            expected = manifest_staged_file_hashes.get(npath)
            if expected and fhash != expected:
                blockers.append(f"preview_file_hash_mismatch_{path.name}")

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "manifest_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
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
        package_dir = "[REDACTED_SECRET_MARKER_DETECTED]"
        combined_payload_hash = ""
        # Clear hashes
        outbox_package_staging_sha256 = ""
        computed_staged_file_hashes = {}

    elif manifest_is_dict and not has_secrets:
        outbox_package_staging_sha256 = hashlib.sha256(_canonical_json(package_manifest).encode("utf-8")).hexdigest()

    # Staged paths output list
    eligible_staged_payload_files = [_normalize_path(p) for p in staged_file_paths] if not has_secrets else []

    # Deterministic active outbox eligibility ID
    intake_material = {
        "outbox_package_staging_id": outbox_package_staging_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    active_outbox_eligibility_id = f"active_outbox_eligibility_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("active_outbox_eligibility_blocked_pending_operator_repair")

    return ActiveOutboxEligibilityPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        active_outbox_eligibility_id=active_outbox_eligibility_id,
        outbox_package_staging_id=outbox_package_staging_id,
        outbox_package_staging_sha256=outbox_package_staging_sha256,
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
        package_dir=package_dir,
        eligible_staged_payload_files=eligible_staged_payload_files,
        eligible_staged_payload_file_hashes=computed_staged_file_hashes,
        combined_payload_hash=combined_payload_hash,
        active_outbox_eligibility_available=available,
        eligible_for_operator_outbox_review=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_active_outbox_eligibility_packet(
    packet: ActiveOutboxEligibilityPacket,
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    packet_path = out_path / f"{packet.active_outbox_eligibility_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 active outbox eligibility gate contract")
    parser.add_argument("package_manifest")
    parser.add_argument("--staged-files", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        manifest = load_json_packet(Path(args.package_manifest), "malformed_outbox_package_staging_json")
        staged_paths = [Path(p) for p in args.staged_files]
        staged_texts: dict[str, str] = {}
        for path in staged_paths:
            text = load_text_file(path, f"preview_file_text_missing_{path.name}")
            staged_texts[str(path)] = text
    except ValueError as exc:
        blocker = str(exc)
        packet = ActiveOutboxEligibilityPacket(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            active_outbox_eligibility_id="active_outbox_eligibility_blocked",
            outbox_package_staging_id="",
            outbox_package_staging_sha256="",
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
            package_dir="",
            eligible_staged_payload_files=[],
            eligible_staged_payload_file_hashes={},
            combined_payload_hash="",
            active_outbox_eligibility_available=False,
            eligible_for_operator_outbox_review=False,
            blockers=[blocker],
            warnings=["active_outbox_eligibility_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        packet_path = out_path / f"{packet.active_outbox_eligibility_id}.json"
        packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    packet = make_active_outbox_eligibility_packet(manifest, staged_paths, staged_texts)
    write_active_outbox_eligibility_packet(packet, Path(args.output_dir))

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
