"""Operator-supplied feedback intake packet builder v6.

Local/manual-only lane: operators copy audience feedback/questions/notes into
fixtures. No network, env, credential, browser, provider, LLM, platform API, or
live action is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_INDEX_PACKET = ROOT / "docs/automation/V6_MANUAL_DISTRIBUTION_EVIDENCE_REGISTRY/manual_distribution_registry_audit_index_packet.json"

SAFETY_FLAGS = {
    "network_call_made": False,
    "provider_call_made": False,
    "llm_provider_call_made": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "browser_session_used": False,
    "public_url_fetch_made": False,
    "platform_api_used": False,
    "live_publish_performed_by_contentops": False,
}

FORBIDDEN_FINANCIAL_WORDING = (
    "financial advice", "trade signal", "buy signal", "sell signal",
    "hold recommendation", "price target", "position sizing",
    "guaranteed return", "prediction guarantee",
)

SAMPLE_FEEDBACK_ITEMS = [
    {
        "feedback_item_id": "operator_feedback_substack_question_001",
        "source_platform": "substack",
        "source_kind": "question",
        "operator_supplied_text": "Reader asked for a plain-English follow-up on how dividend coverage connects to free cash flow quality.",
        "operator_supplied_timestamp": "2026-07-01T12:10:00Z",
        "source_url_text_optional": "operator-redacted-substack-comment-reference",
        "sentiment_label": "question",
        "topic_tags": ["dividend_coverage", "free_cash_flow", "reader_education"],
    },
    {
        "feedback_item_id": "operator_feedback_linkedin_comment_001",
        "source_platform": "linkedin",
        "source_kind": "comment",
        "operator_supplied_text": "Operator noted that LinkedIn commenters wanted a checklist for distinguishing durable margins from one-quarter cost cuts.",
        "operator_supplied_timestamp": "2026-07-01T12:14:00Z",
        "source_url_text_optional": "operator-redacted-linkedin-comment-reference",
        "sentiment_label": "feature_request",
        "topic_tags": ["margin_quality", "checklist", "operator_workflow"],
    },
    {
        "feedback_item_id": "operator_feedback_x_reply_001",
        "source_platform": "x",
        "source_kind": "reply",
        "operator_supplied_text": "Manual X reply note requested a short explainer on why revenue growth can look strong while cash conversion weakens.",
        "operator_supplied_timestamp": "2026-07-01T12:18:00Z",
        "source_url_text_optional": "operator-redacted-x-reply-reference",
        "sentiment_label": "question",
        "topic_tags": ["cash_conversion", "revenue_quality", "explainer"],
    },
    {
        "feedback_item_id": "operator_feedback_manual_note_001",
        "source_platform": "manual_note",
        "source_kind": "manual_note",
        "operator_supplied_text": "Editorial note: collect recurring audience questions into a review-only FAQ candidate before drafting the next article.",
        "operator_supplied_timestamp": "2026-07-01T12:20:00Z",
        "source_url_text_optional": "",
        "sentiment_label": "neutral",
        "topic_tags": ["faq", "backlog", "editorial_planning"],
    },
]


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_audit_index() -> dict[str, Any]:
    return json.loads(AUDIT_INDEX_PACKET.read_text(encoding="utf-8"))


def _url_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest() if value else ""


def _assert_safe_text(value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in FORBIDDEN_FINANCIAL_WORDING):
        raise ValueError("feedback packet contains forbidden financial advice or signal wording")


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    _assert_safe_text(str(item["operator_supplied_text"]))
    url_text = str(item.get("source_url_text_optional", ""))
    return {
        **item,
        "source_url_hash_optional": _url_hash(url_text),
        "source_url_network_verified": False,
        "source_scraped": False,
        "source_api_used": False,
        "operator_supplied_claim": True,
        "safety_flags": {
            "operator_supplied_only": True,
            "source_url_network_verified": False,
            "source_scraped": False,
            "source_api_used": False,
            "no_llm_provider_call": True,
        },
    }


def build_operator_supplied_feedback_intake_packet(feedback_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build a deterministic local feedback intake packet from operator text."""
    audit_index = _load_audit_index()
    normalized_items = [_normalize_item(item) for item in (feedback_items or SAMPLE_FEEDBACK_ITEMS)]
    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "operator_supplied_feedback_intake_v0",
        "task_label": "TASK_CONTENTOPS_V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG_LOOP_V0",
        "registry_packet_id": audit_index["registry_packet_id"],
        "registry_hash": audit_index["registry_hash"],
        "audit_index_packet_id": audit_index["audit_index_packet_id"],
        "audit_index_hash": audit_index["exact_payload_hash"],
        "accepted_manual_platforms": ["Substack", "LinkedIn", "X"],
        "intake_status": "operator_supplied_only",
        "feedback_items": normalized_items,
        "feedback_count": len(normalized_items),
        "forbidden_financial_advice_or_signal_wording_present": False,
        **SAFETY_FLAGS,
    }
    packet["exact_payload_hash"] = _stable_hash(packet)
    packet["feedback_intake_packet_id"] = f"operator_supplied_feedback_intake_{packet['exact_payload_hash'][:16]}"
    return packet


if __name__ == "__main__":
    print(json.dumps(build_operator_supplied_feedback_intake_packet(), indent=2, sort_keys=True))
