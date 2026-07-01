"""Feedback backlog to next article brief candidate builder v6.

Deterministically converts the committed operator feedback backlog summary into a
review-only next article brief candidate packet. No LLM/provider/API/network/
browser/platform action is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops.operator_supplied_feedback_intake_v6 import SAFETY_FLAGS

ROOT = Path(__file__).resolve().parents[1]
BACKLOG_PACKET = ROOT / "docs/automation/V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG/operator_feedback_backlog_summary_packet.json"

TASK_LABEL = "TASK_CONTENTOPS_V6_FEEDBACK_BACKLOG_REVIEW_TO_NEXT_ARTICLE_BRIEF_LOOP_V0"
BLOCKED_CONTROLS = ["approve", "dispatch", "publish", "schedule", "send"]
FORBIDDEN_BRIEF_WORDING = (
    "trade signal",
    "buy signal",
    "sell signal",
    "hold recommendation",
    "price target",
    "position sizing",
    "guaranteed return",
    "prediction guarantee",
)


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_backlog_summary() -> dict[str, Any]:
    return json.loads(BACKLOG_PACKET.read_text(encoding="utf-8"))


def _assert_safe_text(value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in FORBIDDEN_BRIEF_WORDING):
        raise ValueError("next article brief contains forbidden financial advice or signal wording")


def _select_primary_candidate(backlog_summary_packet: dict[str, Any]) -> dict[str, Any]:
    candidates = list(backlog_summary_packet.get("backlog_candidates", []))
    if not candidates:
        raise ValueError("backlog summary packet has no candidates to review")
    return sorted(candidates, key=lambda candidate: (-int(candidate["priority_score"]), str(candidate["candidate_id"])))[0]


def build_feedback_backlog_next_article_brief_packet(
    backlog_summary_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic review-only next article brief candidate packet."""
    backlog = backlog_summary_packet or _load_backlog_summary()
    selected_candidate = _select_primary_candidate(backlog)

    brief_title = f"Review-only brief candidate: {selected_candidate['title']}"
    working_headline = selected_candidate["title"]
    thesis = selected_candidate["article_angle"]
    _assert_safe_text(brief_title)
    _assert_safe_text(working_headline)
    _assert_safe_text(thesis)

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "feedback_backlog_next_article_brief_candidate_v0",
        "task_label": TASK_LABEL,
        "source_backlog_summary_packet_id": backlog["backlog_summary_packet_id"],
        "source_backlog_summary_hash": backlog["exact_payload_hash"],
        "source_feedback_intake_packet_id": backlog["feedback_intake_packet_id"],
        "source_feedback_intake_hash": backlog["feedback_intake_hash"],
        "source_audit_index_packet_id": backlog["audit_index_packet_id"],
        "source_audit_index_hash": backlog["audit_index_hash"],
        "selection_method": "deterministic_highest_priority_score_then_candidate_id",
        "candidate_review_status": "ready_for_operator_review_only",
        "selected_backlog_candidate_id": selected_candidate["candidate_id"],
        "selected_priority_score": selected_candidate["priority_score"],
        "selected_source_feedback_item_ids": selected_candidate["source_feedback_item_ids"],
        "selected_source_platforms": selected_candidate["source_platforms"],
        "selected_topic_tags": selected_candidate["topic_tags"],
        "brief_candidate": {
            "brief_id": f"next_article_brief_candidate_{selected_candidate['candidate_id']}",
            "brief_title": brief_title,
            "working_headline": working_headline,
            "editorial_angle": thesis,
            "audience_need": selected_candidate["rationale"],
            "suggested_outline": [
                "Restate the audience question in plain English.",
                "Define the key financial-quality concepts without advice wording.",
                "Show caveats operators should verify before drafting.",
                "Close with educational takeaways and human-review notes.",
            ],
            "required_operator_review_notes": [
                "Confirm the source feedback text is approved for editorial planning use.",
                "Attach a separate source pack before any canonical draft is requested.",
                "Keep all copy educational and non-advisory.",
            ],
            "not_financial_advice": True,
            "canonical_draft_requested": False,
            "publication_or_dispatch_requested": False,
        },
        "blocked_controls": BLOCKED_CONTROLS,
        "non_readiness_claims": {
            "live_readiness_claimed": False,
            "api_readiness_claimed": False,
            "llm_summary_claimed": False,
            "public_url_verification_claimed": False,
            "dispatch_readiness_claimed": False,
            "canonical_draft_readiness_claimed": False,
        },
        "operator_review_required": True,
        "source_pack_required_before_drafting": True,
        "canonical_draft_created": False,
        "forbidden_financial_advice_or_signal_wording_present": False,
        **SAFETY_FLAGS,
    }
    packet["exact_payload_hash"] = _stable_hash(packet)
    packet["next_article_brief_packet_id"] = f"feedback_backlog_next_article_brief_{packet['exact_payload_hash'][:16]}"
    return packet


if __name__ == "__main__":
    print(json.dumps(build_feedback_backlog_next_article_brief_packet(), indent=2, sort_keys=True))
