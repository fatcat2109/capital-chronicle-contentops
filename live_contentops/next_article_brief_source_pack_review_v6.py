"""Next article brief source pack and review packet builder v6.

Deterministically prepares a local source-pack checklist and operator review packet
from the accepted feedback-backlog next article brief candidate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops.operator_supplied_feedback_intake_v6 import SAFETY_FLAGS

ROOT = Path(__file__).resolve().parents[1]
BRIEF_PACKET = ROOT / "docs/automation/V6_FEEDBACK_BACKLOG_REVIEW_TO_NEXT_ARTICLE_BRIEF/feedback_backlog_next_article_brief_packet.json"

TASK_LABEL = "TASK_CONTENTOPS_V6_NEXT_ARTICLE_BRIEF_SOURCE_PACK_AND_REVIEW_WORKFLOW_V0"
FORBIDDEN_WORDING = (
    "buy", "sell", "hold", "price target", "position sizing",
    "guaranteed prediction", "signal-service", "trading instruction",
    "trade signal", "buy signal", "sell signal", "hold recommendation",
    "guaranteed return", "prediction guarantee",
)


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_brief_packet() -> dict[str, Any]:
    return json.loads(BRIEF_PACKET.read_text(encoding="utf-8"))


def _assert_safe_text(value: str) -> None:
    lowered = value.lower()
    for term in FORBIDDEN_WORDING:
        if term in lowered:
            raise ValueError(f"Packet contains forbidden wording or financial advice: {term}")


def build_next_article_brief_source_pack_review_packet(
    brief_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic next article brief source pack and review packet."""
    brief = brief_packet or _load_brief_packet()
    
    # Assert safety in the input brief
    headline = brief["brief_candidate"]["working_headline"]
    angle = brief["brief_candidate"]["editorial_angle"]
    
    _assert_safe_text(headline)
    _assert_safe_text(angle)

    checklist_items = [
        {
            "check_id": "primary_source_references_required",
            "label": "primary source references required",
            "status": "pending_operator_collection",
            "required_before_drafting": True,
            "evidence_path": None,
            "external_url": None,
            "network_verified": False,
            "operator_supplied_only": True,
        },
        {
            "check_id": "article_outline_evidence_required",
            "label": "article outline evidence required",
            "status": "pending_operator_collection",
            "required_before_drafting": True,
            "evidence_path": None,
            "external_url": None,
            "network_verified": False,
            "operator_supplied_only": True,
        },
        {
            "check_id": "definitions_caveats_required",
            "label": "definitions/caveats required",
            "status": "pending_operator_collection",
            "required_before_drafting": True,
            "evidence_path": None,
            "external_url": None,
            "network_verified": False,
            "operator_supplied_only": True,
        },
        {
            "check_id": "non_advisory_language_review_required",
            "label": "non-advisory language review required",
            "status": "pending_operator_collection",
            "required_before_drafting": True,
            "evidence_path": None,
            "external_url": None,
            "network_verified": False,
            "operator_supplied_only": True,
        },
        {
            "check_id": "final_operator_authorization_required",
            "label": "final operator authorization required",
            "status": "pending_operator_collection",
            "required_before_drafting": True,
            "evidence_path": None,
            "external_url": None,
            "network_verified": False,
            "operator_supplied_only": True,
        },
    ]

    review_questions = [
        "What primary sources support the explanation?",
        "What concepts need definitions?",
        "What risk/caveat language is required?",
        "What should be excluded to avoid advice/signal framing?",
    ]

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "next_article_brief_source_pack_review_v0",
        "task_label": TASK_LABEL,
        "source_next_article_brief_packet_id": brief["next_article_brief_packet_id"],
        "source_next_article_brief_packet_hash": brief["exact_payload_hash"],
        "selected_backlog_candidate_id": brief["selected_backlog_candidate_id"],
        "article_working_headline": headline,
        "source_pack_status": "source_pack_required_pending_operator_collection",
        "operator_review_status": "pending_operator_review",
        "ready_for_llm_drafting": False,
        "ready_for_canonical_draft": False,
        "ready_for_auto_publish": False,
        "ready_for_dispatch": False,
        "live_action_allowed": False,
        "source_pack_checklist": checklist_items,
        "review_questions": review_questions,
        **SAFETY_FLAGS,
        "enabled_publish_send_dispatch_approve_controls": False,
    }
    
    packet["exact_payload_hash"] = _stable_hash(packet)
    packet["source_pack_review_packet_id"] = f"next_article_brief_source_pack_review_{packet['exact_payload_hash'][:16]}"
    return packet


if __name__ == "__main__":
    print(json.dumps(build_next_article_brief_source_pack_review_packet(), indent=2, sort_keys=True))
