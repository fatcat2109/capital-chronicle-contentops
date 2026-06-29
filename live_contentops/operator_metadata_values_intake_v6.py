"""V6 Operator Metadata Values Intake from Metadata Proposal."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SOURCE_PROPOSAL_TASK_LABEL = "TASK_CONTENTOPS_V6_SEO_EDITORIAL_METADATA_PROPOSAL_PACKET_FROM_SOURCE_PACK_INTAKE_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_METADATA_VALUES_INTAKE_FROM_METADATA_PROPOSAL_V0"
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
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass(frozen=True)
class MetadataValuesReviewPacket:
    schema_version: str
    task_label: str
    metadata_values_review_id: str
    metadata_values_id: str
    metadata_proposal_id: str
    metadata_proposal_sha256: str
    source_pack_intake_id: str
    source_pack_id: str
    editorial_workflow_id: str
    operator_id: str
    created_at_manual: str
    canonical_title: str
    canonical_slug: str
    meta_description: str
    focus_keywords: list[str]
    editorial_summary: str
    intended_search_intent: str
    metadata_values_available_for_editorial_review: bool
    metadata_values_finalized: bool = False
    generated_by_llm: bool = False
    operator_supplied: bool = False
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


def _has_secret_marker(value: Any) -> bool:
    text = value.lower() if isinstance(value, str) else _canonical_json(value).lower()
    return any(marker in text for marker in SECRET_MARKERS)


def load_json_packet(path: Path, malformed_label: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(malformed_label) from exc


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


def _validate_proposal(proposal: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if proposal.get("task_label") != SOURCE_PROPOSAL_TASK_LABEL:
        blockers.append("proposal_task_label_invalid")
    if proposal.get("metadata_proposal_available") is not True:
        blockers.append("proposal_not_available")
    if proposal.get("proposal_status") != "METADATA_PROPOSAL_READY_FOR_OPERATOR_REVIEW":
        blockers.append("proposal_status_not_ready")
    if proposal.get("blockers"):
        blockers.append("proposal_has_blockers")
    
    gen_val = proposal.get("generated_metadata_values")
    if gen_val is not None and gen_val != "" and gen_val != {}:
        blockers.append("proposal_generated_metadata_values_not_empty")

    if proposal.get("generated_citations_allowed") is not False:
        blockers.append("proposal_generated_citations_allowed_not_false")
    if proposal.get("citations_verified") is not False:
        blockers.append("proposal_citations_verified_not_false")
    
    blockers.extend(_check_public_and_live_fields(proposal, "proposal"))
    
    if proposal.get("review_only") is not True:
        blockers.append("proposal_review_only_not_true")
    if proposal.get("human_review_required") is not True:
        blockers.append("proposal_human_review_required_not_true")
    if proposal.get("kill_switch_active") is not True:
        blockers.append("proposal_kill_switch_active_not_true")
    if proposal.get("runtime_truth") is not False:
        blockers.append("proposal_runtime_truth_not_false")

    required_keys = ["source_pack_intake_id", "source_pack_intake_sha256", "source_pack_id", "editorial_workflow_id"]
    for key in required_keys:
        if not proposal.get(key):
            blockers.append(f"proposal_{key}_missing")

    return blockers


def _validate_values(values: dict[str, Any], proposal_id: str) -> list[str]:
    blockers: list[str] = []
    required_keys = [
        "schema_version",
        "metadata_values_id",
        "operator_id",
        "created_at_manual",
        "metadata_proposal_id",
        "canonical_title",
        "canonical_slug",
        "meta_description",
        "focus_keywords",
        "editorial_summary",
        "intended_search_intent",
    ]
    for key in required_keys:
        if key not in values or values[key] is None or values[key] == "":
            blockers.append(f"values_{key}_missing")

    if "notes" not in values or values["notes"] is None:
        blockers.append("values_notes_missing")
    elif not isinstance(values["notes"], str):
        blockers.append("values_notes_not_string")

    if "metadata_proposal_id" in values and values["metadata_proposal_id"] != proposal_id:
        blockers.append("values_metadata_proposal_id_mismatch")

    # Length & format rules
    title = values.get("canonical_title")
    if isinstance(title, str):
        if not (20 <= len(title) <= 120):
            blockers.append("values_canonical_title_length_invalid")
    elif title is not None:
        blockers.append("values_canonical_title_not_string")

    slug = values.get("canonical_slug")
    if isinstance(slug, str):
        if not (3 <= len(slug) <= 90):
            blockers.append("values_canonical_slug_length_invalid")
        if not SLUG_RE.match(slug) or "http" in slug or "://" in slug:
            blockers.append("values_canonical_slug_format_invalid")
    elif slug is not None:
        blockers.append("values_canonical_slug_not_string")

    description = values.get("meta_description")
    if isinstance(description, str):
        if not (70 <= len(description) <= 180):
            blockers.append("values_meta_description_length_invalid")
    elif description is not None:
        blockers.append("values_meta_description_not_string")

    keywords = values.get("focus_keywords")
    if isinstance(keywords, list):
        if not (1 <= len(keywords) <= 10):
            blockers.append("values_focus_keywords_count_invalid")
        for idx, kw in enumerate(keywords):
            if not isinstance(kw, str) or not (2 <= len(kw) <= 60):
                blockers.append(f"values_focus_keyword_{idx}_invalid")
    elif keywords is not None:
        blockers.append("values_focus_keywords_not_list")

    summary = values.get("editorial_summary")
    if isinstance(summary, str):
        if not (30 <= len(summary) <= 500):
            blockers.append("values_editorial_summary_length_invalid")
    elif summary is not None:
        blockers.append("values_editorial_summary_not_string")

    intent = values.get("intended_search_intent")
    if isinstance(intent, str):
        if not (10 <= len(intent) <= 300):
            blockers.append("values_intended_search_intent_length_invalid")
    elif intent is not None:
        blockers.append("values_intended_search_intent_not_string")

    # Scan for claims and advice
    text_repr = _canonical_json(values).lower()
    for marker in PUBLIC_READY_MARKERS:
        if marker in text_repr:
            blockers.append(f"values_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in text_repr:
            blockers.append(f"values_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in text_repr:
            blockers.append(f"values_citations_verified_or_generated_claim_detected_{marker}")

    # Trading/financial advice checks
    for rx in TRADING_ADVICE_RE:
        if rx.search(text_repr):
            blockers.append("values_financial_advice_or_signal_framing_detected")
            break

    return blockers


def make_metadata_values_review_packet(
    metadata_proposal_packet: Any,
    metadata_values: Any,
) -> MetadataValuesReviewPacket:
    blockers: list[str] = []

    proposal_is_dict = isinstance(metadata_proposal_packet, dict)
    values_is_dict = isinstance(metadata_values, dict)

    if not proposal_is_dict:
        blockers.append("malformed_metadata_proposal_json")
    if not values_is_dict:
        blockers.append("malformed_operator_metadata_values_json")

    if proposal_is_dict and _has_secret_marker(metadata_proposal_packet):
        blockers.append("proposal_secret_marker_detected")
    if values_is_dict and _has_secret_marker(metadata_values):
        blockers.append("values_secret_marker_detected")

    proposal_id = ""
    source_pack_intake_id = ""
    source_pack_id = ""
    editorial_workflow_id = ""
    metadata_proposal_sha256 = ""

    if proposal_is_dict and "proposal_secret_marker_detected" not in blockers:
        proposal_id = str(metadata_proposal_packet.get("metadata_proposal_id") or "")
        source_pack_intake_id = str(metadata_proposal_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(metadata_proposal_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(metadata_proposal_packet.get("editorial_workflow_id") or "")
        blockers.extend(_validate_proposal(metadata_proposal_packet))
        
        # Hardening: hash is computed only if no secrets are present
        temp_proposal_blockers = sorted(set(blockers))
        if "proposal_secret_marker_detected" not in temp_proposal_blockers:
            metadata_proposal_sha256 = hashlib.sha256(_canonical_json(metadata_proposal_packet).encode("utf-8")).hexdigest()

    if values_is_dict and "values_secret_marker_detected" not in blockers:
        blockers.extend(_validate_values(metadata_values, proposal_id))

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = "proposal_secret_marker_detected" in blockers or "values_secret_marker_detected" in blockers

    metadata_values_id = ""
    operator_id = ""
    created_at_manual = ""
    canonical_title = ""
    canonical_slug = ""
    meta_description = ""
    focus_keywords: list[str] = []
    editorial_summary = ""
    intended_search_intent = ""

    if values_is_dict and not has_secrets:
        metadata_values_id = str(metadata_values.get("metadata_values_id") or "")
        operator_id = str(metadata_values.get("operator_id") or "")
        created_at_manual = str(metadata_values.get("created_at_manual") or "")
        canonical_title = str(metadata_values.get("canonical_title") or "")
        canonical_slug = str(metadata_values.get("canonical_slug") or "")
        meta_description = str(metadata_values.get("meta_description") or "")
        editorial_summary = str(metadata_values.get("editorial_summary") or "")
        intended_search_intent = str(metadata_values.get("intended_search_intent") or "")
        kws = metadata_values.get("focus_keywords")
        if isinstance(kws, list):
            focus_keywords = [str(x) for x in kws]
    elif has_secrets:
        metadata_values_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_title = "[REDACTED_SECRET_MARKER_DETECTED]"
        canonical_slug = "[REDACTED_SECRET_MARKER_DETECTED]"
        meta_description = "[REDACTED_SECRET_MARKER_DETECTED]"
        editorial_summary = "[REDACTED_SECRET_MARKER_DETECTED]"
        intended_search_intent = "[REDACTED_SECRET_MARKER_DETECTED]"

    # Deterministic packet ID
    intake_material = {
        "metadata_proposal_id": proposal_id,
        "metadata_values_id": metadata_values_id,
        "metadata_proposal_sha256": metadata_proposal_sha256,
        "blockers": blockers,
    }
    metadata_values_review_id = f"operator_metadata_values_review_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("metadata_values_review_blocked_pending_operator_repair")

    return MetadataValuesReviewPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        metadata_values_review_id=metadata_values_review_id,
        metadata_values_id=metadata_values_id,
        metadata_proposal_id=proposal_id,
        metadata_proposal_sha256=metadata_proposal_sha256,
        source_pack_intake_id=source_pack_intake_id,
        source_pack_id=source_pack_id,
        editorial_workflow_id=editorial_workflow_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        canonical_title=canonical_title,
        canonical_slug=canonical_slug,
        meta_description=meta_description,
        focus_keywords=focus_keywords,
        editorial_summary=editorial_summary,
        intended_search_intent=intended_search_intent,
        metadata_values_available_for_editorial_review=available,
        operator_supplied=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_metadata_values_review_packet(packet: MetadataValuesReviewPacket, output_dir: Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    packet_path = output_path / f"{packet.metadata_values_review_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 operator metadata values intake contract")
    parser.add_argument("metadata_proposal_packet")
    parser.add_argument("operator_metadata_values")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    proposal = load_json_packet(Path(args.metadata_proposal_packet), "malformed_metadata_proposal_json")
    values = load_json_packet(Path(args.operator_metadata_values), "malformed_operator_metadata_values_json")

    packet = make_metadata_values_review_packet(proposal, values)
    write_metadata_values_review_packet(packet, Path(args.output_dir))
    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
