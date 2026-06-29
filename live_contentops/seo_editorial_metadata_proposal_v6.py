"""V6 SEO Editorial Metadata Proposal Contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SOURCE_TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_PACK_INTAKE_FOR_EDITORIAL_WORKFLOW_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_SEO_EDITORIAL_METADATA_PROPOSAL_PACKET_FROM_SOURCE_PACK_INTAKE_V0"
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

DEFAULT_SEO_REVIEW_CHECKLIST = [
    "define_search_intent_later",
    "validate_title_against_article_later",
    "validate_slug_against_final_title_later",
    "validate_meta_description_against_final_article_later",
    "no_keyword_stuffing_review_required",
]

DEFAULT_EDITORIAL_METADATA_CHECKLIST = [
    "confirm_canonical_article_title_later",
    "confirm_subtitle_or_deck_later",
    "confirm_article_summary_later",
    "confirm_section_structure_later",
    "confirm_no_financial_advice_language",
]

DEFAULT_SOURCE_GROUNDING_CHECKLIST = [
    "source_pack_review_required",
    "verify_claims_before_metadata_finalization",
    "citations_not_verified_in_this_lane",
    "generated_citations_prohibited",
]

DEFAULT_RISK_REVIEW_CHECKLIST = [
    "no_fake_urls",
    "no_fake_metrics",
    "no_publication_readiness_claim",
    "no_dispatch_or_outbox_claim",
    "no_trading_signal_or_advice_framing",
]

DEFAULT_REQUIRED_OPERATOR_ACTIONS = [
    "review_source_pack_quality",
    "confirm_editorial_direction",
    "approve_future_metadata_generation_gate",
    "approve_future_canonical_article_gate",
]

DEFAULT_PROPOSED_SLUG_POLICY = "future_human_or_llm_editorial_slug_must_be_lowercase_hyphenated_alphanumeric"
DEFAULT_PROPOSED_TITLE_POLICY = "future_human_or_llm_editorial_title_must_reflect_h1_and_contain_focus_keywords"
DEFAULT_PROPOSED_DESCRIPTION_POLICY = "future_human_or_llm_editorial_description_must_summarize_accurately_without_hype"
DEFAULT_PROPOSED_KEYWORD_POLICY = "future_human_or_llm_editorial_keywords_must_align_with_grounding_sources"


@dataclass(frozen=True)
class SeoEditorialMetadataProposalPacket:
    schema_version: str
    task_label: str
    metadata_proposal_id: str
    source_pack_intake_id: str
    source_pack_intake_sha256: str
    source_pack_id: str
    editorial_workflow_id: str
    metadata_proposal_available: bool
    proposal_status: str
    seo_review_checklist: list[str]
    editorial_metadata_checklist: list[str]
    source_grounding_checklist: list[str]
    risk_review_checklist: list[str]
    required_operator_actions: list[str]
    proposed_slug_policy: str
    proposed_title_policy: str
    proposed_description_policy: str
    proposed_keyword_policy: str
    generated_metadata_values: None = None
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


def load_source_pack_intake_packet(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("malformed_source_pack_intake_json") from exc


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


def _validate_source_pack_intake(intake: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if intake.get("task_label") != SOURCE_TASK_LABEL:
        blockers.append("intake_task_label_invalid")
    if intake.get("source_pack_intake_available") is not True:
        blockers.append("intake_not_available")
    if intake.get("source_grounding_available_for_editorial_review") is not True:
        blockers.append("intake_grounding_not_available")
    if intake.get("blockers"):
        blockers.append("intake_has_blockers")
    if intake.get("generated_citations_allowed") is not False:
        blockers.append("intake_generated_citations_allowed_not_false")
    if intake.get("citations_verified") is not False:
        blockers.append("intake_citations_verified_not_false")
    blockers.extend(_check_public_and_live_fields(intake, "intake"))
    if intake.get("review_only") is not True:
        blockers.append("intake_review_only_not_true")
    if intake.get("human_review_required") is not True:
        blockers.append("intake_human_review_required_not_true")
    if intake.get("kill_switch_active") is not True:
        blockers.append("intake_kill_switch_active_not_true")
    if intake.get("runtime_truth") is not False:
        blockers.append("intake_runtime_truth_not_false")

    required_keys = ["source_pack_id", "editorial_workflow_id", "source_editorial_workflow_sha256", "source_pack_manifest_sha256"]
    for key in required_keys:
        if not intake.get(key):
            blockers.append(f"intake_{key}_missing")

    sources_count = intake.get("sources_count")
    if not isinstance(sources_count, int) or sources_count <= 0:
        blockers.append("intake_sources_count_invalid")

    for array_key in ["source_ids", "source_types", "evidence_roles"]:
        val = intake.get(array_key)
        if not isinstance(val, list) or not val:
            blockers.append(f"intake_{array_key}_missing_or_empty")

    import copy
    intake_copy = copy.deepcopy(intake)
    
    # Remove standard output fields of the intake schema that contain ready markers
    schema_fields_to_remove = [
        "approved_canonical_article_available",
        "publication_ready",
        "dispatch_allowed",
        "platform_variant_generation_allowed",
        "outbox_creation_allowed",
        "public_url",
        "public_metrics",
        "generated_citations_allowed",
        "citations_verified",
    ]
    for key in schema_fields_to_remove:
        if key in intake_copy:
            del intake_copy[key]

    if isinstance(intake_copy.get("source_types"), list):
        intake_copy["source_types"] = [
            "safe_enum" if t == "public_url_reference" else t
            for t in intake_copy["source_types"]
        ]

    text_repr = _canonical_json(intake_copy).lower()
    for marker in PUBLIC_READY_MARKERS:
        if marker in text_repr:
            blockers.append(f"intake_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in text_repr:
            blockers.append(f"intake_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in text_repr:
            blockers.append(f"intake_citations_verified_or_generated_claim_detected_{marker}")

    return blockers


def make_metadata_proposal_packet(source_pack_intake_packet: Any) -> SeoEditorialMetadataProposalPacket:
    blockers: list[str] = []
    
    intake_is_dict = isinstance(source_pack_intake_packet, dict)
    if not intake_is_dict:
        blockers.append("malformed_source_pack_intake_json")

    if intake_is_dict and _has_secret_marker(source_pack_intake_packet):
        blockers.append("intake_secret_marker_detected")

    source_pack_intake_id = ""
    source_pack_id = ""
    editorial_workflow_id = ""
    source_pack_intake_sha256 = ""

    if intake_is_dict and "intake_secret_marker_detected" not in blockers:
        source_pack_intake_id = str(source_pack_intake_packet.get("source_pack_intake_id") or "")
        source_pack_id = str(source_pack_intake_packet.get("source_pack_id") or "")
        editorial_workflow_id = str(source_pack_intake_packet.get("editorial_workflow_id") or "")
        blockers.extend(_validate_source_pack_intake(source_pack_intake_packet))
        
        # Recalculate blockers list after validation
        temp_blockers = sorted(set(blockers))
        if "intake_secret_marker_detected" not in temp_blockers:
            source_pack_intake_sha256 = hashlib.sha256(_canonical_json(source_pack_intake_packet).encode("utf-8")).hexdigest()

    blockers = sorted(set(blockers))
    available = not blockers
    proposal_status = "METADATA_PROPOSAL_READY_FOR_OPERATOR_REVIEW" if available else "METADATA_PROPOSAL_BLOCKED_PENDING_OPERATOR_REPAIR"

    intake_material = {
        "source_pack_intake_id": source_pack_intake_id,
        "source_pack_id": source_pack_id,
        "editorial_workflow_id": editorial_workflow_id,
        "source_pack_intake_sha256": source_pack_intake_sha256,
        "blockers": blockers,
    }
    metadata_proposal_id = f"seo_editorial_metadata_proposal_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("metadata_proposal_blocked_pending_operator_repair")

    return SeoEditorialMetadataProposalPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        metadata_proposal_id=metadata_proposal_id,
        source_pack_intake_id=source_pack_intake_id,
        source_pack_intake_sha256=source_pack_intake_sha256,
        source_pack_id=source_pack_id,
        editorial_workflow_id=editorial_workflow_id,
        metadata_proposal_available=available,
        proposal_status=proposal_status,
        seo_review_checklist=list(DEFAULT_SEO_REVIEW_CHECKLIST),
        editorial_metadata_checklist=list(DEFAULT_EDITORIAL_METADATA_CHECKLIST),
        source_grounding_checklist=list(DEFAULT_SOURCE_GROUNDING_CHECKLIST),
        risk_review_checklist=list(DEFAULT_RISK_REVIEW_CHECKLIST),
        required_operator_actions=list(DEFAULT_REQUIRED_OPERATOR_ACTIONS),
        proposed_slug_policy=DEFAULT_PROPOSED_SLUG_POLICY,
        proposed_title_policy=DEFAULT_PROPOSED_TITLE_POLICY,
        proposed_description_policy=DEFAULT_PROPOSED_DESCRIPTION_POLICY,
        proposed_keyword_policy=DEFAULT_PROPOSED_KEYWORD_POLICY,
        blockers=blockers,
        warnings=warnings,
    )


def write_metadata_proposal_packet(packet: SeoEditorialMetadataProposalPacket, output_dir: Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    packet_path = output_path / f"{packet.metadata_proposal_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 SEO/editorial metadata proposal contract")
    parser.add_argument("source_pack_intake_packet")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    intake = load_source_pack_intake_packet(Path(args.source_pack_intake_packet))
    packet = make_metadata_proposal_packet(intake)
    write_metadata_proposal_packet(packet, Path(args.output_dir))
    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
