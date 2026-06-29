"""V6 Operator Source Pack Intake for Editorial Workflow."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SOURCE_WORKFLOW_TASK_LABEL = "TASK_CONTENTOPS_V6_ACCEPTED_REVIEW_EDITORIAL_WORKFLOW_PACKET_CONTRACT_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_PACK_INTAKE_FOR_EDITORIAL_WORKFLOW_V0"
SCHEMA_VERSION = "6.0.0"

WORKFLOW_STATUS_READY = "EDITORIAL_WORKFLOW_PACKET_READY_FOR_OPERATOR_REVIEW"
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

ALLOWED_SOURCE_TYPES = {
    "operator_note",
    "local_markdown",
    "local_pdf_reference",
    "local_data_reference",
    "public_url_reference",
    "citation_to_verify_later",
    "other_reference",
}

ALLOWED_EVIDENCE_ROLES = {
    "thesis_support",
    "factual_claim_support",
    "background_context",
    "counterpoint",
    "data_reference",
    "quote_to_verify_later",
    "risk_or_uncertainty",
}


@dataclass(frozen=True)
class SourcePackIntakePacket:
    schema_version: str
    task_label: str
    source_pack_intake_id: str
    source_pack_id: str
    operator_id: str
    created_at_manual: str
    source_pack_purpose: str
    editorial_workflow_id: str
    source_editorial_workflow_sha256: str
    source_pack_manifest_sha256: str
    sources_count: int
    source_ids: list[str]
    source_types: list[str]
    evidence_roles: list[str]
    source_pack_intake_available: bool
    source_grounding_available_for_editorial_review: bool
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


def _validate_editorial_workflow(workflow: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if workflow.get("task_label") != SOURCE_WORKFLOW_TASK_LABEL:
        blockers.append("workflow_task_label_invalid")
    if workflow.get("editorial_workflow_packet_available") is not True:
        blockers.append("workflow_packet_not_available")
    if workflow.get("workflow_status") != WORKFLOW_STATUS_READY:
        blockers.append("workflow_status_not_ready")
    if workflow.get("blockers"):
        blockers.append("workflow_has_blockers")
    blockers.extend(_check_public_and_live_fields(workflow, "workflow"))
    if workflow.get("review_only") is not True:
        blockers.append("workflow_review_only_not_true")
    if workflow.get("kill_switch_active") is not True:
        blockers.append("workflow_kill_switch_active_not_true")
    if workflow.get("runtime_truth") is not False:
        blockers.append("workflow_runtime_truth_not_false")
    for key in ("source_decision_id", "source_decision_sha256", "source_candidate_id", "editorial_workflow_id"):
        if not workflow.get(key):
            blockers.append(f"workflow_{key}_missing")
    return blockers


def _validate_source_pack_manifest(manifest: dict[str, Any], workflow_id: str) -> list[str]:
    blockers: list[str] = []
    required_top = [
        "schema_version",
        "source_pack_id",
        "operator_id",
        "created_at_manual",
        "source_pack_purpose",
        "editorial_workflow_id",
        "sources",
    ]
    for key in required_top:
        if key not in manifest or manifest[key] is None or manifest[key] == "":
            blockers.append(f"manifest_{key}_missing")

    if "editorial_workflow_id" in manifest and manifest["editorial_workflow_id"] != workflow_id:
        blockers.append("manifest_editorial_workflow_id_mismatch")

    sources = manifest.get("sources")
    if not isinstance(sources, list):
        blockers.append("manifest_sources_not_list")
        return blockers

    if not sources:
        blockers.append("manifest_sources_empty")
        return blockers

    required_source_fields = [
        "source_id",
        "source_type",
        "title",
        "locator",
        "provided_by_operator",
        "evidence_role",
        "notes",
    ]

    for idx, item in enumerate(sources):
        if not isinstance(item, dict):
            blockers.append(f"source_item_{idx}_not_dict")
            continue
        for fld in required_source_fields:
            if fld not in item or item[fld] is None or item[fld] == "":
                blockers.append(f"source_item_{idx}_{fld}_missing")

        source_type = item.get("source_type")
        if source_type and source_type not in ALLOWED_SOURCE_TYPES:
            blockers.append(f"source_item_{idx}_source_type_invalid")

        evidence_role = item.get("evidence_role")
        if evidence_role and evidence_role not in ALLOWED_EVIDENCE_ROLES:
            blockers.append(f"source_item_{idx}_evidence_role_invalid")

        if item.get("provided_by_operator") is not True:
            blockers.append(f"source_item_{idx}_provided_by_operator_not_true")

        if "locator" in item and not item["locator"]:
            blockers.append(f"source_item_{idx}_locator_empty")

    import copy
    manifest_copy = copy.deepcopy(manifest)
    if isinstance(manifest_copy.get("sources"), list):
        for item in manifest_copy["sources"]:
            if isinstance(item, dict) and "source_type" in item:
                item["source_type"] = "safe_enum"

    text_repr = _canonical_json(manifest_copy).lower()
    for marker in PUBLIC_READY_MARKERS:
        if marker in text_repr:
            blockers.append(f"source_pack_public_ready_or_approval_claim_detected_{marker}")
    for marker in FAKE_CLAIMS_MARKERS:
        if marker in text_repr:
            blockers.append(f"source_pack_fake_readiness_or_metrics_claim_detected_{marker}")
    for marker in CITATION_CLAIMS_MARKERS:
        if marker in text_repr:
            blockers.append(f"source_pack_citations_verified_or_generated_claim_detected_{marker}")

    return blockers


def make_source_pack_intake_packet(
    editorial_workflow_packet: Any,
    source_pack_manifest: Any,
) -> SourcePackIntakePacket:
    blockers: list[str] = []

    workflow_is_dict = isinstance(editorial_workflow_packet, dict)
    manifest_is_dict = isinstance(source_pack_manifest, dict)

    if not workflow_is_dict:
        blockers.append("malformed_workflow_json")
    if not manifest_is_dict:
        blockers.append("malformed_source_pack_json")

    if workflow_is_dict and _has_secret_marker(editorial_workflow_packet):
        blockers.append("workflow_secret_marker_detected")
    if manifest_is_dict and _has_secret_marker(source_pack_manifest):
        blockers.append("manifest_secret_marker_detected")

    workflow_id = ""
    if workflow_is_dict and "workflow_secret_marker_detected" not in blockers:
        workflow_id = str(editorial_workflow_packet.get("editorial_workflow_id") or "")
        blockers.extend(_validate_editorial_workflow(editorial_workflow_packet))

    if manifest_is_dict and "manifest_secret_marker_detected" not in blockers:
        blockers.extend(_validate_source_pack_manifest(source_pack_manifest, workflow_id))

    blockers = sorted(set(blockers))
    available = not blockers

    has_secrets = "workflow_secret_marker_detected" in blockers or "manifest_secret_marker_detected" in blockers

    source_pack_id = ""
    operator_id = ""
    created_at_manual = ""
    source_pack_purpose = ""
    sources_count = 0
    source_ids: list[str] = []
    source_types: list[str] = []
    evidence_roles: list[str] = []

    if manifest_is_dict and not has_secrets:
        source_pack_id = str(source_pack_manifest.get("source_pack_id") or "")
        operator_id = str(source_pack_manifest.get("operator_id") or "")
        created_at_manual = str(source_pack_manifest.get("created_at_manual") or "")
        source_pack_purpose = str(source_pack_manifest.get("source_pack_purpose") or "")
        sources = source_pack_manifest.get("sources")
        if isinstance(sources, list):
            sources_count = len(sources)
            for item in sources:
                if isinstance(item, dict):
                    source_ids.append(str(item.get("source_id") or ""))
                    source_types.append(str(item.get("source_type") or ""))
                    evidence_roles.append(str(item.get("evidence_role") or ""))
    elif has_secrets:
        source_pack_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        operator_id = "[REDACTED_SECRET_MARKER_DETECTED]"
        created_at_manual = "[REDACTED_SECRET_MARKER_DETECTED]"
        source_pack_purpose = "[REDACTED_SECRET_MARKER_DETECTED]"

    source_editorial_workflow_sha256 = ""
    if workflow_is_dict and "workflow_secret_marker_detected" not in blockers:
        source_editorial_workflow_sha256 = hashlib.sha256(_canonical_json(editorial_workflow_packet).encode("utf-8")).hexdigest()

    source_pack_manifest_sha256 = ""
    if manifest_is_dict and "manifest_secret_marker_detected" not in blockers:
        source_pack_manifest_sha256 = hashlib.sha256(_canonical_json(source_pack_manifest).encode("utf-8")).hexdigest()

    intake_material = {
        "editorial_workflow_id": workflow_id,
        "source_pack_id": source_pack_id,
        "source_editorial_workflow_sha256": source_editorial_workflow_sha256,
        "source_pack_manifest_sha256": source_pack_manifest_sha256,
        "blockers": blockers,
    }
    source_pack_intake_id = f"operator_source_pack_intake_{hashlib.sha256(_canonical_json(intake_material).encode('utf-8')).hexdigest()[:16]}"

    warnings = []
    if not available:
        warnings.append("source_pack_intake_blocked_pending_operator_repair")

    return SourcePackIntakePacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        source_pack_intake_id=source_pack_intake_id,
        source_pack_id=source_pack_id,
        operator_id=operator_id,
        created_at_manual=created_at_manual,
        source_pack_purpose=source_pack_purpose,
        editorial_workflow_id=workflow_id,
        source_editorial_workflow_sha256=source_editorial_workflow_sha256,
        source_pack_manifest_sha256=source_pack_manifest_sha256,
        sources_count=sources_count,
        source_ids=source_ids,
        source_types=source_types,
        evidence_roles=evidence_roles,
        source_pack_intake_available=available,
        source_grounding_available_for_editorial_review=available,
        blockers=blockers,
        warnings=warnings,
    )


def write_source_pack_intake_packet(packet: SourcePackIntakePacket, output_dir: Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    packet_path = output_path / f"{packet.source_pack_intake_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 operator source pack intake contract")
    parser.add_argument("editorial_workflow_packet")
    parser.add_argument("source_pack_manifest")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    workflow = load_json_packet(Path(args.editorial_workflow_packet), "malformed_workflow_json")
    manifest = load_json_packet(Path(args.source_pack_manifest), "malformed_source_pack_json")

    packet = make_source_pack_intake_packet(workflow, manifest)
    write_source_pack_intake_packet(packet, Path(args.output_dir))
    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())