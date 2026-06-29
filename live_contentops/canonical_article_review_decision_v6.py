"""V6 canonical article review-candidate human review decision contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

INTAKE_TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_INTAKE_FROM_MARKDOWN_V0"
TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_REVIEW_CANDIDATE_HUMAN_REVIEW_DECISION_CONTRACT_V0"
SCHEMA_VERSION = "6.0.0"
REVIEW_STATUS = "REVIEW_CANDIDATE_PENDING_HUMAN_REVIEW"
ALLOWED_DECISIONS = {"accept_for_editorial_workflow", "reject", "defer"}
SECRET_MARKERS = ("token", "api_key", "password", "bearer", "cookie", "webhook_url", "private_key", "secret", "credential")
REDACTED_NOTES = "[REDACTED_SECRET_MARKER_DETECTED]"


@dataclass(frozen=True)
class ArticleReviewDecisionInput:
    candidate_packet: dict[str, Any]
    decision: str
    reviewer_id: str
    reviewed_at_manual: str
    review_notes: str = ""


@dataclass(frozen=True)
class ArticleReviewDecision:
    schema_version: str
    task_label: str
    decision_id: str
    source_candidate_id: str
    source_candidate_sha256: str
    decision: str
    reviewer_id: str
    reviewed_at_manual: str
    review_notes: str
    accepted_for_editorial_workflow: bool
    rejected: bool
    deferred: bool
    approved_canonical_article_available: bool = False
    human_review_required: bool = True
    publication_ready: bool = False
    dispatch_allowed: bool = False
    platform_variant_generation_allowed: bool = False
    outbox_creation_allowed: bool = False
    public_url: None = None
    public_metrics: None = None
    review_only: bool = True
    kill_switch_active: bool = True
    runtime_truth: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _has_secret_marker(value: Any) -> bool:
    lowered = _canonical_json(value).lower() if not isinstance(value, str) else value.lower()
    return any(marker in lowered for marker in SECRET_MARKERS)


def _redact_notes(notes: str) -> tuple[str, list[str]]:
    if _has_secret_marker(notes):
        return REDACTED_NOTES, ["review_notes_redacted_secret_marker_detected"]
    return notes, []


def load_review_candidate_packet(path: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("malformed_candidate_json") from exc


def _blocked_public_state(candidate: dict[str, Any]) -> list[str]:
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
        if candidate.get(field_name) is not False:
            blockers.append(f"candidate_{field_name}_not_false")
    for field_name in null_fields:
        if candidate.get(field_name) is not None:
            blockers.append(f"candidate_{field_name}_not_null")
    return blockers


def _candidate_validation_blockers(candidate: dict[str, Any], decision: str, reviewer_id: str, reviewed_at_manual: str) -> list[str]:
    blockers: list[str] = []
    if not isinstance(candidate, dict):
        return ["malformed_candidate_json"]
    if candidate.get("task_label") != INTAKE_TASK_LABEL:
        blockers.append("candidate_task_label_invalid")
    if candidate.get("candidate_status") != REVIEW_STATUS:
        blockers.append("candidate_status_not_pending_human_review")
    if candidate.get("canonical_article_review_candidate_available") is not True:
        blockers.append("candidate_not_available_for_review")
    if candidate.get("redaction_applied") is True:
        blockers.append("candidate_redaction_applied")
    if candidate.get("blockers"):
        blockers.append("candidate_has_blockers")
    blockers.extend(_blocked_public_state(candidate))
    if decision not in ALLOWED_DECISIONS:
        blockers.append("decision_invalid")
    if not reviewer_id:
        blockers.append("reviewer_id_missing")
    if not reviewed_at_manual:
        blockers.append("reviewed_at_manual_missing")
    fields_to_scan = {
        "body_markdown": candidate.get("body_markdown", ""),
        "body_text": candidate.get("body_text", ""),
        "detected_frontmatter": candidate.get("detected_frontmatter", {}),
        "title": candidate.get("title", ""),
        "subtitle": candidate.get("subtitle", ""),
        "description": candidate.get("description", ""),
    }
    if _has_secret_marker(fields_to_scan):
        blockers.append("candidate_secret_marker_detected")
    return sorted(set(blockers))


def make_review_decision(
    candidate_packet: dict[str, Any],
    decision: str,
    reviewer_id: str,
    reviewed_at_manual: str,
    review_notes: str = "",
) -> ArticleReviewDecision:
    blockers = _candidate_validation_blockers(candidate_packet, decision, reviewer_id, reviewed_at_manual)
    safe_notes, warnings = _redact_notes(review_notes)
    if safe_notes != review_notes:
        blockers.append("review_notes_secret_marker_detected")
    candidate_id = str(candidate_packet.get("candidate_id") or "")
    source_hash = hashlib.sha256(_canonical_json(candidate_packet).encode("utf-8")).hexdigest()
    source_file_hash = str(candidate_packet.get("source_file_sha256") or "")
    decision_material = {
        "source_candidate_id": candidate_id,
        "source_candidate_sha256": source_hash,
        "source_file_sha256": source_file_hash,
        "decision": decision,
        "reviewer_id": reviewer_id,
        "reviewed_at_manual": reviewed_at_manual,
        "review_notes": safe_notes,
        "blockers": sorted(set(blockers)),
    }
    decision_id = f"canonical_article_review_decision_{hashlib.sha256(_canonical_json(decision_material).encode('utf-8')).hexdigest()[:16]}"
    accepted = decision == "accept_for_editorial_workflow" and not blockers
    return ArticleReviewDecision(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        decision_id=decision_id,
        source_candidate_id=candidate_id,
        source_candidate_sha256=source_hash,
        decision=decision,
        reviewer_id=reviewer_id,
        reviewed_at_manual=reviewed_at_manual,
        review_notes=safe_notes,
        accepted_for_editorial_workflow=accepted,
        rejected=(decision == "reject" and not blockers),
        deferred=(decision == "defer" and not blockers),
        blockers=sorted(set(blockers)),
        warnings=warnings,
    )


def write_review_decision_packet(decision: ArticleReviewDecision, output_dir: Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    packet_path = output_path / f"{decision.decision_id}.json"
    packet_path.write_text(json.dumps(asdict(decision), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 canonical article review decision contract")
    parser.add_argument("candidate_packet")
    parser.add_argument("--decision", required=True, choices=sorted(ALLOWED_DECISIONS))
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--reviewed-at-manual", required=True)
    parser.add_argument("--review-notes", default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    candidate = load_review_candidate_packet(Path(args.candidate_packet))
    review_decision = make_review_decision(
        candidate,
        decision=args.decision,
        reviewer_id=args.reviewer_id,
        reviewed_at_manual=args.reviewed_at_manual,
        review_notes=args.review_notes,
    )
    write_review_decision_packet(review_decision, Path(args.output_dir))
    return 1 if review_decision.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
