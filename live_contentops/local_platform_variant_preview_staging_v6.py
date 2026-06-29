"""V6 Local Platform Variant Preview Staging from Metadata Values."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SOURCE_TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_METADATA_VALUES_INTAKE_FROM_METADATA_PROPOSAL_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_LOCAL_PLATFORM_VARIANT_PREVIEW_STAGING_FROM_METADATA_VALUES_V0"
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
class VariantPreviewStagingPacket:
    schema_version: str
    task_label: str
    variant_preview_staging_id: str
    metadata_values_review_id: str
    metadata_values_review_sha256: str
    metadata_values_id: str
    metadata_proposal_id: str
    source_pack_intake_id: str
    source_pack_id: str
    editorial_workflow_id: str
    canonical_slug: str
    canonical_title: str
    preview_platforms: list[str]
    preview_files: list[str]
    variant_preview_staging_available: bool
    variant_previews_generated: bool
    preview_only: bool = True
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
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


def load_markdown(path: Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("markdown_decode_failed") from exc
    except OSError as exc:
        raise ValueError("markdown_missing") from exc


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


def _validate_metadata_text_claims(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    fields_to_scan = [
        "canonical_title",
        "canonical_slug",
        "meta_description",
        "editorial_summary",
        "intended_search_intent",
    ]
    
    texts_to_scan: list[str] = []
    for fld in fields_to_scan:
        val = packet.get(fld)
        if isinstance(val, str):
            texts_to_scan.append(val)
            
    focus_kws = packet.get("focus_keywords")
    if isinstance(focus_kws, list):
        for kw in focus_kws:
            if isinstance(kw, str):
                texts_to_scan.append(kw)
                
    for text in texts_to_scan:
        lowered = text.lower()
        
        # Prohibited claims
        for marker in PUBLIC_READY_MARKERS:
            if marker in lowered:
                blockers.append(f"metadata_public_ready_or_approval_claim_detected_{marker}")
        for marker in FAKE_CLAIMS_MARKERS:
            if marker in lowered:
                blockers.append(f"metadata_fake_readiness_or_metrics_claim_detected_{marker}")
        for marker in CITATION_CLAIMS_MARKERS:
            if marker in lowered:
                blockers.append(f"metadata_citations_verified_or_generated_claim_detected_{marker}")

        # Trading/financial advice checks
        for rx in TRADING_ADVICE_RE:
            if rx.search(lowered):
                blockers.append("metadata_financial_advice_or_signal_framing_detected")
                break

        # Dispatch instructions check
        dispatch_instructions = ["dispatch_allowed: true", "publish: true", "supervised_dispatch"]
        if any(inst in lowered for inst in dispatch_instructions):
            blockers.append("metadata_live_dispatch_instructions_detected")

    return blockers


def _validate_metadata_values_review(packet: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if packet.get("task_label") != SOURCE_TASK_LABEL:
        blockers.append("metadata_task_label_invalid")
    if packet.get("metadata_values_available_for_editorial_review") is not True:
        blockers.append("metadata_not_available")
    if packet.get("metadata_values_finalized") is not False:
        blockers.append("metadata_finalized_not_false")
    if packet.get("generated_by_llm") is not False:
        blockers.append("metadata_generated_by_llm_not_false")
    if packet.get("operator_supplied") is not True:
        blockers.append("metadata_operator_supplied_not_true")
    if packet.get("generated_citations_allowed") is not False:
        blockers.append("metadata_generated_citations_allowed_not_false")
    if packet.get("citations_verified") is not False:
        blockers.append("metadata_citations_verified_not_false")
    
    blockers.extend(_check_public_and_live_fields(packet, "metadata"))
    
    if packet.get("review_only") is not True:
        blockers.append("metadata_review_only_not_true")
    if packet.get("human_review_required") is not True:
        blockers.append("metadata_human_review_required_not_true")
    if packet.get("kill_switch_active") is not True:
        blockers.append("metadata_kill_switch_active_not_true")
    if packet.get("runtime_truth") is not False:
        blockers.append("metadata_runtime_truth_not_false")
    if packet.get("blockers"):
        blockers.append("metadata_has_blockers")

    required_keys = ["metadata_values_id", "metadata_proposal_id", "metadata_proposal_sha256", "source_pack_intake_id", "source_pack_id", "editorial_workflow_id"]
    for key in required_keys:
        if not packet.get(key):
            blockers.append(f"metadata_{key}_missing")

    required_values = ["canonical_title", "canonical_slug", "meta_description", "focus_keywords", "editorial_summary", "intended_search_intent"]
    for val in required_values:
        if not packet.get(val):
            blockers.append(f"metadata_{val}_missing_or_empty")

    # Only run claim scans on metadata text fields if the required fields are present
    if not any(f"metadata_{val}_missing_or_empty" in blockers for val in required_values):
        blockers.extend(_validate_metadata_text_claims(packet))

    return blockers


def _validate_markdown_text(text: str) -> list[str]:
    blockers: list[str] = []
    if not text.strip():
        blockers.append("markdown_empty")
        return blockers

    # Scan for secret-like markers
    if _has_secret_marker(text):
        blockers.append("markdown_secret_marker_detected")

    lowered = text.lower()
    
    # Prohibited claims
    for marker in PUBLIC_READY_MARKERS:
        if marker in lowered:
            blockers.append(f"markdown_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"markdown_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in lowered:
            blockers.append(f"markdown_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(lowered):
            blockers.append("markdown_financial_advice_or_signal_framing_detected")
            break

    # Dispatch instructions check
    dispatch_instructions = ["dispatch_allowed: true", "publish: true", "supervised_dispatch"]
    if any(inst in lowered for inst in dispatch_instructions):
        blockers.append("markdown_live_dispatch_instructions_detected")

    return blockers


def make_variant_preview_staging_packet(
    metadata_values_review_packet: Any,
    markdown_text: str,
    output_dir: Path,
) -> VariantPreviewStagingPacket:
    blockers: list[str] = []

    metadata_is_dict = isinstance(metadata_values_review_packet, dict)
    if not metadata_is_dict:
        blockers.append("malformed_metadata_values_review_json")

    # Check secret markers
    if metadata_is_dict and _has_secret_marker(json.dumps(metadata_values_review_packet)):
        blockers.append("metadata_secret_marker_detected")
    
    # Process markdown blockers
    if isinstance(markdown_text, str):
        blockers.extend(_validate_markdown_text(markdown_text))
    else:
        blockers.append("markdown_not_string")

    metadata_values_review_id = ""
    metadata_values_id = ""
    metadata_proposal_id = ""
    source_pack_intake_id = ""
    source_pack_id = ""
    editorial_workflow_id = ""
    canonical_slug = ""
    canonical_title = ""
    metadata_values_review_sha256 = ""

    if metadata_is_dict and "metadata_secret_marker_detected" not in blockers:
        metadata_values_review_id = str(metadata_values_review_packet.get("metadata_values_review_id") or "")
        metadata_values_id = str(metadata_values_review_packet.get("metadata_values_id") or "")
        metadata_proposal_id = str(metadata_values_review_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(metadata_values_review_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(metadata_values_review_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(metadata_values_review_packet.get("editorial_workflow_id") or "")
        canonical_slug = str(metadata_values_review_packet.get("canonical_slug") or "")
        canonical_title = str(metadata_values_review_packet.get("canonical_title") or "")
        
        blockers.extend(_validate_metadata_values_review(metadata_values_review_packet))
        
        # Hardening: hash is computed only if no secrets are present
        temp_blockers = sorted(set(blockers))
        if "metadata_secret_marker_detected" not in temp_blockers and "markdown_secret_marker_detected" not in temp_blockers:
            metadata_values_review_sha256 = hashlib.sha256(_canonical_json(metadata_values_review_packet).encode("utf-8")).hexdigest()

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = "metadata_secret_marker_detected" in blockers or "markdown_secret_marker_detected" in blockers

    if has_secrets:
        metadata_values_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        metadata_proposal_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_intake_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        editorial_workflow_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_slug = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_title = "[REDACTED_SECRET_MARKER_DETECTED]"

    # Deterministic preview file paths (only if available)
    preview_platforms = ["substack", "discord"] if available else []
    preview_files: list[str] = []
    if available:
        preview_files = [
            str(Path(output_dir) / f"{canonical_slug}_substack_preview.md"),
            str(Path(output_dir) / f"{canonical_slug}_discord_preview.md"),
        ]

    # Deterministic ID
    intake_material = {
        "metadata_values_review_id": metadata_values_review_id,
        "metadata_values_review_sha256": metadata_values_review_sha256,
        "blockers": blockers,
    }
    variant_preview_staging_id = f"local_platform_variant_preview_staging_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("variant_preview_staging_blocked_pending_operator_repair")

    return VariantPreviewStagingPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        variant_preview_staging_id=variant_preview_staging_id,
        metadata_values_review_id=metadata_values_review_id,
        metadata_values_review_sha256=metadata_values_review_sha256,
        metadata_values_id=metadata_values_id,
        metadata_proposal_id=metadata_proposal_id,
        source_pack_intake_id=source_pack_intake_id,
        source_pack_id=source_pack_id,
        editorial_workflow_id=editorial_workflow_id,
        canonical_slug=canonical_slug,
        canonical_title=canonical_title,
        preview_platforms=preview_platforms,
        preview_files=preview_files,
        variant_preview_staging_available=available,
        variant_previews_generated=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_variant_preview_files(
    packet: VariantPreviewStagingPacket,
    metadata_values_review_packet: dict,
    markdown_text: str,
    output_dir: Path,
) -> list[Path]:
    if not packet.variant_preview_staging_available:
        return []

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    slug = metadata_values_review_packet["canonical_slug"]
    title = metadata_values_review_packet["canonical_title"]
    desc = metadata_values_review_packet["meta_description"]
    summary = metadata_values_review_packet["editorial_summary"]
    source_pack_id = metadata_values_review_packet["source_pack_id"]

    # 1. Substack Preview
    substack_content = f"""# {title}

