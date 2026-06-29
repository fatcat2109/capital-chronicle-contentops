"""V6 Local Active Outbox Creation from Operator Review Decision."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DECISION_TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_ACTIVE_OUTBOX_REVIEW_DECISION_FROM_ELIGIBILITY_GATE_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_ACTIVE_OUTBOX_CREATION_FROM_OPERATOR_REVIEW_DECISION_V0"
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
class ActiveOutboxEntry:
    schema_version: str
    task_label: str
    active_outbox_entry_id: str
    platform: str
    payload_file: str
    payload_sha256: str
    source_staged_payload_file: str
    source_staged_payload_sha256: str
    combined_payload_hash: str
    operator_active_outbox_review_decision_id: str
    active_outbox_eligibility_id: str
    outbox_package_staging_id: str
    canonical_slug: str
    canonical_title: str
    entry_status: str
    dispatch_payload_created: bool = False
    dispatch_allowed: bool = False
    approval_for_dispatch: bool = False
    publication_ready: bool = False
    public_url: None = None
    public_metrics: None = None
    review_only: bool = True
    human_review_required: bool = True
    kill_switch_active: bool = True
    runtime_truth: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LocalActiveOutboxManifest:
    schema_version: str
    task_label: str
    local_active_outbox_manifest_id: str
    operator_active_outbox_review_decision_id: str
    operator_review_decision_sha256: str
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
    active_outbox_dir: str
    active_outbox_entries: list[str]
    active_outbox_payload_files: list[str]
    active_outbox_payload_file_hashes: dict[str, str]
    source_staged_payload_file_hashes: dict[str, str]
    combined_payload_hash: str
    local_active_outbox_created: bool
    active_outbox_entry_created: bool
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


def _validate_decision_packet(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != DECISION_TASK_LABEL:
        blockers.append("decision_task_label_invalid")
    if packet.get("active_outbox_creation_decision_available") is not True:
        blockers.append("decision_not_available")
    if packet.get("active_outbox_creation_approved") is not True:
        blockers.append("decision_not_approved")
    if packet.get("approval_for_outbox_creation") is not True:
        blockers.append("decision_approval_for_outbox_creation_not_true")
    if packet.get("active_outbox_entry_created") is not False:
        blockers.append("decision_active_outbox_entry_created_not_false")
    if packet.get("approval_for_dispatch") is not False:
        blockers.append("decision_approval_for_dispatch_not_false")
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

    if packet.get("decision") != "approve_active_outbox_creation":
        blockers.append("decision_value_invalid")
    if packet.get("approval_phrase") != "APPROVE_LOCAL_ACTIVE_OUTBOX_CREATION_ONLY_NOT_DISPATCH":
        blockers.append("decision_approval_phrase_invalid")
    if packet.get("approval_scope") != "active_outbox_creation_only":
        blockers.append("decision_approval_scope_invalid")

    # Required fields check
    required_keys = [
        "operator_active_outbox_review_decision_id",
        "operator_review_decision_id",
        "active_outbox_eligibility_id",
        "active_outbox_eligibility_sha256",
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

    # Checked file count
    files = packet.get("reviewed_staged_payload_files", [])
    if not isinstance(files, list) or len(files) != 2:
        blockers.append("decision_reviewed_staged_payload_files_count_invalid")

    hashes = packet.get("reviewed_staged_payload_file_hashes", {})
    if not isinstance(hashes, dict) or len(hashes) != 2:
        blockers.append("decision_reviewed_staged_payload_file_hashes_count_invalid")

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


def make_local_active_outbox_manifest(
    decision_packet: Any,
    staged_file_paths: list[Path],
    staged_file_texts: dict[str, str],
    output_dir: Path,
) -> LocalActiveOutboxManifest:
    blockers: list[str] = []

    decision_is_dict = isinstance(decision_packet, dict)
    if not decision_is_dict:
        blockers.append("malformed_operator_review_decision_json")

    # Scan decision for secrets
    if decision_is_dict and _has_secret_marker(json.dumps(decision_packet)):
        blockers.append("decision_secret_marker_detected")

    operator_active_outbox_review_decision_id = ""
    operator_review_decision_sha256 = ""
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
    decision_staged_file_hashes: dict[str, str] = {}

    if decision_is_dict and "decision_secret_marker_detected" not in blockers:
        blockers.extend(_validate_decision_packet(decision_packet))
        
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

        # Staged files expected hashes from decision
        for k, v in decision_packet.get("reviewed_staged_payload_file_hashes", {}).items():
            decision_staged_file_hashes[_normalize_path(k)] = str(v)

        # Enforce exact path matching
        supplied_normalized = [_normalize_path(p) for p in staged_file_paths]
        decision_normalized = [_normalize_path(p) for p in decision_packet.get("reviewed_staged_payload_files", [])]

        if len(staged_file_paths) != 2:
            blockers.append("preview_file_paths_count_invalid")
        if len(set(supplied_normalized)) != len(supplied_normalized):
            blockers.append("preview_file_paths_duplicate_detected")
        if supplied_normalized != decision_normalized:
            blockers.append("preview_file_paths_order_mismatch")

    # Staged payload file texts validation & hashing
    computed_staged_file_hashes: dict[str, str] = {}
    for path in staged_file_paths:
        npath = _normalize_path(path)
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
            
            # Compare to decision hash
            expected = decision_staged_file_hashes.get(npath)
            if expected and fhash != expected:
                blockers.append(f"preview_file_hash_mismatch_{path.name}")

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = (
        "decision_secret_marker_detected" in blockers or
        any("secret_marker_detected" in b for b in blockers)
    )

    if has_secrets:
        # Redact IDs
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
        operator_review_decision_sha256 = ""
        computed_staged_file_hashes = {}

    elif decision_is_dict and not has_secrets:
        operator_review_decision_sha256 = hashlib.sha256(_canonical_json(decision_packet).encode("utf-8")).hexdigest()

    # Active outbox paths
    active_outbox_dir = ""
    active_outbox_entries: list[str] = []
    active_outbox_payload_files: list[str] = []
    active_outbox_payload_file_hashes: dict[str, str] = {}

    if available:
        package_dirname = f"{canonical_slug}_{combined_payload_hash[:16]}"
        active_outbox_dir_path = Path(output_dir) / package_dirname
        active_outbox_dir = str(active_outbox_dir_path.resolve()).replace("\\", "/")
        
        active_outbox_entries = [
            str((active_outbox_dir_path / "substack_outbox_entry.json").resolve()).replace("\\", "/"),
            str((active_outbox_dir_path / "discord_outbox_entry.json").resolve()).replace("\\", "/"),
        ]
        
        active_outbox_payload_files = [
            str((active_outbox_dir_path / "substack_payload.md").resolve()).replace("\\", "/"),
            str((active_outbox_dir_path / "discord_payload.md").resolve()).replace("\\", "/"),
        ]
        
        # Payload hashes match computed staged hashes
        active_outbox_payload_file_hashes[active_outbox_payload_files[0]] = computed_staged_file_hashes.get(_normalize_path(staged_file_paths[0]), "")
        active_outbox_payload_file_hashes[active_outbox_payload_files[1]] = computed_staged_file_hashes.get(_normalize_path(staged_file_paths[1]), "")

    # Deterministic active outbox manifest ID
    intake_material = {
        "operator_active_outbox_review_decision_id": operator_active_outbox_review_decision_id,
        "combined_payload_hash": combined_payload_hash,
        "blockers": blockers,
    }
    local_active_outbox_manifest_id = f"local_active_outbox_manifest_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("local_active_outbox_creation_blocked_pending_operator_repair")

    return LocalActiveOutboxManifest(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        local_active_outbox_manifest_id=local_active_outbox_manifest_id,
        operator_active_outbox_review_decision_id=operator_active_outbox_review_decision_id,
        operator_review_decision_sha256=operator_review_decision_sha256,
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
        active_outbox_dir=active_outbox_dir,
        active_outbox_entries=active_outbox_entries,
        active_outbox_payload_files=active_outbox_payload_files,
        active_outbox_payload_file_hashes=active_outbox_payload_file_hashes,
        source_staged_payload_file_hashes=decision_staged_file_hashes,
        combined_payload_hash=combined_payload_hash,
        local_active_outbox_created=available,
        active_outbox_entry_created=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_local_active_outbox(
    manifest: LocalActiveOutboxManifest,
    decision_packet: dict,
    staged_file_paths: list[Path],
    staged_file_texts: dict[str, str],
    output_dir: Path,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Write manifest first
    manifest_path = out_path / f"{manifest.local_active_outbox_manifest_id}.json"
    manifest_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not manifest.local_active_outbox_created:
        return manifest_path

    # Copy files into active outbox directory
    active_outbox_dir_path = Path(manifest.active_outbox_dir)
    active_outbox_dir_path.mkdir(parents=True, exist_ok=True)

    # Copy payloads
    for path in staged_file_paths:
        npath = _normalize_path(path)
        text = None
        for k, v in staged_file_texts.items():
            if _normalize_path(k) == npath:
                text = v
                break
        
        target_name = "substack_payload.md" if "substack" in path.name.lower() else "discord_payload.md"
        target_path = active_outbox_dir_path / target_name
        target_path.write_text(text, encoding="utf-8")

    # Generate outbox entry JSON files
    for platform in ["substack", "discord"]:
        p_file = manifest.active_outbox_payload_files[0] if platform == "substack" else manifest.active_outbox_payload_files[1]
        p_sha = manifest.active_outbox_payload_file_hashes[p_file]
        
        src_file = _normalize_path(staged_file_paths[0]) if platform == "substack" else _normalize_path(staged_file_paths[1])
        src_sha = manifest.source_staged_payload_file_hashes[src_file]
        
        entry = ActiveOutboxEntry(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            active_outbox_entry_id=f"active_outbox_entry_{platform}_{hashlib.sha256((platform + manifest.local_active_outbox_manifest_id).encode('utf-8')).hexdigest()[:16]}",
            platform=platform,
            payload_file=p_file,
            payload_sha256=p_sha,
            source_staged_payload_file=src_file,
            source_staged_payload_sha256=src_sha,
            combined_payload_hash=manifest.combined_payload_hash,
            operator_active_outbox_review_decision_id=manifest.operator_active_outbox_review_decision_id,
            active_outbox_eligibility_id=manifest.active_outbox_eligibility_id,
            outbox_package_staging_id=manifest.outbox_package_staging_id,
            canonical_slug=manifest.canonical_slug,
            canonical_title=manifest.canonical_title,
            entry_status="local_active_outbox_pending_dispatch_review",
        )
        
        entry_name = f"{platform}_outbox_entry.json"
        entry_path = active_outbox_dir_path / entry_name
        entry_path.write_text(json.dumps(asdict(entry), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local active outbox creation contract")
    parser.add_argument("decision_packet")
    parser.add_argument("--staged-files", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    try:
        decision = load_json_packet(Path(args.decision_packet), "malformed_operator_review_decision_json")
        staged_paths = [Path(p) for p in args.staged_files]
        staged_texts: dict[str, str] = {}
        for path in staged_paths:
            text = load_text_file(path, f"preview_file_text_missing_{path.name}")
            staged_texts[str(path)] = text
    except ValueError as exc:
        blocker = str(exc)
        manifest = LocalActiveOutboxManifest(
            schema_version=SCHEMA_VERSION,
            task_label=TASK_LABEL,
            local_active_outbox_manifest_id="local_active_outbox_manifest_blocked",
            operator_active_outbox_review_decision_id="",
            operator_review_decision_sha256="",
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
            active_outbox_dir="",
            active_outbox_entries=[],
            active_outbox_payload_files=[],
            active_outbox_payload_file_hashes={},
            source_staged_payload_file_hashes={},
            combined_payload_hash="",
            local_active_outbox_created=False,
            active_outbox_entry_created=False,
            blockers=[blocker],
            warnings=["local_active_outbox_creation_blocked_pending_operator_repair"],
        )
        out_path = Path(args.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        manifest_path = out_path / f"{manifest.local_active_outbox_manifest_id}.json"
        manifest_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    manifest = make_local_active_outbox_manifest(decision, staged_paths, staged_texts, Path(args.output_dir))
    write_local_active_outbox(manifest, decision, staged_paths, staged_texts, Path(args.output_dir))

    return 1 if manifest.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
