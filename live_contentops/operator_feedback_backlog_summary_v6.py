"""Operator feedback backlog summary builder v6.

Deterministically groups operator-supplied feedback into local next-article
backlog candidates. No LLM/provider/API/network/browser/platform action.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

from live_contentops.operator_supplied_feedback_intake_v6 import (
    SAFETY_FLAGS,
    build_operator_supplied_feedback_intake_packet,
)

BACKLOG_TOPIC_MAP = {
    "free_cash_flow": {
        "candidate_id": "backlog_candidate_cash_flow_quality_explainer",
        "title": "Cash-flow quality explainer for audience follow-up",
        "rationale": "Multiple operator-supplied questions ask for plain-English cash-flow and revenue-quality context.",
        "article_angle": "Explain how cash conversion, revenue quality, and dividend coverage fit together without giving financial advice.",
    },
    "cash_conversion": {
        "candidate_id": "backlog_candidate_cash_flow_quality_explainer",
        "title": "Cash-flow quality explainer for audience follow-up",
        "rationale": "Multiple operator-supplied questions ask for plain-English cash-flow and revenue-quality context.",
        "article_angle": "Explain how cash conversion, revenue quality, and dividend coverage fit together without giving financial advice.",
    },
    "margin_quality": {
        "candidate_id": "backlog_candidate_margin_quality_checklist",
        "title": "Durable margin quality checklist",
        "rationale": "Operator-supplied LinkedIn feedback requested a checklist for separating durable margins from temporary cost actions.",
        "article_angle": "Create an educational checklist for margin durability signals and caveats.",
    },
    "faq": {
        "candidate_id": "backlog_candidate_manual_distribution_faq",
        "title": "Manual distribution feedback FAQ",
        "rationale": "Operator editorial note asks to consolidate recurring audience questions before the next draft.",
        "article_angle": "Turn recurring manual feedback into a review-only FAQ backlog candidate.",
    },
}


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _candidate_for_tag(tag: str) -> dict[str, str] | None:
    return BACKLOG_TOPIC_MAP.get(tag)


def build_operator_feedback_backlog_summary_packet(
    feedback_intake_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic backlog candidates from operator-supplied feedback only."""
    intake = feedback_intake_packet or build_operator_supplied_feedback_intake_packet()
    tag_counts: Counter[str] = Counter()
    candidate_sources: dict[str, set[str]] = {}
    candidates_by_id: dict[str, dict[str, Any]] = {}

    for item in intake["feedback_items"]:
        for tag in item.get("topic_tags", []):
            tag_counts[str(tag)] += 1
            mapped = _candidate_for_tag(str(tag))
            if not mapped:
                continue
            candidate_id = mapped["candidate_id"]
            candidates_by_id.setdefault(candidate_id, {
                **mapped,
                "source_feedback_item_ids": [],
                "source_platforms": [],
                "topic_tags": [],
                "priority_score": 0,
                "readiness_status": "ready_for_operator_review_only",
                "not_financial_advice": True,
            })
            candidate_sources.setdefault(candidate_id, set()).add(str(item["source_platform"]))
            candidates_by_id[candidate_id]["source_feedback_item_ids"].append(item["feedback_item_id"])
            candidates_by_id[candidate_id]["topic_tags"].extend(item.get("topic_tags", []))

    backlog_candidates: list[dict[str, Any]] = []
    for candidate_id, candidate in candidates_by_id.items():
        unique_tags = sorted(set(candidate["topic_tags"]))
        unique_items = sorted(set(candidate["source_feedback_item_ids"]))
        platforms = sorted(candidate_sources.get(candidate_id, set()))
        priority_score = len(unique_items) * 10 + len(platforms) * 5 + sum(tag_counts[tag] for tag in unique_tags)
        backlog_candidates.append({
            **candidate,
            "source_feedback_item_ids": unique_items,
            "source_platforms": platforms,
            "topic_tags": unique_tags,
            "priority_score": priority_score,
        })

    backlog_candidates.sort(key=lambda candidate: (-candidate["priority_score"], candidate["candidate_id"]))
    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "operator_feedback_backlog_summary_v0",
        "task_label": intake["task_label"],
        "feedback_intake_packet_id": intake["feedback_intake_packet_id"],
        "feedback_intake_hash": intake["exact_payload_hash"],
        "audit_index_packet_id": intake["audit_index_packet_id"],
        "audit_index_hash": intake["audit_index_hash"],
        "summary_method": "deterministic_tag_grouping_no_llm",
        "backlog_status": "ready_for_operator_review_only",
        "feedback_count": intake["feedback_count"],
        "candidate_count": len(backlog_candidates),
        "topic_counts": dict(sorted(tag_counts.items())),
        "backlog_candidates": backlog_candidates,
        "blocked_controls": ["approve", "dispatch", "publish", "schedule", "send"],
        "non_readiness_claims": {
            "live_readiness_claimed": False,
            "api_readiness_claimed": False,
            "llm_summary_claimed": False,
            "public_url_verification_claimed": False,
            "dispatch_readiness_claimed": False,
        },
        **SAFETY_FLAGS,
    }
    packet["exact_payload_hash"] = _stable_hash(packet)
    packet["backlog_summary_packet_id"] = f"operator_feedback_backlog_summary_{packet['exact_payload_hash'][:16]}"
    return packet


if __name__ == "__main__":
    print(json.dumps(build_operator_feedback_backlog_summary_packet(), indent=2, sort_keys=True))
