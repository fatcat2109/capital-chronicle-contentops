"""V6 accepted review editorial workflow packet contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SOURCE_TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_HUMAN_REVIEW_DECISION_CONTRACT_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_ACCEPTED_REVIEW_EDITORIAL_WORKFLOW_PACKET_CONTRACT_V0"
SCHEMA_VERSION = "6.0.0"
WORKFLOW_STATUS_READY = "EDITORIAL_WORKFLOW_PACKET_READY_FOR_OPERATOR_REVIEW"
WORKFLOW_STATUS_BLOCKED = "EDITORIAL_WORKFLOW_PACKET_BLOCKED_PENDING_OPERATOR_REPAIR"
SECRET_MARKERS = ("token", "api_key", "password", "bearer", "cookie", "webhook_url", "private_key", "secret", "credential")

DEFAULT_EDIT_CHECKLIST = [
    "structure_review_required",
    "clarity_review_required",
    "source_grounding_review_required",
    "no_financial_advice_review_required",
    "publication_approval_required_later",
]
DEFAULT_FACTUAL_REVIEW_QUEUE = [
    "verify_claims_against_operator_sources",
    "identify_missing_sources",
    "flag_unsupported_numbers_or_dates",
    "flag_market_advice_language",
]
DEFAULT_SOURCE_GROUNDING_REQUIREMENTS = [
    "operator_source_pack_required",
    "citation_evidence_required_later",
    "no_generated_citations_allowed",
]
DEFAULT_REQUIRED_OPERATOR_ACTIONS = [
    "provide_or_confirm_source_pack",
    "complete_editorial_review",
    "explicitly_approve_canonical_article_in_future_gate",
]


@dataclass(frozen=True)
class EditorialWorkflowPacket:
    schema_version: str
    task_label: str
    editorial_workflow_id: str
    source_decision_id: str
    source_decision_sha256: str
    source_candidate_id: str
    workflow_status: str
    editorial_workflow_packet_available: bool
    edit_checklist: list[str]
    factual_review_queue: list[str]
    source_grounding_requirements: list[str]
    required_operator_actions: list[str]
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
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


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _has_secret_marker(value: Any) -> bool:
    text = value.lower() if isinstance(value, str) else _canonical_json(value).lower()
    return any(marker in text for marker in SECRET_MARKERS)


def load_review_decision_packet(path: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("malformed_decision_json") from exc


def _public_state_blockers(packet: dict[str, Any]) -> list[str]:
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
            blockers.append(f"decision_{field_name}_not_false")
    for field_name in null_fields:
        if packet.get(field_name) is not None:
            blockers.append(f"decision_{field_name}_not_null")
    return blockers


def _validation_blockers(decision_packet: Any) -> list[str]:
    if not isinstance(decision_packet, dict):
        return ["malformed_decision_json"]
    blockers: list[str] = []
    if decision_packet.get("task_label") != SOURCE_TASK_LABEL:
        blockers.append("decision_task_label_invalid")
    if decision_packet.get("decision") != "accept_for_editorial_workflow":
        blockers.append("decision_not_accept_for_editorial_workflow")
    if decision_packet.get("accepted_for_editorial_workflow") is not True:
        blockers.append("accepted_for_editorial_workflow_not_true")
    if decision_packet.get("rejected") is not False:
        blockers.append("decision_rejected_not_false")
    if decision_packet.get("deferred") is not False:
        blockers.append("decision_deferred_not_false")
    if decision_packet.get("blockers"):
        blockers.append("decision_has_blockers")
    blockers.extend(_public_state_blockers(decision_packet))
    if decision_packet.get("review_only") is not True:
        blockers.append("decision_review_only_not_true")
    if decision_packet.get("kill_switch_active") is not True:
        blockers.append("decision_kill_switch_active_not_true")
    if decision_packet.get("runtime_truth") is not False:
        blockers.append("decision_runtime_truth_not_false")
    if not decision_packet.get("source_candidate_id"):
        blockers.append("source_candidate_id_missing")
    if not decision_packet.get("source_candidate_sha256"):
        blockers.append("source_candidate_sha256_missing")
    if _has_secret_marker(decision_packet):
        blockers.append("decision_secret_marker_detected")
    return sorted(set(blockers))


def make_editorial_workflow_packet(decision_packet: dict[str, Any]) -> EditorialWorkflowPacket:
    blockers = _validation_blockers(decision_packet)
    is_dict = isinstance(decision_packet, dict)
    source_decision_id = str(decision_packet.get("decision_id") or "") if is_dict else ""
    source_candidate_id = str(decision_packet.get("source_candidate_id") or "") if is_dict else ""
    source_decision_sha256 = hashlib.sha256(_canonical_json(decision_packet).encode("utf-8")).hexdigest()
    workflow_material = {
        "source_decision_id": source_decision_id,
        "source_decision_sha256": source_decision_sha256,
        "source_candidate_id": source_candidate_id,
        "blockers": blockers,
    }
    workflow_id = f"accepted_review_editorial_workflow_{hashlib.sha256(_canonical_json(workflow_material).encode('utf-8')).hexdigest()[:16]}"
    available = not blockers
    return EditorialWorkflowPacket(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        editorial_workflow_id=workflow_id,
        source_decision_id=source_decision_id,
        source_decision_sha256=source_decision_sha256,
        source_candidate_id=source_candidate_id,
        workflow_status=WORKFLOW_STATUS_READY if available else WORKFLOW_STATUS_BLOCKED,
        editorial_workflow_packet_available=available,
        edit_checklist=list(DEFAULT_EDIT_CHECKLIST),
        factual_review_queue=list(DEFAULT_FACTUAL_REVIEW_QUEUE),
        source_grounding_requirements=list(DEFAULT_SOURCE_GROUNDING_REQUIREMENTS),
        required_operator_actions=list(DEFAULT_REQUIRED_OPERATOR_ACTIONS),
        blockers=blockers,
        warnings=[] if available else ["editorial_workflow_blocked_pending_operator_repair"],
    )


def write_editorial_workflow_packet(packet: EditorialWorkflowPacket, output_dir: Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    packet_path = output_path / f"{packet.editorial_workflow_id}.json"
    packet_path.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 accepted review editorial workflow packet contract")
    parser.add_argument("decision_packet")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    decision_packet = load_review_decision_packet(Path(args.decision_packet))
    packet = make_editorial_workflow_packet(decision_packet)
    write_editorial_workflow_packet(packet, Path(args.output_dir))
    return 1 if packet.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())