<!--
META_DESCRIPTION: {desc}
-->

> **LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION**

## Editorial Summary
{summary}

## Canonical Draft Preview
{markdown_text}
"""
    substack_path = out_path / f"{slug}_substack_preview.md"
    substack_path.write_text(substack_content, encoding="utf-8")

    # 2. Discord Preview
    discord_content = f"""> **LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH**

**Community Drop Preview**
Title: {title}
Summary: {summary}

*Reminder: This content is grounded in operator source pack {source_pack_id}.*
"""
    discord_path = out_path / f"{slug}_discord_preview.md"
    discord_path.write_text(discord_content, encoding="utf-8")

    return [substack_path, discord_path]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 local platform variant preview staging contract")
    parser.add_argument("metadata_values_review_packet")
    parser.add_argument("canonical_article_draft")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    proposal = load_json_packet(Path(args.metadata_values_review_packet), "malformed_metadata_values_review_json")
    markdown_text = load_markdown(Path(args.canonical_article_draft))

    packet = make_variant_preview_staging_packet(proposal, markdown_text, Path(args.output_dir))
    write_variant_preview_files(packet, proposal, markdown_text, Path(args.output_dir))
    
    # Write the staging packet JSON
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    packet_path = output_path / f"{packet.variant_preview_staging_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
